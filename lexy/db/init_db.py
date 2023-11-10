import logging

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import close_all_sessions
from sqlmodel import SQLModel

from lexy.db.seed import sample_data
from lexy.db.session import sync_engine
from lexy import models  # noqa
# from lexy.indexes import IndexManager
# from lexy.indexes import index_manager


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

db = SyncSessionLocal()


def add_sample_data_to_db(session=db):
    # check if data already exists
    if session.query(models.Collection).count() > 0:
        logger.info("Collection data already exists")
    else:
        session.add(models.Collection(**sample_data["default_collection"]))
        session.add(models.Collection(**sample_data["code_collection"]))
        session.commit()
    if session.query(models.Document).count() > 0:
        logger.info("Document data already exists")
    else:
        session.add(models.Document(**sample_data["document_1"]))
        session.add(models.Document(**sample_data["document_2"]))
        session.add(models.Document(**sample_data["document_3"]))
        session.add(models.Document(**sample_data["document_4"]))
        session.add(models.Document(**sample_data["document_5"]))
        session.commit()
    if session.query(models.Transformer).count() > 0:
        logger.info("Transformer data already exists")
    else:
        session.add(models.Transformer(**sample_data["transformer_1"]))
        session.add(models.Transformer(**sample_data["transformer_2"]))
        session.commit()
    if session.query(models.Index).count() > 0:
        logger.info("Index data already exists")
    else:
        session.add(models.Index(**sample_data["index_1"]))
        session.commit()
    if session.query(models.TransformerIndexBinding).count() > 0:
        logger.info("TransformerIndexBinding data already exists")
    else:
        session.add(models.TransformerIndexBinding(**sample_data["binding_1"]))
        session.commit()


def init_db(session=db):
    logger.info("Initializing database")

    logger.info("Creating tables")
    SQLModel.metadata.create_all(sync_engine)

    logger.info("Adding sample data")
    # TODO: replace this with default data in step below
    add_sample_data_to_db(session)

    logger.info("Creating default indexes")
    # TODO: create default indexes - currently this is done in add_sample_data_to_db

    logger.info("Creating index models")
    # index_manager = IndexManager()
    # index_manager.create_index_models()
    SQLModel.metadata.create_all(sync_engine)

    logger.info("Finished initializing database")


def drop_tables(session=db, drop_all=True):
    """ Drop all tables in the database

    WARNING: This will drop all indexes and celery tables too!
    If you get an error, you'll need to initiate IndexManager first.

    Args:
        session: database session
        drop_all: drop all tables, including indexes and celery tables
    """
    logger.info("Dropping tables")
    session.commit()
    session.close_all()
    close_all_sessions()
    if drop_all:
        SQLModel.metadata.reflect(bind=session.bind)
    SQLModel.metadata.drop_all(sync_engine)
    logger.info("Dropped tables")


def reset_db(session=db, drop_all=True):
    logger.info("Resetting database")
    drop_tables(session, drop_all=drop_all)
    init_db(session)
    logger.info("Finished resetting database")

