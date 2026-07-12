# ADR-003: Use PostgreSQL for the ingestion job queue

- Status: Accepted
- Date: 2026-07-12

## Decision

The first production-shaped version uses an `ingestion_jobs` table and `FOR UPDATE SKIP LOCKED` rather than adding Redis and Celery.

## Consequence

The stack remains smaller while preserving independent workers, retries and durable progress. The queue can be replaced behind a worker protocol if measured load requires it.

