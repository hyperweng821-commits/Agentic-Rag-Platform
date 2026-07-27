# Development Guide

## Current scope

The executable backend contains the Phase 3 foundation plus AF-1 knowledge
bases, secure local document intake, durable document/job records,
deduplication, and retry transitions.

Authentication, parsing, chunks, embeddings, indexing, retrieval, RAG, Agent,
evaluation and workers are not implemented.

## Required tools

For Phase 3 backend development:

- Python 3.12
- uv `>=0.9,<1`
- Docker Engine with Docker Compose v2

Node.js is needed only when explicitly working on the `frontend` profile. Ollama model downloads are not required for Phase 3.

## Local Python setup

From the repository root:

```bash
cp .env.example .env
cd apps/api
uv python install 3.12
uv sync --frozen --extra dev
```

Start PostgreSQL from the repository root:

```bash
docker compose up -d postgres
```

Start FastAPI from `apps/api`:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Phase 3 Compose startup

The default profile starts only PostgreSQL and FastAPI:

```bash
docker compose up --build
```

The default services are:

- `postgres`
- `api`

Equivalent Make target:

```bash
make up
```

Stop them with:

```bash
docker compose down
```

## Reserved profiles

ChromaDB and Ollama are isolated behind `rag`:

```bash
docker compose --profile rag up --build
# or: make up-rag
```

React is isolated behind `frontend`:

```bash
docker compose --profile frontend up --build
# or: make up-frontend
```

These commands only expose future infrastructure. They do not indicate that the corresponding business functionality exists in Phase 3.

There is no worker service or worker Python entry point in AF-1. Durable
ingestion jobs remain pending until AF-2 implements execution.
Neither `make up` nor `scripts/bootstrap.sh` pulls Ollama models.

The optional ChromaDB service in `compose.test.yaml` is also isolated behind the `rag` profile. The Phase 3 pytest suite does not use Compose.

## Quality checks

From `apps/api`:

```bash
uv sync --frozen --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
uv run pytest --cov=app
python -m compileall app tests
```

The pytest environment pins every Settings field used by the foundation, disables dotenv loading before collection and clears the Settings cache before and after every test. Health tests replace the database dependency with an AsyncMock, so they never connect to a developer PostgreSQL instance.

## Alembic

From `apps/api`:

```bash
uv run alembic current
uv run alembic heads
uv run alembic history
```

Phase 3 contains no business models and therefore no empty migration revision. Add model imports and generate a migration only when real ORM models are introduced.

## Current layering rule

- `app/api` owns HTTP routing, dependencies and error mapping.
- `app/core` owns configuration and logging.
- `app/db` owns the declarative base, engine and sessions.
- `app/schemas/common.py` owns infrastructure response contracts.
- Future domain directories are boundaries only and contain no Python implementation.
