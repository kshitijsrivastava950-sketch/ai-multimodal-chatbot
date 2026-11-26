import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    """
    Attempts to connect to MySQL database first.
    If MySQL is unavailable or credentials fail, falls back gracefully to SQLite.
    """
    mysql_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
    )
    
    try:
        engine = create_engine(
            mysql_url,
            pool_recycle=3600,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3}
        )
        with engine.connect():
            logger.info("Successfully connected to MySQL database.")
            return engine
    except Exception as e:
        logger.warning(
            f"MySQL connection to {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB} "
            f"failed ({e}). Falling back to local SQLite database."
        )
        sqlite_path = Path(settings.SQLITE_DB_PATH)
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_url = f"sqlite:///{sqlite_path}"
        engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False}
        )
        logger.info(f"Using SQLite database at {sqlite_path}")
        return engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
