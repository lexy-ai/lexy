import logging
from typing import TYPE_CHECKING

from fastapi import Depends

from lexy.storage.client import get_s3_client
from lexy.core.config import settings
from lexy.models import Binding, Document
from lexy.schemas.filters import filter_documents
from lexy.core.celery_tasks import celery, save_records_to_index

if TYPE_CHECKING:
    import boto3


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def generate_tasks_for_document(doc: Document,
                                      s3_client: "boto3.client" = Depends(get_s3_client)) -> list[dict]:
    """ Generate tasks for a document based on bindings and filters.

    Args:
        doc (Document): The document for which to generate tasks
        s3_client (boto3.client): The S3 client to use for generating presigned object URLs

    Returns:
        list[dict]: A list of tasks that were created for the document
    """
    logger.debug(f"Generating tasks for document {doc.document_id}")

    # initiate list of tasks
    tasks = []

    # loop through bindings for this document
    for binding in doc.collection.bindings:

        # check if binding is enabled
        if binding.status != 'on':
            logger.debug(f"Skipping binding {binding} because it is not enabled (status: "
                         f"{binding.status})")
            continue

        # check if document matches binding filters
        if binding.filter and not binding.filter_obj.document_meets_conditions(doc):
            logger.debug(f"Skipping binding {binding} because document does not match filters")
            continue

        # generate the task
        # TODO: add a condition to check if the document has a storage url before running refresh_object_urls
        doc.refresh_object_urls(s3_client=s3_client)
        task_name = binding.transformer.celery_task_name
        task = celery.send_task(
            task_name,
            args=[doc],
            kwargs=binding.transformer_params,
            link=save_records_to_index.s(document_id=doc.document_id,
                                         text=doc.content,
                                         index_id=binding.index_id,
                                         binding_id=binding.binding_id)
        )

        tasks.append({"task_id": task.id, "document_id": doc.document_id})

    logger.debug(f"Created {len(tasks)} tasks for document {doc.document_id}: "
                 f"[{', '.join([t['task_id'] for t in tasks])}]")
    return tasks


# TODO: remove session arg and run async after update to SQLAlchemy 2.0
def process_new_binding(session,
                        binding: Binding,
                        s3_client: "boto3.client" = Depends(get_s3_client)) -> tuple[Binding, list[dict]]:
    """ Process a new binding.

    Steps involved:
        1. Infer values for "lexy_index_fields" if not specified
        2. Create tasks for all documents in the collection that match the binding filters
        3. Switch binding status to 'on'

    Args:
        binding (Binding): The binding to process
        s3_client (boto3.client): The S3 client to use for generating presigned object URLs

    Returns:
        tuple[Binding, list[dict]]: The binding and the tasks that were created

    Raises:
        ValueError:
            - If the binding does not have a transformer or an index associated with it
            - If the binding does not have `lexy_index_fields` defined in `binding.transformer_params` AND
                `binding.index.index_fields` is not defined

    """
    logger.info(f"Processing new {binding = }")

    # check if binding has a valid transformer
    if binding.transformer is None:
        raise ValueError(f"{binding = } does not have a transformer associated with it")

    # check if binding has a valid index
    if binding.index is None:
        raise ValueError(f"{binding = } does not have an index associated with it")

    # check that the binding has lexy_index_fields defined
    if "lexy_index_fields" not in binding.transformer_params.keys():
        logger.info(f"{binding = } does not have 'lexy_index_fields' defined in 'transformer_params'")
        if len(binding.index.index_fields) > 0:
            logger.info(f"Will assign them using 'index_fields' from index '{binding.index.index_id}'.")

            # it seems this next line is required because binding.transformer_params is a JSON field
            #   see https://github.com/sqlalchemy/sqlalchemy/discussions/6473
            binding.transformer_params = dict(binding.transformer_params)

            binding.transformer_params["lexy_index_fields"] = list(binding.index.index_fields.keys())
            logger.info(f"Updated binding.transformer_params: {binding.transformer_params}")
        else:
            raise ValueError(f"{binding = } does not have 'lexy_index_fields' defined in 'transformer_params' "
                             f"and index '{binding.index.index_id}' does not have 'index_fields' defined. Either "
                             f"define 'lexy_index_fields' in 'transformer_params' or define 'index_fields' for index "
                             f"'{binding.index.index_id}'.")

    # filter documents in the collection that match the binding filters
    if binding.filter:
        filter_obj = binding.filter_obj
        documents = filter_documents(binding.collection.documents, filter_obj)
    else:
        documents = binding.collection.documents

    # initiate list of tasks
    tasks = []

    # generate tasks for documents
    task_name = binding.transformer.celery_task_name
    for doc in documents:
        # TODO: add a condition to check if the document has a storage url before running refresh_object_urls
        doc.refresh_object_urls(s3_client=s3_client)
        task = celery.send_task(
            task_name,
            args=[doc],
            kwargs=binding.transformer_params,
            link=save_records_to_index.s(document_id=doc.document_id,
                                         text=doc.content,
                                         index_id=binding.index_id,
                                         binding_id=binding.binding_id)
        )
        tasks.append({"task_id": task.id, "document_id": doc.document_id})

    # switch binding status to 'on'
    prev_status = binding.status
    binding.status = 'on'
    logger.info(f"Set status for {binding = } - from '{prev_status}' to 'on'")

    logger.info(f"Created {len(tasks)} tasks for {binding = }: "
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

    reload_modules = [
        "lexy.indexes",
        "lexy.core.celery_tasks"
    ]
    transformer_modules = list(settings.worker_transformer_imports)
    reload_modules.extend(transformer_modules)
    print("reload_modules:", reload_modules)

    response = celery.control.broadcast("pool_restart",
                                        arguments={
                                            "reload": True,
                                            "modules": reload_modules
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
