# ADR-005: Enforce tool policy and approval

- Status: Accepted
- Date: 2026-07-27

## Context

The P0 tool and approval substrate is planned and unimplemented. Model output
cannot authorize actions or redefine their risk.

## Decision

Native and future MCP tools use one internal registry. The registry owns tool
identity, version, input schema, and risk; the model cannot lower or redefine
risk. Deterministic policy runs before every execution attempt and returns
`allow`, `deny`, or `require_approval`.

Write and external actions require one-shot approval. Approval binds the exact
tool version, canonical argument digest, target scope, policy version, and
expiry. Changed arguments require a new approval. Destructive P0 tools are
disabled. Approval handlers record decisions and never execute tools.

MCP is P1 and must enter through an adapter behind the internal registry.

## Consequences

Every attempted action has a deterministic, traceable policy outcome. Approval
cannot be reused for a different action.
