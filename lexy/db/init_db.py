import logging

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import close_all_sessions
from sqlmodel import SQLModel

from lexy.core.config import settings as app_settings
from lexy.db.sample_data import default_data, sample_docs
from lexy.db.session import sync_engine
from lexy import models  # noqa: make sure all models are imported before initializing DB


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
            c = session.query(models.Collection).filter(
                models.Collection.collection_name == b["collection_name"]
            ).first()
            if c:
                session.add(models.Binding(**b, collection_id=c.collection_id))
            else:
                logger.warning(f"Collection '{b['collection_name']}' not found for seed "
                               f"binding - skipping binding")
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
            c = session.query(models.Collection).filter(
                models.Collection.collection_name == doc["collection_name"]
            ).first()
            if c:
                session.add(models.Document(**doc, collection_id=c.collection_id))
                session.commit()
            else:
                logger.warning(f"Collection '{doc['collection_name']}' not found for sample "
                               f"document - skipping sample document")


def add_first_superuser_to_db(session=db, settings=app_settings):
    superuser = session.query(models.User).filter(models.User.email == settings.FIRST_SUPERUSER_EMAIL).first()
    if superuser:
        # issue a warning if superuser already exists in the database
        logger.warning("Superuser already exists - skipping superuser")
    else:
        # adding superuser
        session.add(models.User.create(
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD.get_secret_value(),
            is_superuser=True
        ))
        session.commit()


def init_db(session=db, seed_data=False):
    logger.info(f"Initializing database (seed_data={seed_data})")

    logger.info("Creating tables (SQLModel.metadata.create_all)")
    SQLModel.metadata.create_all(sync_engine)

    # TODO: add data via crud functions instead of directly adding to the session
    if seed_data is True:
        logger.info("Adding superuser")
        add_first_superuser_to_db(session)

        logger.info("Adding default seed data")
        add_default_data_to_db(session)

        logger.info("Adding sample documents")
        add_sample_docs_to_db(session)

    logger.info("Finished initializing database")


def drop_tables(session=db, drop_all=True, dry_run=True):
    """ Drop all tables in the database

    WARNING: This will drop all indexes and celery tables too!
    If you get an error, you'll need to initiate IndexManager first.

    Args:
        session: database session
        drop_all: drop all tables, including indexes and celery tables
        dry_run: whether to actually drop the tables
    """
    logger.debug("Running drop_tables")
    session.commit()
    session.close_all()
    close_all_sessions()
    if drop_all:
        SQLModel.metadata.reflect(bind=session.bind)
    db_table_names = ", ".join(SQLModel.metadata.tables.keys())
    logger.info(f"Dropping database tables..."
                f"\n\tengine.url: {sync_engine.url}"
                f"\n\tdb_table_names: {db_table_names}")
    if dry_run is False:
        SQLModel.metadata.drop_all(sync_engine)
        logger.info("Dropped tables")
    else:
        logger.info("Did not drop tables -- set `dry_run=False` to drop")


def reset_db(session=db, drop_all=True, dry_run=True):
    """ Reset the database

        WARNING: this may not work as expected - use the make target `drop-db-tables` instead
    """
    logger.info("Resetting database")
    drop_tables(session, drop_all=drop_all, dry_run=dry_run)
    init_db(session, seed_data=True)
    logger.info("Finished resetting database")
