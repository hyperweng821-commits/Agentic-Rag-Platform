# ADR-006: Version configuration and use deterministic fakes

- Status: Accepted
- Date: 2026-07-27

## Context

P0 runtime and evaluation capabilities are planned and unimplemented.
Reproducibility requires configuration provenance and infrastructure-independent
ordinary tests.

## Decision

Agent, prompt, tool, policy, retrieval, and evaluation configurations are
versioned. Agent Runs record their version keys and configuration digests.
Ordinary unit tests use deterministic fake models, vector stores, and tools and
require no Ollama, Chroma, MCP, or network.

Fake evaluation validates mechanics only; fake results cannot be reported as
product-quality metrics. Real evaluation records the dataset digest, model,
configuration, denominator, and environment context. Hidden chain-of-thought
and unrestricted provider reasoning are not stored.

## Consequences

Mechanical tests remain deterministic and distinct from evidence-bearing real
evaluation. Reported metrics retain enough provenance for interpretation and
reproduction.
