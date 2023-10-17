import importlib
import logging

from lexy.models import Document, TransformerIndexBinding
from lexy.core.celery_tasks import save_result_to_index, save_records_to_index
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

    # loop through transformer bindings for this document
    for binding in doc.collection.transformer_index_bindings:

        # check if binding is enabled
        if binding.status != 'on':
            logger.info(f"Skipping transformer index binding {binding} because it is not enabled (status: "
                        f"{binding.status})")
            continue

        # check if document matches binding filters
        if binding.filters and not all(f(doc) for f in binding.filters):
            logger.info(f"Skipping transformer index binding {binding} because document does not match filters")
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
            link=save_result_to_index.s(document_id=doc.document_id,
                                        text=doc.content,
                                        index_id=binding.index_id)
        )
        tasks.append({"task_id": task.id, "document_id": doc.document_id})

    logger.info(f"Created {len(tasks)} tasks for document {doc.document_id}: "
                f"[{', '.join([t['task_id'] for t in tasks])}]")
    return tasks


# TODO: this should move to lexy.indexes.IndexManager
def create_new_index_table(index_id: str):
    """ Create a new index model and its associated table (requires that the index row already exists in the database).

    Steps involved:
        1. Create index model
        2. Create associated index table

    Args:
        index_id (str): The ID of the index to create

    """
    logger.info(f"Creating new index {index_id}")
    index = index_manager.get_index(index_id)
    if index_id in index_manager.index_models.keys():
        logger.info(f"Index model for '{index_id}' already exists")
        index_model = index_manager.index_models.get(index_id)
    else:
        index_model = index_manager.create_index_model(index)
    if index_manager.table_exists(index.index_table_name):
        logger.warning(f"Index table '{index.index_table_name}' already exists")
    index_model.metadata.create_all(index_manager.db.bind.engine)


async def process_new_binding(binding: TransformerIndexBinding, create_index_table: bool = False) \
        -> tuple[TransformerIndexBinding, list[dict]]:
    """ Process a new transformer index binding.

    Steps involved:
        1. Create index table if it doesn't exist
        2. Create tasks for all documents in the collection that match the binding filters
        3. Switch binding status to 'on'

    Args:
        binding: The binding to process
        create_index_table: whether to create the index table if it doesn't exist (default: False)

    Returns:
        tuple[TransformerIndexBinding, list[dict]]: The binding and the tasks that were created

    """
    logger.info(f"Processing new transformer index binding {binding}")

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
            create_new_index_table(binding.index_id)
            # update binding
            binding.index = index_manager.get_index(binding.index_id)
        else:
            raise Exception(f"Binding {binding} does not have an index associated with it")

    # create tasks for all documents in the collection that match the binding filters
    if binding.filters:
        documents = [doc for doc in binding.collection.documents if all(f(doc) for f in binding.filters)]
    else:
        documents = binding.collection.documents

    # initiate list of tasks
    tasks = []

    # generate tasks
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

