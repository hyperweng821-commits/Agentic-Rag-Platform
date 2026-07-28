# Development Guide

## Current scope

The executable backend contains the Phase 3 foundation, AF-1 knowledge intake,
and the AF-2A persistence foundation. PostgreSQL now represents durable
attempt, progress, claim, lease, and retry scheduling metadata plus ordered
authoritative document chunks.

AF-2A does not parse documents, produce chunk content, execute workers, generate
embeddings, or write to Chroma. Retrieval, RAG, Agent, evaluation, and
authentication are also not implemented.

## Required tools

For backend development:

- Python 3.12
- uv `>=0.9,<1`
- Docker Engine with Docker Compose v2

Node.js is needed only when explicitly working on the `frontend` profile.
Ollama model downloads are not required for AF-2A.

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

## Current Compose startup

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

These commands only expose future infrastructure. They do not indicate that
the corresponding business functionality exists in AF-2A.

There is no worker service or worker Python entry point in AF-2A. Durable
ingestion jobs remain pending until AF-2C implements claiming and execution.
AF-2B first adds parsers, normalization, and deterministic chunking without a
background execution loop.
Neither `make up` nor `scripts/bootstrap.sh` pulls Ollama models.

The optional ChromaDB service in `compose.test.yaml` is also isolated behind
the `rag` profile. Ordinary backend tests do not require Compose.

## Quality checks

From `apps/api`:

```bash
uv lock --check
uv sync --frozen --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
python -m compileall app tests
```

The pytest environment pins every Settings field used by the foundation, disables dotenv loading before collection and clears the Settings cache before and after every test. Health tests replace the database dependency with an AsyncMock, so they never connect to a developer PostgreSQL instance.

## Alembic

Normal development migrations run inside the API container so the application
uses its Compose network and locked environment. From the repository root:

```bash
docker compose up -d
docker compose exec api uv run alembic upgrade head
docker compose exec api uv run alembic current
```

For read-only migration inspection from `apps/api`:

```bash
uv run alembic current
uv run alembic heads
uv run alembic history
```

AF-2A adds a second reversible revision after
`20260727_0001_af1_knowledge_intake.py`; the AF-1 revision is not edited.
Existing rows receive safe defaults for newly required job metadata before
constraints are applied.

## AF-2A persistence contract

- Ingestion states remain `pending`, `processing`, `completed`, and `failed`.
- Attempts are non-negative and cannot exceed a positive maximum; progress is
  constrained to 0 through 100. Claim fields are all absent or all present,
  claimant identifiers cannot be blank, and lease expiry follows claim time.
- Queue-order, scheduled-retry, and expired-lease indexes support future AF-2C
  queries without introducing a worker in AF-2A.
- `DocumentChunk` rows use stable UUIDs, cascading document ownership,
  zero-based ordering, normalized nonempty text, non-negative token counts,
  timestamps, and a unique `(document_id, chunk_index)` key.
- Repositories flush but do not commit; the calling use case owns the
  transaction.

AF-2B will supply parsers, normalization, and deterministic chunking. AF-2C
will use the job metadata for claiming, bounded retries, lease recovery, and
transactional chunk replacement. Embedding and vector-store work remains in
AF-2D and AF-2E.

## Current layering rule

- `app/api` owns the unchanged HTTP routing, dependencies and error mapping.
- `app/core` owns configuration and logging.
- `app/db` owns the declarative base, engine, sessions, business models, and
  persistence queries.
- `app/services` owns AF-1 use-case sequencing and transaction boundaries.
- `app/ingestion` contains only AF-1 local storage; parser execution remains
  deferred.
