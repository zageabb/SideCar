FROM node:22-alpine AS frontend
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --system sidecar \
    && useradd --system --gid sidecar --home-dir /app sidecar \
    && mkdir -p /data/uploads \
    && chown -R sidecar:sidecar /app /data
COPY backend/app ./app
COPY --from=frontend /src/frontend/dist ./static
RUN chown -R sidecar:sidecar /app
ENV SIDECAR_STATIC_DIR=/app/static
ENV SIDECAR_DB_PATH=/data/sidecar.db
ENV SIDECAR_UPLOAD_DIR=/data/uploads
USER sidecar
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
