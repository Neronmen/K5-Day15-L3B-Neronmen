import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="ms-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_DIR"] = f"{_tmp}/storage"
os.environ["JWT_SECRET"] = "test-secret-key-that-is-long-enough-for-hs256"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["TASK_BACKEND"] = "inline"
os.environ["DEMO_CLASS_ON_SIGNUP"] = "false"
os.environ["EMBEDDING_MODEL"] = "none"
# Khoá giả: test không bao giờ gọi API thật (xem fixture no_real_llm)
os.environ["DEEPSEEK_API_KEY"] = "test-key"
os.environ["MODEL_CHAT"] = "deepseek:deepseek-chat"
os.environ["MODEL_GRADING"] = "deepseek:deepseek-chat"
os.environ["MODEL_VISION"] = "gemini:gemini-2.5-flash"
os.environ["GEMINI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core import llm  # noqa: E402
from app.db import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def no_real_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("Test đã cố gọi API model thật")

    monkeypatch.setattr(llm, "_openai_client", boom)
    monkeypatch.setattr(llm, "_gemini_client", boom)


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


def register(client, email, role, name=None, password="matkhau123"):
    r = client.post("/auth/register", json={"email": email, "password": password, "name": name or email, "role": role})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
