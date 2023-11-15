import importlib
import logging

from lexy.models import Document, Binding
from lexy.core.celery_tasks import celery, save_records_to_index
from lexy.indexes import index_manager


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def generate_tasks_for_document(doc: Document) -> list[dict]:
    """ Generate tasks for a document based on bindings and filters.

    Args:
        doc (Document): The document to generate tasks for

    Returns:
        list[dict]: A list of tasks that were created for the document
    """
    logger.info(f"Generating tasks for document {doc.document_id}")

    # initiate list of tasks
    tasks = []

    # loop through bindings for this document
    for binding in doc.collection.bindings:

        # check if binding is enabled
        if binding.status != 'on':
            logger.info(f"Skipping binding {binding} because it is not enabled (status: "
                        f"{binding.status})")
            continue

        # check if document matches binding filters
        if binding.filters and not all(f(doc) for f in binding.filters):
            logger.info(f"Skipping binding {binding} because document does not match filters")
            continue

        # import the transformer function
        # TODO: just import the function from celery?
        tfr_mod_name, tfr_func_name = binding.transformer.path.rsplit('.', 1)
        tfr_module = importlib.import_module(tfr_mod_name)
        transformer_func = getattr(tfr_module, tfr_func_name)

        # generate the task
        task = transformer_func.apply_async(
            args=[doc.content],
            kwargs=binding.transformer_params,
            link=save_records_to_index.s(document_id=doc.document_id,
                                         text=doc.content,
                                         index_id=binding.index_id)
        )
        tasks.append({"task_id": task.id, "document_id": doc.document_id})

    logger.info(f"Created {len(tasks)} tasks for document {doc.document_id}: "
                f"[{', '.join([t['task_id'] for t in tasks])}]")
    return tasks


# TODO: this should move to lexy.indexes.IndexManager
def create_new_index_table(index_id: str):
    """ Create a new index model and its associated table.

    This requires that the index row already exists in the database.

    Steps involved:
        1. Get the index object from the indexes table
        2. Create (or get) the corresponding index model
        2. Create associated index table in the database

    Args:
        index_id (str): The ID of the index to create
    """
    logger.info(f"Creating new index table for {index_id}")
    index = index_manager.get_index(index_id)
    if index_id in index_manager.index_models.keys():
        logger.info(f"Index model for '{index_id}' already exists")
        index_model = index_manager.index_models.get(index_id)
    else:
        index_model = index_manager.create_index_model(index)
    if index_manager.table_exists(index.index_table_name):
        logger.warning(f"lexy.core.events: Index table '{index.index_table_name}' already exists")
    logger.debug(f"index_model: {index_model}")
    index_model.metadata.create_all(index_manager.db.bind.engine)


async def process_new_binding(binding: Binding, create_index_table: bool = False) \
        -> tuple[Binding, list[dict]]:
    """ Process a new binding.

    Steps involved:
        1. Create index table if it doesn't exist
        2. Create tasks for all documents in the collection that match the binding filters
        3. Switch binding status to 'on'

    Args:
        binding: The binding to process
        create_index_table: whether to create the index table if it doesn't exist (default: False)

    Returns:
        tuple[Binding, list[dict]]: The binding and the tasks that were created
    """
    # TODO: update this function to potentially create the index object in the database if it doesn't exist. in this
    #  case, require a value for "lexy_index_fields"
    # TODO: if types are not specified, infer them from the transformer below using
    #  `transformer_func.__wrapped__.__annotations__.get('return')`

    logger.info(f"Processing new binding {binding}")

    # check if binding has a valid transformer
    if binding.transformer is None:
        raise Exception(f"Binding {binding} does not have a transformer associated with it")
    if binding.transformer.path is None:
        raise Exception(f"Binding {binding} does not have a valid transformer path associated with it")

    # import the transformer function
    # TODO: just import the function from celery?
    tfr_mod_name, tfr_func_name = binding.transformer.path.rsplit('.', 1)
    tfr_module = importlib.import_module(tfr_mod_name)
    transformer_func = getattr(tfr_module, tfr_func_name)

    # check if binding has a valid index
    if binding.index is None:
        logger.info(f"Binding {binding} does not have an index associated with it")
        # create index table
        if create_index_table:
            logger.info(f"Creating index table for binding {binding}")
            create_new_index_table(binding.index_id)
            # update binding
            binding.index = index_manager.get_index(binding.index_id)
        else:
            raise Exception(f"Binding {binding} does not have an index associated with it")

    # check that the binding has lexy_index_fields defined
    if "lexy_index_fields" not in binding.transformer_params.keys():
        logger.info(f"Binding {binding} does not have 'lexy_index_fields' defined in 'transformer_params'")
        if len(binding.index.index_fields) > 0:
            logger.info(f"Will assign them using 'index_fields' from index '{binding.index.index_id}'.")

            # it seems this next line is required because binding.transformer_params is a JSON field
            #   see https://github.com/sqlalchemy/sqlalchemy/discussions/6473
            binding.transformer_params = dict(binding.transformer_params)

            binding.transformer_params["lexy_index_fields"] = list(binding.index.index_fields.keys())
            logger.info(f"Updated binding.transformer_params: {binding.transformer_params}")
        else:
            raise Exception(f"Binding {binding} does not have 'lexy_index_fields' defined in 'transformer_params' "
                            f"and index '{binding.index.index_id}' does not have 'index_fields' defined. Either define "
                            f"'lexy_index_fields' in 'transformer_params' or define 'index_fields' for index "
                            f"'{binding.index.index_id}'.")

    # filter documents in the collection that match the binding filters
    if binding.filters:
        documents = [doc for doc in binding.collection.documents if all(f(doc) for f in binding.filters)]
    else:
        documents = binding.collection.documents

    # initiate list of tasks
    tasks = []

    # generate tasks for documents
    # TODO: should this be done as a celery group?
    for doc in documents:
        task = transformer_func.apply_async(
            args=[doc.content],
            kwargs=binding.transformer_params,
            link=save_records_to_index.s(document_id=doc.document_id,
                                         text=doc.content,
                                         index_id=binding.index_id)
        )
        tasks.append({"task_id": task.id, "document_id": doc.document_id})

    # switch binding status to 'on'
    prev_status = binding.status
    binding.status = 'on'
    logger.info(f"Set status for binding {binding}: from '{prev_status}' to 'on'")

    logger.info(f"Created {len(tasks)} tasks for binding {binding}: "
                f"[{', '.join([t['task_id'] for t in tasks])}]")

    return binding, tasks


def restart_celery_worker(workername: str) -> dict:
    """ Restart a celery worker.

    Args:
        workername: The hostname of the worker to restart

    Returns:
        dict: The response from the worker
    """
    logger.debug(f"Broadcasting signal 'pool_restart' to celery worker {workername}")
    response = celery.control.broadcast("pool_restart",
                                        arguments={
                                            "reload": True,
                                            "modules": [
                                                "lexy.indexes",
                                                "lexy.core.celery_tasks"
                                            ]
                                        },
                                        destination=[workername],
                                        reply=True,
                                        timeout=3)
    if response and "ok" in response[0][workername]:
        logger.info(f"Restarting '{workername}' worker's pool")
    else:
        logger.error(response)
        reason = error_reason(workername, response)
        logger.error(f"Failed to restart the '{workername}' pool: {reason}")
    return response


def error_reason(workername, response):
    """ Extracts error message from response. """
    for res in response:
        try:
            return res[workername].get("error", "Unknown reason")
        except KeyError:
            pass
    logger.error("Failed to extract error reason from '%s'", response)
    return "Unknown reason"
