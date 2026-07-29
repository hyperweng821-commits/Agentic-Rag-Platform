# Security Policy

## Supported versions

Security updates are applied to the latest release on `main`.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub private vulnerability reporting after the repository is published.

Never commit passwords, API keys, private documents, model data or production configuration. Use `.env.example` only as a schema for local settings.

## Implemented local knowledge boundary

AF-2S1 provides a bounded local-first access boundary:

- operators provision local users; there is no public registration;
- passwords are stored only as Argon2id hashes;
- concurrent Argon2 verification and rehash work is bounded per API process
  and runs without retaining a database transaction;
- SQL bound parameters remain redacted even when statement echoing is enabled;
- authentication uses expiring and revocable opaque server-side sessions;
- only SHA-256 digests of session and CSRF tokens are persisted;
- the session cookie is `HttpOnly`, and authenticated writes require
  session-bound CSRF proof;
- owner/editor/viewer knowledge-base memberships scope knowledge bases,
  documents, and ingestion jobs in PostgreSQL queries;
- hidden and absent objects share the same public `404`;
- unowned legacy knowledge bases fail closed until explicitly claimed by an
  operator.
- private authentication and knowledge responses use
  `Cache-Control: private, no-store`.

PostgreSQL is the authorization source. Chroma contains rebuildable derived
data and must never establish identity, membership, document state, or access.
Future retrieval must re-authorize every Chroma candidate through PostgreSQL
before returning private content.

The default Compose project does not publish PostgreSQL, Chroma, or Ollama.
Development API and Web ports bind to `127.0.0.1`. These local defaults are
defense in depth, not a production security claim.

## Known deferred work

AgentForge is not production-ready. AF-2S2/P1 retains SSO and external identity
providers, MFA, password reset, email verification, organization and advanced
membership administration, enterprise audit retention, separate
worker/database roles, hostile-document resource containment, TLS and
production secret management, and additional deployment hardening.

AF-3 retrieval, RAG, Agent Runtime, tools, and approvals are unimplemented.
