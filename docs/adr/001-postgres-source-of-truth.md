# ADR-001: PostgreSQL is the source of truth

- Status: Accepted
- Date: 2026-07-12

## Decision

PostgreSQL owns business records, original chunks, jobs, conversations, traces and evaluations. ChromaDB is a rebuildable vector index keyed by the same chunk UUIDs.

## Consequence

Cross-store writes are idempotent and eventually consistent. A document becomes queryable only after both relational data and vector indexing are complete.

