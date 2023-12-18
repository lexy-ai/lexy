import logging

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import close_all_sessions
from sqlmodel import SQLModel

from lexy.db.sample_data import default_data, sample_docs
from lexy.db.session import sync_engine
from lexy import models  # noqa


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

db = SyncSessionLocal()


def add_default_data_to_db(session=db):
    # issue a warning if default seed data already exists in the database

    logger.info("Adding default collections")
    if session.query(models.Collection).count() > 0:
        logger.warning("Collection data already exists - skipping collection data")
    else:
        for c in default_data["collections"]:
            session.add(models.Collection(**c))
        session.commit()

    logger.info("Adding default transformers")
    if session.query(models.Transformer).count() > 0:
        logger.warning("Transformer data already exists - skipping transformer data")
    else:
        for t in default_data["transformers"]:
            session.add(models.Transformer(**t))
        session.commit()

    logger.info("Adding default indexes")
    if session.query(models.Index).count() > 0:
        logger.warning("Index data already exists - skipping index data")
    else:
        for i in default_data["indexes"]:
            session.add(models.Index(**i))
        session.commit()

    logger.info("Adding default bindings")
    if session.query(models.Binding).count() > 0:
        logger.warning("Binding data already exists - skipping binding data")
    else:
        for b in default_data["bindings"]:
            session.add(models.Binding(**b))
        session.commit()


def add_sample_docs_to_db(session=db):
    # issue a warning if sample documents already exist in the database
    logger.info("Adding sample documents")
    if session.query(models.Document).count() > 0:
        logger.warning("Sample documents already exist - skipping sample documents")
    else:
        # adding sample documents for code collection only - will add sample documents for default collection once
        # the default index and binding are created through appropriate crud endpoints
        for doc in sample_docs["code_collection_sample_docs"]:
            session.add(models.Document(**doc))
        session.commit()


def init_db(session=db, seed_data=False):
    logger.info("Initializing database")

    logger.info("Creating tables")
    SQLModel.metadata.create_all(sync_engine)

    # TODO: add data via crud functions instead of directly adding to the session
    if seed_data is True:
        logger.info("Adding default seed data")
        add_default_data_to_db(session)

        logger.info("Adding sample documents")
        add_sample_docs_to_db(session)

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
    init_db(session, seed_data=True)
    logger.info("Finished resetting database")

