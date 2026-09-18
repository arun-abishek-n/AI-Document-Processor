"""SQLAlchemy engine/session setup.

SQLite by default (see config.DATABASE_URL) — zero setup for a demo. The
same `Base`/`SessionLocal` work unchanged against a hosted Postgres URL if
DATABASE_URL is overridden, since nothing here is SQLite-specific.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

import config

# check_same_thread=False is only needed for SQLite: FastAPI may serve a
# request on a different thread than the one that opened the connection.
_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(config.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models here (not at module top-level) so every model class is
    # registered on Base.metadata before create_all runs, without creating
    # a circular import between database.py and models.py.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
