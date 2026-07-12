# Agentic RAG Platform

An observable and locally deployable Agentic RAG platform being built with React, FastAPI, PostgreSQL, ChromaDB, Docker and Ollama.

## Project status

**Phase 3 — Backend Foundation**

Implemented and tested:

- typed configuration with Pydantic Settings
- FastAPI application factory and lifespan management
- SQLAlchemy 2.0 asynchronous PostgreSQL engine and sessions
- stable `/api/v1` versioning
- PostgreSQL-backed readiness endpoint
- structured logging and request correlation
- unified 404, validation, application and unknown-error responses
- CORS configuration
- asynchronous Alembic environment
- isolated unit tests and 90% coverage gate
- Docker and GitHub Actions foundations

Not implemented yet:

- users and authentication
- document upload and ingestion
- Embedding and ChromaDB access
- Ollama integration
- retrieval, RAG and Agent workflows
- background workers
- evaluation features

Future directories are retained with `.gitkeep` or documentation and contain no placeholder Python implementations.

## Quick start with Docker

Prerequisites:

- Git
- Docker Engine with Docker Compose v2

After copying the repository HTTPS URL from GitHub:

```bash
git clone <repository-url> agentic-rag-platform
cd agentic-rag-platform
cp .env.example .env
docker compose up --build
```

No host Python, Node.js, PostgreSQL, Ollama or ChromaDB installation is required for the default Phase 3 startup.

The default command starts exactly:

- `postgres`
- `api`

When both containers are healthy, verify the backend:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "agentic-rag-backend",
  "version": "0.1.0",
  "database": "healthy"
}
```

API documentation is available at <http://localhost:8000/docs>.

Stop the stack with:

```bash
docker compose down
```

Equivalent helper commands are available:

```bash
make up
make up-rag
make up-frontend
```

`make up` and `scripts/bootstrap.sh` explicitly start only `postgres` and `api`.

## Optional future infrastructure

These profiles expose infrastructure only; they do not imply that future business behavior is implemented.

Start ChromaDB and Ollama with the backend:

```bash
docker compose --profile rag up --build
# or: make up-rag
```

Start the React shell with the backend:

```bash
docker compose --profile frontend up --build
# or: make up-frontend
```

No worker service exists in Phase 3. It will be introduced only with a real ingestion workflow.
Neither the default startup nor the bootstrap script downloads Ollama models.

## Local backend development

Prerequisites:

- Python 3.12
- uv `>=0.9,<1`
- PostgreSQL, normally started through Docker Compose

```bash
cp .env.example .env
docker compose up -d postgres
cd apps/api
uv sync --frozen --extra dev
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Backend quality checks

Run from `apps/api`:

```bash
uv sync --frozen --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
uv run pytest --cov=app
python -m compileall app tests
```

The tests use dependency overrides and mocks. They do not require PostgreSQL, Docker, ChromaDB or Ollama.

## Repository map

| Path | Responsibility |
| --- | --- |
| `apps/api` | FastAPI backend foundation, Alembic and backend tests |
| `apps/web` | React application shell, isolated behind the `frontend` profile |
| `packages/api-client` | TypeScript API-client package boundary |
| `docs` | Architecture, ADRs, development and engineering reports |
| `eval` | Future evaluation datasets and generated reports |
| `infra` | Local infrastructure initialization assets |

## Documentation

- [System architecture](docs/architecture.md)
- [Current project structure](docs/project-structure.md)
- [Backend foundation](docs/backend-foundation.md)
- [Development guide](docs/development.md)
- [Engineering review](docs/engineering-review.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Configuration and secrets

`.env.example` contains local development defaults only. Copy it to `.env`; never commit `.env`, credentials, private documents or production data.

Production deployments must replace all development credentials through environment variables or a secret-management system.

## License

This project is licensed under the [MIT License](LICENSE).
