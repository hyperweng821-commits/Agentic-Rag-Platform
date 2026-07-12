# Phase 3 Engineering Review

Review date: 2026-07-12  
Scope: Backend Foundation only  
Business features added: none

## 1. Executive verdict

The Phase 3 backend is typed, isolated from external services during tests, and ready for continued development. The health-check exception boundary now distinguishes infrastructure failures from programming defects, the default Compose topology contains only PostgreSQL and FastAPI, and future backend areas contain no placeholder Python implementations.

The code-quality gate passes. The release verdict is **conditional pass** because the review environment has no Docker CLI: image build and container runtime behavior were not executed locally. The repository CI workflow contains the missing Compose build and health smoke test, which must pass on a Docker-capable runner before the release gate is considered fully observed.

Phase 4 has not started.

## 2. Review findings and changes

| Area | Finding | Resolution |
| --- | --- | --- |
| Health endpoint | Endpoint already caught only timeout and SQLAlchemy failures. | Kept the successful response contract and 503 mapping unchanged; expanded tests across four programming-error types. |
| Session dependency | Failed request transactions must be rolled back without changing the original error. | Retained an intentional catch that rolls back and immediately re-raises; the context manager closes the session. |
| Request middleware | Unexpected failures need structured request telemetry without changing global error mapping. | Retained an intentional catch that logs and immediately re-raises; the global handler still owns the public 500 response. |
| Global errors | Unknown errors were safely hidden but correlation was implicit in the error log. | Added the request ID explicitly to the structured exception event; the public 500 response is unchanged. |
| Worker | Historical worker was a `SystemExit` placeholder. | Confirmed that both the Python entry point and Compose worker service are absent. Only the future directory boundary remains. |
| Compose | Future services were profiled, but the API retained an unused upload volume. | Default remains `postgres` and `api`; removed the unused future volume and documented explicit profiles. |
| Developer entry points | README was not sufficient as the primary clone-to-run path; Make targets mixed current and future builds. | Added a Phase 3 quick start and made API-only/current targets explicit. |
| CI | Container job built images but did not run the Phase 3 health contract. | Added Compose startup, HTTP readiness verification and unconditional teardown. |
| Python tooling | Ruff lacked an explicit first-party import boundary. | Added `known-first-party = ["app"]` and normalized affected imports. |
| Repository hygiene | Common Python build/log artifacts were not fully ignored. | Extended `.gitignore` without ignoring any source or lock file. |
| Repeatable frontend checks | Prettier scanned ignored generated output after a local build. | Added workspace-level `.prettierignore` files for generated build, coverage and test artifacts. |

## 3. Health-check exception boundary

The dependency chain is:

```text
GET /api/v1/health
  -> get_db_session
  -> check_database_connection
  -> AsyncSession.execute("SELECT 1")
```

The endpoint catches exactly:

- built-in `TimeoutError`, including expiry of `asyncio.timeout`
- `SQLAlchemyError`, including SQLAlchemy-wrapped database connection and operational errors

The public mapping is:

| Failure | HTTP status | Error code | Handler |
| --- | ---: | --- | --- |
| `OperationalError` or another `SQLAlchemyError` | 503 | `DATABASE_UNAVAILABLE` | Health endpoint |
| Health-check `TimeoutError` | 503 | `DATABASE_UNAVAILABLE` | Health endpoint |
| `RuntimeError` | 500 | `INTERNAL_SERVER_ERROR` | Global unknown-error handler |
| `AttributeError` | 500 | `INTERNAL_SERVER_ERROR` | Global unknown-error handler |
| `ValueError` | 500 | `INTERNAL_SERVER_ERROR` | Global unknown-error handler |
| `TypeError` | 500 | `INTERNAL_SERVER_ERROR` | Global unknown-error handler |

No connection URL, password, driver detail or private exception text is returned to the caller. `health.py` contains no `except Exception`. The only two intentional catch-and-rethrow boundaries are request-session rollback in `app/api/dependencies.py` and failed-request logging in `app/core/logging.py`; neither maps an error to `DATABASE_UNAVAILABLE`. Registering `Exception` as the final FastAPI handler remains the public unknown-error boundary.

## 4. Empty-module classification

The scan covered every Python source file under `apps/api/app/` and checked for docstring-only modules, `pass`, TODO markers, `NotImplementedError`, empty classes, empty functions and `SystemExit` placeholders.

### Class A — required package boundaries

These seven zero-behavior `__init__.py` files remain because their packages contain real Phase 3 code:

- `app/__init__.py`
- `app/api/__init__.py`
- `app/api/v1/__init__.py`
- `app/api/v1/endpoints/__init__.py`
- `app/core/__init__.py`
- `app/db/__init__.py`
- `app/schemas/__init__.py`

### Class B — future module boundaries

These directories remain as `.gitkeep` boundaries and do not present themselves as implemented Python packages:

- `app/agent/`
- `app/agent/nodes/`
- `app/agent/tools/`
- `app/db/models/`
- `app/db/repositories/`
- `app/evaluation/`
- `app/ingestion/`
- `app/ingestion/parsers/`
- `app/llm/`
- `app/observability/`
- `app/retrieval/`
- `app/services/`
- `app/workers/`

`app/agent/prompts/README.md` is directory documentation, not executable placeholder code.

### Class C — meaningless placeholder Python files

None remain. No source file was deleted during this review because the earlier cleanup had already removed all Class C Python files and the invalid worker.

Generated `__pycache__` data is ignored by Git and excluded from release artifacts; it is not source or a retained module.

## 5. Files modified in this review

- `.env.example`
- `.github/workflows/ci.yml`
- `.gitignore`
- `Makefile`
- `README.md`
- `compose.yaml`
- `compose.test.yaml`
- `apps/api/alembic/env.py`
- `apps/api/app/api/dependencies.py`
- `apps/api/app/api/errors.py`
- `apps/api/app/core/logging.py`
- `apps/api/pyproject.toml`
- `apps/api/tests/unit/test_database.py`
- `apps/api/tests/unit/test_errors.py`
- `apps/api/tests/unit/test_health.py`
- `apps/api/tests/unit/test_settings.py`
- `apps/api/tests/conftest.py`
- `apps/web/.prettierignore` (new)
- `docs/api.md`
- `docs/architecture.md`
- `docs/backend-foundation.md`
- `docs/deployment.md`
- `docs/development.md`
- `docs/project-structure.md`
- `docs/engineering-review.md` (new)
- `packages/api-client/.prettierignore` (new)
- `scripts/bootstrap.sh`

`alembic/env.py` and the two listed test files whose behavior did not change received only deterministic Ruff import ordering. `uv.lock` did not change because no dependency changed.

## 6. Files deleted in this review

None.

The invalid `apps/api/app/workers/ingestion_worker.py` file and its Compose service were already absent when this formal review began. They were not recreated.

## 7. Retained Phase 3 backend files

Implemented source retained:

- `app/main.py`
- `app/core/config.py`
- `app/core/logging.py`
- `app/api/dependencies.py`
- `app/api/errors.py`
- `app/api/router.py`
- `app/api/v1/router.py`
- `app/api/v1/endpoints/health.py`
- `app/db/base.py`
- `app/db/session.py`
- `app/schemas/common.py`
- the seven Class A package markers listed above

Infrastructure and tests retained:

- `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/.gitkeep`
- `Dockerfile`, `.dockerignore`, `.python-version`, `pyproject.toml`, `uv.lock`
- `tests/conftest.py`, four focused unit-test modules and necessary test boundaries
- all Class B directory boundaries listed above

Repository-level governance, architecture, frontend-shell and infrastructure assets were retained; no unrelated source was removed.

## 8. GitHub quality review

| File | Review result |
| --- | --- |
| `.gitignore` | Covers secrets, local overrides, caches, coverage, build products, logs, Node output, runtime data and editor files. `.env.example` and required `.gitkeep` files remain trackable. |
| `README.md` | Provides an honest Phase 3 status, four-command clone-to-run path, exact default services, health verification and links to detailed docs. |
| `Makefile` | Defaults to help; current `up`/`build` targets are API-focused; future RAG/frontend operations are explicit. No worker target exists. |
| `apps/api/Dockerfile` | Uses Python 3.12, locked `uv` sync, development/production targets, non-root runtime and an HTTP health check. No source change was required. |
| `compose.yaml` | Uses repository-relative build contexts and bind mounts. Default services are only `postgres` and `api`; future services are opt-in. |
| `compose.test.yaml` | Keeps optional ChromaDB infrastructure behind the `rag` profile; Phase 3 unit tests do not use it. |
| `apps/api/pyproject.toml` | Centralizes dependencies, Python 3.12 policy, strict Mypy, Ruff, pytest-asyncio and a 90% branch-coverage gate. |

The two workspace-level `.prettierignore` files prevent generated `dist`, coverage and browser-test output from contaminating repeatable formatting checks.

The intended fresh-developer path is:

```bash
git clone <repository-url> agentic-rag-platform
cd agentic-rag-platform
cp .env.example .env
docker compose up --build
```

It requires only Git and Docker Compose on the host. Paths are repository-relative, and the default stack does not require host Python, Node.js, PostgreSQL, ChromaDB or Ollama. Development credentials are explicit local-only defaults and are not suitable for production.

The review workspace is a source snapshot without `.git` metadata, so tracked-file state and a real GitHub remote could not be inspected here. The README deliberately uses `<repository-url>` until the repository is published.

## 9. Compose topology

| Service | Profile | Starts by default | Phase 3 behavior |
| --- | --- | --- | --- |
| `postgres` | default | Yes | PostgreSQL persistence and readiness |
| `api` | default | Yes | FastAPI Backend Foundation |
| `chroma` | `rag` | No | Reserved infrastructure only |
| `ollama` | `rag` | No | Reserved infrastructure only |
| `web` | `frontend` | No | Existing React shell only |
| `worker` | absent | No | Reintroduced only with real ingestion behavior |

An `ingestion` profile was not added because there is no valid worker image or command. Adding a service that exits or performs no work would violate the no-placeholder requirement. A real worker and its `ingestion` profile belong to the future ingestion phase.

Static Compose assertions confirmed the default/profile membership and repository-relative Dockerfile paths. These assertions do not replace Docker Compose parsing or runtime validation.

## 10. Test-quality review

| Requirement | Evidence | Result |
| --- | --- | --- |
| No real PostgreSQL | Health dependency is overridden with an `AsyncMock`; the test URL uses a deliberately unused local port. | Passed |
| No Docker dependency | Tests use in-process `ASGITransport`. | Passed |
| No Ollama dependency | No Ollama application import or call exists. | Passed |
| No ChromaDB dependency | No Chroma application import or call exists. | Passed |
| Settings cache isolation | Autouse fixture clears `get_settings()` before and after every test. | Passed |
| Environment isolation | `pytest_configure` pins all consumed settings and disables dotenv loading before collection; autouse fixture repeats the pinning per test. | Passed |
| Clear names | Test names state behavior and expected result. | Passed |
| Meaningful coverage | Tests assert public contracts, error boundaries, session cleanup, lifecycle disposal and setting validation. | Passed |

Targeted application-creation and health tests also passed while the launching shell supplied hostile values for every Settings field and the repository contained an intentionally malformed `.env`. This confirms that neither developer environment variables nor a developer dotenv file alter the test configuration.

## 11. Validation commands and results

Executed from `apps/api` unless noted:

```bash
export UV_CACHE_DIR=/tmp/phase3-review-uv-cache
export UV_PROJECT_ENVIRONMENT=/tmp/phase3-review-venv
uv sync --frozen --extra dev
uv lock --check
uv run ruff check .
uv run ruff format --check .
MYPY_CACHE_DIR=/tmp/phase3-review-mypy-cache \
  uv run mypy app
uv run pytest
uv run pytest --cov=app
python -m compileall app tests
APP_NAME=host-pollution APP_VERSION=99.99.99 \
  DATABASE_URL=postgresql://invalid \
  uv run pytest --no-cov -q \
    tests/unit/test_health.py::test_application_can_be_created \
    tests/unit/test_health.py::test_health_check_returns_healthy
uv build

# Repository root
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
```

Final results:

| Check | Result |
| --- | --- |
| Frozen dependency sync | Passed |
| Lock consistency | Passed |
| Ruff | Passed |
| Ruff format | Passed; 25 files already formatted |
| Strict Mypy | Passed; 18 source files |
| pytest | Passed; 24 tests |
| Coverage | 95.86%; configured minimum remains 90% |
| Hostile environment and malformed dotenv check | Passed; 2 targeted tests |
| Python compileall | Passed |
| Python source/wheel build | Passed |
| Frontend and API-client lint | Passed |
| Frontend and API-client format | Passed |
| Frontend and API-client type check | Passed |
| Frontend unit tests | Passed |
| Frontend and API-client build | Passed |

The first sandboxed `uv` attempt could not write `/root/.cache/uv`; setting a writable `/tmp` cache resolved it. The first Mypy attempt also encountered a malformed pre-existing workspace cache (`database disk image is malformed`); re-running against a new cache directory passed. A first two-test isolation probe triggered the repository-wide 90% coverage gate because only two tests were selected; both tests themselves passed, and the probe was rerun with `--no-cov`. The two full-suite runs independently passed the unchanged coverage gate. These were command-environment or diagnostic-scope effects, not project failures.

## 12. Docker and Compose validation

Neither `docker` nor `podman` is installed in the review environment.

**Docker validation was not actually executed.**

Consequently, these runtime checks remain unobserved locally:

```bash
docker compose config --quiet
docker compose build api
docker compose up -d postgres api
docker compose ps
curl http://localhost:8000/api/v1/health
docker compose down
```

Static YAML assertions passed for service/profile membership, worker absence, build paths, removed upload volume and the test ChromaDB profile. This is reported only as static Compose inspection, not as a successful Docker build or Compose runtime.

The GitHub Actions container job now performs Compose parsing, image builds, `postgres`/`api` startup, the public health request and unconditional cleanup. That workflow was configured but not executed from this source-only environment.

## 13. Current tree

```text
agentic-rag-platform/
├── .github/workflows/{ci.yml,release.yml,security.yml}
├── apps/
│   ├── api/
│   │   ├── alembic/{versions/.gitkeep,env.py,script.py.mako}
│   │   ├── app/
│   │   │   ├── agent/{nodes/.gitkeep,prompts/README.md,tools/.gitkeep,.gitkeep}
│   │   │   ├── api/{v1/{endpoints/{__init__.py,health.py},__init__.py,router.py},__init__.py,dependencies.py,errors.py,router.py}
│   │   │   ├── core/{__init__.py,config.py,logging.py}
│   │   │   ├── db/{models/.gitkeep,repositories/.gitkeep,__init__.py,base.py,session.py}
│   │   │   ├── evaluation/.gitkeep
│   │   │   ├── ingestion/{parsers/.gitkeep,.gitkeep}
│   │   │   ├── llm/.gitkeep
│   │   │   ├── observability/.gitkeep
│   │   │   ├── retrieval/.gitkeep
│   │   │   ├── schemas/{__init__.py,common.py}
│   │   │   ├── services/.gitkeep
│   │   │   ├── workers/.gitkeep
│   │   │   ├── __init__.py
│   │   │   └── main.py
│   │   ├── tests/{contract/.gitkeep,fixtures/.gitkeep,integration/.gitkeep,unit/,__init__.py,conftest.py}
│   │   ├── {.dockerignore,.python-version,Dockerfile,alembic.ini,pyproject.toml,uv.lock}
│   └── web/{.prettierignore,...}
├── docs/{adr/,api.md,architecture.md,backend-foundation.md,deployment.md,development.md,engineering-review.md,evaluation.md,project-structure.md}
├── eval/
├── infra/postgres/init/001_extensions.sql
├── packages/api-client/{.prettierignore,...}
├── sample-data/
├── scripts/
└── {.env.example,.gitignore,CONTRIBUTING.md,LICENSE,Makefile,README.md,SECURITY.md,compose.test.yaml,compose.yaml,package.json,package-lock.json}
```

The expanded, file-by-file tree remains in [project-structure.md](project-structure.md).

## 14. Deferred work and final gate

Intentionally deferred to later phases:

- authentication and users
- document upload, parsing and ingestion
- business ORM models, repositories and migrations
- Embedding and ChromaDB integration
- Ollama and LLM adapters
- retrieval, RAG and Agent workflows
- a real background worker and `ingestion` profile
- evaluation behavior and production observability
- production secrets, TLS, backups and deployment hardening

Release/environment items still to verify:

- execute the Docker/Compose smoke sequence on a Docker-capable host
- observe the updated GitHub Actions workflow after the repository is published
- replace the README clone placeholder with the real GitHub URL

**Phase 3 Complete standard: conditional pass.** Code, typing, tests, coverage, structure and documentation meet the Phase 3 bar. Full acceptance requires only the unexecuted Docker/Compose smoke gate; no Phase 4 implementation is required to close it.
