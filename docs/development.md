# Development Guide

## Current scope

The executable backend contains the Phase 3 foundation, AF-1 knowledge intake,
durable ingestion/indexing through AF-2B, and the minimal AF-2S1
knowledge-access boundary. PostgreSQL stores authoritative users, sessions,
memberships, job state, and ordered normalized chunks. The AF-2B worker parses
managed source artifacts, replaces chunks transactionally, generates Ollama
embeddings, and updates a rebuildable Chroma index.

Retrieval, RAG, Agent, and evaluation are not implemented. AF-2S2 identity and
operational hardening remains P1.

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

The default Compose PostgreSQL service is intentionally not published to the
host. For the normal local workflow, run the API inside Compose:

```bash
docker compose up --build
```

To run FastAPI directly from `apps/api`, provide a separately managed
PostgreSQL endpoint in `DATABASE_URL`; starting the default Compose `postgres`
service does not expose port 5432 to a host process:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Current Compose startup

The default profile starts only PostgreSQL and FastAPI:

```bash
docker compose up --build
```

The default services are:

- `postgres`
- `api`

PostgreSQL is reachable by containers at `postgres:5432` but has no host port.
The API is the only default host-facing service and binds to
`127.0.0.1:${API_PORT:-8000}`.

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
network. PostgreSQL, Chroma, and Ollama have no host-published ports in the
default project; the API and optional Web service bind only to `127.0.0.1`.

The optional ChromaDB service in `compose.test.yaml` is also isolated behind
the `rag` profile. Test PostgreSQL and Chroma ports bind only to `127.0.0.1`.
Ordinary backend tests do not require Compose.

## Database access

Use Compose execution rather than publishing PostgreSQL to the host:

```bash
docker compose exec postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

Application and migration commands use the internal `postgres:5432` service
address:

```bash
docker compose exec api uv run alembic current
docker compose exec api uv run alembic upgrade head
```

Do not add an unauthenticated Chroma debug port to the default workflow.

## AF-2S1 local access setup

AF-2S1 has no public registration or frontend login screen. Bootstrap an active
local user with the operator CLI; the command prompts for the password without
echoing it:

```bash
docker compose exec api uv run python -m app.cli.security \
  bootstrap-user --email owner@example.com
```

The email is normalized, duplicates are rejected, and neither the password nor
its Argon2id hash is printed.

The AF-2S1 migration deliberately leaves existing knowledge bases unowned and
therefore hidden from all user-facing requests. Preview and then explicitly
claim only still-unowned knowledge bases for an existing user:

```bash
docker compose exec api uv run python -m app.cli.security \
  claim-legacy-knowledge-bases --owner-email owner@example.com --dry-run

docker compose exec api uv run python -m app.cli.security \
  claim-legacy-knowledge-bases --owner-email owner@example.com
```

The claim is transactional and idempotent and reports counts only. It never
creates or guesses a user.

Login sets an `HttpOnly` `agentforge_session` cookie and a readable
`agentforge_csrf` cookie by default. For authenticated writes, clients must
copy the CSRF cookie value into `X-CSRF-Token`. Cookie names, bounded session
TTL, `Secure`, and `SameSite` behavior are configured with
`SESSION_COOKIE_NAME`, `CSRF_COOKIE_NAME`, `SESSION_TTL_SECONDS`,
`SESSION_COOKIE_SECURE`, and `SESSION_COOKIE_SAMESITE`. Do not add an
authentication-disabled development mode.

`ARGON2_MAX_CONCURRENCY` bounds memory-intensive password verification and
rehashing to two concurrent jobs per API process by default and accepts values
from 1 through 8. Login reads a primitive user snapshot in a short transaction,
releases the database connection before bounded Argon2 work, then locks and
rechecks the user in a short write transaction before creating the session.

Credentialed browser clients must originate from an explicit
`CORS_ORIGINS` entry. Wildcard CORS is rejected; adding an origin does not
replace session, CSRF, or membership checks.

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

The pytest environment pins every Settings field used by the foundation,
disables dotenv loading before collection, and clears the Settings cache
before and after every test. Health tests replace the database dependency with
an AsyncMock, so they never connect to a developer PostgreSQL instance.

Live AF-2A and AF-2S tests use only the explicit
`AF2A_TEST_DATABASE_URL`. Locally, those tests skip when the variable is
intentionally absent. Under `CI=true`, absence is a test failure so
infrastructure coverage cannot skip behind a green backend job. With the
isolated test Compose PostgreSQL running, execute the complete suite with:

```bash
AF2A_TEST_DATABASE_URL=postgresql+asyncpg://agentic_rag_test:test_only@127.0.0.1:55432/agentic_rag_test \
  uv run pytest
```

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
AF-2S1 adds `20260729_0004` local-user, opaque-session, and
knowledge-base-membership tables without rewriting existing knowledge data.
Downgrading it to `20260728_0003` preserves pre-AF-2S knowledge bases,
documents, ingestion jobs, and chunks, but destructively removes AF-2S users,
sessions, and memberships. Re-upgrading recreates empty access-boundary tables;
it does not fabricate or restore the deleted AF-2S rows. Legacy knowledge
bases remain unowned and fail closed until the operator claim command is run.

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

- `app/api` owns HTTP routing, authenticated principal dependencies, and error
  mapping; endpoints contain no SQL or role-name checks.
- `app/core` owns configuration and logging.
- `app/security` owns Argon2id password handling, opaque-session
  authentication, CSRF validation, principal construction, and capability
  policy.
- `app/db` owns the declarative base, engine, database sessions, business
  models, user-scoped persistence queries, and explicitly separate
  worker/internal persistence queries.
- `app/services` owns AF-1 intake plus AF-2B processing/rebuild sequencing and
  AF-2S1 access-boundary transaction sequencing.
- `app/cli` owns operator-only user bootstrap and legacy-data claim commands.
- `app/ingestion` owns managed storage, parsing, deterministic transformation,
  embedding, and vector-store boundaries and adapters.
- `app/workers` owns polling, signal handling, and CLI composition; it does not
  own SQL queries or provider-specific behavior.
