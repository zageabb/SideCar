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


def test_file_upload_retry_is_idempotent(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/login", json={"identity": "Gez", "pin": "1234"})

    payload = {
        "data": {"body": "with attachment", "client_message_id": "retry-file-1"},
        "files": [("files", ("retry.txt", b"same file", "text/plain"))],
    }
    first = client.post("/api/messages/with-files", **payload)
    assert first.status_code == 201

    second = client.post("/api/messages/with-files", **payload)
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]
    assert len(second.json()["attachments"]) == 1

    history = client.get("/api/messages").json()
    matching = [m for m in history if m["client_message_id"] == "retry-file-1"]
    assert len(matching) == 1


def test_authenticated_websocket_receives_messages(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/login", json={"identity": "Gez", "pin": "1234"})

    with client.websocket_connect("/ws") as websocket:
        presence = websocket.receive_json()
        assert presence["type"] == "presence.changed"
        assert presence["identity"] == "Gez"
        assert presence["online"] is True

        response = client.post(
            "/api/messages",
            json={"body": "live message", "client_message_id": "ws-live-1"},
        )
        assert response.status_code == 201

        event = websocket.receive_json()
        assert event["type"] == "message.created"
        assert event["message"]["body"] == "live message"
        assert event["message"]["client_message_id"] == "ws-live-1"


def test_unauthenticated_websocket_is_rejected(tmp_path):
    client = make_client(tmp_path)
    try:
        with client.websocket_connect("/ws") as websocket:
            websocket.receive_text()
    except Exception:
        return
    raise AssertionError("Unauthenticated WebSocket connection should be rejected")


def test_message_history_survives_application_reload(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/login", json={"identity": "Gez", "pin": "1234"})
    created = client.post(
        "/api/messages",
        json={"body": "persist me", "client_message_id": "persist-1"},
    )
    assert created.status_code == 201

    reloaded = make_client(tmp_path)
    reloaded.post("/api/login", json={"identity": "Tanya", "pin": "1234"})
    history = reloaded.get("/api/messages")
    assert history.status_code == 200
    matches = [m for m in history.json() if m["client_message_id"] == "persist-1"]
    assert len(matches) == 1
    assert matches[0]["body"] == "persist me"


def test_attachment_history_survives_application_reload(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/login", json={"identity": "Gez", "pin": "1234"})

    created = client.post(
        "/api/messages/with-files",
        data={"body": "", "client_message_id": "persist-file-1"},
        files=[("files", ("persist.txt", b"durable attachment", "text/plain"))],
    )
    assert created.status_code == 201
    attachment_id = created.json()["attachments"][0]["id"]

    reloaded = make_client(tmp_path)
    reloaded.post("/api/login", json={"identity": "Tanya", "pin": "1234"})
    history = reloaded.get("/api/messages")
    assert history.status_code == 200
    matching = [m for m in history.json() if m["client_message_id"] == "persist-file-1"]
    assert len(matching) == 1
    assert matching[0]["attachments"][0]["id"] == attachment_id

    download = reloaded.get(matching[0]["attachments"][0]["download_url"])
    assert download.status_code == 200
    assert download.content == b"durable attachment"


def test_clear_chat_requires_authentication(tmp_path):
    client = make_client(tmp_path)
    assert client.delete("/api/messages").status_code == 401


def test_clear_chat_removes_messages_and_attachments(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/login", json={"identity": "Gez", "pin": "1234"})

    created = client.post(
        "/api/messages/with-files",
        data={"body": "temporary", "client_message_id": "clear-1"},
        files=[("files", ("clear-me.txt", b"delete me", "text/plain"))],
    )
    assert created.status_code == 201
    attachment = created.json()["attachments"][0]

    upload_dir = tmp_path / "uploads"
    stored_files = list(upload_dir.iterdir())
    assert len(stored_files) == 1

    cleared = client.delete("/api/messages")
    assert cleared.status_code == 200
    payload = cleared.json()
    assert payload["status"] == "ok"
    assert payload["deleted_attachments"] == 1
    assert payload["cleanup_failures"] == []

    assert client.get("/api/messages").json() == []
    assert not any(upload_dir.iterdir())
    assert client.get(attachment["download_url"]).status_code == 404


def test_clear_chat_broadcasts_to_connected_clients(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/login", json={"identity": "Tanya", "pin": "1234"})

    with client.websocket_connect("/ws") as websocket:
        presence = websocket.receive_json()
        assert presence["type"] == "presence.changed"

        cleared = client.delete("/api/messages")
        assert cleared.status_code == 200

        event = websocket.receive_json()
        assert event["type"] == "chat.cleared"
        assert event["cleared_by"] == "Tanya"
