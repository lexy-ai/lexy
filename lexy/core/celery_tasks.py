"""
Celery tasks for lexy storage.

Sources:
    - Task instantiation:
        - https://stackoverflow.com/a/17224993
        - https://docs.celeryq.dev/en/latest/userguide/tasks.html#instantiation
    - Extending the storage backend:
        - https://stackoverflow.com/questions/60281347/is-it-possible-to-extend-celery-so-results-would-be-store-to-several-mongodb-co
        - https://docs.celeryq.dev/en/stable/userguide/configuration.html#override-backends
"""
from typing import Any
from uuid import UUID

import numpy as np
import torch
from celery import current_app as celery, Task
from celery.utils.log import get_logger, get_task_logger
from sqlalchemy.orm import sessionmaker

from lexy.api.deps import index_manager
from lexy.db.session import sync_engine


logger = get_logger(__name__)
task_logger = get_task_logger(__name__)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


class DatabaseTask(Task):
    _db = None
    _index_manager = index_manager

    @property
    def db(self):
        if self._db is None:
            self._db = SyncSessionLocal()
        return self._db

    @property
    def index_manager(self):
        if self._index_manager is None:
            task_logger.debug("_index_manager is None - reloading and assigning index manager")
            self._index_manager = index_manager
            task_logger.debug(f"Assigned index manager with index models: {self._index_manager.index_models}")
        if self._index_manager.index_models == {}:
            task_logger.debug("index_manager.index_models is empty - running index_manager.create_index_models()")
            self._index_manager.create_index_models()
            task_logger.debug(f"index_manager.index_models: {self._index_manager.index_models}")
        return self._index_manager

    def restart_worker(self, msg):
        """ Restart the celery worker of the current task. """
        task_logger.info(f"Called restart_worker with message: {msg}")
        task_logger.debug("---------------- prior to restart ----------------")
        self.print_index_manager_models()
        task_logger.debug(f"Broadcasting signal 'pool_restart' to celery worker {self.request.hostname}")
        response = self.app.control.broadcast("pool_restart",
                                              arguments={
                                                  "reload": True,
                                                  "modules": [
                                                      "lexy.api.deps",
                                                      "lexy.core.celery_tasks"
                                                  ]
                                              },
                                              destination=[self.request.hostname],
                                              reply=True,
                                              timeout=3)
        self.reset_index_manager()
        task_logger.debug("---------------- after restart ----------------")
        self.print_index_manager_models()
        return response

    def reset_index_manager(self):
        task_logger.debug('resetting index manager')
        self._index_manager = None

    def print_index_manager_models(self):
        sorted_models = sorted(self.index_manager.index_models.items(), key=lambda x: x[0])
        print(f"index_manager.index_models:\n", "\n".join([f"{k}: {v}" for k, v in sorted_models]))


def convert_arrays_to_lists(obj):
    """ Convert numpy arrays and PyTorch tensors to lists in a dictionary or list of dictionaries.

    Args:
        obj: dictionary or list of dictionaries to convert

    Returns:
        Same type as obj: dictionary or list of dictionaries with numpy arrays and PyTorch tensors converted to lists

    Examples:
        >>> convert_arrays_to_lists({"a": np.array([1, 2, 3]), "b": {"c": torch.tensor([4, 5, 6])}})
        {'a': [1, 2, 3], 'b': {'c': [4, 5, 6]}}

        >>> convert_arrays_to_lists([{"a": torch.tensor([1, 2, 3])}, {"b": np.array([4, 5, 6])}])
        [{'a': [1, 2, 3]}, {'b': [4, 5, 6]}]
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (np.ndarray, torch.Tensor)):
                obj[key] = value.tolist()
            elif isinstance(value, (dict, list)):
                obj[key] = convert_arrays_to_lists(value)
    elif isinstance(obj, list):
        return [convert_arrays_to_lists(item) for item in obj]
    return obj


@celery.task(base=DatabaseTask, bind=True, name="lexy.db.save_result_to_index")
def save_result_to_index(self, res, document_id, text, index_id):
    """ Save the result of a transformer to an index. """
    task_logger.debug(f"Starting DB task 'save_result_to_index' for index {index_id} "
                      f"with task ID {self.request.id} and parent task ID {self.request.parent_id}")

    try:
        # noinspection PyPep8Naming
        IndexClass = self.index_manager.index_models[index_id]
    except KeyError:
        print(f"index model for {index_id} doesn't exist - will attempt to refresh index manager")
        self.reset_index_manager()
        # noinspection PyPep8Naming
        IndexClass = self.index_manager.index_models[index_id]

    self.db.add(
        # TODO: IndexClass needs to use kwargs from `index_fields`
        IndexClass(document_id=document_id, embedding=res.tolist(), text=text, task_id=self.request.parent_id)
    )
    try:
        self.db.commit()
    except Exception as e:
        self.db.rollback()
        raise e


@celery.task(base=DatabaseTask, bind=True, name="lexy.db.save_records_to_index")
def save_records_to_index(self,
                          records: list[dict[str, Any]],
                          document_id: UUID,
                          text: str,
                          index_id: str,
                          binding_id: int = None):
    """ Save the output of a transformer to an index. """
    task_logger.debug(f"Starting DB task 'save_records_to_index' for index {index_id} "
                      f"with task ID {self.request.id} and parent task ID {self.request.parent_id}")

    try:
        # noinspection PyPep8Naming
        IndexClass = self.index_manager.index_models[index_id]
    except KeyError:
        task_logger.warning(f"index model for {index_id} doesn't exist - will attempt to refresh index manager")
        self.reset_index_manager()
        # noinspection PyPep8Naming
        IndexClass = self.index_manager.index_models[index_id]

    for record in records:
        record = convert_arrays_to_lists(record)
        self.db.add(
            IndexClass(
                document_id=document_id,
                text=text,
                task_id=self.request.parent_id,
                binding_id=binding_id,
                **record
            )
        )
    try:
        self.db.commit()
    except Exception as e:
        self.db.rollback()
        raise e


@celery.task(base=DatabaseTask, bind=True, name="lexy.db.restart_db_worker")
def restart_db_worker(self, msg):
    """ Restart the celery worker of the current task. """
    response = self.restart_worker(msg=msg)
    task_logger.info(f"restart_db_worker response: {response}")
    return response
