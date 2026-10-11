import importlib
import os
from pathlib import Path

from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    os.environ["SIDECAR_DB_PATH"] = str(tmp_path / "sidecar.db")
    os.environ["SIDECAR_PIN"] = "1234"
    os.environ["SIDECAR_SECRET"] = "test-secret"
    os.environ["SIDECAR_UPLOAD_DIR"] = str(tmp_path / "uploads")
    os.environ["SIDECAR_PROXY_PREFIX"] = "/apps/sidecar"

    import app.db as db
    import app.security as security
    import app.main as main

    importlib.reload(db)
    importlib.reload(security)
    importlib.reload(main)
    return TestClient(main.app)


def test_proxy_login_scopes_secure_cookie_to_sidecar_mount(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post(
        "/api/login",
        json={"identity": "Gez", "pin": "1234"},
        headers={
            "x-forwarded-prefix": "/apps/sidecar",
            "x-forwarded-proto": "https",
        },
    )

    cookie = response.headers["set-cookie"]
    assert response.status_code == 200
    assert "sidecar_session=" in cookie
    assert "Path=/apps/sidecar/" in cookie
    assert "Secure" in cookie
    assert "HttpOnly" in cookie


def test_lan_login_retains_root_cookie_path(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post(
        "/api/login", json={"identity": "Tanya", "pin": "1234"}
    )

    cookie = response.headers["set-cookie"]
    assert response.status_code == 200
    assert "Path=/" in cookie
    assert "Path=/apps/sidecar/" not in cookie


def test_proxy_logout_deletes_cookie_at_the_same_mount(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post(
        "/api/logout",
        headers={"x-forwarded-prefix": "/apps/sidecar"},
    )

    cookie = response.headers["set-cookie"]
    assert response.status_code == 200
    assert "sidecar_session=" in cookie
    assert "Path=/apps/sidecar/" in cookie
    assert "Max-Age=0" in cookie
