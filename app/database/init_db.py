from app.database.base import Base
from app.database.session import get_engine
from app.models import entities  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())

