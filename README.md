# Sidecar

Sidecar is a private two-person web chat and quick handoff tool for Gez and Tanya.

The first test build already supports:
- Gez/Tanya identity selection
- private PIN access
- persistent SQLite message history
- live WebSocket delivery
- reconnect status
- copy button on received/sent text
- Docker deployment

File transfer, drag/drop and clipboard attachments are the next development slice.

## Quick test with Docker

```bash
git pull
cp .env.example .env
# edit SIDECAR_PIN and SIDECAR_SECRET if desired
docker compose up --build
```

Open:

```text
http://<server-ip>:8088
```

Default development PIN if you do not create an `.env` file:

```text
sidecar
```

For a real/private deployment, change the PIN and secret.

To test two-person chat, open Sidecar in two browsers or two devices. Log one in as Gez and one as Tanya, using the same PIN. Messages should appear live on both and remain after refresh/restart.

## Local development

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export PYTHONPATH=backend
export SIDECAR_DB_PATH=./data/sidecar.db
export SIDECAR_PIN=sidecar
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`.

## Validation

```bash
PYTHONPATH=backend pytest -q backend/tests
cd frontend && npm install && npm run build
docker build -t sidecar:test .
```

## Current limitation

This is the **first test build**, focused on proving the chat/persistence path. Attachment transfer, Finder/Explorer drag/drop and clipboard image/file handling remain planned in `DEVELOPMENT.md`.
