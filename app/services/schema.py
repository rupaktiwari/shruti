from sqlalchemy import inspect, text

from app.core.logging_config import get_logger
from app.db.postgres import Base, engine

logger = get_logger(__name__)


def prepare_database() -> None:
    """Create tables. Drop the old hotel tables if this database still has them.

    Reservations and documents-without-a-notebook belong to the concierge
    version. Those rows cannot be mapped onto Smriti notebooks, so they are
    removed once, on startup, before the new tables are created.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        if "reservations" in tables:
            logger.info("Dropping leftover reservations table")
            connection.execute(text("DROP TABLE IF EXISTS reservations CASCADE"))
        if "documents" in tables:
            columns = {column["name"] for column in inspector.get_columns("documents")}
            if "notebook_id" not in columns:
                logger.info("Replacing documents table that had no notebook")
                connection.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
    Base.metadata.create_all(bind=engine)
