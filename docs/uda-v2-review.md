# UDA V2 review — Sidecar (DEV-020)

**Review-only container candidate. No production Docker or data changes.**

Source inspected: `README.md`, `Dockerfile` and `docker-compose.yml`.
The Dockerfile has Node 22 frontend and Python 3.12 API stages; it publishes
the frontend bundle under `/app/static` and runs Uvicorn on internal port
8000. Compose publishes 8088:8000 and exposes `/api/health`.

Persistence: named Compose volume `sidecar-data` mounted at `/data`, holding
SQLite `sidecar.db` and `uploads/`. **The real Docker volume may be
project-prefixed**: never create, rename, overwrite or delete a volume based
only on this manifest. Inspect exact live volume ID, mount owner, SQLite
journal/WAL, backups, and restore procedure first.

Credentials: the **draft Compose file now requires explicit**
`SIDECAR_PIN`, `SIDECAR_SECRET` and `SIDECAR_SECURE_COOKIE` values;
missing or empty settings fail Compose interpolation rather than falling
back to sample credentials/cookie mode. This prevents accidental fallback
through this Compose path **only**. The backend `security.py` still
contains development defaults if run directly, and users could deliberately
supply weak secrets. Before production activation, verify effective secret
names and reject known weak/default values at the actual runtime trust
boundary. Preserve actual UDA/Caddy authentication, WebSocket upgrade
support, HTTPS cookie mode and session scope. The live registry group,
volume ID and host port still require read-only verification.

Remaining gates:
- [ ] Canonical V2 JSON Schema and UDA semantic validation.
- [ ] Source-pinned isolated Docker build and test with disposable volume.
- [ ] Validate WebSockets, attachment upload/download, health and prefix URLs
      behind the authenticated reverse proxy.
- [ ] Read-only Desktop comparison of live Docker port/volume identifiers and
      Caddy/UDA configuration.
- [ ] Verify secret *names only*, safe nondefault credentials and backup/restore.
- [ ] Independent application owner approval for lifecycle and data retention.

Do not deploy the candidate before these gates and explicit authorisation.

## Source-only Compose safety increment — 20 November 2026

Draft `docker-compose.yml` no longer silently inserts known PIN, signing
secret or cookie-mode defaults. Three dependency-free tests in
`backend/tests/test_uda_compose_security.py` were reproduced and run in a
disposable local workspace: **3 passed, 0 failed**. The test checks
missing-value interpolation requirements and unchanged volume/health source
contracts; it did **not** run Docker Compose, mount a real volume, inspect
live secrets, test WebSockets or exercise the running app. The current
installed SideCar image is unchanged. Keep the secret trust, actual
Docker volume, backup/restore and proxy acceptance gates open.
