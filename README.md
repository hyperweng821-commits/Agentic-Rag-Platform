# AgentForge

AgentForge is a local-first, observable and policy-controlled AI agent runtime
for private engineering workflows.

## Project status

AgentForge currently includes the completed Phase 3 application foundation,
AF-0 product boundary, and AF-1 private document intake with durable PostgreSQL
jobs. It is not production-ready, and later ingestion, retrieval, agent, and
RAG capabilities described in the roadmap remain plans.

### Implemented now

- FastAPI application foundation
- typed configuration
- async PostgreSQL infrastructure
- health and readiness behavior
- structured logging and request correlation
- unified error handling
- React and Vite foundation
- Docker and CI foundations
- knowledge-base records and metadata APIs
- secure local PDF, Markdown and text upload
- streamed SHA-256 deduplication within a knowledge base
- durable pending ingestion-job records and idempotent failed-job retry

### Planned only

- document parsing and ingestion execution
- chunks
- embeddings
- Chroma indexing
- hybrid retrieval
- Agent Runtime
- Tool Registry
- tool policies
- approval workflow
- structured Agent Trace
- evaluation
- MCP
- memory

Directories retained with `.gitkeep` reserve possible future locations; they are
not implementations.

AF-1 accepts and stores source files and creates durable jobs, but no worker
executes those jobs yet. Uploaded documents therefore remain pending until AF-2
adds the explicitly deferred processing pipeline.

## Quick start with Docker

Prerequisites:

- Git
- Docker Engine with Docker Compose v2

```bash
git clone <repository-url> agentforge
cd agentforge
cp .env.example .env
docker compose up --build
```

The default command starts only `postgres` and `api`. When both containers are
healthy, verify the backend:

```bash
curl http://localhost:8000/api/v1/health
```

The compatibility response remains:

```json
{
  "status": "healthy",
  "service": "agentic-rag-backend",
  "version": "0.1.0",
  "database": "healthy"
}
```

API documentation is available at <http://localhost:8000/docs>.

Uploaded files use the local `upload_data` volume. Configure
`MAX_UPLOAD_SIZE_BYTES` to change the default 10 MiB per-file limit.

```bash
docker compose down
```

Equivalent helpers are `make up`, `make up-rag`, and `make up-frontend`.
The latter two expose optional infrastructure or the frontend shell; they do
not imply that planned product capabilities exist.

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

## Quality checks

Run backend checks from `apps/api`:

```bash
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
python -m compileall app
```

Run frontend checks from the repository root:

```bash
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
npm run test:e2e
```

Ordinary unit tests do not require Ollama, ChromaDB, MCP, or network access.

## Repository map

| Path | Responsibility |
| --- | --- |
| `apps/api` | FastAPI foundation, AF-1 intake domain, migration, and backend tests |
| `apps/web` | React application shell |
| `packages/api-client` | TypeScript API-client package boundary |
| `docs` | Product boundary, architecture, roadmap, and decisions |
| `eval` | Reserved future evaluation data and reports |
| `infra` | Local infrastructure initialization assets |

## Documentation

- [Approved baseline](docs/baseline.md)
- [Product definition](docs/product.md)
- [Roadmap](docs/roadmap.md)
- [System architecture](docs/architecture.md)
- [Backend foundation](docs/backend-foundation.md)
- [Development guide](docs/development.md)
- [Engineering review](docs/engineering-review.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Configuration and secrets

`.env.example` contains local development defaults only. Copy it to `.env`;
never commit `.env`, credentials, private documents, or production data.

## License

This project is licensed under the [MIT License](LICENSE).
