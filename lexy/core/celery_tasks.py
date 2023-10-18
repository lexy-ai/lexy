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

from celery import current_app as celery, Task
from celery.utils.log import get_logger, get_task_logger
from sqlalchemy.orm import sessionmaker

from lexy.db.session import sync_engine
from lexy.indexes import index_manager
# from lexy.indexes import IndexManager
# from lexy.models.embedding import Embedding


logger = get_logger(__name__)
task_logger = get_task_logger(__name__)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


# index_mgr = IndexManager()
# index_mgr.create_index_models()


class DatabaseTask(Task):
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SyncSessionLocal()
        return self._db

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


# @celery.task(base=DatabaseTask, bind=True, name="lexy.db.save_embedding")
# def save_embedding_to_db(self, res, document_id, text):
#     task_logger.debug(f"Starting DB task 'save_embedding' for {self.request.id} with parent {self.request.parent_id}")
#     self.db.add(
#         Embedding(document_id=document_id, embedding=res.tolist(), text=text, task_id=self.request.parent_id)
#     )
#     self.db.commit()


@celery.task(base=DatabaseTask, bind=True, name="lexy.db.save_result_to_index")
def save_result_to_index(self, res, document_id, text, index_id):
    """ Save the result of a transformer to an index. """
    task_logger.debug(f"Starting DB task 'save_result_to_index' for index {index_id} "
                      f"with task ID {self.request.id} and parent task ID {self.request.parent_id}")
    # noinspection PyPep8Naming
    IndexClass = index_manager.index_models[index_id]
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
    # noinspection PyPep8Naming
    IndexClass = index_manager.index_models[index_id]
    for record in records:
        self.db.add(
            IndexClass(document_id=document_id, text=text, task_id=self.request.parent_id, **record)
        )
    self.db.commit()
