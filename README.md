# Sidecar

Sidecar is a private two-person web chat and quick handoff tool for Gez and Tanya.

The current test build supports:
- Gez/Tanya identity selection
- private PIN access
- persistent SQLite message history
- live WebSocket delivery
- reconnect status
- copy button on text
- secure persistent file attachments
- file-only and text+file messages
- multi-file upload
- drag/drop from Finder/Explorer
- pasted screenshots and browser-exposed clipboard files
- inline image previews
- authenticated downloads
- Docker deployment

The default upload limit is 100 MB per file and can be changed with `SIDECAR_MAX_UPLOAD_BYTES`.

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

For file transfer, drag one or more files anywhere over the Sidecar window, use the **+** button, or paste a screenshot into the message box. A file can be sent without any text.

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

Clipboard-file paste support depends on what the browser and operating system expose. Screenshot/image paste is expected to work broadly; Finder/Explorer copied-file paste may vary, so drag/drop and the **+** file picker remain supported fallbacks.


## Production deployment

See `docs/DEPLOYMENT.md` for HTTPS/reverse-proxy setup, persistent storage, backup/restore, and the deployment upgrade checklist.
