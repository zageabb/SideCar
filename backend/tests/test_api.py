import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient


def make_client(tmp_path: Path):
    os.environ["SIDECAR_DB_PATH"] = str(tmp_path / "sidecar.db")
    os.environ["SIDECAR_PIN"] = "1234"
    os.environ["SIDECAR_SECRET"] = "test-secret"
    os.environ["SIDECAR_UPLOAD_DIR"] = str(tmp_path / "uploads")
    os.environ["SIDECAR_MAX_UPLOAD_BYTES"] = "1048576"

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


def test_file_upload_and_download(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/login", json={"identity": "Gez", "pin": "1234"})

    response = client.post(
        "/api/messages/with-files",
        data={"body": "", "client_message_id": "file-client-1"},
        files=[("files", ("example.txt", b"hello from sidecar", "text/plain"))],
    )
    assert response.status_code == 201
    message = response.json()
    assert message["body"] == ""
    assert len(message["attachments"]) == 1
    attachment = message["attachments"][0]
    assert attachment["original_filename"] == "example.txt"
    assert attachment["size_bytes"] == len(b"hello from sidecar")

    download = client.get(attachment["download_url"])
    assert download.status_code == 200
    assert download.content == b"hello from sidecar"

    client.post("/api/logout")
    assert client.get(attachment["download_url"]).status_code == 401


def test_upload_size_limit(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/login", json={"identity": "Tanya", "pin": "1234"})

    response = client.post(
        "/api/messages/with-files",
        data={"body": "", "client_message_id": "file-client-2"},
        files=[("files", ("too-big.bin", b"x" * (1024 * 1024 + 1), "application/octet-stream"))],
    )
    assert response.status_code == 413
