# AgentForge roadmap

AF-0, AF-1, AF-2A, the explicitly approved end-to-end AF-2B scope, and the
minimal AF-2S1 knowledge-access boundary are implemented. Current `main` also
contains two partial AF-3A prerequisites: the pure retrieval-request validator
and `SessionAuthenticationProof`. AF-3A is not complete; all other AF-3 runtime
work remains planned. Interfaces are introduced only with their first
consuming feature. No phase begins before the previous phase meets its
acceptance criteria. P1 work cannot block the P0 recruiting demo.

## AF-0 — Product boundary and safe branding

**Objective:** Establish the product boundary without changing Phase 3
functionality.

**Included scope:** Current uncommitted work: verified Phase 3 baseline,
engineering rules, public AgentForge branding, product definition, roadmap,
and architecture decisions.

**Explicit exclusions:** Business functionality, dependencies, migrations,
runtime contracts, tools, and release claims.

**Acceptance criteria:** Documentation distinguishes implemented Phase 3,
planned P0, deferred P1, and excluded scope; presentation branding is safe;
compatibility identifiers remain unchanged.

**Proposed commit message:** `docs: define AgentForge product boundary`

## AF-1 — Knowledge intake and durable jobs

**Status:** Implemented.

**Objective:** Add planned private document intake with durable job records.

**Included scope:** `KnowledgeBase`, `Document`, `IngestionJob`, SQLAlchemy
models, repositories, services, a local file-storage boundary, secure upload
API, SHA-256 deduplication, idempotency, the first Alembic migration, and tests.

**Explicit exclusions:** Chunks, embeddings, Chroma, Agent Runtime, and tools.

**Implemented result:** Upload validation, durable records, SHA-256
deduplication, idempotent retry transitions, local storage, a reversible
migration, and deterministic tests. Jobs are created but not executed; parsing
and later ingestion work begin in AF-2.

**Proposed commit message:** `feat(knowledge): add private document intake and durable jobs`

## AF-2 — Durable ingestion and vector indexing

AF-2 is delivered in bounded stages so its persistence, deterministic
transformation, execution, adapter, and integration concerns remain separate.

### AF-2A — Schema and persistence foundation

**Status:** Implemented.

**Objective:** Prepare PostgreSQL for durable ingestion without executing the
pipeline.

**Included scope:** Preserve the AF-1 `pending`, `processing`, `completed`, and
`failed` states; add maximum-attempt, progress, claim, lease, and retry
scheduling metadata; add the PostgreSQL-authoritative `DocumentChunk` model;
add constraints, indexes, a reversible migration, repository primitives, and
focused tests.

**Explicit exclusions:** Parsing, text normalization, chunking algorithms,
workers, polling, job claiming, embeddings, Chroma writes, retrieval, and API
changes.

**Implemented result:** Existing AF-1 records remain compatible. Future work
can locate queued/retryable jobs and expired leases efficiently, while ordered
normalized chunks have stable UUIDs and a unique document/index identity.

**Proposed commit message:** `feat(ingestion): add AF-2A persistence foundation`

### AF-2B — Deterministic processing and rebuildable vector indexing

**Status:** Implemented.

**Objective:** Turn the AF-2A durable foundation into an executable,
deterministic, and rebuildable ingestion pipeline.

**Included scope:** Isolated text, Markdown, and extractable-text PDF parsers;
canonical normalization; deterministic overlapping chunks with hashes and
source provenance; transactional chunk replacement; PostgreSQL-safe claiming,
leases, bounded retries, cancellation, and expired-work recovery; explicit
`EmbeddingModel` and `VectorStore` boundaries with deterministic fakes; Ollama
embeddings; idempotent Chroma indexing; and document/knowledge-base rebuild
commands.

**Implemented result:** Supported managed files produce deterministic
PostgreSQL-authoritative chunks. The worker uses short transactions for claims
and lifecycle transitions, never spans slow parser/provider work with an open
transaction, and does not mark completion before vector indexing succeeds.
Chroma vector IDs derive from durable chunks and the index can be regenerated
without treating Chroma as authoritative.

**Explicit exclusions:** Retrieval APIs, semantic or hybrid search, RAG,
reranking, Agent Runtime, tools, OCR, arbitrary URL ingestion, and
client-provided filesystem paths.

**Acceptance criteria:** Supported files produce deterministic authoritative
chunks; jobs recover through bounded leases and retries; Chroma rebuilds from
PostgreSQL; deterministic fake-adapter, lifecycle, concurrency, and
cancellation tests pass.

**Proposed commit message:** `feat(ingestion): add deterministic processing and rebuildable indexing`

## AF-2S — Knowledge-access security boundary

AF-2S separates the minimal P0 boundary required before private retrieval from
broader P1 identity and deployment hardening.

### AF-2S1 — Local authentication and object authorization

**Status:** Implemented.

**Objective:** Ensure every user-facing private knowledge operation has an
authenticated principal and a PostgreSQL-authoritative object-access boundary
before AF-3 retrieval begins.

**Included scope:** Operator-provisioned local users; Argon2id password hashes;
opaque, expiring, revocable server-side sessions whose raw tokens are not
persisted; `HttpOnly` session cookies; session-bound CSRF protection;
knowledge-base owner/editor/viewer memberships; capability-based policy;
principal-scoped SQL queries for knowledge bases, documents, and ingestion
jobs; atomic owner membership on knowledge-base creation; fail-closed legacy
knowledge bases with an explicit operator claim command; and loopback/internal
Compose exposure defaults.

**Explicit exclusions:** Public registration, frontend authentication UI,
password reset, email verification, MFA, OAuth, SSO, external identity
providers, organization administration, membership-management endpoints,
document deletion, retrieval, RAG, Agent Runtime, tools, and approvals.

**Implemented result:** Health and readiness remain public. Authentication uses
`login`, `logout`, and `me`; knowledge APIs require a live active-user session,
and state-changing requests require valid CSRF proof. Non-member objects are
indistinguishable from absent objects. Chroma remains a derived index and
never authorizes access. Worker/internal persistence operations remain
separate from user-scoped HTTP queries.

**Acceptance criteria:** Authentication, expiry, revocation, CSRF, role
capabilities, cross-user isolation, SQL-scoped access, legacy-data
preservation, explicitly destructive AF-2S downgrade behavior, and rendered
Compose exposure are covered without weakening existing AF-1 or AF-2 behavior.
Downgrade preserves pre-AF-2S knowledge data while removing AF-2S users,
sessions, and memberships.

**Proposed commit message:** `feat(security): add authenticated knowledge access boundary`

### AF-2S2 — Extended identity and operational hardening

**Status:** P1; planned and unimplemented.

**Included scope:** SSO and external identity providers, MFA, password reset,
email verification, organization administration, advanced membership
administration, enterprise audit retention, separate worker/database roles,
hostile-document resource containment, production secret and TLS policy, and
additional deployment hardening.

AF-2S2 does not block the local recruiting demonstration and is not part of
AF-2S1.

## AF-3 — Hybrid retrieval and citations

**Status:** Incomplete. Only the pure AF-3A retrieval-request validator and
`SessionAuthenticationProof` are merged; no retrieval orchestration, keyword
or dense retrieval, final validator/loader, fusion, internal authoritative
retrieval record, public Evidence, Citation, or HTTP retrieval behavior is
implemented.

### AF-3 canonical project-control record

The active documentation work is classified as Parent `AF-3-DOC-R1`, current
remediation `AF-3-DOC-R1-R5`, **Canonical Project-Control Cycle Record
Remediation**. The preceding
`AF3_DOC_R1_R4_INDEPENDENT_APPROVAL_REVIEW` result is `BLOCK`. The R5
Documentation Remediation Gate changes only this canonical record; once its
exact manifest is frozen, its stop state and only permitted current gate are
the Independent Read-Only Documentation Approval Review. The Commit Gate,
AF-3A-03, AF-3B, and AF-3C remain `BLOCKED`. This record is updated only by the
bounded gate that changes it, and the remediation cannot approve itself.

Canonical AF-3 phase and slice ownership is frozen as follows:

| Work ID | Owner and scope | Entry/exit state |
| --- | --- | --- |
| AF-3-DOC-R1 | Design Architect/remediation writer owns the documentation contract only. Remediation cycles append `-R1`, `-R2`, and later monotonically increasing suffixes without changing this parent. | Must be independently approved, committed, reviewed, and merged before runtime work is authorized. Current cycle is `AF-3-DOC-R1-R5`; its frozen stop state is the Independent Read-Only Documentation Approval Review. |
| AF-3A-01 | Pure retrieval-request validator. | `MERGED`; not an AF-3A close. |
| AF-3A-02 | `SessionAuthenticationProof` and `authenticate_session_with_proof`. | `MERGED`; not an AF-3A close. |
| AF-3A-03 | Proof-aware initial access plus scoped deterministic keyword SQL. | `BLOCKED` until AF-3-DOC-R1 is merged and a separate implementation-start approval is issued. |
| AF-3A-04 | First provider-independent final `REPEATABLE READ`, `READ ONLY` validator/loader and internal authoritative retrieval record. | `BLOCKED` until AF-3A-03 is merged and separately authorized. |
| AF-3A-05 | Provider-independent concurrency, deletion, failure, all-sink security, and AF-3A phase close. | `BLOCKED` until AF-3A-04 is merged and separately authorized; AF-3A becomes `CLOSED` only after its complete owner-filtered ledger exit set passes on merged `main`. |
| AF-3B | Embedding, read-only Chroma query, bounded dense handling, hybrid union, and deterministic fusion. | `BLOCKED` until AF-3A is `CLOSED`; closes only from AF-3B-owned rows plus the named AF-3A regression reruns. |
| AF-3C | HTTP, public Evidence/Citation, serialization, public errors/cache/privacy, and the complete public retrieval gate. | `BLOCKED` until AF-3B is `CLOSED`; its merge does not imply production readiness. |

The frozen order is AF-3-DOC-R1 merge, AF-3A-03, AF-3A-04, AF-3A-05 and
AF-3A closure, AF-3B and its closure, then AF-3C. `MERGED` and `CLOSED`, role
separation, session reuse, baseline hashing, evidence invalidation, risk-based
verification, single-writer operation, and output requirements use the
repository-wide framework in `../AGENTS.md`. The acceptance tuple and its
owner/boundary/status/oracle remain canonical only in
`retrieval-security-acceptance.md`.

The underlying documentation candidate addresses four independently confirmed
contract defects: incomplete all-sink applicability, AF-3C HTTP outcomes mixed
into AF-3A acceptance, a citation-success HTTP boundary assigned to public
Evidence, and a non-executable RET-PROV-043 level expansion. R5 changes no
runtime or security contract; it only corrects the canonical cycle, preceding
review result, and post-remediation stop gate after the R4 BLOCK. The control
framework also treats phase/slice mismatch, classifying a merged slice as a
closed phase, repeating still-valid reviews/tests, using a stale or incorrectly
scoped hash baseline, concurrent writers, cross-repository contamination,
self-approval, and reuse of invalidated evidence as stop-worthy project risks.
Those controls do not invent unrecorded historical events or any reviewer
finding beyond the last complete visible finding.

Remaining AF-3 implementation cannot begin until the documentation-only
security design gate in ADR-008 and `retrieval-security-acceptance.md`
completes the governance sequence below. The gate defines required behavior;
it does not implement or authorize retrieval.

The complete AF-3 design-to-implementation governance sequence is:

1. documentation candidate authored;
2. independent read-only review;
3. actionable findings remediated;
4. independent re-review of the exact remediated manifest;
5. separate approval to commit;
6. controlled documentation commit;
7. push to a dedicated remote branch;
8. Draft PR creation;
9. GitHub-hosted CI and documentation checks;
10. independent PR merge-gate review;
11. resolution of any PR or CI findings;
12. separate mark-ready approval;
13. separate merge approval;
14. merge into `main`;
15. local `main` synchronization and branch cleanup;
16. separate explicit approval for the next AF-3A implementation slice; and
17. creation of a new AF-3A implementation branch for that slice.

A PASS from a local design review is not commit approval. A committed local
branch is not implementation approval. An open or merged design PR is not
itself approval for more AF-3A implementation. The next AF-3A runtime slice
begins only after this remediated design contract is merged into `main` and a
separate implementation-start authorization is issued. This remediation
candidate stops for step 4 and does not claim that any later step is complete.

AF-3 cannot be considered complete until its executable adversarial
candidate-validation and untrusted-evidence suite passes. AF-2S2 remains P1
and does not block the P0 recruiting demonstration. Completing AF-3 would not
make AgentForge production-ready.

### AF-3A — Scoped retrieval contracts and PostgreSQL keyword baseline

**Status:** In progress and incomplete. Current `main` contains only the pure
retrieval-request validator and `SessionAuthenticationProof` prerequisites.

**Objective:** Establish the bounded one-knowledge-base retrieval contract and
the first PostgreSQL-scoped candidate path without introducing an external
vector query.

**Included scope:** Provider-independent service and domain contracts that
AF-3C may later map to HTTP: a decoded in-memory request mapping with exact
`query`/`requested_count` fields, strict types/default/extra-field policy, and
a strict Unicode-scalar/UTF-8 query domain that semantically rejects any U+0000
before NFC as validation, not normalization, because PostgreSQL text cannot
represent code zero,
exact NFC and whitespace normalization with no case folding/NFKC/NFKD/excluded-
whitespace transformation, ordered post-normalization scalar then strict
UTF-8 byte limits, and fixed P0-v1 count domains; exactly one target knowledge
base; preservation of the internal `SessionAuthenticationProof`; one short
proof-aware initial live-session, active-user, exact-target access operation;
membership- and document-state-scoped deterministic PostgreSQL keyword
candidates with the 128-row total-order cutoff; the first implementation of
the shared final authoritative PostgreSQL candidate-validation and internal
authoritative retrieval record loader transaction using
`REPEATABLE READ` and `READ ONLY`, with fixed-snapshot reauthorization and no
AF-3A, AF-3B, or AF-3C read-write exception; deterministic fake adapters; unit
and real-PostgreSQL integration, concurrency, and fault-injection tests. Every
AF-3A canonical success or failure row also runs the shared recursive scanner
as a non-HTTP sidecar over all sinks observable at that row's exact boundary
and level, including applicable database and internal authoritative retrieval
record sinks. The internal authoritative retrieval record is
frozen, slotted, non-public, fully materialized before commit, and keeps
trusted control/provenance separate from text classified only as
`untrusted_document_content`.

**Explicit exclusions:** Chroma queries, dense retrieval, RRF, public
`Evidence`, public `Citation`, HTTP retrieval endpoints, answer generation,
prompt construction, RAG, ChatModel execution, reranking, Agent Runtime,
tools, and approvals.

**Acceptance criteria:** The pure domain request accepts exactly one decoded,
non-coercing in-memory mapping and has independently executable
minimum/equality/plus-one boundaries. It has no request-wire, media, bounded-
body, JSON-token, HTTP status/envelope/header/cache, or public-response oracle;
those outcomes belong only to AF-3C. AF-3A sees a decoded U+0000 value and
raises its internal `RetrievalRequestValidationError` before NFC, keyword SQL,
or the final transaction, with no normalization, embedding, Chroma/Provider,
public Evidence, or HTTP work. Whether U+0000 arrived as literal or escaped
JSON is not an AF-3A distinction. U+0000 is rejected rather than transformed
or sent to PostgreSQL, while the adjacent U+0001 control is accepted and
preserved so the rule does not become a blanket Unicode-`Cc` prohibition.
Proof-aware initial access, scoped keyword work, final validation, and all
their results remain internal provider-independent operations. Keyword candidates
are bounded and scoped in SQL from the first query; the exact score/native-
UUID order precedes `LIMIT
128`, including tied rows across a 129-row cutoff fixture; global search and
unrestricted worker repositories are absent from user-facing retrieval; the
shared first final validator/loader batch-checks current
membership, capability, target knowledge base, completed-document state, and
chunk identity; `completed` status is insufficient when persisted
`content_sha256` is null or invalid; no runtime hash, timestamp, UUID, or
provider value invents a revision; authoritative text and provenance load only
from PostgreSQL; client document/chunk IDs never authorize; ordinary tests use
deterministic fakes. AF-3A is not complete until proof-aware initial access,
scoped keyword retrieval, the first final validator/loader, final
reauthentication and access classification, fixed-snapshot candidate
validation, and their AF-3A concurrency gates are implemented, reviewed,
tested, and merged.

**Proposed commit message:** `feat(retrieval): add scoped keyword retrieval contracts`

### AF-3B — Dense candidate validation and deterministic hybrid fusion

**Status:** Planned and unimplemented.

**Objective:** Add bounded dense candidate hints and deterministic hybrid
fusion without allowing provider data to become authority.

**Entry gate:** AF-3B MUST NOT begin dense retrieval, Provider querying, or
fusion until every AF-3A prerequisite above is implemented, tested, reviewed,
and merged. AF-3B may reuse those controls; it may not absorb, duplicate, or
begin the missing scoped keyword path or first final PostgreSQL validator/
loader.

**Included scope:** Query embedding through the existing `EmbeddingModel`
boundary with a distinct no-database-resource lifecycle barrier and failure/
cancellation cleanup; a bounded Chroma query operation added alongside its
first consumer; raw-HTTP compatibility identifier
`chroma-http-v2-1.5.9`, exact bounded version probe,
outbound keys, canonical eight-key response/null/cardinality/encoding schema,
and strict P0-v1 wire/decode/field/metadata/nesting response bounds; exact
response-fatal versus candidate-local taxonomy with immutable absolute source
positions; malformed, stale, duplicate, ineligible, and cross-scope candidate
handling; reuse of the AF-3A final
authoritative PostgreSQL transaction, which for AF-3A, AF-3B, and AF-3C MUST
use `REPEATABLE READ` and `READ ONLY` after provider work; current AF-3 permits
no read-write exception, and any future exception requires a separately
approved ADR change, a new acceptance case, and an explicit security and
transaction review before implementation; fixed-snapshot session/user,
membership, capability, document, chunk, provenance, and internal
authoritative retrieval record validation;
deterministic candidate-union partitioning into 64-row batches and bounded
query counts; deterministic deduplication; exact-rational fixed-constant RRF
with 12-place display-only serialization; explicit required-Provider,
keyword/database, later-batch, connection/timeout, and final-commit failure
semantics with no fallback; separate hybrid final-commit and hybrid later-
batch all-sink regressions after successful Provider work; bounded candidate
handling and fusion; the shared recursive scanner on every AF-3B canonical
success or failure row over the non-HTTP embedding/Provider/hybrid and
reachable regression sinks at that row's exact boundary and level; applicable
AF-3A non-HTTP regression reruns; and deterministic
Provider-adapter, real-PostgreSQL, concurrency, and fault-injection tests.

**Explicit exclusions:** Scoped keyword implementation, the first final
validator/loader, public Evidence or Citation schemas, model-based reranking,
silent keyword-only fallback, answer generation, prompt construction, RAG,
ChatModel execution, HTTP endpoints, Agent Runtime, tools, and approvals.

**Acceptance criteria:** Chroma supplies only bounded untrusted candidate IDs
and rank/distance hints. The pinned raw HTTP v2 request/response contract
passes exact version, key, null, encoding, cardinality, empty/nonempty fixture,
and unknown/missing-field tests without requesting documents or metadata.
P0-v1 hard ceilings are 1,048,576 raw/wire bytes,
2,097,152 decoded bytes, 128 candidate-ID bytes, 4,096 bytes per untrusted
string, 32 metadata entries, 128 metadata-key bytes, 1,024 metadata-value
bytes, and JSON depth 16. Provider wire responses use strict RFC 8259 JSON:
literal `NaN`, `Infinity`, and `-Infinity` tokens are invalid JSON, and a
syntactically valid unsupported-range distance such as `1e400` is outside the
finite IEEE-754 binary64 domain. Both are response-fatal before candidate
iteration and produce no partial internal authoritative retrieval record or
keyword-only fallback; AF-3C later maps them to planned generic `503`.
Numeric tests mutate only `distances[0][0]` in an otherwise canonical
envelope. Only after
bounded decoding succeeds may a named typed adapter, SDK boundary, or
deterministic test double omit one candidate whose typed score is equivalent
to `float("nan")`, `float("inf")`, or `float("-inf")`; other valid candidates
retain their original absolute ranks and exact contributions, no non-finite
value is serialized into conforming JSON, and PostgreSQL remains the only
authorization, internal authoritative retrieval record, provenance, and later
citation authority. Bounded
unsolicited Provider text and metadata never become response or authorization
data.

`GET /api/v2/version` uses the same incremental wire/decode/content-encoding
profile and first-plus-one-byte abort as query responses; it has no unbounded
special case. The query contains exactly one configured-dimension finite
embedding, with the conformance fixture fixing dimension 4 and exact vector
`[0.25, -0.5, 0.0, 1.0]`. The permitted unsolicited response grammar is
individually tested for null/string document elements, null metadata elements,
and shallow string/finite-number/boolean metadata values; nested containers,
null object values, non-finite numbers, wrong element types, and forbidden
charset/encoding branches are individually fatal. For default `R = 10`,
`C = 40`, so `P = 40` passes and `P = 41` is fatal independently of the global
128 ceiling.

No database transaction, checked-out connection, Session, or
SessionTransaction spans embedding or Chroma work; each has a separate
observable barrier and final validation begins only after both complete. The final transaction's first
authoritative statement uses one freshly sampled, timezone-aware injected UTC
`final_now`, fixes one `REPEATABLE READ` snapshot, and revalidates
session, active user, exact target, membership, and current read capabilities.
Every deterministically partitioned candidate batch and all
PostgreSQL-authoritative internal authoritative retrieval record fields load
in that snapshot; no
authorization-sensitive reload follows commit.
Changes before snapshot acquisition are visible, changes after it govern later
requests, and the design claims no asynchronous cancellation. Batch or
transaction failure discards all accumulated records. Identical inputs produce
identical UUID-sorted partitions, exact `ceil(U / 64)` validation-batch query
counts, and exact-rational RRF with `RRF_K = 60`, the documented
`(3,80)`/`(24,30)` collision, and the ADR-008 tie order.

**Proposed commit message:** `feat(retrieval): validate dense candidates and fuse deterministically`

### AF-3C — Evidence, citations, authenticated API and adversarial evaluation

**Status:** Planned and unimplemented.

**Objective:** Expose bounded PostgreSQL-authoritative evidence and stable
citations through exactly two authenticated operations and prove the design
gate with executable adversarial fixtures.

**Included scope:** `Evidence` responses with explicit
PostgreSQL-authoritative versus deterministic-derived field partitions;
`untrusted_document_content` classification; exactly
`POST /api/v1/knowledge-bases/{knowledge_base_id}/retrieval` and
`POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve`, with no
other public endpoint; a shared incremental 65,536-application-body-octet
limit with exact/plus-one/streamed-plus-one and precedence oracles; citation
resolution whose sole strict body field carries the existing CitationReference
structure, reauthenticates the current opaque session and active user,
authorizes the canonical route target, resolves every field and revision only
through one final PostgreSQL `REPEATABLE READ`, `READ ONLY` snapshot, and never
trusts a cached/prebuilt Principal or caller reference field; authenticated
retrieval mapping the AF-3A domain contract;
real-authenticated-request proof that its actual final transaction reports
`transaction_isolation = repeatable read` and `transaction_read_only = on`
through its first final authorization query or an equivalent same-transaction
test hook without an earlier authorization-sensitive query, earlier snapshot
acquisition, or substitution of another transaction or session; private/no-store
responses; existing `401` and
hidden-object `404` integration; planned generic `503` retrieval-unavailable
behavior; deterministic retrieval fixtures; executable candidate-manipulation,
fixed-snapshot concurrency, privacy, citation, provider-bound, and
untrusted-evidence cases; source-isolated no-fallback fixtures; and the same
recursive public all-sink exact/substring scanner on every AF-3C canonical
success or failure row at its exact boundary and level, with only exact public
Evidence or citation-resolution response fields allowlisted; bounded non-
content retrieval metrics.

The generic API framework retains `403`, but current owner/editor/viewer
retrieval grants every member role the read capabilities. AF-3C does not
fabricate a member-without-read `403` fixture. Any future role or policy that
makes retrieval `403` reachable requires a separately approved policy change
and new acceptance case.

**Explicit exclusions:** Answer generation, prompt construction, RAG,
ChatModel execution, reranking, Agent Runtime, tools, approvals,
advanced prompt-injection detection, model/runtime consumer guardrails, parser
sandboxing, hostile-document resource containment, and production hardening.

**Acceptance criteria:** PostgreSQL-authoritative public Evidence identity,
text,
hash, display source, and persisted provenance load from the fixed final
snapshot; absolute source ranks, exact fused rational/display, fused rank,
fixed trust literal, and citation reference use only their ADR-008 permitted
derivations. Citation variants for missing, expired, revoked, and
inactive-user sessions each return generic `401`, no content, no post-auth
target/citation/document/chunk/membership SQL, private/no-store, and no
Provider call. A persisted non-null valid content hash is required; no host
path, secret, raw embedding, Provider text, or raw Chroma metadata is exposed
as authority.
Both POST operations enforce authentication, canonical exact-target
authorization, supported media, bounded body, strict JSON, closed schema, and
operation semantics in that order. Exactly 65,536 ASGI application-body octets
may proceed; byte 65,537 aborts before parsing or downstream work. Citation
success is the exact closed PostgreSQL-authoritative identity/content/hash/
display/provenance object plus reconstructed CitationReference and fixed
untrusted classification; no Provider, embedding, keyword, RRF, storage,
dynamic-hash, cache, filesystem, alternate-token, or extra-response work is
permitted.
Document content remains `untrusted_document_content` and cannot create a
system/developer field, authorization/scope, provider configuration, Tool
Policy, tool name/argument/execution object, approval, secret-access request,
or citation/provenance authority. AF-3C tests only that retrieval-layer
boundary, not nonexistent RAG, ChatModel, Agent Runtime, tool, or approval
consumers. Each later consuming phase must add its own future consuming-phase
acceptance cases. Private cache and public error contracts are deterministic;
Provider/keyword/database/commit failures prove no fallback or accumulated
public Evidence. Every AF-3A, AF-3B, and AF-3C canonical row incorporates the
scanner sidecar at its own boundary and level; the RET-PRIV success/failure
matrices are conformance and negative controls, not the only covered rows.
AF-3C success-only and failure sentinels are recursively
scanned across public HTTP/serialization, ordinary, structured keys/nested
values, access, exception, trace/span event, and response metadata/body sinks,
with no general response-object exemption. AF-3A separately owns its non-HTTP
database and internal authoritative retrieval record scans, and AF-3B
separately owns non-HTTP embedding/Provider/hybrid scans. All AF-3 cases in
`retrieval-security-acceptance.md` are executable and pass at every specified
test level.

AF-3C remains the sole owner of HTTP, request-wire, media, public-error,
cache, serialization, public Evidence, public Citation, and public all-sink
privacy behavior. Those obligations remain explicitly unimplemented and do
not block an otherwise passing AF-3B non-HTTP exit classification.

**Proposed commit message:** `feat(retrieval): add authenticated evidence and citations`

## AF-4 — Unified tool substrate and native tools

**Objective:** Add the planned policy-controlled native tool substrate.

**Included scope:** Tool contract, Tool Registry, Tool Policy, Tool Executor,
Knowledge Search Tool, Repository Search Tool, Repository Read Tool, Issue
Draft Tool, and filesystem security tests.

**Explicit exclusions:** MCP, shell execution, repository modification,
automatic code editing, destructive tools, and real issue publication.

**Acceptance criteria:** Every execution passes validated arguments through
deterministic policy and the executor; filesystem scope and denial paths are
tested.

**Proposed commit message:** `feat(tools): add policy-controlled native tools`

## AF-5A — Run persistence and deterministic fake runtime

**Objective:** Add the planned durable, bounded runtime foundation.

**Included scope:** `AgentRun`, `AgentStep`, durable states, fixed budgets,
checkpointing, fake `ChatModel`, and deterministic runtime tests.

**Explicit exclusions:** Real model execution, planner behavior, tool
execution, verifier behavior, and approvals.

**Acceptance criteria:** Fake runs checkpoint, resume, and terminate
deterministically within explicit tested budgets.

**Proposed commit message:** `feat(agent): add durable bounded runtime foundation`

## AF-5B — Planner, tools, verifier and local model

**Objective:** Add the planned bounded analysis loop and local model adapter.

**Included scope:** Planner, tool selection, observations, Verifier, supported
recommendation, correct abstention, Ollama `ChatModel`, and bounded revision.

**Explicit exclusions:** Approval pause/resume, MCP, memory, and unbounded
execution.

**Acceptance criteria:** Bounded runs produce citation-supported
recommendations or correct abstention with deterministic fake coverage and
separate local-model validation.

**Proposed commit message:** `feat(agent): add planning verification and local model execution`

## AF-5C — Approval pause and resume

**Objective:** Add the planned exact-action approval lifecycle.

**Included scope:** `ToolExecution`, `ApprovalRequest`, exact-action binding,
`waiting_approval`, rejection, expiry, worker resume, and local issue-draft
result.

**Explicit exclusions:** Real GitHub publication, destructive tools, and
approval handlers that execute tools directly.

**Acceptance criteria:** Write attempts pause; decisions bind exact actions;
rejection and expiry prevent execution; approved work resumes through the
worker.

**Proposed commit message:** `feat(approval): add exact-action approval and resume`

## AF-6 — Complete React demonstration flow

**Objective:** Add the planned end-to-end recruiting demonstration UI.

**Included scope:** Knowledge base, document upload, ingestion status, task
submission, Agent Run status, evidence and citations, trace timeline, approval
panel, final recommendation, and local issue draft.

**Explicit exclusions:** P1 features, real issue publication, and repository
modification.

**Acceptance criteria:** One complete React workflow demonstrates ingestion,
bounded analysis, citations, rejection, exact-action approval, and local
result.

**Proposed commit message:** `feat(web): add AgentForge recruiting workflow`

## AF-7 — Reproducible evaluation

**Objective:** Add the planned reproducible evaluation system.

**Included scope:** Versioned datasets, dataset digests, retrieval metrics,
citation metrics, policy metrics, agent outcome metrics, fake-versus-real
separation, and evaluation reports.

**Explicit exclusions:** Claims based on fake mechanics, unversioned datasets,
and P1 capabilities.

**Acceptance criteria:** Reports record denominators, digests, versions, and
environment context; repeated fake runs are deterministic; real results remain
clearly separated.

**Proposed commit message:** `feat(eval): add reproducible AgentForge evaluation`

## AF-8 — Hardening and recruiting release

**Objective:** Package the planned P0 recruiting demo for repeatable local use.

**Included scope:** Synthetic demo corpus, clean-machine startup, recovery
behavior, Chroma rebuild, failure-path tests, full-stack E2E, demo video,
architecture diagram, final README, and resume bullets.

**Explicit exclusions:** P1 work, production-readiness claims, Kubernetes, and
microservice decomposition.

**Acceptance criteria:** The documented demo completes on a clean machine,
recovery and rebuild paths pass, full-stack E2E passes, and published claims
cite measured evidence.

**Proposed commit message:** `chore(release): package AgentForge recruiting demo`
