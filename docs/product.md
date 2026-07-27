# AgentForge product definition

## Product definition

AgentForge is a local-first, observable and policy-controlled AI agent runtime
for private engineering workflows.

Only the implemented Phase 3 application foundation currently exists. All P0
runtime, ingestion, retrieval, tool, approval, trace, and evaluation
capabilities below are planned and unimplemented. P1 enhancements are
deferred. Excluded scope is listed explicitly.

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

The complete workflow is planned and unimplemented:

1. Create or select a knowledge base.
2. Upload PDF, Markdown, TXT or failed-test material.
3. Validate and store the source file.
4. Create a durable ingestion job.
5. Parse, normalize and deterministically chunk the document.
6. Store chunks in PostgreSQL.
7. Build a rebuildable Chroma index.
8. Submit a failed-test analysis task.
9. Create a bounded Agent Run.
10. Search knowledge and allowed repository files.
11. Verify claims against citations.
12. Produce a repair recommendation.
13. Prepare an issue draft.
14. Pause for exact-action approval.
15. Approve or reject.
16. Display the final result and structured trace.

## P0 recruiting MVP

The planned, unimplemented P0 scope is:

- knowledge-base creation;
- safe PDF, Markdown and TXT intake;
- durable ingestion jobs;
- deterministic chunking;
- PostgreSQL chunk source of truth;
- Chroma rebuildable vector index;
- PostgreSQL keyword retrieval;
- dense + keyword + RRF retrieval;
- stable citations;
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
- prompt-injection guard;
- OpenTelemetry;
- real GitHub issue creation;
- authentication and RBAC;
- multiple LLM providers.

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
