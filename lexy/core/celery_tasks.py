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
import importlib
from typing import Any
from uuid import UUID

import numpy as np
from celery import current_app as celery, Task
from celery.utils.log import get_logger, get_task_logger
from sqlalchemy.orm import sessionmaker

import lexy.indexes
from lexy.db.session import sync_engine


logger = get_logger(__name__)
task_logger = get_task_logger(__name__)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


class DatabaseTask(Task):
    _db = None
    _index_manager = lexy.indexes.index_manager

    @property
    def db(self):
        if self._db is None:
            self._db = SyncSessionLocal()
        return self._db

    @property
    def index_manager(self):
        if self._index_manager is None:
            task_logger.debug("_index_manager is None - reloading and assigning index manager")
            importlib.reload(lexy.indexes)
            self._index_manager = lexy.indexes.index_manager
            task_logger.debug(f"Assigned index manager with index models: {self._index_manager.index_models}")
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
                                                      "lexy.indexes",
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

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # if task fails because the table doesn't exist, refresh the db connection and try again
        # FIXME: this isn't working. to reproduce, drop a table and run a task that saves to it
        if "relation" in str(exc):
            # example of error:
            #   ProgrammingError('(psycopg2.errors.UndefinedTable) relation "index__default_text_embeddings_v6" does
            #   not exist'
            task_logger.info(f"Task {task_id} failed because the table doesn't exist. Refreshing the db connection "
                             f"and trying again.")
            self.db.rollback()
            self.db.close()
            self._db = None
            # self.db()
            # self.run(*args, **kwargs)
            self.retry(*args, **kwargs, exc=exc, throw=False, countdown=1)
        else:
            super().on_failure(exc, task_id, args, kwargs, einfo)


def convert_arrays_to_lists(d: dict) -> dict:
    """ Convert numpy arrays to lists in a dictionary.

    Args:
        d: dictionary to convert

    Returns:
        dict: dictionary with numpy arrays converted to lists

    Examples:
        >>> convert_arrays_to_lists({"a": np.array([1, 2, 3]), "b": {"c": np.array([4, 5, 6])}})
        {'a': [1, 2, 3], 'b': {'c': [4, 5, 6]}}

    """
    for key, value in d.items():
        if isinstance(value, np.ndarray):
            d[key] = value.tolist()
        elif isinstance(value, dict):
            d[key] = convert_arrays_to_lists(value)
    return d


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
    self.db.commit()


@celery.task(base=DatabaseTask, bind=True, name="lexy.db.save_records_to_index")
def save_records_to_index(self, records: list[dict[str, Any]], document_id: UUID, text: str, index_id: str):
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
            IndexClass(document_id=document_id, text=text, task_id=self.request.parent_id, **record)
        )

    self.db.commit()


@celery.task(base=DatabaseTask, bind=True, name="lexy.db.restart_db_worker")
def restart_db_worker(self, msg):
    """ Restart the celery worker of the current task. """
    response = self.restart_worker(msg=msg)
    task_logger.info(f"restart_db_worker response: {response}")
    return response
