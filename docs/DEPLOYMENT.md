# Sidecar Deployment

Sidecar is designed to run as a single Docker Compose service behind an optional HTTPS reverse proxy.

## Production environment

Copy the example file:

```bash
cp .env.example .env
```

Set at least:

```env
SIDECAR_PORT=8088
SIDECAR_PIN=choose-a-private-pin
SIDECAR_SECRET=replace-with-a-long-random-secret
SIDECAR_SECURE_COOKIE=false
SIDECAR_MAX_UPLOAD_BYTES=104857600
```

Use a long random value for `SIDECAR_SECRET`.

If Sidecar is served through HTTPS, set:

```env
SIDECAR_SECURE_COOKIE=true
```

Do not enable secure cookies while accessing Sidecar only through plain HTTP, because browsers will not return a Secure cookie over HTTP.

## Start / update

```bash
git pull
docker compose up --build -d
docker compose ps
```

Health check:

```bash
curl http://127.0.0.1:8088/api/health
```

Expected result:

```json
{"status":"ok"}
```

## Reverse proxy

The reverse proxy must forward normal HTTP requests and WebSocket upgrades to Sidecar.

### Nginx example

```nginx
server {
    listen 443 ssl;
    server_name sidecar.example.internal;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

TLS certificate configuration is intentionally not included because it depends on the existing reverse-proxy setup.

## Persistent data

Docker Compose stores all durable Sidecar state in the named volume:

```text
sidecar-data
```

Inside that volume:

```text
/data/sidecar.db
/data/uploads/
```

Both the database and upload directory are required for a complete backup.

## Backup

Stop Sidecar briefly for a consistent SQLite + attachment snapshot:

```bash
docker compose stop sidecar
mkdir -p backups
docker run --rm \
  -v sidecar_sidecar-data:/source:ro \
  -v "$PWD/backups:/backup" \
  alpine sh -c 'cd /source && tar czf /backup/sidecar-data-$(date +%Y%m%d-%H%M%S).tar.gz .'
docker compose start sidecar
```

The actual Docker volume name may differ if the Compose project name is overridden. Check it with:

```bash
docker volume ls | grep sidecar
```

## Restore

Stop Sidecar and restore only from a trusted backup:

```bash
docker compose stop sidecar
docker run --rm \
  -v sidecar_sidecar-data:/target \
  -v "$PWD/backups:/backup:ro" \
  alpine sh -c 'rm -rf /target/* && tar xzf /backup/<backup-file>.tar.gz -C /target'
docker compose start sidecar
```

After restore, verify:

```bash
curl http://127.0.0.1:8088/api/health
```

Then log in and confirm message/attachment history.

## Upgrade check

After every update:

1. `docker compose up --build -d`
2. confirm the health endpoint;
3. open Sidecar as both users;
4. send one text message;
5. transfer one small file;
6. confirm the peer receives both live;
7. refresh and confirm both remain in history.

## HTTPS note

HTTPS is recommended even on the LAN because browser clipboard APIs are more consistent in a secure context. Sidecar still supports plain-HTTP LAN access, including the fallback client-message ID path added after BUG-001.


## Helper scripts

Sidecar now includes:

```text
scripts/backup.sh
scripts/restore.sh
```

Backup:

```bash
sh scripts/backup.sh
```

Restore:

```bash
sh scripts/restore.sh backups/<backup-file>.tar.gz
```

If your Docker Compose project name is not `sidecar`, set `SIDECAR_VOLUME_NAME` to the actual named volume before running either script.
