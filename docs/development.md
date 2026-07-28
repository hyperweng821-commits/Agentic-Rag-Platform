# Development Guide

## Current scope

The executable backend contains the Phase 3 foundation, AF-1 knowledge intake,
and durable ingestion/indexing through AF-2B. PostgreSQL stores authoritative
job state and ordered normalized chunks. The AF-2B worker parses managed source
artifacts, replaces chunks transactionally, generates Ollama embeddings, and
updates a rebuildable Chroma index.

Retrieval, RAG, Agent, evaluation, and authentication are not implemented.

## Required tools

For backend development:

- Python 3.12
- uv `>=0.9,<1`
- Docker Engine with Docker Compose v2

Node.js is needed only when explicitly working on the `frontend` profile.
Ollama and Chroma are needed only for real AF-2B worker or rebuild runs.
Ordinary tests use deterministic fakes and require neither service nor a model
download.

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

## AF-2B infrastructure profile

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

The `rag` profile starts the Ollama and Chroma services consumed by AF-2B. It
does not add retrieval or RAG APIs, and neither `make up-rag` nor
`scripts/bootstrap.sh` pulls the configured Ollama embedding model. The worker
is an explicit CLI process rather than an always-running Compose service.
Only Ollama joins the dedicated `model_egress` network needed for explicit
model pulls; PostgreSQL and Chroma remain confined to the internal backend
network.

The optional ChromaDB service in `compose.test.yaml` is also isolated behind
the `rag` profile. Ordinary backend tests do not require Compose.

## Ingestion worker and index rebuild

Start the AF-2B infrastructure, pull the configured local models, and apply
migrations before running the worker:

```bash
make up-rag
make pull-models
docker compose exec api uv run alembic upgrade head
```

Process at most one available job and exit:

```bash
docker compose exec api uv run python -m app.workers.ingestion_worker --once
```

Poll continuously with the configured
`INGESTION_WORKER_POLL_INTERVAL_SECONDS`:

```bash
docker compose exec api uv run python -m app.workers.ingestion_worker
```

Rebuild the derived index for one PostgreSQL-authoritative document or
knowledge base without an HTTP retrieval endpoint:

```bash
docker compose exec api uv run python -m app.workers.ingestion_worker \
  rebuild --document-id 00000000-0000-0000-0000-000000000000

docker compose exec api uv run python -m app.workers.ingestion_worker \
  rebuild --knowledge-base-id 00000000-0000-0000-0000-000000000000
```

The rebuild subcommand also accepts bounded `--max-chunks`,
`--max-documents`, and `--max-chunks-per-document` overrides. A rebuild that
reports any per-document failure exits nonzero. `SIGINT` and `SIGTERM` cancel
and join in-flight work before provider clients and the database pool close.
Knowledge-base rebuilds report and skip non-completed documents so they cannot
delete vectors concurrently produced by an active ingestion attempt.

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

AF-2A adds the reversible `20260728_0002` revision after
`20260727_0001_af1_knowledge_intake.py`. AF-2B adds the focused reversible
`20260728_0003` chunk-provenance revision without editing either merged
revision. Its new hash, offset, and page-range columns remain nullable so
existing authoritative chunks are not assigned fabricated provenance.

## AF-2 ingestion contract

- Ingestion states remain `pending`, `processing`, `completed`, and `failed`.
- Attempts are non-negative and cannot exceed a positive maximum; progress is
  constrained to 0 through 100. Claim fields are all absent or all present,
  claimant identifiers cannot be blank, and lease expiry follows claim time.
- Queue-order, scheduled-retry, and expired-lease indexes support concurrent,
  skip-locked claiming and bounded expired-lease recovery.
- `DocumentChunk` rows use deterministic UUIDs derived from the document,
  chunk index, and content hash, plus cascading document ownership, zero-based
  ordering, normalized nonempty text, non-negative token counts, timestamps,
  hashes, optional source provenance, and a unique `(document_id, chunk_index)`
  key.
- Repositories flush but do not commit; the calling use case owns the
  transaction.
- Parsing, normalization, and embedding/vector calls happen outside long-lived
  database transactions.
- PostgreSQL chunks are authoritative. Chroma stores derived vectors under
  stable chunk-based IDs and can be rebuilt for one document or knowledge base.
- Jobs and documents become completed only after Chroma accepts the vectors;
  processing failures remain retryable within the configured attempt bound.

## Current layering rule

- `app/api` owns the unchanged HTTP routing, dependencies and error mapping.
- `app/core` owns configuration and logging.
- `app/db` owns the declarative base, engine, sessions, business models, and
  persistence queries.
- `app/services` owns AF-1 intake plus AF-2B processing/rebuild sequencing and
  transaction boundaries.
- `app/ingestion` owns managed storage, parsing, deterministic transformation,
  embedding, and vector-store boundaries and adapters.
- `app/workers` owns polling, signal handling, and CLI composition; it does not
  own SQL queries or provider-specific behavior.
