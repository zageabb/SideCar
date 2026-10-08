from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, File, Form, HTTPException, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .db import connect, init_db
from .security import COOKIE_NAME, PIN, USERS, make_token, read_token

app = FastAPI(title="Sidecar", version="0.2.0")
init_db()

UPLOAD_DIR = Path(os.getenv("SIDECAR_UPLOAD_DIR", "/data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = int(os.getenv("SIDECAR_MAX_UPLOAD_BYTES", str(100 * 1024 * 1024)))


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


def row_to_message(row: Any, conn: Any | None = None) -> dict[str, Any]:
    message = {
        "id": row["id"],
        "sender": row["sender"],
        "body": row["body"],
        "created_at": row["created_at"],
        "client_message_id": row["client_message_id"],
        "attachments": [],
    }
    if conn is not None:
        attachments = conn.execute(
            "SELECT id, original_filename, mime_type, size_bytes "
            "FROM attachments WHERE message_id = ? ORDER BY created_at ASC",
            (row["id"],),
        ).fetchall()
        message["attachments"] = [
            {
                "id": item["id"],
                "original_filename": item["original_filename"],
                "mime_type": item["mime_type"],
                "size_bytes": item["size_bytes"],
                "download_url": f"/api/attachments/{item['id']}",
            }
            for item in attachments
        ]
    return message


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
    return [row_to_message(row, conn) for row in rows]


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
            return row_to_message(existing, conn)

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

    message["attachments"] = []
    await manager.broadcast({"type": "message.created", "message": message})
    return message


@app.post("/api/messages/with-files", status_code=201)
async def create_message_with_files(
    client_message_id: str = Form(...),
    body: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    sidecar_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    sender = require_user(sidecar_session)
    clean_body = body.strip()
    if not clean_body and not files:
        raise HTTPException(status_code=422, detail="Message needs text or at least one file")
    if len(client_message_id) > 100:
        raise HTTPException(status_code=422, detail="Client message ID is too long")

    with connect() as conn:
        existing = conn.execute(
            "SELECT id, sender, body, created_at, client_message_id "
            "FROM messages WHERE client_message_id = ?",
            (client_message_id,),
        ).fetchone()
        if existing:
            return row_to_message(existing, conn)

        message_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO messages(id, sender, body, created_at, client_message_id) VALUES (?, ?, ?, ?, ?)",
            (message_id, sender, clean_body, created_at, client_message_id),
        )

        saved_paths: list[Path] = []
        try:
            for upload in files:
                original = Path(upload.filename or "file").name
                suffix = Path(original).suffix[:20]
                stored_filename = f"{uuid.uuid4()}{suffix}"
                target = UPLOAD_DIR / stored_filename

                size = 0
                with target.open("wb") as handle:
                    while True:
                        chunk = await upload.read(1024 * 1024)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > MAX_UPLOAD_BYTES:
                            raise HTTPException(
                                status_code=413,
                                detail=f"{original} exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit",
                            )
                        handle.write(chunk)
                saved_paths.append(target)

                attachment_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO attachments(id, message_id, original_filename, stored_filename, mime_type, size_bytes, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        attachment_id,
                        message_id,
                        original,
                        stored_filename,
                        upload.content_type or "application/octet-stream",
                        size,
                        created_at,
                    ),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            for path in saved_paths:
                path.unlink(missing_ok=True)
            raise

        row = conn.execute(
            "SELECT id, sender, body, created_at, client_message_id FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()
        message = row_to_message(row, conn)

    await manager.broadcast({"type": "message.created", "message": message})
    return message


@app.get("/api/attachments/{attachment_id}")
def download_attachment(
    attachment_id: str, sidecar_session: str | None = Cookie(default=None)
) -> FileResponse:
    require_user(sidecar_session)
    with connect() as conn:
        row = conn.execute(
            "SELECT original_filename, stored_filename, mime_type FROM attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Attachment not found")

    path = UPLOAD_DIR / row["stored_filename"]
    if not path.exists() or path.parent.resolve() != UPLOAD_DIR.resolve():
        raise HTTPException(status_code=404, detail="Attachment file not found")

    return FileResponse(
        path,
        media_type=row["mime_type"],
        filename=row["original_filename"],
    )


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
