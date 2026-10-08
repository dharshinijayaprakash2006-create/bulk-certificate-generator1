import os
import tempfile
from pathlib import Path

# Must be set BEFORE the app is imported.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp).as_posix()}/test.db"
os.environ["OUTPUT_DIR"] = str(Path(_tmp) / "generated")

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c