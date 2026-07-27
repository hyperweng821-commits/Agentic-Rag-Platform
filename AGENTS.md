# AgentForge engineering rules

These rules apply to the entire repository.

## Scope and evidence

- Source code is the source of truth.
- A `.gitkeep` file is not implementation.
- Deleted Phase 4 or Phase 5 work must not be reconstructed.
- Implement only the explicitly approved phase.
- Do not add unused abstractions. Add an interface only with its first
  consuming feature.
- Do not fabricate tests, results, coverage, performance, or quality metrics.
- Do not persist or expose hidden chain-of-thought.

## Architecture

- Keep AgentForge a modular monolith; do not introduce premature
  microservices.
- PostgreSQL is the business source of truth.
- ChromaDB is a rebuildable index, never the authoritative business store.
- Keep external SDKs behind adapters introduced alongside real consumers.
- Keep Agent execution bounded by explicit limits.

## Tools and approval

- Apply deterministic policy before every tool execution.
- Write actions and external actions require approval.
- Destructive P0 actions are disabled.

## Testing and data changes

- Ordinary tests use deterministic fake adapters.
- Ordinary unit tests require no Ollama, ChromaDB, MCP, or network.
- Migrations must be reversible and tested.

## Repository operations

- Do not commit or push automatically.
- Final reports must identify changed files, validation performed, limitations,
  and deferred work.
