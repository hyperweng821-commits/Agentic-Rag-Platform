# AgentForge roadmap

AF-0, AF-1, AF-2A, the explicitly approved end-to-end AF-2B scope, and the
minimal AF-2S1 knowledge-access boundary are implemented. AF-3 onward remain
planned and unimplemented. Interfaces are introduced only with their first
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

**Status:** Planned and unimplemented.

AF-3 implementation cannot begin until the documentation-only security design
gate in ADR-008 and `retrieval-security-acceptance.md` completes the governance
sequence below. The gate defines required behavior; it does not implement or
authorize retrieval.

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
16. separate explicit AF-3A implementation-start approval; and
17. creation of a new AF-3A implementation branch.

A PASS from a local design review is not commit approval. A committed local
branch is not implementation approval. An open or merged design PR is not
itself AF-3A implementation approval. AF-3A begins only after the design
contract is merged into `main` and a separate implementation-start
authorization is issued. This remediation candidate stops for step 4 and does
not claim that any later step is complete.

AF-3 cannot be considered complete until its executable adversarial
candidate-validation and untrusted-evidence suite passes. AF-2S2 remains P1
and does not block the P0 recruiting demonstration. Completing AF-3 would not
make AgentForge production-ready.

### AF-3A — Scoped retrieval contracts and PostgreSQL keyword baseline

**Status:** Planned and unimplemented.

**Objective:** Establish the bounded one-knowledge-base retrieval contract and
the first PostgreSQL-scoped candidate path without introducing an external
vector query.

**Included scope:** Retrieval request and domain contracts; exactly one target
knowledge base; live-principal and existing read-capability enforcement;
bounded query and result limits; membership- and document-state-scoped
PostgreSQL keyword candidates; one shared authoritative candidate-validation
and evidence-loading contract; deterministic fake adapters; unit and
PostgreSQL integration tests.

**Explicit exclusions:** Chroma queries, dense retrieval, RRF, HTTP retrieval
endpoints, answer generation, RAG, reranking, Agent Runtime, tools, and
approvals.

**Acceptance criteria:** Keyword candidates are bounded and scoped in SQL from
the first query; global search and unrestricted worker repositories are absent
from user-facing retrieval; the shared validator batch-checks current
membership, capability, target knowledge base, completed-document state, and
chunk identity; `completed` status is insufficient when persisted
`content_sha256` is null or invalid; no runtime hash, timestamp, UUID, or
provider value invents a revision; authoritative text and provenance load only
from PostgreSQL; client document/chunk IDs never authorize; ordinary tests use
deterministic fakes.

**Proposed commit message:** `feat(retrieval): add scoped keyword retrieval contracts`

### AF-3B — Dense candidate validation and deterministic hybrid fusion

**Status:** Planned and unimplemented.

**Objective:** Add bounded dense candidate hints and deterministic hybrid
fusion without allowing provider data to become authority.

**Included scope:** Query embedding through the existing `EmbeddingModel`
boundary; a bounded Chroma query operation added alongside its first consumer;
strict P0-v1 wire/decode/field/metadata/nesting response bounds; exact
response-fatal versus candidate-local taxonomy; malformed, stale, duplicate,
ineligible, and cross-scope candidate handling; one final `REPEATABLE READ`,
normally `READ ONLY`, PostgreSQL transaction after provider work;
fixed-snapshot session/user, membership, capability, document, chunk,
Evidence, and provenance validation; deterministic candidate-union
partitioning and bounded query counts; deterministic deduplication;
fixed-constant RRF; explicit required-provider and final-transaction failure
semantics; deterministic adapter and concurrency tests.

**Explicit exclusions:** Model-based reranking, silent keyword-only fallback,
answer generation, RAG, HTTP endpoints, Agent Runtime, tools, and approvals.

**Acceptance criteria:** Chroma supplies only bounded untrusted candidate IDs
and rank/score hints. P0-v1 hard ceilings are 1,048,576 raw/wire bytes,
2,097,152 decoded bytes, 128 candidate-ID bytes, 4,096 bytes per untrusted
string, 32 metadata entries, 128 metadata-key bytes, 1,024 metadata-value
bytes, and JSON depth 16. Provider text and metadata never become response or
authorization data. Response-fatal violations produce planned generic `503`,
no partial dense result, no Evidence, and no keyword-only fallback;
candidate-local invalidity omits only that record.

No database transaction spans provider work. The final transaction's first
authoritative statement fixes one `REPEATABLE READ` snapshot and revalidates
session, active user, exact target, membership, and current read capabilities.
Every deterministically partitioned candidate batch and all Evidence fields
load in that snapshot; no authorization-sensitive reload follows commit.
Changes before snapshot acquisition are visible, changes after it govern later
requests, and the design claims no asynchronous cancellation. Batch or
transaction failure discards all accumulated records. Identical inputs produce
identical UUID-sorted partitions, exact `ceil(U / B)` validation-batch query
counts, and deterministic RRF with `RRF_K = 60` and the ADR-008 tie order.

**Proposed commit message:** `feat(retrieval): validate dense candidates and fuse deterministically`

### AF-3C — Evidence, citations, authenticated API and adversarial evaluation

**Status:** Planned and unimplemented.

**Objective:** Expose bounded PostgreSQL-authoritative evidence and stable
citations through an authenticated retrieval API and prove the design gate
with executable adversarial fixtures.

**Included scope:** Authoritative `Evidence` responses; explicit
`untrusted_document_content` classification; stable citation resolution with
current access and revision checks; authenticated one-knowledge-base retrieval
API; private/no-store responses; existing `401` and hidden-object `404`
integration; planned generic `503` retrieval-unavailable behavior;
deterministic retrieval fixtures; executable candidate-manipulation,
fixed-snapshot concurrency, privacy, citation, provider-bound, and
untrusted-evidence cases; bounded non-content retrieval metrics.

The generic API framework retains `403`, but current owner/editor/viewer
retrieval grants every member role the read capabilities. AF-3C does not
fabricate a member-without-read `403` fixture. Any future role or policy that
makes retrieval `403` reachable requires a separately approved policy change
and new acceptance case.

**Explicit exclusions:** Answer generation, prompt construction, RAG,
ChatModel execution, reranking, Agent Runtime, tools, approvals,
advanced prompt-injection detection, model/runtime consumer guardrails, parser
sandboxing, hostile-document resource containment, and production hardening.

**Acceptance criteria:** Every evidence field and citation resolves from
the fixed final PostgreSQL snapshot or current citation-resolution rows; a
persisted non-null valid content hash is required; no host path, secret, raw
embedding, provider text, or raw Chroma metadata is exposed as authority.
Document content remains `untrusted_document_content` and cannot create a
system/developer field, authorization/scope, provider configuration, Tool
Policy, tool name/argument/execution object, approval, secret-access request,
or citation/provenance authority. AF-3C tests only that retrieval-layer
boundary, not nonexistent RAG, ChatModel, Agent Runtime, tool, or approval
consumers. Each later consuming phase must add its own future consuming-phase
acceptance cases. Private cache and public error contracts are deterministic;
all AF-3 cases in `retrieval-security-acceptance.md` are executable and pass at
every specified test level.

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
