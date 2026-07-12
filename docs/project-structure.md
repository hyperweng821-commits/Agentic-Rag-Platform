# Agentic RAG Platform — Current Project Structure

> Current implementation: Phase 3 Backend Foundation  
> Domain status: authentication, documents, ingestion, retrieval, RAG, Agent, evaluation and workers are not implemented

## 1. Structure policy

The repository keeps the architecture boundaries approved in Phase 1 and Phase 2, but a directory is not represented as an implemented Python package until it contains real code.

Current rules:

1. Phase 3 infrastructure modules are executable, typed and tested.
2. Future backend areas contain `.gitkeep` or a directory-level README only.
3. Future areas do not contain placeholder `__init__.py` or docstring-only Python modules.
4. The worker process is absent until document ingestion is implemented.
5. Only PostgreSQL and FastAPI start in the default Compose profile.
6. ChromaDB and Ollama are reserved behind the `rag` profile.
7. React is reserved behind the `frontend` profile.

## 2. Complete Phase 3 backend tree

```text
agentic-rag-platform/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── release.yml
│       └── security.yml
├── apps/
│   ├── api/
│   │   ├── alembic/
│   │   │   ├── versions/
│   │   │   │   └── .gitkeep
│   │   │   ├── env.py
│   │   │   └── script.py.mako
│   │   ├── app/
│   │   │   ├── agent/
│   │   │   │   ├── nodes/
│   │   │   │   │   └── .gitkeep
│   │   │   │   ├── prompts/
│   │   │   │   │   └── README.md
│   │   │   │   ├── tools/
│   │   │   │   │   └── .gitkeep
│   │   │   │   └── .gitkeep
│   │   │   ├── api/
│   │   │   │   ├── v1/
│   │   │   │   │   ├── endpoints/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   └── health.py
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── router.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── errors.py
│   │   │   │   └── router.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py
│   │   │   │   └── logging.py
│   │   │   ├── db/
│   │   │   │   ├── models/
│   │   │   │   │   └── .gitkeep
│   │   │   │   ├── repositories/
│   │   │   │   │   └── .gitkeep
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   └── session.py
│   │   │   ├── evaluation/
│   │   │   │   └── .gitkeep
│   │   │   ├── ingestion/
│   │   │   │   ├── parsers/
│   │   │   │   │   └── .gitkeep
│   │   │   │   └── .gitkeep
│   │   │   ├── llm/
│   │   │   │   └── .gitkeep
│   │   │   ├── observability/
│   │   │   │   └── .gitkeep
│   │   │   ├── retrieval/
│   │   │   │   └── .gitkeep
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   └── common.py
│   │   │   ├── services/
│   │   │   │   └── .gitkeep
│   │   │   ├── workers/
│   │   │   │   └── .gitkeep
│   │   │   ├── __init__.py
│   │   │   └── main.py
│   │   ├── tests/
│   │   │   ├── contract/
│   │   │   │   └── .gitkeep
│   │   │   ├── fixtures/
│   │   │   │   └── .gitkeep
│   │   │   ├── integration/
│   │   │   │   └── .gitkeep
│   │   │   ├── unit/
│   │   │   │   ├── agent/
│   │   │   │   │   └── .gitkeep
│   │   │   │   ├── ingestion/
│   │   │   │   │   └── .gitkeep
│   │   │   │   ├── retrieval/
│   │   │   │   │   └── .gitkeep
│   │   │   │   ├── services/
│   │   │   │   │   └── .gitkeep
│   │   │   │   ├── test_database.py
│   │   │   │   ├── test_errors.py
│   │   │   │   ├── test_health.py
│   │   │   │   └── test_settings.py
│   │   │   ├── __init__.py
│   │   │   └── conftest.py
│   │   ├── .dockerignore
│   │   ├── .python-version
│   │   ├── Dockerfile
│   │   ├── alembic.ini
│   │   ├── pyproject.toml
│   │   └── uv.lock
│   └── web/
│       ├── e2e/
│       ├── public/
│       └── src/
├── docs/
│   ├── adr/
│   ├── api.md
│   ├── architecture.md
│   ├── backend-foundation.md
│   ├── deployment.md
│   ├── development.md
│   ├── engineering-review.md
│   ├── evaluation.md
│   └── project-structure.md
├── eval/
├── infra/
│   └── postgres/
│       └── init/
│           └── 001_extensions.sql
├── packages/
│   └── api-client/
├── sample-data/
├── scripts/
├── .env.example
├── compose.test.yaml
├── compose.yaml
├── Makefile
├── README.md
└── package.json
```

The tree expands the complete Phase 3 backend. Existing frontend, governance and architecture assets remain unchanged by the backend cleanup.

## 3. Implemented backend files

| File | Responsibility |
| --- | --- |
| `apps/api/app/main.py` | Creates FastAPI, installs lifespan, CORS, request context, errors and versioned routes. |
| `apps/api/app/core/config.py` | Validates immutable Pydantic settings and caches one process-wide instance. |
| `apps/api/app/core/logging.py` | Configures structured logging, request correlation and API response headers. |
| `apps/api/app/api/dependencies.py` | Provides request-scoped AsyncSession and cached settings dependencies. |
| `apps/api/app/api/errors.py` | Defines public infrastructure exceptions and global exception handlers. |
| `apps/api/app/api/router.py` | Mounts API versions under `/api`. |
| `apps/api/app/api/v1/router.py` | Mounts version 1 routes under `/v1`. |
| `apps/api/app/api/v1/endpoints/health.py` | Implements `GET /api/v1/health` with PostgreSQL readiness. |
| `apps/api/app/db/base.py` | Provides SQLAlchemy 2.0 DeclarativeBase and naming conventions. |
| `apps/api/app/db/session.py` | Configures AsyncEngine, async_sessionmaker, readiness query and disposal. |
| `apps/api/app/schemas/common.py` | Defines health, validation and error response schemas. |
| `apps/api/alembic/env.py` | Loads settings and Base metadata for async online/offline migrations. |

## 4. Required Python package markers

Only importable Phase 3 packages retain `__init__.py`:

| Package | Reason |
| --- | --- |
| `app` | Backend application package. |
| `app.api` | HTTP infrastructure package. |
| `app.api.v1` | Versioned API package. |
| `app.api.v1.endpoints` | Contains the implemented health endpoint. |
| `app.core` | Contains implemented configuration and logging. |
| `app.db` | Contains implemented database foundation. |
| `app.schemas` | Contains implemented shared schemas. |
| `tests` | Backend test package. |

Future directories intentionally have no `__init__.py`, so their presence cannot be mistaken for implemented Python modules.

## 5. Reserved future directories

| Directory | Boundary only; implementation deferred |
| --- | --- |
| `app/agent/` | Agent workflow, nodes, tools and state. |
| `app/db/models/` | Business ORM models. |
| `app/db/repositories/` | Business persistence queries. |
| `app/evaluation/` | RAG and answer evaluation. |
| `app/ingestion/` | Document parsing, chunking and indexing. |
| `app/llm/` | Ollama and model-provider adapters. |
| `app/observability/` | Future metrics and distributed tracing beyond current logging. |
| `app/retrieval/` | Dense, keyword, fusion and reranking logic. |
| `app/services/` | Business use-case orchestration. |
| `app/workers/` | Future document-ingestion worker. |

These directories contain only `.gitkeep` or documentation. No future business Python code exists in Phase 3.

## 6. Backend tests

| File | Responsibility |
| --- | --- |
| `tests/conftest.py` | Pins deterministic test settings, clears the Settings cache before and after every test, and overrides database sessions. |
| `tests/unit/test_database.py` | Verifies session close, rollback, metadata naming and engine disposal. |
| `tests/unit/test_errors.py` | Verifies 404, validation, custom and unknown error responses. |
| `tests/unit/test_health.py` | Verifies success, OperationalError, TimeoutError, four internal-error types and CORS behavior. |
| `tests/unit/test_settings.py` | Verifies settings validation, caching and log-format selection. |

Tests never require a developer PostgreSQL instance.

## 7. Compose profiles

| Service | Profile | Default startup |
| --- | --- | --- |
| `postgres` | default | Yes |
| `api` | default | Yes |
| `chroma` | `rag` | No |
| `ollama` | `rag` | No |
| `web` | `frontend` | No |
| `worker` | absent | No worker exists in Phase 3 |

The optional `chroma` service in `compose.test.yaml` also uses the `rag` profile. It is not required by the isolated Phase 3 unit tests.

Stage 3 startup:

```bash
docker compose up --build
```

Future profiles can be started explicitly when their implementation phase begins:

```bash
docker compose --profile rag up --build
docker compose --profile frontend up --build
```

Profiles reserve infrastructure only; they do not imply that RAG or frontend business features are implemented.

## 8. Boundary rules

1. Health is the only implemented v1 endpoint.
2. The health success payload remains stable.
3. Database and timeout failures map to `DATABASE_UNAVAILABLE`; programming errors reach the global 500 handler.
4. Session dependencies close after each request and roll back on request failure.
5. Alembic reads `Base.metadata`; model imports are added only when real models exist.
6. No worker entry point exists until a real ingestion workflow is available.
7. Future source modules are added together with their behavior and tests, not as empty shells.
