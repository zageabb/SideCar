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

Credentials: Compose uses unsafe fallback defaults for `SIDECAR_PIN` and
`SIDECAR_SECRET`. V2 intentionally names the required secrets without values.
Never substitute or permit the sample defaults in production. Confirm
`SIDECAR_SECURE_COOKIE` and UDA/Caddy trusted proxy, WebSocket upgrade support
and session scope. Actual registry group and deployed host port require
verification against the running host; the V2 loopback binding is a proposed
hardening change, not confirmation of current deployment.

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
