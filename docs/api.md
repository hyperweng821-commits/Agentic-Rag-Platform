# API guide

The canonical endpoint inventory is defined in `architecture.md`. Concrete request and response examples will be generated from FastAPI OpenAPI as endpoints are implemented.

Public compatibility rules:

- All endpoints use the `/api/v1` prefix.
- Error codes remain stable even when human-readable messages change.
- Breaking contract changes require a new API version or an explicit migration plan.

## Phase 3 implemented endpoint

Only the following endpoint is currently implemented:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | FastAPI and PostgreSQL readiness check |

All authentication, document, ingestion, retrieval, RAG, Agent and evaluation endpoints in the architecture document remain proposed contracts for later phases.
