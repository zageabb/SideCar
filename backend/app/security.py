from __future__ import annotations

import base64
import hashlib
import hmac
import os

SECRET = os.getenv("SIDECAR_SECRET", "change-me-in-production").encode("utf-8")
PIN = os.getenv("SIDECAR_PIN", "sidecar")
COOKIE_NAME = "sidecar_session"
USERS = {"Gez", "Tanya"}


def make_token(identity: str) -> str:
    if identity not in USERS:
        raise ValueError("invalid identity")
    sig = hmac.new(SECRET, identity.encode("utf-8"), hashlib.sha256).hexdigest()
    raw = f"{identity}|{sig}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def read_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        identity, sig = raw.split("|", 1)
    except Exception:
        return None
    if identity not in USERS:
        return None
    expected = hmac.new(SECRET, identity.encode("utf-8"), hashlib.sha256).hexdigest()
    return identity if hmac.compare_digest(sig, expected) else None
