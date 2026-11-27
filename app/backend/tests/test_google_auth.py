"""Đăng nhập Google: ID token được giả lập, không gọi Google thật."""
import pytest

from app.core.config import settings
from app.routers import auth
from tests.conftest import register


@pytest.fixture()
def google(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "test-client.apps.googleusercontent.com")
    tokens = {}

    def fake_verify(credential):
        if credential not in tokens:
            raise ValueError("bad token")
        return tokens[credential]

    monkeypatch.setattr(auth, "verify_google_token", fake_verify)

    def make(email, sub, verified=True, name="Người dùng Google"):
        cred = f"cred-{sub}-" + "x" * 20
        tokens[cred] = {"email": email, "sub": sub, "email_verified": verified, "name": name}
        return cred
    return make


def test_google_disabled_without_client_id(client):
    assert client.get("/auth/config").json() == {"google_client_id": None}
    assert client.post("/auth/google", json={"credential": "x" * 30}).status_code == 503


def test_new_google_user_needs_role_then_can_login(client, google):
    cred = google("co.lan@gmail.com", "g-1", name="Cô Lan")
    assert client.post("/auth/google", json={"credential": cred}).status_code == 404  # từ trang Đăng nhập
    r = client.post("/auth/google", json={"credential": cred, "role": "teacher"})
    assert r.status_code == 200 and r.json()["user"]["role"] == "teacher" and r.json()["user"]["name"] == "Cô Lan"
    again = client.post("/auth/google", json={"credential": cred})
    assert again.status_code == 200 and again.json()["user"]["id"] == r.json()["user"]["id"]
    assert client.post("/auth/login", json={"email": "co.lan@gmail.com", "password": "bat-ky-gi"}).json()["detail"] == \
        "Tài khoản này đăng nhập bằng Google"


def test_invalid_or_unverified_token_rejected(client, google):
    assert client.post("/auth/google", json={"credential": "gia-mao-" + "x" * 20, "role": "student"}).status_code == 401
    cred = google("chua@gmail.com", "g-2", verified=False)
    assert client.post("/auth/google", json={"credential": cred, "role": "student"}).status_code == 401


def test_invited_student_activates_with_google(client, google):
    t = register(client, "gv@x.vn", "teacher")
    c = client.post("/teacher/classes", json={"name": "Lớp A", "subject": "Toán"}, headers=t).json()
    client.post(f"/teacher/classes/{c['id']}/students", json={"emails": ["giabao@gmail.com"]}, headers=t)
    cred = google("giabao@gmail.com", "g-3", name="Trần Gia Bảo")
    assert client.post("/auth/google", json={"credential": cred, "role": "teacher"}).status_code == 409
    r = client.post("/auth/google", json={"credential": cred})
    assert r.status_code == 200 and r.json()["user"]["role"] == "student"
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert [x["id"] for x in client.get("/student/home", headers=h).json()["classes"]] == [c["id"]]
    members = client.get(f"/teacher/classes/{c['id']}", headers=t).json()["members"]
    assert members[0]["activated"] is True and members[0]["name"] == "Trần Gia Bảo"


def test_password_account_links_google(client, google):
    register(client, "hs@gmail.com", "student", name="HS")
    cred = google("hs@gmail.com", "g-4")
    r = client.post("/auth/google", json={"credential": cred})
    assert r.status_code == 200 and r.json()["user"]["name"] == "HS"
    other = google("hs@gmail.com", "g-khac")
    assert client.post("/auth/google", json={"credential": other}).status_code == 409
