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

Future private AF-3 operations are required to:

- expose exactly two AF-3C operations and no others:
  `POST /api/v1/knowledge-bases/{knowledge_base_id}/retrieval` with exact JSON
  fields `query` (required string) and `requested_count` (optional strict
  integer default `10`), and
  `POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve` with the
  sole required string field `citation_reference` containing the existing
  canonical `af3:citation:v1:<knowledge-base-UUID>:<chunk-UUID>:<hash>`
  structure; both use a canonical lowercase UUID path and forbid coercion,
  duplicate keys, aliases, extras, alternate endpoints, and alternate citation
  tokens;
- authenticate current session/user first, parse and authorize the exact
  target second, require `application/json` third, incrementally collect the
  body fourth, then apply strict JSON, closed schema, operation semantics, and
  retrieval/final-citation work, preserving generic `401`, hidden `404`, and
  authorized-caller `422` outcomes in that order;
- bound both POST bodies to exactly 65,536 application-body octets exposed to
  ASGI before JSON decoding; allow equality, abort immediately on byte 65,537,
  never use an unbounded `body()` followed by a length check, and perform no
  parsing/schema/normalization/retrieval/final-resolution work after overflow;
- after strict JSON decoding, closed-schema validation, exact string-type
  validation, Unicode-scalar validation, and strict UTF-8 representability,
  reject any occurrence of U+0000 before NFC; this is
  semantic validation, not normalization, and must not remove, replace,
  collapse, whitespace-map, or
  U+FFFD-map U+0000, convert it to an empty/zero-keyword query, send it to
  PostgreSQL and translate a driver/database failure, or reject all Unicode
  `Cc` controls; a literal unescaped NUL in a JSON string fails strict JSON,
  while the ASCII escape `"\u0000"` is valid JSON and reaches this semantic
  gate;
- only after the U+0000 gate, normalize `query` by NFC exactly once, the exact
  ADR-008 Unicode-whitespace trim/collapse rule, and no other transform;
  validate 1–2,048 normalized Unicode scalar values first and 1–4,096 strict
  UTF-8 bytes second, before retrieval;
- for an authenticated and initially authorized escaped-U+0000 request,
  preserve the allowed earlier authentication, canonical-target parsing,
  exact-target membership/capability authorization, media, bounded-body,
  strict-JSON, closed-schema, and exact-type gates, then return generic
  `422 VALIDATION_ERROR` with private/no-store and perform no NFC/whitespace
  normalization, keyword statements, embedding calls, Chroma/Provider calls,
  or final authoritative transactions, producing no Evidence;
- use exact P0-v1 counts: requested maximum `50`, dense over-fetch factor `4`,
  dense/Provider maximum `128`, keyword maximum `128`, unique-union maximum
  `192`, and validation batches of `64`, with the count relationships and
  equality/plus-one behavior fixed in ADR-008; for `R = 10`, configured
  `C = 40`, so `P = 40` is accepted and `P = 41` is fatal despite remaining
  below the global 128 ceiling;
- require a live authenticated principal and exactly one target knowledge
  base;
- check current PostgreSQL membership and read capability before slow
  embedding or vector-provider work;
- treat embedding and Chroma as separate resource-lifecycle barriers: after
  all initial/request work and before either call, retain no PostgreSQL
  connection, transaction, Session, or SessionTransaction and do not begin the
  final transaction; embedding failure has no keyword fallback, and controlled
  cancellation cannot leave a database resource or start later work;
- reject client-supplied document or chunk IDs as authorization inputs;
- treat every Chroma result as an untrusted, bounded candidate hint and never
  use provider filters, text, metadata, scores, or provenance as authority;
- perform no external I/O inside the final database transaction;
- enforce the unconditional current AF-3 transaction contract: the final
  authoritative PostgreSQL transaction for AF-3A, AF-3B, and AF-3C MUST use
  `REPEATABLE READ` and `READ ONLY` after external provider work; current AF-3
  permits no read-write exception, and any future exception requires a
  separately approved ADR change, a new acceptance case, and an explicit
  security and transaction review before implementation;
- prove in the real authenticated request's actual final transaction that
  `current_setting('transaction_isolation') = 'repeatable read'` and
  `current_setting('transaction_read_only') = 'on'` through the actual first
  final authorization query or an equivalent same-transaction test hook,
  without an earlier authorization-sensitive query, earlier snapshot
  acquisition, a helper transaction, the concurrent mutation actor's
  transaction, or an unrelated database session;
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
- source authoritative Evidence identity, scope, text, persisted hash, source
  identity, and provenance only from the fixed PostgreSQL snapshot, while
  deriving source ranks only from validated absolute-rank maps, fused values
  only from exact RRF, trust only from the fixed literal, and citation
  references only from authoritative target/chunk IDs and hash;
- require `Document.status = 'completed'` and a persisted non-null chunk
  `content_sha256` matching 64 lowercase hexadecimal characters;
- omit legacy null-hash chunks without dynamically hashing text or inventing a
  revision from timestamps, UUIDs, Chroma, or provider metadata;
- require the persisted hash for citation creation; make citation resolution
  start from the opaque cookie and reauthenticate the current session and
  active user rather than trust a cached/prebuilt Principal, then reauthorize
  the canonical route target and use one final PostgreSQL `REPEATABLE READ`,
  `READ ONLY` snapshot to recheck current access/eligibility/identity/hash and
  load every response field; treat caller reference components only as
  locators, return only the exact authoritative citation-resolution object,
  and perform no Provider, embedding, keyword, RRF, storage, dynamic-hash,
  cache, alternate-token, or filesystem work;
- ignore Chroma text and metadata as authorization, evidence, or citation
  authority;
- scope PostgreSQL keyword candidates in SQL and send keyword and dense
  candidates through the same final validation boundary;
- use preserved absolute one-based source ranks and exact-rational RRF with
  `RRF_K = 60`, integer cross-multiplication for ordering, display-only
  12-place round-half-even score strings, no raw-score fusion, no P0 reranker,
  and the tie order fixed in ADR-008;
- label private document content semantically as
  `untrusted_document_content`;
- ensure the AF-3 retrieval layer creates no system/developer instruction,
  authorization/scope, provider configuration, Tool Policy, tool name or
  argument, execution, approval, secret-access request, or citation authority
  from document content;
- use private/no-store behavior for every retrieval/citation success or
  failure and the same recursive exact-plus-substring secrecy scan across
  application/access/exception records, structured keys/nested values,
  traces/spans/events, HTTP/Provider transports, exposed SQL/driver
  diagnostics, and response headers/metadata/body; allowlist only exact
  intended public Evidence or citation-response field paths, never a whole
  response object; and
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

Repository truth pins raw HTTP v2 compatibility identifier
`chroma-http-v2-1.5.9` against `chromadb/chroma:1.5.9`; there is no Chroma SDK
dependency. The future query adapter must verify exact JSON version `"1.5.9"`
through `GET /api/v2/version` under the same incremental wire/decode/content-
encoding limits as the query response, then send one v2 collection `/query` request
with only `query_embeddings`, bounded `n_results`, one-target
`where.knowledge_base_id.$eq`, and `include: ["distances"]`. It must not
request documents, metadata, embeddings, URIs, data, or document filters.
The version probe has no unbounded exception: exact wire/decoded equality is
accepted, the first plus-one byte or forbidden encoding/expansion aborts
before complete materialization and `/query`, and failure returns the generic
planned `503 RETRIEVAL_UNAVAILABLE` with no fallback or partial Evidence. The exact conformance query contains one
dimension-4 fake vector `[0.25, -0.5, 0.0, 1.0]` in unchanged order; every
configuration likewise sends exactly one finite configured-dimension vector,
without truncation, padding, replacement, or duplication.

The canonical response has exactly `ids`, `embeddings`, `documents`, `uris`,
`data`, `metadatas`, `distances`, and `include`; unknown/duplicate/missing keys
are fatal. `ids` and `distances` are aligned one-query matrices,
`embeddings`/`uris`/`data` are null, `include` is exactly `["distances"]`,
and unsolicited bounded aligned documents/metadata are ignored. Strict UTF-8
without a BOM, JSON media type with no parameter or only `charset=utf-8`, and
absent/`identity` or single-token `gzip` content encoding are the only
supported wire encodings; the complete null/cardinality/type policy is
normative in ADR-008. Absolute dense rank is assigned from the original
aligned position before local validation and is never compacted.
An unsolicited document element is only null or a bounded string. An
unsolicited metadata element is only null or a shallow object with bounded
distinct string keys and string, supported finite-number, or boolean values;
nested objects/arrays, null object values, non-finite/unsupported-range
numbers, and wrong element types are fatal without broadening this grammar.

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
JSON decode. Provider wire responses use strict RFC 8259 JSON. Literal wire
tokens `NaN`, `Infinity`, and `-Infinity` are invalid JSON; a syntactically
valid JSON numeric token outside the supported finite IEEE-754 binary64
distance domain, including `1e400`, is an unsupported Provider numeric
representation.
Both categories are response-fatal before candidate iteration. A permissive
decoder must not turn the literal tokens into candidate-local values, and a
decoder that maps `1e400` to infinity must not reclassify that wire-fatal
response. Every raw numeric fixture is the complete canonical response with
only one `distances[0][0]` token changed, so it cannot false-pass on an
unrelated envelope defect. These conditions and any transport, decode, body,
nesting, structural envelope, candidate-count, position-reconstruction, or
per-field hard-limit violation produce a planned generic
`503 RETRIEVAL_UNAVAILABLE`, no Evidence, no partial result, no keyword-only
fallback, and no candidate-local continuation.

Within a bounded structurally valid response, malformed canonical IDs,
unknown/stale/cross-scope/inaccessible/ineligible candidates, individually
invalid records, and present wrong-type optional scores are candidate-local
omissions. Candidate-local non-finite handling is permitted only at the named
post-decoder typed-adapter boundary: bounded strict RFC 8259 JSON decoding has
already succeeded, and a typed provider adapter, SDK, or deterministic test
double returns a candidate score equivalent to `float("nan")`,
`float("inf")`, or `float("-inf")`. Only that candidate is omitted; other
valid candidates may continue. PostgreSQL remains the only authorization,
Evidence, provenance, and citation authority. These typed values were not
transported by conforming JSON. A typed adapter's diagnostic `None` remains
valid, but a missing/short canonical Chroma distance array is fatal. Fusion
uses the unchanged absolute list rank. Bounded Provider text/metadata
disagreement is ignored for authority. Duplicates retain the earliest source
rank. If all candidates are locally omitted and final authorization still
succeeds, the result is authorized empty Evidence.

AF-3B/AF-3C hybrid retrieval has no degradation mode: a Provider-fatal path
must discard a known eligible keyword sentinel, and a keyword/database-fatal
path must discard a known eligible dense sentinel. Positive dense-only,
keyword-only, and mixed-source fixtures prove which source supplied each
result. A later-batch, database-connection, supported database-timeout, or
final-commit failure discards all accumulated Evidence and returns the same
generic required-provider/final-database `503`.

Success and failure use one recursive scanner over ordinary messages, every
structured key/nested value, access and exception records, trace/span names/
attributes/events, HTTP and Provider transport records, exposed SQL/database/
driver diagnostics, and response headers/metadata/body. Exact equality and
substring presence both fail. Nonempty retrieval, authorized-empty retrieval,
and citation success inject success-only sentinels; fatal variants inject
Provider/database details. Only the intended exact Evidence or citation-
response field for a public value is allowlisted. No enclosing response,
header, metadata, diagnostic, or transport state is generally exempt.

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
