# AgentForge product definition

## Product definition

AgentForge is a local-first, observable and policy-controlled AI agent runtime
for private engineering workflows.

The Phase 3 application foundation, AF-0 product boundary, AF-1 knowledge
intake, AF-2 durable processing/indexing, and the minimal AF-2S1
knowledge-access boundary are implemented. Local users authenticate through
opaque server-side sessions, and knowledge bases, documents, and ingestion
jobs are scoped through owner/editor/viewer memberships. AF-2 executes durable
jobs and maintains PostgreSQL-authoritative chunks plus a rebuildable Chroma
index. Retrieval, runtime, tool, approval, trace, and evaluation capabilities
below remain planned. The product is not production-ready, and broader AF-2S2
identity and operational hardening is deferred to P1.

## Primary user

Software engineering, platform engineering and technical-support teams working
with private documentation, source code, failed-test reports and operational
information.

## Primary use case

Analyse a failed software test by searching private documentation and an
explicitly allowed repository, collecting evidence, producing a supported
repair recommendation and preparing a local issue draft.

This use case is planned and unimplemented.

## Target workflow

The complete workflow is not yet implemented:

1. Authenticate a locally provisioned user. **Implemented in AF-2S1.**
2. Create or select an authorized knowledge base. **Implemented in AF-1 and scoped in AF-2S1.**
3. Upload PDF, Markdown or TXT material. **Implemented in AF-1 and scoped in AF-2S1.**
4. Validate and store the source file. **Implemented in AF-1.**
5. Create a durable ingestion job. **Implemented in AF-1.**
6. Parse, normalize and deterministically chunk the document. **Implemented in AF-2B.**
7. Store authoritative chunks in PostgreSQL. **Implemented in AF-2B.**
8. Build a rebuildable Chroma index. **Implemented in AF-2B.**
9. Submit a failed-test analysis task.
10. Create a bounded Agent Run.
11. Search knowledge and allowed repository files.
12. Verify claims against citations.
13. Produce a repair recommendation.
14. Prepare an issue draft.
15. Pause for exact-action approval.
16. Approve or reject.
17. Display the final result and structured trace.

## P0 recruiting MVP

The P0 scope combines the implemented foundation described above with the
planned retrieval, runtime, tool, approval, UI, and evaluation work:

- knowledge-base creation;
- local operator-provisioned users and opaque session authentication;
- owner/editor/viewer knowledge-base authorization;
- safe PDF, Markdown and TXT intake;
- durable ingestion jobs;
- deterministic chunking;
- PostgreSQL chunk source of truth;
- Chroma rebuildable vector index;
- PostgreSQL keyword retrieval;
- dense + keyword + RRF retrieval;
- stable citations;
- AF-3 semantic trust boundary: retrieved document content is
  `untrusted_document_content`; document instructions have no policy authority,
  cannot alter authorization or knowledge-base scope, create approvals, choose
  or configure tools, establish citation/provenance authority, or configure
  providers; adversarial untrusted-evidence fixtures are required;
- bounded Agent Runtime;
- code-defined Tool Registry;
- Knowledge Search Tool;
- Repository Search Tool;
- Repository Read Tool;
- Issue Draft Tool;
- deterministic Tool Policy;
- approval for write actions;
- structured Agent Run Trace;
- deterministic fake-adapter tests;
- reproducible evaluation;
- one complete React workflow;
- Docker Compose local demo.

## P1 enhancements

The following work is deferred until after P0:

- reranking;
- MCP adapter and one MCP server;
- long-term memory;
- advanced prompt-injection detection beyond the P0 semantic trust boundary;
- model- and runtime-specific untrusted-evidence consumer guardrails;
- parser sandboxing and broader hostile-document resource containment;
- quotas and rate limits;
- production secrets and TLS;
- broader deployment hardening;
- OpenTelemetry;
- real GitHub issue creation;
- SSO and external identity providers;
- MFA, password reset, and email verification;
- organization and advanced membership administration;
- enterprise audit retention;
- separate worker/database roles;
- multiple LLM providers.

P0 does not defer all prompt-injection handling: AF-3 must preserve the
semantic boundary above even before later consumers exist. It does not claim
to prevent every prompt injection. Each later RAG, ChatModel, Agent Runtime, or
tool-consuming phase must add its own future consuming-phase acceptance cases.
The P1 items provide advanced detection, consumer-specific guardrails, and
operational containment rather than replacing the P0 trust classification.

## Non-goals before the recruiting demo

Excluded from P0:

- multi-agent teams;
- autonomous swarms;
- drag-and-drop workflow builder;
- general shell execution;
- repository modification;
- automatic code editing;
- destructive tools;
- real GitHub publication in P0;
- Kubernetes;
- microservice decomposition;
- plugin marketplace;
- billing;
- model training;
- unlimited execution loops.

## Recruiting demonstration

The Payments Service failed refund idempotency test scenario is the target
recruiting demonstration, not current behavior:

1. Create the Payments Service knowledge base.
2. Upload architecture notes, API documentation and a failed-test report.
3. Show ingestion progress.
4. Submit the failed refund idempotency analysis task.
5. Show the public plan and fixed execution budgets.
6. Show knowledge and repository citations.
7. Show verifier support or correct abstention.
8. Prepare an issue draft.
9. Reject the first proposed write action to prove nothing executes.
10. Create and approve a new exact action.
11. Display the local issue draft and structured trace.
12. Display an evaluation summary.

## Target success criteria

No target in this table has been measured or achieved.

| Criterion | Target | Status |
| --- | --- | --- |
| Clean-machine end-to-end demo completion | Complete the documented demo without manual data repair | Target — not yet measured |
| Deterministic runtime boundedness | Every run terminates within configured bounds | Target — not yet measured |
| Policy-before-tool enforcement | Policy evaluates every tool execution attempt | Target — not yet measured |
| No write action before valid approval | Zero write executions without valid approval | Target — not yet measured |
| Approval integrity | Exact approved action is the only action eligible to resume | Target — not yet measured |
| Citation resolvability | Every emitted citation resolves to stored evidence | Target — not yet measured |
| Recall@5 | ≥ 0.80 | Target — not yet measured |
| MRR@10 | ≥ 0.70 | Target — not yet measured |
| Citation correctness | ≥ 0.90 | Target — not yet measured |
| Groundedness | ≥ 0.85 | Target — not yet measured |
| Correct abstention | ≥ 0.80 | Target — not yet measured |
| Supported recommendation or correct abstention | ≥ 0.90 | Target — not yet measured |
| Ingestion idempotency | Reprocessing identical input creates no duplicate logical records | Target — not yet measured |
| Chroma rebuildability | Rebuild the index from PostgreSQL-authoritative data | Target — not yet measured |
| Unit-test infrastructure independence | Ordinary unit tests use no Ollama, Chroma, MCP or network | Target — not yet measured |
| Evaluation reproducibility | Same versioned inputs and fakes reproduce the same report | Target — not yet measured |
