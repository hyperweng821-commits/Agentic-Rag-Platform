# Approved baseline

## Authority

Commit `e0e1e01cd61eb7a2f7bd750da02f343b79830e2e` is the permanent approved
pre-AF-0 functional baseline. The local Phase 3 source snapshot was
checksum-identical to that commit: it contained no additions, content
modifications, or deletions.

AF-0 is being developed on the temporary `feat/agentforge-evolution` feature
branch, which may later be merged. The feature branch is not the permanent
baseline. Git history and source code are the source of truth.

## Functional baseline

The approved Phase 3 baseline implements:

- the FastAPI application foundation;
- typed configuration;
- asynchronous PostgreSQL infrastructure;
- health and readiness behavior;
- structured logging and request correlation;
- unified error handling;
- the React/Vite foundation;
- Docker and CI foundations.

It does not implement document ingestion, chunks, embeddings, Chroma indexing,
hybrid retrieval, an Agent Runtime, tools, policies, approvals, structured
Agent Run Trace, evaluation, MCP, or memory. Those capabilities remain planned
or deferred.

## Compatibility

Package names, service names, API paths, health response identifiers, Compose
identities, and all other compatibility identifiers remain unchanged from the
approved Phase 3 baseline.

AF-0 changes documentation and presentation branding only. It does not change
dependencies, locks, migrations, backend behavior, endpoints, health behavior,
or Compose identity.
