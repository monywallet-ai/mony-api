from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import settings
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
            "database_session_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
    finally:
        database_logger.debug("database_session_closed")
        db.close()