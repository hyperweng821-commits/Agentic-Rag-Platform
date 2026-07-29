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

**Objective:** Add planned deterministic cited hybrid retrieval.

**Included scope:** PostgreSQL keyword search, Chroma dense retrieval,
deterministic RRF, evidence objects, citation resolution, and retrieval
evaluation fixtures.

**Explicit exclusions:** Reranking, Agent Runtime, and tools.

**Acceptance criteria:** Scoped retrieval produces bounded evidence with
stable resolvable citations and reproducible fixture results.

**Proposed commit message:** `feat(retrieval): add cited hybrid retrieval`

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
