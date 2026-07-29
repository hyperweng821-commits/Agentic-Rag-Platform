# API guide

The canonical endpoint inventory is defined in `architecture.md`. Concrete request and response examples will be generated from FastAPI OpenAPI as endpoints are implemented.

Public compatibility rules:

- All endpoints use the `/api/v1` prefix.
- Error codes remain stable even when human-readable messages change.
- Breaking contract changes require a new API version or an explicit migration plan.

## Implemented endpoints

The health, AF-2S1 authentication, and authenticated knowledge-intake
endpoints are implemented:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health` | FastAPI and PostgreSQL readiness check |
| `POST` | `/api/v1/auth/login` | Authenticate a local user and set session and CSRF cookies |
| `POST` | `/api/v1/auth/logout` | Revoke the current session and clear both cookies |
| `GET` | `/api/v1/auth/me` | Return the current authenticated user contract |
| `POST` | `/api/v1/knowledge-bases` | Create a knowledge base and owner membership atomically |
| `GET` | `/api/v1/knowledge-bases` | List visible knowledge bases, oldest-first, with bounded pagination |
| `GET` | `/api/v1/knowledge-bases/{id}` | Retrieve one visible knowledge base |
| `POST` | `/api/v1/knowledge-bases/{id}/documents` | Stream and store one authorized PDF, Markdown or text document |
| `GET` | `/api/v1/knowledge-bases/{id}/documents` | List visible document metadata with bounded pagination |
| `GET` | `/api/v1/documents/{id}` | Retrieve visible document metadata |
| `GET` | `/api/v1/ingestion-jobs/{id}` | Retrieve visible durable job status |
| `POST` | `/api/v1/ingestion-jobs/{id}/retry` | Idempotently requeue an authorized failed job |

`GET /api/v1/health` and `POST /api/v1/auth/login` are unauthenticated.
Authentication endpoints do not provide public registration.

Login accepts an email and password. A successful login sets
`agentforge_session` as an `HttpOnly` cookie and `agentforge_csrf` as a
frontend-readable cookie by default. Both use `SameSite=Strict` by default and
follow the configured `Secure` policy. The session cookie is scoped to
`/api/v1`; the CSRF cookie is scoped to `/` so the frontend can read and mirror
it into the request header. Cookie names are configurable.
The login and `/auth/me` JSON bodies contain only `id` and normalized `email`;
the internal session identifier, raw tokens, and persisted token digests are
never public response fields.

Every other endpoint in the table requires a live session for an active user.
State-changing authenticated requests, including logout, must copy the raw
CSRF cookie value into the `X-CSRF-Token` header. The server validates it
against the digest bound to the current session. Login itself does not require
CSRF proof.

Authorization is capability-based:

| Operation | Owner | Editor | Viewer |
| --- | --- | --- | --- |
| Read knowledge-base, document, and job metadata | Yes | Yes | Yes |
| Upload a document | Yes | Yes | No |
| Retry a failed job | Yes | Yes | No |

Any active authenticated user may create a knowledge base and becomes its
owner. There are no membership-management HTTP endpoints.

Public access failures are intentionally bounded:

- a missing, malformed, unknown, expired, or revoked session, or an inactive
  user, returns `401`;
- missing or invalid CSRF proof returns `403`;
- an absent resource and an existing resource outside the principal's
  memberships both return the same `404`;
- a member who can see a resource but lacks the requested capability receives
  `403`.

Login, logout, `/auth/me`, every authenticated knowledge response, and private
API error responses use `Cache-Control: private, no-store`. Public health
remains unauthenticated and outside this private cache policy.

New uploads return HTTP 201. An identical SHA-256 within the same knowledge
base returns the existing authorized document and job with HTTP 200 and
`duplicate: true`. Files are limited by `MAX_UPLOAD_SIZE_BYTES`. Response
bodies never expose host storage paths, password hashes, raw session tokens,
or session/CSRF digests.

AF-2 executes pending ingestion jobs through the worker, but it exposes no
processing or rebuild HTTP endpoint. Retrieval, RAG, Agent, tool, approval and
evaluation endpoints remain proposed contracts for later phases. AF-3 is
unimplemented.
