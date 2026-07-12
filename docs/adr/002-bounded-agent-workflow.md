# ADR-002: Use a bounded agent workflow

- Status: Accepted
- Date: 2026-07-12

## Decision

The Agentic RAG flow is a finite state machine with at most two retrieval attempts and one answer revision.

## Consequence

Latency, failure modes and tests remain predictable. Structured step outcomes are stored, while hidden chain-of-thought is not persisted or displayed.

