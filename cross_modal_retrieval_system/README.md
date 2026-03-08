# Cross Modal Retrieval System (Chapter 5)

This project implements the Chapter 5 system using:
- Backend: Python + FastAPI + PyTorch, with Kafka/Milvus adapters.
- Frontend: React + TypeScript (Vite).

## Structure

- `backend/`: FastAPI modular backend.
- `frontend/`: React UI for similar retrieval, photo search, and text search.

## Backend Setup

```bash
cd backend
source .venv/bin/activate
uv sync
```

Copy env template:

```bash
cp .env.example .env
```

Run API:

```bash
PYTHONPATH=src uvicorn app.main:app --reload --port 8000
```

Run tests:

```bash
PYTHONPATH=src .venv/bin/pytest -q
```

Run smoke integration script:

```bash
PYTHONPATH=src .venv/bin/python scripts/e2e_smoke.py
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## One-Command Local Stack (Docker Compose)

Start all services:

```bash
cd cross_modal_retrieval_system
docker compose up -d --build
```

Check running services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f backend
docker compose logs -f nginx
```

Stop stack:

```bash
docker compose down
```

This stack includes:
- `milvus` (with `etcd` + `minio`)
- `kafka`
- `backend` (FastAPI, internal `8000`)
- `nginx` (single browser entry, host port `80`)

Notes:
- In `docker-compose.yml`, backend is configured with `USE_MOCK_QUEUE=false` and uses Kafka directly.
- `nginx` serves frontend static files and reverse proxies `/api/*` to backend.
- `nginx` backend upstream is switchable via `NGINX_BACKEND_UPSTREAM`:
  - default (container backend): `backend:8000`
  - local debug backend: `host.docker.internal:8000`
- Example local-debug mode:
  - `NGINX_BACKEND_UPSTREAM=host.docker.internal:8000 docker compose up -d --build nginx`
- Milvus gRPC is mapped to host `19530`, so local backend can connect with `MILVUS_URI=http://127.0.0.1:19530`.

## Implemented APIs

- `POST /api/v1/ingest/products`
- `POST /api/v1/ingest/replay` (consume from Kafka topic and replay indexing)
- `POST /api/v1/hash/update`
- `POST /api/v1/retrieval/similar-image`
- `POST /api/v1/retrieval/photo-search`
- `POST /api/v1/retrieval/text-search`
- `GET /api/v1/health`
