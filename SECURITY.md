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

## Required future AF-3 retrieval boundary

AF-3 remains planned and unimplemented. ADR-008 and the retrieval security
acceptance specification define requirements for later implementation; a
documentation decision does not provide a runtime control.

Future private retrieval is required to:

- require a live authenticated principal and exactly one target knowledge
  base;
- check current PostgreSQL membership and read capability before slow
  embedding or vector-provider work;
- reject client-supplied document or chunk IDs as authorization inputs;
- treat every Chroma result as an untrusted, bounded candidate hint and never
  use provider filters, text, metadata, scores, or provenance as authority;
- perform no external I/O inside the final database transaction;
- begin one final PostgreSQL `REPEATABLE READ`, normally `READ ONLY`,
  transaction after external provider work;
- use that transaction's first authoritative statement to acquire one fixed
  snapshot and recheck session validity, active-user state, exact target,
  membership, and current read capabilities;
- sort the unique canonical candidate union by chunk UUID, split it into
  deterministic contiguous validation batches, and validate every batch in
  that same snapshot;
- load all authoritative Evidence content and provenance in that transaction,
  with no authorization-sensitive reload after commit;
- discard all accumulated candidates after any authorization, batch,
  transaction, or database failure and never return partial Evidence;
- source authoritative evidence text, content hash, source identity,
  provenance, and citation resolution only from PostgreSQL;
- require `Document.status = 'completed'` and a persisted non-null chunk
  `content_sha256` matching 64 lowercase hexadecimal characters;
- omit legacy null-hash chunks without dynamically hashing text or inventing a
  revision from timestamps, UUIDs, Chroma, or provider metadata;
- require the persisted hash for citation creation and current reauthorized
  citation resolution;
- ignore Chroma text and metadata as authorization, evidence, or citation
  authority;
- scope PostgreSQL keyword candidates in SQL and send keyword and dense
  candidates through the same final validation boundary;
- use deterministic one-based RRF with `RRF_K = 60`, no raw-score fusion, no
  P0 reranker, and the tie order fixed in ADR-008;
- label private document content semantically as
  `untrusted_document_content`;
- ensure the AF-3 retrieval layer creates no system/developer instruction,
  authorization/scope, provider configuration, Tool Policy, tool name or
  argument, execution, approval, secret-access request, or citation authority
  from document content;
- use private/no-store cache behavior and content-free normal retrieval logs;
  and
- implement the adversarial candidate-manipulation, concurrency,
  prompt-injection, privacy, error, and citation fixtures defined in
  `docs/retrieval-security-acceptance.md`.

The fixed final snapshot is the request linearization point. Session, user,
membership, capability, document, or chunk changes committed before snapshot
acquisition are visible. Authentication loss produces generic `401`; current
target access loss produces hidden `404`; candidate ineligibility causes
non-disclosing omission. Changes committed after acquisition govern later
requests and do not retroactively cancel the current response. This rule does
not claim asynchronous cancellation of Python, embedding, Chroma, or response
serialization.

The initial P0-v1 provider-response hard ceilings are:

| Bound | Ceiling |
| --- | ---: |
| Raw/wire response | 1,048,576 bytes |
| Decoded/decompressed response | 2,097,152 bytes |
| Candidate ID | 128 UTF-8 bytes |
| Individual untrusted string | 4,096 UTF-8 bytes |
| Metadata entries per candidate | 32 |
| Metadata key | 128 UTF-8 bytes |
| Metadata scalar/string value | 1,024 UTF-8 bytes |
| JSON nesting depth | 16 |

The adapter rejects an excessive declared length before body read, streams and
counts raw bytes when a length is absent or dishonest, enforces both wire and
decoded bounds for compression, and never starts with an unbounded full-body
JSON decode. A transport, decode, body, nesting, structural envelope,
candidate-count, position-reconstruction, or per-field hard-limit violation is
a whole-response failure: planned generic `503 RETRIEVAL_UNAVAILABLE`, no
partial dense result, no Evidence, and no keyword-only fallback.

Within a bounded structurally valid response, malformed canonical IDs,
unknown/stale/cross-scope/inaccessible/ineligible candidates, individually
invalid records, and present wrong-type or non-finite optional scores are
candidate-local omissions. A missing score remains valid; fusion uses list
rank. Bounded provider text/metadata disagreement is ignored for authority.
Duplicates retain the earliest source rank. If all candidates are locally
omitted and final authorization still succeeds, the result is authorized empty
Evidence.

Document text may contain prompt-injection attempts even when an owner uploaded
it, ingestion completed, PostgreSQL stores it, it has a valid citation, or it
ranks first. AF-3 may return such text only as quoted untrusted evidence. It
must not let content change policy, authorization, execution, provider
configuration, citations, or trusted instructions.

This planned semantic boundary is not a claim of complete prompt-injection
prevention or hostile-document containment. Every later RAG, ChatModel, Agent
Runtime, or tool-consuming phase must add its own future consuming-phase
acceptance cases proving it does not elevate untrusted Evidence. Advanced
prompt-injection detection, model/runtime-specific consumer guardrails, parser
sandboxing, separate worker/database roles, production quotas and rate limits,
production secret management, TLS, and broader hostile-document resource
containment remain AF-2S2/P1 work.

All current owner/editor/viewer members have the relevant retrieval read
capabilities. The generic API framework can represent `403`, but AF-3 must not
fabricate a current member-without-read-capability fixture. Current non-member
and hidden-target behavior remains generic `404`; a future reachable retrieval
`403` requires an approved role/policy change and a new acceptance fixture.

The documentation governance sequence in ADR-008 and `docs/roadmap.md` must
complete through merge to `main`, local synchronization, and a separate
implementation-start authorization before an AF-3A branch is created. A local
review PASS, a local commit, or an open/merged design PR does not authorize
implementation.

## Known deferred work

AgentForge is not production-ready. AF-2S2/P1 retains SSO and external identity
providers, MFA, password reset, email verification, organization and advanced
membership administration, enterprise audit retention, separate
worker/database roles, hostile-document resource containment, TLS and
production secret management, and additional deployment hardening.

AF-3 retrieval, RAG, Agent Runtime, tools, and approvals are unimplemented.
