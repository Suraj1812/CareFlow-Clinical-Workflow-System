from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _sqlite_connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def configure_database(database_url: str) -> None:
    global engine, SessionLocal
    engine = create_engine(
        database_url,
        connect_args=_sqlite_connect_args(database_url),
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_engine() -> Engine:
    if engine is None:
        raise RuntimeError("Database has not been configured")
    return engine


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Database has not been configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

