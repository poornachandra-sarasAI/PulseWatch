"""Database engine and session factory for synchronous application code."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False)


def get_db():
    """Yield one database session for a FastAPI request or service operation."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
