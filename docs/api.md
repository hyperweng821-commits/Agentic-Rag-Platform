# API guide

The canonical endpoint inventory is defined in `architecture.md`. Concrete request and response examples will be generated from FastAPI OpenAPI as endpoints are implemented.

Public compatibility rules:

- All endpoints use the `/api/v1` prefix.
- Error codes remain stable even when human-readable messages change.
- Breaking contract changes require a new API version or an explicit migration plan.

## Implemented endpoints

The Phase 3 health endpoint and AF-1 knowledge-intake endpoints are implemented:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | FastAPI and PostgreSQL readiness check |
| `POST` | `/api/v1/knowledge-bases` | Create a knowledge base |
| `GET` | `/api/v1/knowledge-bases` | List knowledge bases, oldest-first, with bounded pagination |
| `GET` | `/api/v1/knowledge-bases/{id}` | Retrieve one knowledge base |
| `POST` | `/api/v1/knowledge-bases/{id}/documents` | Stream and store one PDF, Markdown or text document |
| `GET` | `/api/v1/knowledge-bases/{id}/documents` | List document metadata with bounded pagination |
| `GET` | `/api/v1/documents/{id}` | Retrieve document metadata |
| `GET` | `/api/v1/ingestion-jobs/{id}` | Retrieve durable job status |
| `POST` | `/api/v1/ingestion-jobs/{id}/retry` | Idempotently requeue the same failed job |

New uploads return HTTP 201. An identical SHA-256 within the same knowledge
base returns the existing document and job with HTTP 200 and `duplicate: true`.
Files are limited by `MAX_UPLOAD_SIZE_BYTES` and responses never expose host
storage paths.

AF-1 creates pending jobs but does not execute them. Authentication, parsing,
chunks, embeddings, indexing, retrieval, RAG, Agent, tool, approval and
evaluation endpoints remain proposed contracts for later phases.
