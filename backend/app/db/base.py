"""SQLAlchemy declarative base shared by all database models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
