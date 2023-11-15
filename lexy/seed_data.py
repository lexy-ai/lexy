import logging

from lexy.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    init_db(seed_data=True)


def main() -> None:
    logger.info("Creating initial seed data")
    init()
    logger.info("Initial seed data created")


if __name__ == "__main__":
    main()
