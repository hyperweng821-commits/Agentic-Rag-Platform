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

## Retrieval authentication and target visibility

**Authentication failure and target invisibility are separate outcomes, and
their evaluation order is the security property.**

Authentication must be evaluated before any target lookup. An invalid,
expired, revoked, or otherwise unusable credential must produce the same
`401` response for every target.

After authentication succeeds, an absent target and a target the caller is
not entitled to discover must produce the same hidden `404` response.

A `403` remains valid only when an authenticated caller can legitimately know
that the resource exists but lacks permission for the requested non-hidden
operation.

Do not reorder authentication and target-visibility checks. Do not
short-circuit final reauthorization when a candidate collection is empty. No
empty-result optimization may bypass final authentication or target
authorization.

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

## Project control framework

- The roadmap is the canonical phase/slice and gate source. An implemented or
  merged slice is never evidence that its parent phase is complete.
- A work session executes one explicitly named bounded gate, then stops. It may
  not promote itself into the next gate or acquire commit, release, or merge
  authority from a review result.
- Exactly one active writer may touch a worktree. Do not use background agents,
  parallel writers, a second work, or concurrent formatting/code-generation
  processes against that worktree. Read-only checks may run concurrently only
  when they cannot mutate repository state.
- Work is isolated to the declared repository root. Do not inspect, search,
  modify, or report on sibling projects. A cross-project path or result is a
  stop condition and invalidates the affected evidence.
- Before any edit, record and compare the repository root, branch, full HEAD,
  index state, non-ignored untracked paths, changed-path set, rename/mode/type
  state, `git diff --stat`, `git diff --check`, SHA-256 of the exact
  `git diff --full-index --binary` byte stream, SHA-256 of every in-scope
  worktree file, and any gate-specific parsed inventory. A mismatch from the
  approved baseline stops the gate before editing.
- Never repair a baseline mismatch with reset, restore, clean, stash, checkout,
  rebase, or branch switching. Preserve pre-existing work and report the exact
  mismatch plus the one next action.

### Roles and sessions

- **Design Architect:** authors the contract and phase boundaries; cannot
  approve that authored manifest.
- **Independent Reviewer:** uses a fresh read-only session to review the exact
  manifest; cannot edit it or supply commit authority.
- **Implementation Agent:** writes only the separately authorized slice and
  cannot approve its own implementation.
- **Commit Agent:** after explicit commit-gate approval, verifies and commits
  only the approved manifest; it does not push.
- **Release Agent:** after separate approval, pushes, opens or updates the PR,
  and reports hosted checks; it does not merge.
- **Merge Reviewer:** independently reviews the exact PR head and unresolved
  hosted evidence without writing the branch.
- **Merge Agent:** merges only the independently approved exact PR head after
  explicit merge authority.
- **Phase Closure Reviewer:** in a fresh read-only session, verifies the merged
  `main` state and every phase exit criterion; it cannot infer `CLOSED` from a
  merged slice or PR.

A session may be reused only within the same role and bounded gate while its
baseline remains exact. Any manifest edit invalidates prior approval of that
manifest. Independent review, authority escalation, merge review, and phase
closure require a new session. No implementer, author, remediator, or merge
agent may act as its own required independent reviewer.

### Evidence and verification

- Evidence is valid only for its recorded repository root, branch, HEAD,
  index/untracked shape, changed-path manifest, diff/file hashes, environment,
  and gate. A changed byte invalidates the affected file hash, complete diff
  hash, diff statistics, parsed inventories, and any approval of the old
  manifest. A HEAD, index, untracked-path, dependency, service, or environment
  change invalidates every result that depends on it.
- Truncated reviewer output proves nothing after its last complete visible
  finding. Never invent or extrapolate a finding, PASS, test result, or status.
- Use risk-based verification: documentation gates run document/ledger/parser,
  structure, hash, and diff checks; implementation gates run targeted unit and
  boundary tests for changed behavior plus only invalidated integration,
  concurrency, fault, or service-backed evidence; commit gates recheck the
  exact approved manifest; release/merge gates use the exact remote head and
  hosted evidence; closure gates verify merged `main` and the full exit set.
- Do not repeat a still-valid review or test merely to accumulate evidence.
  Rerun only when its inputs were invalidated or the current gate explicitly
  requires a distinct boundary.
- The executable acceptance identity is the gate-specific canonical tuple,
  including case ID, variant, test level, owner, execution boundary, status,
  and oracle. Prose cannot silently merge a slice, level, owner, or oracle.

`MERGED` means the exact change is present on `main`; it does not mean its
phase is `CLOSED`. `CLOSED` requires a Phase Closure Reviewer to verify every
exit criterion and required acceptance tuple on merged `main`. Remediation
cycles use the canonical parent work ID plus monotonically increasing `-R1`,
`-R2`, and later suffixes; a remediation never changes the parent phase/slice
identity.

For Codex work, prefer the strongest available frontier coding model with high
or xhigh reasoning for architecture, security, independent review, merge
review, and phase closure; use high reasoning for implementation and medium or
high reasoning for mechanical commit/release verification. Model choice is a
recommendation, not evidence or approval, and role/session separation still
applies.

Every gate output must state the canonical classification, current gate,
valid and invalid evidence, work performed, stop point, and exactly one next
step. Final gate reports must also record the resulting repository identity,
manifest, hashes, inventory, validation results, limitations, and deferred
work.
