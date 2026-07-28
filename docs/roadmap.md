# AgentForge roadmap

AF-0, AF-1, and AF-2A are implemented. AF-2B onward remain planned and
unimplemented. Interfaces are introduced only with their first consuming
feature. No phase begins before the previous phase meets its acceptance
criteria. P1 work cannot block the P0 recruiting demo.

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

### AF-2B — Parsing, normalization, and deterministic chunking

**Objective:** Add isolated PDF, Markdown, and text parsers, canonical text
normalization, and deterministic chunk production.

**Explicit exclusions:** Worker execution, job claiming, embeddings, and
vector-store writes.

### AF-2C — Worker execution, leases, retries, and recovery

**Objective:** Claim eligible PostgreSQL jobs, enforce attempt and lease
bounds, recover expired work, persist chunks transactionally, and record safe
outcomes.

**Explicit exclusions:** Embedding generation and Chroma writes.

### AF-2D — Embedding and vector-store boundaries

**Objective:** Introduce `EmbeddingModel` and `VectorStore` boundaries with
deterministic fakes and their first consumers.

**Explicit exclusions:** End-to-end Chroma indexing and rebuild behavior.

### AF-2E — Chroma indexing and rebuild

**Objective:** Add idempotent Chroma indexing, PostgreSQL-authoritative index
rebuild, and end-to-end ingestion integration.

**AF-2 acceptance criteria:** Supported files produce deterministic
authoritative chunks; jobs recover through bounded leases and retries; Chroma
rebuilds from PostgreSQL; fake-adapter and end-to-end tests pass.

**AF-2 explicit exclusions:** Retrieval APIs, Agent Runtime, tools, and
reranking.

## AF-3 — Hybrid retrieval and citations

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
