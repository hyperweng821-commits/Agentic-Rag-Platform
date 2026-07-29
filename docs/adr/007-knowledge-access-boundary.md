# ADR-007: Establish the knowledge-access boundary before retrieval

- Status: Accepted
- Date: 2026-07-28

## Context

AF-1 and AF-2 store and process private documents, but their original HTTP
surface had no authenticated principal or object-level access boundary.
Introducing retrieval first would make a document UUID, a derived Chroma
record, or an overly broad query sufficient to cross knowledge-base
boundaries.

The recruiting workflow needs a small local-first boundary now. It does not
need a general-purpose identity platform. SSO, external identity providers,
public registration, password recovery, MFA, organization administration, and
advanced membership administration remain P1 work.

## Decision

AF-2S1 adds local users with normalized email addresses and Argon2id password
hashes. Users are provisioned only through an operator CLI; there is no public
registration endpoint.

Authentication uses opaque, cryptographically random server-side sessions
instead of JWTs. PostgreSQL stores only SHA-256 digests of the session and CSRF
tokens. Sessions expire, can be revoked, and stop working when their user is
inactive. The raw session token is sent in an `HttpOnly` cookie. A separate
frontend-readable CSRF cookie is bound to the same session, and
state-changing authenticated requests must supply its value in the
`X-CSRF-Token` request header. Both cookies use the configured `SameSite` and
`Secure` policy; the session cookie is scoped to `/api/v1`.

Opaque sessions were selected because immediate logout, operator revocation,
bounded expiry, and inactive-user enforcement are server-side requirements.
They avoid introducing refresh-token rotation and distributed JWT revocation
before those mechanisms have a consumer.

Public registration is excluded because local operator provisioning is the
only current account-lifecycle requirement; exposing remote account creation
would add abuse and verification surfaces without a consuming feature.

Argon2 verification and rehashing run outside database transactions on one
application-owned bounded executor. The default permits two concurrent Argon2
jobs per process. Login uses a short primitive-snapshot read followed, after
password work, by a short locked write that rechecks active state and the
observed hash before it updates a stale hash and creates a session.

Authorization uses knowledge-base memberships instead of a single
`owner_id`. This supports the first real collaboration roles without requiring
schema replacement later:

| Capability | Owner | Editor | Viewer |
| --- | --- | --- | --- |
| Create a knowledge base | Any active user | Any active user | Any active user |
| Read knowledge-base metadata | Yes | Yes | Yes |
| Read document and ingestion-job metadata | Yes | Yes | Yes |
| Upload a document | Yes | Yes | No |
| Retry a failed ingestion job | Yes | Yes | No |

The capability policy owns these mappings. HTTP endpoints do not contain
role-name conditionals.

User-facing repository queries include membership scope in SQL. Documents are
scoped through their knowledge base, and ingestion jobs are scoped through
their document and knowledge base. An object that is absent and an object
hidden by membership both return `404`. An authenticated member who can see an
object but lacks the requested capability receives `403`.

Authentication and CSRF failures follow this public contract:

- missing, malformed, unknown, expired, or revoked sessions, and inactive
  users: `401`;
- missing, malformed, or mismatched CSRF proof on an authenticated write:
  `403`;
- absent or non-member objects: `404`;
- visible objects for a member without the required capability: `403`.

Creating a knowledge base creates its owner membership in the same database
transaction. Existing knowledge bases are not assigned a fabricated owner by
the migration. They fail closed in user-facing list and lookup operations
until an operator explicitly claims unowned knowledge bases for an existing
user.

PostgreSQL remains authoritative. Chroma is an unauthenticated, rebuildable
derived index and can never establish identity, membership, document status,
or authorization. Future retrieval must scope candidates through PostgreSQL
and re-authorize every result before returning document content.

User-facing scoped repositories and worker/internal repositories remain
explicitly separate. The ingestion worker can continue processing legacy
durable jobs without pretending to act as an end user, while HTTP code cannot
accidentally use unrestricted worker queries.

The default Compose project no longer publishes PostgreSQL, Chroma, or Ollama
to the host. API and Web development ports bind to loopback. This reduces the
default exposure surface but is not a production deployment claim.

Private authentication and knowledge responses, including bounded 401, 403,
and scoped 404 failures, are marked `Cache-Control: private, no-store`.

## Consequences

Private-document retrieval cannot begin until this boundary is implemented and
tested. Legacy data remains durable and processable internally but invisible
to user APIs until explicitly claimed. Revocation and CSRF checks require a
PostgreSQL lookup, which is an intentional correctness tradeoff for this
local-first modular monolith.

AF-2S2 remains P1. It includes SSO and external identity providers, MFA,
password reset, email verification, organization and advanced membership
administration, enterprise audit retention, separate worker/database roles,
hostile-document resource containment, production secret/TLS configuration,
and further deployment hardening.

AF-3 retrieval, RAG, Agent Runtime, tools, and approvals remain unimplemented.
