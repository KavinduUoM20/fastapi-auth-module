import logging
from fastapi import HTTPException
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    engine = create_engine(settings.DB_URL)
except Exception as e:
    logger.error(f"Failed to create database engine: {e}", exc_info=True)
    raise

def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating database tables: {e}", exc_info=True)
        raise

def get_db():
    session = Session(engine)
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database session error: {e}", exc_info=True)
        raise
    except Exception as e:
        # Check if it's an HTTPException (expected business logic exception)
        # HTTPExceptions don't need rollback as they're typically raised before DB changes
        if not isinstance(e, HTTPException):
            session.rollback()
            logger.error(f"Unexpected error in database session: {e}", exc_info=True)
        raise
    finally:
        session.close()
