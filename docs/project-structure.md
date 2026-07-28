# AgentForge — Current Project Structure

> Current implementation: Phase 3 foundation, AF-0 product boundary, AF-1
> knowledge intake, and AF-2A ingestion persistence.
> Domain status: knowledge bases, secure source-file storage, document
> metadata, durable ingestion jobs with lease/retry metadata, and the
> PostgreSQL-authoritative `DocumentChunk` model are implemented. Job execution,
> parsing, chunk production, embeddings, indexing, retrieval, RAG, Agent,
> evaluation, and workers are not implemented.

## 1. Structure policy

The repository keeps the architecture boundaries approved in Phase 1 and Phase 2, but a directory is not represented as an implemented Python package until it contains real code.

Current rules:

1. Implemented infrastructure and persistence modules are executable, typed
   and tested.
2. Future backend areas contain `.gitkeep` or a directory-level README only.
3. Future areas do not contain placeholder `__init__.py` or docstring-only Python modules.
4. The worker process is absent until AF-2C document ingestion execution.
5. Only PostgreSQL and FastAPI start in the default Compose profile.
6. ChromaDB and Ollama are reserved behind the `rag` profile.
7. React is reserved behind the `frontend` profile.

## 2. Baseline tree and implemented additions

The historical Phase 3 tree below remains useful as the pre-AF-1 baseline.
AF-1 adds real model, repository, ingestion-storage, service, schema, endpoint,
migration, and test modules in the corresponding previously reserved
directories. AF-2A extends those model and repository modules and adds a second
migration for ingestion-job metadata and `DocumentChunk`. The live source tree
is authoritative.

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

The implemented AF-1 and AF-2A additions to that baseline are:

```text
apps/api/
├── alembic/versions/
│   ├── 20260727_0001_af1_knowledge_intake.py
│   └── 20260728_0002_af2a_ingestion_foundation.py
├── app/
│   ├── api/v1/endpoints/knowledge.py
│   ├── db/
│   │   ├── models/{__init__.py,knowledge.py}
│   │   └── repositories/{__init__.py,knowledge.py}
│   ├── ingestion/{__init__.py,storage.py}
│   ├── schemas/knowledge.py
│   └── services/{__init__.py,knowledge_intake.py}
└── tests/unit/
    ├── test_knowledge_api.py
    ├── test_knowledge_models.py
    ├── test_knowledge_repositories.py
    ├── test_knowledge_service.py
    ├── test_migration.py
    └── test_storage.py
```

AF-2A deliberately adds no parser, worker, embedding, vector-store, or API
module.

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
| `apps/api/app/api/v1/endpoints/knowledge.py` | Implements the AF-1 knowledge-base, document, and ingestion-job contracts. |
| `apps/api/app/db/base.py` | Provides SQLAlchemy 2.0 DeclarativeBase and naming conventions. |
| `apps/api/app/db/session.py` | Configures AsyncEngine, async_sessionmaker, readiness query and disposal. |
| `apps/api/app/db/models/knowledge.py` | Defines AF-1 records and the AF-2A ingestion-job and document-chunk persistence model. |
| `apps/api/app/db/repositories/knowledge.py` | Provides flush-only, transaction-aware knowledge and chunk persistence queries. |
| `apps/api/app/ingestion/storage.py` | Implements bounded local source-file storage for AF-1. |
| `apps/api/app/schemas/common.py` | Defines health, validation and error response schemas. |
| `apps/api/app/schemas/knowledge.py` | Defines the unchanged AF-1 public request and response contracts. |
| `apps/api/app/services/knowledge_intake.py` | Owns AF-1 upload, deduplication, and retry use cases. |
| `apps/api/alembic/env.py` | Loads settings and Base metadata for async online/offline migrations. |
| `apps/api/alembic/versions/20260728_0002_af2a_ingestion_foundation.py` | Adds AF-2A job metadata, constraints, indexes, and authoritative chunk storage. |

## 4. Required Python package markers

Only implemented importable packages retain `__init__.py`:

| Package | Reason |
| --- | --- |
| `app` | Backend application package. |
| `app.api` | HTTP infrastructure package. |
| `app.api.v1` | Versioned API package. |
| `app.api.v1.endpoints` | Contains implemented health and AF-1 knowledge endpoints. |
| `app.core` | Contains implemented configuration and logging. |
| `app.db`, `app.db.models`, `app.db.repositories` | Contain implemented database infrastructure and persistence. |
| `app.ingestion` | Contains the consumed AF-1 local-storage adapter. |
| `app.schemas` | Contains implemented shared and knowledge API schemas. |
| `app.services` | Contains the consumed AF-1 knowledge-intake service. |
| `tests` | Backend test package. |

Future directories intentionally have no `__init__.py`, so their presence cannot be mistaken for implemented Python modules.

## 5. Reserved future directories

| Directory | Boundary only; implementation deferred |
| --- | --- |
| `app/agent/` | Agent workflow, nodes, tools and state. |
| `app/evaluation/` | RAG and answer evaluation. |
| `app/ingestion/parsers/` | AF-2B document parsing and normalization. |
| `app/llm/` | Ollama and model-provider adapters. |
| `app/observability/` | Future metrics and distributed tracing beyond current logging. |
| `app/retrieval/` | Dense, keyword, fusion and reranking logic. |
| `app/workers/` | AF-2C document-ingestion worker. |

These directories contain only `.gitkeep` or documentation. Their presence
does not imply that later AF-2 stages are implemented.

## 6. Backend tests

| File | Responsibility |
| --- | --- |
| `tests/conftest.py` | Pins deterministic test settings, clears the Settings cache before and after every test, and overrides database sessions. |
| `tests/unit/test_database.py` | Verifies session close, rollback, metadata naming and engine disposal. |
| `tests/unit/test_errors.py` | Verifies 404, validation, custom and unknown error responses. |
| `tests/unit/test_health.py` | Verifies success, OperationalError, TimeoutError, four internal-error types and CORS behavior. |
| `tests/unit/test_knowledge_api.py` | Verifies AF-1 public knowledge-intake contracts. |
| `tests/unit/test_knowledge_models.py` | Verifies AF-1 and AF-2A model defaults, relationships, constraints, and indexes. |
| `tests/unit/test_knowledge_repositories.py` | Verifies query shape, ordering, and flush-only chunk replacement. |
| `tests/unit/test_knowledge_service.py` | Verifies AF-1 orchestration, deduplication, retry, and file cleanup. |
| `tests/unit/test_migration.py` | Verifies both Alembic revisions produce reversible PostgreSQL DDL. |
| `tests/unit/test_settings.py` | Verifies settings validation, caching and log-format selection. |
| `tests/unit/test_storage.py` | Verifies secure bounded local file storage. |

Ordinary tests never require a developer PostgreSQL, Ollama, ChromaDB, MCP, or
network service.

## 7. Compose profiles

| Service | Profile | Default startup |
| --- | --- | --- |
| `postgres` | default | Yes |
| `api` | default | Yes |
| `chroma` | `rag` | No |
| `ollama` | `rag` | No |
| `web` | `frontend` | No |
| `worker` | absent | No worker exists in AF-2A |

The optional `chroma` service in `compose.test.yaml` also uses the `rag`
profile. It is not required by ordinary backend tests.

Current startup:

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

1. The health and AF-1 knowledge-intake endpoints are implemented; AF-2A adds
   no public API contract.
2. Endpoints contain no SQL or filesystem logic, services own use-case
   transactions, and repositories flush without committing.
3. PostgreSQL owns documents, jobs, lease/retry metadata, and normalized
   chunks; Chroma remains a future rebuildable index.
4. Ingestion states remain `pending`, `processing`, `completed`, and `failed`.
5. Alembic revision `20260727_0001` remains unchanged; AF-2A is a second
   reversible revision.
6. No parser, worker entry point, embedding adapter, or Chroma write exists in
   AF-2A.
7. Future source modules are added together with their behavior and tests, not
   as empty shells.
