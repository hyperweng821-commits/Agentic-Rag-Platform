# ADR-004: Define the Agent Runtime boundary

- Status: Accepted
- Date: 2026-07-27

## Context

The P0 Agent Runtime is planned and unimplemented. It must coordinate bounded
work without leaking orchestration framework types across the application.

## Decision

`AgentRuntime` is an internal application boundary. P0 uses an explicit bounded
state machine supporting `queued`, `running`, `waiting_approval`, and terminal
states, including resume after approval. Step, tool-call, retrieval-attempt,
revision, and wall-clock limits are explicit and testable. Hidden
chain-of-thought is never stored.

LangGraph is not a P0 dependency. Any future LangGraph support remains behind
`AgentRuntime`; LangGraph types cannot appear in endpoints, services, tools, or
domain models.

## Consequences

Runtime persistence and resume behavior remain framework-independent and
testable. Interfaces and adapters are introduced only with their first
consuming feature.
