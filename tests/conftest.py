import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "careflow-test.db"
    app = create_app(Settings(database_url=f"sqlite:///{db_path}", log_level="CRITICAL"))
    with TestClient(app) as test_client:
        yield test_client

