from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings
from app.core.logging import database_logger

# Create the database engine
engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        database_logger.debug("database_session_created")
        yield db
    except Exception as e:
        database_logger.error(
            "database_session_error", error=str(e), error_type=type(e).__name__
        )
        raise
    finally:
        database_logger.debug("database_session_closed")
        db.close()


def health_check_database() -> bool:
    """
    Check if database is healthy and responsive.

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            database_logger.debug("database_health_check_passed")
            return True
        finally:
            db.close()
    except Exception as e:
        database_logger.error("database_health_check_failed", error=str(e))
        return False
