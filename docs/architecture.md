# AgentForge architecture

## Current implementation status

The Phase 3 foundation and AF-1 knowledge intake are implemented:

- FastAPI application factory and lifecycle;
- typed configuration;
- asynchronous PostgreSQL engine and session infrastructure;
- versioned API routing, health/readiness behavior, and unified errors;
- structured logging and request correlation;
- React/Vite application foundation;
- Docker Compose and CI foundations.
- durable `KnowledgeBase`, `Document`, and `IngestionJob` PostgreSQL records;
- secure local PDF, Markdown and text intake with streamed hashing;
- database-enforced per-knowledge-base deduplication;
- idempotent retry transitions for failed ingestion jobs.

The health and AF-1 metadata/upload/job endpoints are implemented. AF-1 does
not execute jobs. Parsing, chunks, embeddings, Chroma indexing, retrieval,
agent, tool, approval, trace, and evaluation capabilities are planned and
unimplemented. P1 enhancements are deferred.

## Architectural principles

- Keep a modular monolith and do not split microservices in P0.
- Keep PostgreSQL as the business source of truth.
- Treat ChromaDB as a rebuildable index.
- Maintain an explicit internal Agent Runtime boundary.
- Apply deterministic Tool Policy before every execution attempt.
- Require approval for write and external actions.
- Record a public structured trace without hidden chain-of-thought.
- Introduce adapters only with their first consumers.
- Use deterministic fake adapters for ordinary tests.
- Do not use LangGraph in P0.
- Do not use MCP in P0.

## Target module architecture

The diagram is a planned, unimplemented P0 target except for the existing React
UI foundation, FastAPI HTTP foundation, and PostgreSQL infrastructure. Arrows
show permitted dependency direction; they do not imply that every persistence
operation is strictly sequential:

```mermaid
flowchart TD
    UI["React UI foundation; workflow planned"]
    HTTP["FastAPI HTTP boundary; business APIs planned"]
    Services["Application Services (planned)"]
    Worker["Worker (planned)"]
    Ingestion["Ingestion Pipeline (planned)"]
    Runtime["Agent Runtime (planned)"]
    Executor["Tool Executor (planned)"]
    Registry["Tool Registry (planned)"]
    Policy["Tool Policy (planned)"]
    Approval["Approval Service (planned)"]
    Trace["Trace Recorder (planned)"]
    Knowledge["Knowledge Search Tool (planned)"]
    Repository["Repository Search / Read Tool (planned)"]
    Issue["Issue Draft Tool (planned)"]
    Retriever["Hybrid Retriever (planned)"]
    ChatAdapter["ChatModel Adapter (planned)"]
    EmbeddingAdapter["EmbeddingModel Adapter (planned)"]
    VectorAdapter["VectorStore Adapter (planned)"]
    PG[(PostgreSQL infrastructure; business data planned)]
    Chroma[(ChromaDB rebuildable index; planned)]
    Ollama["Ollama provider (planned)"]
    Files[(Local File Storage; AF-1)]
    LocalRepo[(Scoped Local Repository; planned)]

    UI --> HTTP
    HTTP --> Services
    Services -->|"Persist business state, jobs, runs, approvals"| PG
    PG -->|"Claim durable work"| Worker

    Worker --> Ingestion
    Worker --> Runtime
    Ingestion --> Files
    Ingestion --> PG
    Ingestion --> EmbeddingAdapter
    EmbeddingAdapter --> Ollama
    Ingestion --> VectorAdapter
    VectorAdapter --> Chroma

    Runtime --> ChatAdapter
    ChatAdapter --> Ollama
    Runtime --> Trace
    Trace --> PG

    Runtime --> Executor
    Executor --> Registry
    Registry --> Policy
    Policy -. "allow / deny / require_approval" .-> Executor
    Policy --> Approval
    Approval --> PG

    Executor --> Knowledge
    Executor --> Repository
    Executor --> Issue
    Knowledge --> Retriever
    Retriever --> PG
    Retriever --> VectorAdapter
    Repository --> LocalRepo
    Issue --> PG
```

Application Services persist durable work but never invoke worker processes.
The Worker claims eligible work from PostgreSQL and invokes either the planned
Ingestion Pipeline or planned Agent Runtime.

The only legal planned tool invocation path is `Agent Runtime → Tool Executor →
Tool Registry → Tool Policy`. The registry owns tool identity, version, input
schema, and risk classification. Policy returns `allow`, `deny`, or
`require_approval`. An allowed Tool Executor dispatches only the resolved
native tool through its permitted application port.

Approval decisions are persisted through the Approval Service. Approval
endpoints and the Approval Service never execute tools. After approval, the
Worker resumes the Agent Runtime, which returns through the Tool Executor. The
executor re-resolves the tool, revalidates canonical arguments, and re-runs
policy before execution.

MCP remains outside P0. Future P1 MCP tools must enter through an MCP adapter
behind the same internal Tool Registry and Tool Executor path; MCP cannot
create a second execution or policy path.

## Ingestion flow

AF-1 implements upload validation, local storage, and durable records. The
remaining processing flow is planned for AF-2:

```mermaid
flowchart LR
    Upload["Upload (AF-1)"] --> Validate["Validate (AF-1)"]
    Validate --> Storage["Local storage (AF-1)"]
    Storage --> Records["PostgreSQL Document + IngestionJob (AF-1)"]
    Records --> Claim["Worker claim (planned)"]
    Claim --> Parse["Parse (planned)"]
    Parse --> Normalize["Normalize (planned)"]
    Normalize --> Chunk["Chunk (planned)"]
    Chunk --> PGChunks["PostgreSQL chunks (planned)"]
    PGChunks --> Embed["Embed (planned)"]
    Embed --> Upsert["Chroma upsert (planned)"]
    Upsert --> Ready["Ready (planned)"]
```

PostgreSQL is authoritative. Chroma can be rebuilt from PostgreSQL-authoritative
records. A document is not searchable until all required persistence and index
states are complete.

## Planned hybrid retrieval flow

This P0 flow is planned and unimplemented:

```mermaid
flowchart LR
    Query["Query (planned)"] --> Embedding["Embedding (planned)"]
    Embedding --> Dense["Chroma dense candidates (planned)"]
    Query --> Keyword["PostgreSQL keyword candidates (planned)"]
    Dense --> Validate["Scope and status validation (planned)"]
    Keyword --> Validate
    Validate --> RRF["RRF (planned)"]
    RRF --> Evidence["Bounded evidence (planned)"]
    Evidence --> Citations["Stable citations (planned)"]
```

P0 has no reranker. Reranking is deferred P1 work.

## Planned Agent execution flow

This flow is planned and unimplemented:

```mermaid
flowchart LR
    Task["Task (planned)"] --> Precheck["Deterministic pre-check (planned)"]
    Precheck --> Queued["Queued Agent Run (planned)"]
    Queued --> Claim["Worker claim (planned)"]
    Claim --> Planner["Planner (planned)"]
    Planner --> Selection["Tool selection (planned)"]
    Selection --> Executor["Tool Executor (planned)"]
    Executor --> Registry["Tool Registry (planned)"]
    Registry --> Policy["Tool Policy (planned)"]
    Policy --> Dispatch{"Execute or wait for approval (planned)"}
    Dispatch --> Observation["Observation (planned)"]
    Observation --> Verifier["Verifier (planned)"]
    Verifier --> Outcome["Result, bounded retry or abstention (planned)"]
    Outcome --> Trace["Final structured trace (planned)"]
```

Limits for steps, tool calls, retrieval attempts, revisions, and wall-clock
time are explicit and testable. Numeric defaults are intentionally not assigned
until the consuming runtime feature is designed and validated.

## Tool policy and approval

The planned P0 rules are:

- the model may request a tool but cannot authorize execution;
- the registry owns tool identity, version, input schema, and risk;
- arguments are validated and canonicalized before policy evaluation;
- policy returns `allow`, `deny`, or `require_approval`;
- approval binds the exact tool version, canonical arguments digest, target
  scope, policy version, and expiry;
- changed arguments require a new approval;
- destructive P0 tools are disabled;
- approval endpoints store decisions but never execute tools directly.

P1 MCP support, if approved, enters through an adapter behind the same Tool
Registry.

## Trace and evaluation

Planned Agent Run Trace records public structured events only and never hidden
chain-of-thought. Deterministic fake adapters validate mechanics; fake results
are not product-quality metrics. Real runs produce product-quality metrics only
with recorded evidence.

Evaluation records dataset, model, prompt, retrieval, tool, and policy versions,
along with configuration digests, denominators, and environment context. P0
evaluation is planned and unimplemented.

## Dependency boundaries

| Boundary | Rule |
| --- | --- |
| Endpoints | Contain no SQL, Chroma, Ollama, or filesystem logic |
| Application services | Own use-case sequencing and transaction boundaries |
| Repositories | Own SQLAlchemy queries |
| AgentRuntime | Exposes no LangGraph types |
| Tools | Execute only through Tool Executor |
| Adapters | Keep external SDK types inside adapters |
| Frontend | Uses API contracts only |
| MCP | May later enter through an adapter behind the existing Tool Registry boundary |

These boundaries describe planned P0 work unless the current implementation
status says otherwise.

## Architecture decisions

- [ADR-001: PostgreSQL is the source of truth](adr/001-postgres-source-of-truth.md)
- [ADR-002: Use a bounded agent workflow](adr/002-bounded-agent-workflow.md)
- [ADR-003: Use PostgreSQL for the ingestion job queue](adr/003-postgres-job-queue.md)
- [ADR-004: Define the Agent Runtime boundary](adr/004-agent-runtime-boundary.md)
- [ADR-005: Enforce tool policy and approval](adr/005-tool-policy-and-approval.md)
- [ADR-006: Version configuration and use deterministic fakes](adr/006-versioned-config-and-fakes.md)
