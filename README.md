# AgentForge

AgentForge is a local-first, observable and policy-controlled AI agent runtime
for private engineering workflows.

## Project status

AgentForge currently includes the completed Phase 3 application foundation,
AF-0 product boundary, AF-1 private document intake, the AF-2A persistence
foundation, AF-2B durable document processing with rebuildable vector
indexing, and the minimal AF-2S1 authenticated knowledge-access boundary. It is
not production-ready. Retrieval, agent, and RAG capabilities described in the
roadmap remain plans.

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
- bounded retry, progress, claim, lease, and retry-scheduling job metadata
- text, Markdown, and extractable-text PDF parsing
- deterministic normalization and overlapping chunk production
- PostgreSQL-authoritative ordered chunks with hashes and source provenance
- PostgreSQL-safe worker claiming, bounded retries, and expired-lease recovery
- Ollama embedding and Chroma vector-store adapters behind explicit boundaries
- idempotent document and knowledge-base vector-index rebuilds
- operator-provisioned local users with Argon2id password hashes
- opaque, expiring and revocable server-side sessions with CSRF protection
- owner/editor/viewer knowledge-base memberships and SQL-scoped object access
- fail-closed legacy knowledge bases with an explicit operator claim command

### Planned only

- hybrid retrieval
- Agent Runtime
- Tool Registry
- tool policies
- approval workflow
- structured Agent Trace
- evaluation
- MCP
- memory
- AF-2S2 external identity and production operational hardening

Directories retained with `.gitkeep` reserve possible future locations; they are
not implementations.

AF-1 accepts and stores source files and creates durable jobs. AF-2A added the
schema and repository foundation while preserving the `pending`, `processing`,
`completed`, and `failed` states. AF-2B now claims those jobs, parses only
server-managed artifacts, writes deterministic chunks to PostgreSQL, generates
embeddings through Ollama, and maintains Chroma as a derived index. PostgreSQL
remains authoritative, so the vector index can be rebuilt for one document or
one knowledge base without an HTTP retrieval API.

AF-2S1 requires a live active-user session for every knowledge API. Any active
user may create a knowledge base and becomes its owner. Owners and editors can
read, upload, and retry; viewers can read. Non-member resources are returned as
`404`, and Chroma metadata never grants access. There is no public registration
or frontend authentication UI.

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

The default command starts only `postgres` and `api`. PostgreSQL is internal to
Compose, while the API binds only to `127.0.0.1`. When both containers are
healthy, verify the public health endpoint:

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

Apply database migrations from the repository root:

```bash
docker compose up -d
docker compose exec api uv run alembic upgrade head
docker compose exec api uv run alembic current
```

Create the first local user through the operator CLI. It prompts for a password
without echoing it:

```bash
docker compose exec api uv run python -m app.cli.security \
  bootstrap-user --email owner@example.com
```

Existing pre-AF-2S knowledge bases intentionally remain inaccessible until an
operator previews and applies an explicit claim:

```bash
docker compose exec api uv run python -m app.cli.security \
  claim-legacy-knowledge-bases --owner-email owner@example.com --dry-run
```

```bash
docker compose down
```

Equivalent helpers are `make up`, `make up-rag`, and `make up-frontend`.
`make up-rag` starts the Ollama and Chroma infrastructure consumed by AF-2B;
it does not pull the configured embedding model automatically. The frontend
profile remains an application shell and does not imply that planned retrieval
or agent capabilities exist. PostgreSQL, Chroma, and Ollama have no
host-published ports in the default project; the API and optional Web service
bind only to loopback.

## Local backend development

Prerequisites:

- Python 3.12
- uv `>=0.9,<1`
- PostgreSQL

```bash
cp .env.example .env
cd apps/api
uv sync --frozen --extra dev
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Direct host-side FastAPI development requires a separately reachable
PostgreSQL URL. The default Compose PostgreSQL service is deliberately not
published to the host. For normal Compose development, run the API in its
container and access the database with:

```bash
docker compose exec postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## Quality checks

Run backend checks from `apps/api`:

```bash
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
python -m compileall app tests
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
Live PostgreSQL tests opt in through `AF2A_TEST_DATABASE_URL`; CI supplies it
and treats a missing value as a failure rather than a skip.

## Repository map

| Path | Responsibility |
| --- | --- |
| `apps/api` | FastAPI, AF-1 intake, AF-2 ingestion/indexing, migrations, workers, and backend tests |
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
- [Knowledge-access boundary decision](docs/adr/007-knowledge-access-boundary.md)
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
