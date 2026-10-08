from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .db import connect, init_db
from .security import COOKIE_NAME, PIN, USERS, make_token, read_token

app = FastAPI(title="Sidecar", version="0.1.0")
init_db()


class LoginRequest(BaseModel):
    identity: str
    pin: str


class MessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    client_message_id: str = Field(min_length=1, max_length=100)


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for websocket in list(self.connections):
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)


manager = ConnectionManager()


def require_user(token: str | None) -> str:
    user = read_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def row_to_message(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "sender": row["sender"],
        "body": row["body"],
        "created_at": row["created_at"],
        "client_message_id": row["client_message_id"],
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/login")
def login(payload: LoginRequest, response: Response) -> dict[str, str]:
    if payload.identity not in USERS or payload.pin != PIN:
        raise HTTPException(status_code=401, detail="Invalid identity or PIN")
    response.set_cookie(
        COOKIE_NAME,
        make_token(payload.identity),
        httponly=True,
        samesite="strict",
        secure=os.getenv("SIDECAR_SECURE_COOKIE", "false").lower() == "true",
        max_age=60 * 60 * 24 * 30,
    )
    return {"identity": payload.identity}


@app.post("/api/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(COOKIE_NAME)
    return {"status": "ok"}


@app.get("/api/me")
def me(sidecar_session: str | None = Cookie(default=None)) -> dict[str, str]:
    return {"identity": require_user(sidecar_session)}


@app.get("/api/messages")
def messages(sidecar_session: str | None = Cookie(default=None)) -> list[dict[str, Any]]:
    require_user(sidecar_session)
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, sender, body, created_at, client_message_id "
            "FROM messages ORDER BY created_at ASC LIMIT 500"
        ).fetchall()
    return [row_to_message(row) for row in rows]


@app.post("/api/messages", status_code=201)
async def create_message(
    payload: MessageRequest, sidecar_session: str | None = Cookie(default=None)
) -> dict[str, Any]:
    sender = require_user(sidecar_session)
    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Message cannot be blank")

    with connect() as conn:
        existing = conn.execute(
            "SELECT id, sender, body, created_at, client_message_id "
            "FROM messages WHERE client_message_id = ?",
            (payload.client_message_id,),
        ).fetchone()
        if existing:
            return row_to_message(existing)

        message = {
            "id": str(uuid.uuid4()),
            "sender": sender,
            "body": body,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "client_message_id": payload.client_message_id,
        }
        conn.execute(
            "INSERT INTO messages(id, sender, body, created_at, client_message_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                message["id"],
                message["sender"],
                message["body"],
                message["created_at"],
                message["client_message_id"],
            ),
        )

    await manager.broadcast({"type": "message.created", "message": message})
    return message


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    identity = read_token(websocket.cookies.get(COOKIE_NAME))
    if not identity:
        await websocket.close(code=4401)
        return

    await manager.connect(websocket)
    await manager.broadcast({"type": "presence.changed", "identity": identity, "online": True})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(
            {"type": "presence.changed", "identity": identity, "online": False}
        )


STATIC_DIR = Path(os.getenv("SIDECAR_STATIC_DIR", "/app/static"))
if STATIC_DIR.exists():
    assets = STATIC_DIR / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}")
    def spa(path: str) -> FileResponse:
        candidate = STATIC_DIR / path
        if path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
