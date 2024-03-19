import logging

from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from lexy.db.session import sync_engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


def init() -> None:
    try:
        db = SyncSessionLocal()
        # Try to create session to check if DB is awake
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(e)
        raise e


def main() -> None:
    logger.info("Attempting to connect to database")
    init()
    logger.info("Connected to database")


if __name__ == "__main__":
    main()
