import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient


def make_client(tmp_path: Path):
    os.environ["SIDECAR_DB_PATH"] = str(tmp_path / "sidecar.db")
    os.environ["SIDECAR_PIN"] = "1234"
    os.environ["SIDECAR_SECRET"] = "test-secret"

    import app.db as db
    import app.security as security
    import app.main as main

    importlib.reload(db)
    importlib.reload(security)
    importlib.reload(main)
    return TestClient(main.app)


def test_health(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/api/health").json() == {"status": "ok"}


def test_auth_and_persistent_message_history(tmp_path):
    client = make_client(tmp_path)

    assert client.get("/api/messages").status_code == 401
    assert client.post(
        "/api/login", json={"identity": "Gez", "pin": "bad"}
    ).status_code == 401

    login = client.post("/api/login", json={"identity": "Gez", "pin": "1234"})
    assert login.status_code == 200

    message = client.post(
        "/api/messages",
        json={"body": "Hello Tanya", "client_message_id": "client-1"},
    )
    assert message.status_code == 201
    assert message.json()["sender"] == "Gez"

    duplicate = client.post(
        "/api/messages",
        json={"body": "Hello Tanya", "client_message_id": "client-1"},
    )
    assert duplicate.json()["id"] == message.json()["id"]

    history = client.get("/api/messages")
    assert history.status_code == 200
    assert [m["body"] for m in history.json()] == ["Hello Tanya"]
