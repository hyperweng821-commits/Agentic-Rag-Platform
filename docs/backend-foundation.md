# Phase 3 — Backend Foundation

This document describes the final Phase 3 backend after the targeted engineering cleanup. Phase 4 has not started.

## 1. Implemented scope

Phase 3 implements only:

- Pydantic V2 settings with process-wide caching
- structured logging and request correlation
- SQLAlchemy 2.0 AsyncEngine and async_sessionmaker
- request-scoped AsyncSession dependency injection
- SQLAlchemy DeclarativeBase
- unified application and framework error responses
- `/api/v1` route versioning
- `GET /api/v1/health`
- PostgreSQL readiness checking
- FastAPI lifespan cleanup
- explicit CORS policy
- async Alembic configuration
- Docker packaging
- isolated pytest coverage
- Ruff and strict Mypy configuration

It does not implement users, authentication, documents, ingestion, Embedding, ChromaDB access, Ollama access, retrieval, RAG, Agent, evaluation or workers.

## 2. Source cleanup

Future backend directories remain visible for architecture continuity, but contain only `.gitkeep` or documentation:

```text
app/
├── agent/
│   ├── nodes/.gitkeep
│   ├── prompts/README.md
│   ├── tools/.gitkeep
│   └── .gitkeep
├── db/
│   ├── models/.gitkeep
│   └── repositories/.gitkeep
├── evaluation/.gitkeep
├── ingestion/
│   ├── parsers/.gitkeep
│   └── .gitkeep
├── llm/.gitkeep
├── observability/.gitkeep
├── retrieval/.gitkeep
├── services/.gitkeep
└── workers/.gitkeep
```

All docstring-only future Python modules were removed. The placeholder worker that raised `SystemExit` and its Compose service were also removed.

The complete current backend tree is maintained in [project-structure.md](project-structure.md).

## 3. Implemented file responsibilities

| File | Responsibility |
| --- | --- |
| `apps/api/app/main.py` | FastAPI factory, lifespan, CORS, middleware, handlers and routes. |
| `apps/api/app/core/config.py` | Immutable validated settings and one-entry cache. |
| `apps/api/app/core/logging.py` | Structured logs, request IDs and version headers. |
| `apps/api/app/api/dependencies.py` | Settings and request-scoped AsyncSession dependencies. |
| `apps/api/app/api/errors.py` | Common infrastructure exceptions and global error handlers. |
| `apps/api/app/api/router.py` | `/api` prefix. |
| `apps/api/app/api/v1/router.py` | `/v1` prefix and endpoint registration. |
| `apps/api/app/api/v1/endpoints/health.py` | Service and PostgreSQL readiness. |
| `apps/api/app/db/base.py` | Async-compatible DeclarativeBase and constraint naming. |
| `apps/api/app/db/session.py` | Engine, sessionmaker, readiness query and disposal. |
| `apps/api/app/schemas/common.py` | Health, validation and error schemas. |
| `apps/api/alembic/env.py` | Async online/offline Alembic environment. |
| `apps/api/tests/conftest.py` | Deterministic environment, cache reset, ASGI client and database mock. |
| `apps/api/tests/unit/test_database.py` | Session and lifecycle tests. |
| `apps/api/tests/unit/test_errors.py` | Unified error protocol tests. |
| `apps/api/tests/unit/test_health.py` | Health success and failure-boundary tests. |
| `apps/api/tests/unit/test_settings.py` | Settings validation and cache tests. |

## 4. Health API contract

Path:

```text
GET /api/v1/health
```

Successful response remains unchanged:

```json
{
  "status": "healthy",
  "service": "agentic-rag-backend",
  "version": "0.1.0",
  "database": "healthy"
}
```

Database OperationalError or health timeout returns HTTP 503:

```json
{
  "error": {
    "code": "DATABASE_UNAVAILABLE",
    "message": "Database is unavailable.",
    "details": {
      "database": "unhealthy"
    },
    "request_id": "request correlation ID"
  }
}
```

The health endpoint catches only:

- `TimeoutError`
- `SQLAlchemyError`

Programming errors such as `RuntimeError`, `AttributeError`, `ValueError` and `TypeError` are not mislabeled as database outages. They reach the global handler and return HTTP 500 with `INTERNAL_SERVER_ERROR`.

Neither 503 nor 500 responses expose connection URLs, passwords or internal exception messages.

## 5. Test isolation

`tests/conftest.py` applies deterministic environment values before application modules are collected. It also clears `get_settings()` before and after every test.

The pytest process explicitly sets `Settings.model_config["env_file"]` to `None` before test collection and restores it during pytest shutdown. Developer `.env` files are therefore not read by the test suite; production Settings behavior is unchanged outside pytest.

The isolated values cover:

- application name and version
- environment and debug mode
- logging settings
- database URL and pool settings
- health-check timeout
- CORS origins

Health tests replace `get_db_session` with an `AsyncMock`. No test connects to a real PostgreSQL service.

The session dependency retains one intentional `except Exception`: it rolls back failed request work and immediately re-raises the original exception. The async session context closes the session on both success and failure. Request logging similarly records unknown failures and re-raises them; neither boundary converts errors into database failures.

## 6. Compose topology

Default Phase 3 command:

```bash
docker compose up --build
```

Default services:

- `postgres`
- `api`

Future RAG infrastructure is opt-in:

```bash
docker compose --profile rag up --build
```

This adds:

- `chroma`
- `ollama`

Future frontend infrastructure is opt-in:

```bash
docker compose --profile frontend up --build
```

This adds `web`. There is no worker service in Phase 3.

`compose.test.yaml` also keeps its optional ChromaDB service behind the `rag` profile. Unit tests do not start that file or any container.

## 7. Local installation and startup

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

Verify:

```bash
curl -i http://localhost:8000/api/v1/health
```

## 8. Alembic

From `apps/api`:

```bash
uv run alembic current
uv run alembic heads
uv run alembic history
```

No empty migration is created in Phase 3 because there are no business models. When real models are introduced in a later phase:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
```

## 9. Quality commands

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

Configured coverage threshold remains 90%.

## 10. Verified result

| Check | Result |
| --- | --- |
| Frozen dependency installation | Passed |
| Ruff lint | Passed |
| Ruff format check | Passed |
| Strict Mypy | Passed for 18 current source files |
| pytest | 24 passed |
| Coverage | 95.86%, threshold 90% |
| OperationalError health path | HTTP 503, `DATABASE_UNAVAILABLE` |
| TimeoutError health path | HTTP 503, `DATABASE_UNAVAILABLE` |
| RuntimeError health path | HTTP 500, `INTERNAL_SERVER_ERROR` |
| Real PostgreSQL dependency in tests | None |

The formal close-out review is recorded in [engineering-review.md](engineering-review.md).

## 11. Docker verification status

The current execution environment does not provide a Docker CLI.

**Docker validation was not actually executed.**

The following commands remain to be run on a Docker-capable machine or by the GitHub Actions container job:

```bash
docker compose config --quiet
docker compose build api
docker compose up -d postgres api
docker compose ps
curl http://localhost:8000/api/v1/health
docker compose down
```

No static inspection is described as a successful Docker build or runtime test.

## 12. Common errors

### Health returns 503 locally

Check PostgreSQL and confirm that a host-run API uses `localhost`:

```bash
docker compose ps postgres
docker compose logs postgres
```

### Database URL validation fails

The backend requires the async driver scheme:

```text
postgresql+asyncpg://user:password@host:port/database
```

### Frozen installation reports a stale lock

After an intentional dependency change:

```bash
uv lock
uv sync --frozen --extra dev
```

Commit `pyproject.toml` and `uv.lock` together.
