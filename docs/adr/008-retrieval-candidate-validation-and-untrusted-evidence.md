# ADR-008: Validate retrieval candidates in PostgreSQL and treat evidence as untrusted

- Status: Proposed design gate under remediation; no AF-3 runtime behavior is
  implemented or authorized by this decision
- Date: 2026-07-29

## Context

AF-2B stores authoritative normalized chunks and provenance in PostgreSQL and
maintains Chroma as a rebuildable derived index. The current `VectorStore`
boundary supports initialization, writes, and scoped deletes; it has no query
operation. Stable Chroma record IDs use `chunk:<UUID>`, where the UUID belongs
to a PostgreSQL `DocumentChunk`. Chroma receives derived text and metadata for
indexing, but none of those fields is an authorization, evidence, or citation
source.

AF-2S1 supplies live opaque sessions, active-user checks,
owner/editor/viewer memberships, capability policy, membership-scoped user
repositories, generic hidden-object `404` behavior, and separate
worker/internal repositories. It does not implement retrieval. A principal
resolved before slow embedding or Chroma work is not proof that its session,
user, membership, target, document, or chunk remains eligible afterward.

AF-3 will combine PostgreSQL keyword candidates with dense candidates from an
external provider. Provider output may be malformed, oversized, stale,
cross-scope, duplicated, or adversarial. Persisted document text may contain
instructions aimed at later model or tool consumers. This ADR fixes the P0
retrieval security contract before a query adapter, retrieval endpoint,
`Evidence` source type, or `Citation` source type is introduced.

## Decision

AF-3 retrieval is a bounded operation over exactly one target knowledge base.
It performs:

1. a short PostgreSQL access check before embedding or Chroma work;
2. bounded keyword and dense candidate generation without retaining a
   PostgreSQL transaction or checked-out connection across external work; and
3. one short, final PostgreSQL `REPEATABLE READ` transaction that reauthorizes,
   validates every candidate batch, and loads every authoritative response
   value.

PostgreSQL is authoritative. Chroma output is a bounded untrusted candidate
hint. Keyword and dense identities enter one final validator. Retrieved text is
classified as `untrusted_document_content`: evidence data with no instruction,
policy, authorization, tool, approval, or provenance authority.

This decision is an implementation prerequisite, not an implementation record.
AF-3 remains planned and unimplemented.

## Normative requirement index

The following identifiers are the complete normative runtime security-
requirement index for this ADR. The detailed sections define their precise
meaning. The acceptance specification maps every identifier to one or more
stable case IDs. Governance approvals and production-readiness disclaimers are
non-runtime review gates and are verified by the governance process rather
than assigned to an incapable test layer.

| ID | Normative requirement |
| --- | --- |
| ADR-008-R01 | Every request initially authenticates a live, active principal from an existing, unexpired, unrevoked session, names exactly one target knowledge base, and authorizes from PostgreSQL; client document or chunk IDs never establish access. |
| ADR-008-R02 | Initial authorization completes before external provider work, and no PostgreSQL transaction or connection is retained across embedding, Chroma, network, parser, or filesystem work. |
| ADR-008-R03 | The final transaction is normatively `REPEATABLE READ` and normally `READ ONLY`; its first authoritative statement fixes the snapshot and revalidates session, user, target, membership, and current read capabilities. |
| ADR-008-R04 | Every validation batch and every authoritative Evidence field loads within the same fixed final snapshot, with no authorization-sensitive PostgreSQL reload after commit. |
| ADR-008-R05 | The final snapshot is the request linearization point; changes before it are visible, changes after it govern later requests, and no asynchronous cancellation is claimed. |
| ADR-008-R06 | Final validation and Evidence loading are all-or-nothing; any required batch or transaction failure discards accumulated records and produces the planned generic retrieval failure. |
| ADR-008-R07 | PostgreSQL alone supplies authoritative identity, scope, document/chunk state, text, hash, source identity, provenance, and citation resolution. |
| ADR-008-R08 | A chunk is retrieval- and citation-eligible only when its document is completed and its persisted `content_sha256` is a non-null lowercase 64-hex SHA-256 value; no retrieval-time revision fallback is allowed. |
| ADR-008-R09 | Citation resolution reauthenticates, scopes to one knowledge base, and requires the same current persisted chunk hash; citation possession never authorizes access. |
| ADR-008-R10 | Chroma filters, IDs, text, metadata, scores, and provenance never authorize, widen scope, or supply authoritative response fields. |
| ADR-008-R11 | Provider-response limit profile P0-v1 applies inclusive wire, decoded, candidate-ID, string, and metadata ceilings plus the exact container-counting JSON-depth algorithm before normal candidate processing. |
| ADR-008-R12 | Every response-fatal provider-contract condition, including an absent required candidate collection, produces the planned generic `503`, no partial dense result, no Evidence, and no keyword-only fallback. |
| ADR-008-R13 | Every candidate-local condition omits only that bounded record; an authorized request whose candidates are all locally omitted returns empty Evidence without disclosing reasons. |
| ADR-008-R14 | Provider score is optional and non-authoritative; present wrong-type or non-finite scores omit that candidate, while fusion uses provider list rank and ignores bounded provider text/metadata disagreement. |
| ADR-008-R15 | Duplicate IDs retain the earliest rank per source and produce at most one Evidence item per authoritative chunk. |
| ADR-008-R16 | Query characters, query UTF-8 bytes, requested results, dense over-fetch, keyword candidates, provider candidates, candidate union, and SQL work have finite versioned bounds. |
| ADR-008-R17 | P0-v1 keyword SQL is scoped before scoring and deterministically ranks PostgreSQL-authoritative `simple` text-search matches by score then native UUID; HTTP retrieval cannot call unscoped worker/internal paths or expose global counts. |
| ADR-008-R18 | Candidate union ordering, partitioning, validation query count, record reconstruction, and failure behavior follow the deterministic batching contract. |
| ADR-008-R19 | P0 fusion uses the fixed `RRF_K = 60`, one-based source ranks, the specified formula and tie order, and no raw-score fusion or reranker. |
| ADR-008-R20 | Evidence uses an allowlisted PostgreSQL projection, stable citation identity, and `untrusted_document_content`; it excludes secrets, storage paths, embeddings, and provider authority. |
| ADR-008-R21 | AF-3 enforces the P0 semantic trust boundary: content cannot create trusted instructions, authorization/scope, provider configuration, tools, approvals, secret requests, or citation authority. |
| ADR-008-R22 | Every later RAG, ChatModel, Agent Runtime, or tool-consuming phase adds its own consuming-phase acceptance cases; AF-3 does not claim to test nonexistent consumers. |
| ADR-008-R23 | Authentication, hidden-resource, provider-failure, valid present-empty provider response, authorized-empty, and private cache behavior are deterministic; current AF-3 roles do not fabricate an unreachable retrieval `403`. |
| ADR-008-R24 | Normal logs exclude queries, content, secrets, raw payloads, and identifying retrieval artifacts; telemetry is bounded and content-free. |
| ADR-008-R25 | P0 retrieval response bounds and semantic trust controls remain distinct from AF-2S2/P1 parser sandboxing and broader hostile-document, identity, and deployment hardening. |

## Detailed security contract

### Request and initial authorization boundary

Every future private retrieval request must:

- resolve a live authenticated `Principal` through the existing opaque-session
  boundary;
- name exactly one target knowledge-base UUID;
- require current PostgreSQL membership plus `KNOWLEDGE_BASE_READ` and
  `DOCUMENT_READ`;
- reject or ignore client-supplied document IDs or chunk IDs as authorization
  inputs;
- complete a PostgreSQL session, active-user, exact-target, membership, and
  capability check before embedding or Chroma work begins; and
- complete the final PostgreSQL boundary described below even when keyword and
  dense candidate sets are empty.

The initial authentication read requires the session to exist, remain
unexpired, and have `revoked_at IS NULL`, and requires the associated user to
be active. A session whose revocation was already committed before the request
began is rejected with the existing generic authentication failure before
target lookup, keyword retrieval, embedding, Chroma, or candidate validation.
The final-snapshot authentication recheck protects against changes during an
otherwise valid request; it is not a substitute for this initial rejection.

The initial check, any SQL-scoped keyword query, and the final transaction are
separate short operations. No transaction or checked-out connection may be
retained while waiting for embedding, Chroma, network, parser, filesystem, or
other external I/O.

The current production role matrix gives owner, editor, and viewer the
retrieval read capabilities. AF-3 therefore has no reachable
member-without-read-capability runtime fixture and must not invent one,
monkeypatch one into an integration test, add a fourth role, or change the
matrix. The generic API framework can represent `403` for a visible member
lacking a requested capability, but a future policy that makes retrieval
`403` reachable requires a separately approved policy change and a new
fixture. Current non-member, missing, and hidden targets use generic `404`.

### Atomic final PostgreSQL boundary

After all external embedding and Chroma work completes, retrieval enters one
short final PostgreSQL transaction with these normative properties:

- isolation level is `REPEATABLE READ`;
- mode is `READ ONLY`, unless a later implementation demonstrates that the
  selected driver or database cannot support read-only mode for this flow and
  records a separately reviewed exception;
- no embedding, Chroma, network, parser, filesystem, or other external I/O
  occurs inside it;
- the first authoritative statement acquires the fixed transaction snapshot
  and atomically revalidates session validity, active-user status, the exact
  target knowledge base, current membership, and current read capabilities;
- every candidate-validation batch and every authoritative Evidence field is
  read using that same fixed snapshot;
- authoritative content, hash, source display identity, and provenance load
  before the transaction completes;
- no second PostgreSQL content or provenance load occurs after commit;
- after commit, the application may serialize only already-loaded immutable
  response values and may not perform another authorization-sensitive fetch;
- validation and evidence loading are all-or-nothing; no record accumulated
  from an earlier batch survives authorization failure, an unvalidated
  required batch, transaction failure, or database failure; and
- transaction or database failure produces the explicit planned generic
  `503 RETRIEVAL_UNAVAILABLE` response and never partial Evidence.

The initial session/user/membership/capability statement is accounted for
separately from candidate-validation batch queries.

The fixed final snapshot is the request linearization point:

1. A session, user, membership, capability, document, or chunk change committed
   before snapshot acquisition is visible to the request.
2. Authentication loss visible at that snapshot produces the existing generic
   `401 AUTHENTICATION_REQUIRED`.
3. Target membership or access loss visible at that snapshot produces the
   existing hidden-resource `404 NOT_FOUND`. Under the current role matrix,
   capability loss cannot occur independently while membership remains.
4. Candidate document or chunk ineligibility visible at that snapshot omits
   the candidate without disclosing why.
5. A change committed after snapshot acquisition does not retroactively cancel
   the current request; it governs later requests.
6. This contract does not claim asynchronous cancellation of Python,
   embedding, Chroma, or response-serialization work.
7. A change after final commit cannot trigger a second
   authorization-sensitive database read for that response because all
   response evidence was already loaded within the fixed snapshot.

This is a defined request linearization rule, not a claim that revocation can
instantaneously cancel arbitrary work already in flight.

### PostgreSQL authority and eligibility

PostgreSQL is the business source of truth for:

- principal identity, active-user state, and session validity;
- membership, role, capabilities, and exact target scope;
- document identity, knowledge-base ownership, and processing state;
- chunk identity, document ownership, normalized text, and revision;
- source display identity and source provenance; and
- citation creation and resolution.

A document status of `completed` is necessary but not sufficient for
retrieval. An authoritative chunk is eligible only when its persisted
`content_sha256` is non-null and valid under the current repository format:
exactly 64 lowercase hexadecimal characters matching `^[0-9a-f]{64}$`.

A completed legacy document may contain chunks whose hash is null. Those
chunks must not become Evidence or citations. Retrieval must not substitute a
dynamically calculated hash, `updated_at`, chunk UUID, Chroma metadata,
provider metadata, or another implicit revision token. Legacy content becomes
eligible only after an explicitly approved reprocessing or re-ingestion
pipeline persists the normal authoritative hash.

Citation creation requires the persisted non-null hash. A stable citation
reference binds at least the authoritative chunk UUID and that hash. Citation
resolution is another authenticated, one-knowledge-base PostgreSQL operation.
It rechecks current access, completed document state, chunk identity, and the
persisted expected hash. It fails closed with generic `404` when access is
absent, the expected hash is absent, or the current hash no longer matches.

No response text, filename, page range, offsets, content hash, document
identity, knowledge-base identity, or citation identity may be sourced from
Chroma `documents` or `metadatas`.

### Chroma provider request and P0-v1 response limits

The Chroma request asks only for fields required by candidate handling,
principally candidate IDs and provider rank/distance information. Provider
documents, text, and provenance are not requested as authoritative response
material.

The versioned initial provider-response profile is:

| P0-v1 limit | Hard ceiling |
| --- | ---: |
| Raw/wire response bytes | 1,048,576 bytes |
| Decoded/decompressed response bytes | 2,097,152 bytes |
| Canonical candidate-ID UTF-8 length | 128 bytes |
| Untrusted individual string field | 4,096 UTF-8 bytes |
| Metadata entries per candidate | 32 |
| Metadata key | 128 UTF-8 bytes |
| Metadata scalar/string value | 1,024 UTF-8 bytes |
| JSON nesting depth | 16 |

These values are P0 defaults and hard ceilings for the initial contract. Only a
later reviewed version may revise them.

Every ceiling in this table is inclusive. Raw/wire bytes, decoded bytes,
candidate-ID bytes, individual-string bytes, metadata-entry count,
metadata-key bytes, metadata-value bytes, and JSON depth are accepted when the
measured value is less than or equal to the applicable ceiling. Equality does
not cause truncation or omission. A counter rejects only when the applicable
value exceeds its ceiling.

The adapter enforces the profile in this order:

1. If a truthful `Content-Length` is present and exceeds 1,048,576, reject
   before reading the body.
2. If `Content-Length` is absent, false, or smaller than the actual body,
   stream raw bytes and abort as soon as cumulative wire bytes exceed
   1,048,576.
3. If compression is used, independently enforce both the raw/wire ceiling and
   the 2,097,152-byte decoded/decompressed ceiling.
4. Do not invoke an unbounded full-body JSON decoder before transport and
   decode limits pass.
5. Materialize a decoded body only after both applicable byte ceilings pass.
6. Enforce ID, individual string, metadata-entry, metadata-key,
   metadata-value, and nesting ceilings during or immediately after bounded
   parsing and before normal candidate processing.
7. Any transport, decode, body, nesting, or per-field hard-limit violation is
   a whole-response provider-contract failure.

#### Exact P0-v1 JSON depth counting

JSON depth is the maximum number of JSON container nodes on any path from the
root to a value. Only objects and arrays are containers. The bounded streaming
parser applies this exact algorithm:

1. A scalar root has depth 0.
2. A root object or root array has depth 1.
3. Entering a child object or child array increments container depth by exactly
   one.
4. A scalar object value or scalar array element does not increment depth.
5. An empty object or empty array still counts as one container at its assigned
   depth.
6. Object keys do not count as values or containers.
7. The maximum depth is the highest active container depth encountered while
   streaming tokens.
8. Before pushing a new object or array onto the parser stack, compute
   `next_depth = current_container_depth + 1`.
9. Reject immediately when `next_depth > 16`.
10. Do not fully materialize a structure whose next container would exceed the
    limit.

The following simple fixtures therefore have exact depths:

| JSON | Depth |
| --- | ---: |
| `0` | 0 |
| `{}` | 1 |
| `[]` | 1 |
| `{"v": 0}` | 1 |
| `{"v": []}` | 2 |
| `[{"v": [0]}]` | 3 |

The canonical recursive boundary fixtures are:

```text
D0 = 0

For n >= 1:
    Dn = {"v": D(n-1)}  when n is odd
    Dn = [D(n-1)]       when n is even
```

Under this algorithm, D0 has depth 0, D1 has depth 1, D16 has depth 16,
and D17 has depth 17. The depth guard accepts D16 and passes control to the
next validation stage. Passing the depth guard does not make an otherwise
invalid provider envelope valid: a canonical D16 fixture that later fails
envelope validation is classified as that later envelope error, never
`DEPTH_LIMIT_EXCEEDED`. The parser rejects D17 before full materialization,
envelope validation, or candidate processing. A D17 failure is whole-response
fatal and produces planned generic `503 RETRIEVAL_UNAVAILABLE`, no Evidence,
no partial dense list, and no keyword-only fallback.

These provider-response bounds do not claim complete hostile-document
containment. Parser sandboxing and broader resource containment remain
AF-2S2/P1 work.

### Exact provider validation taxonomy

The classification pivot is whether the bounded, structurally valid provider
envelope can still preserve a deterministic position for each candidate
record. An invalid ID value alone does not make an envelope response-fatal.

A supported, bounded envelope whose required candidate collection is present
with the correct empty collection type is a structurally valid zero-result
provider response. Every required parallel collection is also present with
length zero, there are deterministically zero provider positions, and no
malformed placeholder record is introduced. The adapter returns an empty dense
candidate list. This result does not produce `503`, synthesize a candidate,
raise a missing-collection error, enable keyword-only degraded mode, or skip
final authorization.

An absent required candidate collection is different: it remains a
response-fatal provider-contract violation with the generic failure and
no-fallback behavior below.

For a position-preserving record envelope made of independently identifiable
candidate records whose positions are deterministic, each of the following is
a candidate-local omission:

- an absent candidate ID field;
- a candidate ID whose JSON value is not a string, including `null`, boolean,
  number, array, or object; and
- a bounded string ID that is not canonical `chunk:<UUID>`.

The invalid record does not make the entire response fatal. It produces no
Evidence, supplies no authority, and cannot widen scope. Surrounding
structurally valid candidates remain eligible for normal processing, including
PostgreSQL validation. Omitting the invalid record does not renumber or compact
the deterministic provider positions: surviving candidates retain their
original source ranks and relative provider order. The existing RRF formula
and complete tie order are unchanged.

Position reconstruction failure remains whole-response fatal. This includes:

- parallel arrays with different lengths;
- a required array element absent in a way that prevents deterministic
  candidate-position reconstruction;
- a top-level structure that does not permit deterministic mapping between
  candidate IDs and ranks or positions;
- a missing required candidate collection; or
- any response shape that prevents reconstruction of provider ordering.

The following conditions are whole-response fatal:

- network or timeout failure;
- wire or decoded body-limit violation;
- invalid JSON;
- excessive nesting;
- wrong top-level response shape;
- missing required candidate collection;
- mismatched parallel-array lengths;
- candidate count above the configured maximum;
- unsupported envelope version;
- any per-field hard-limit violation; and
- a data structure that prevents deterministic candidate-position
  reconstruction.

Every whole-response fatal condition produces generic planned
`503 RETRIEVAL_UNAVAILABLE`, no partial dense list, no keyword-only fallback,
and no Evidence.

The following conditions are candidate-local omissions when the surrounding
decoded response is bounded and structurally valid:

- an absent candidate ID field in a position-preserving record envelope;
- a non-string candidate ID (`null`, boolean, number, array, or object) in a
  position-preserving record envelope;
- an ID has the correct bounded string type but is not canonical
  `chunk:<UUID>`;
- the canonical ID names an unknown chunk;
- the canonical ID is stale;
- the candidate is outside the exact target knowledge base;
- the candidate belongs to an inaccessible object;
- the current document or chunk is ineligible;
- an optional present score is wrong-type, `NaN`, positive infinity, or
  negative infinity; or
- the individual candidate record is otherwise invalid without making
  candidate positions ambiguous.

Candidate-local omissions do not disclose their reasons. Remaining candidates
retain their original source ranks and relative provider order. If every
candidate is locally omitted and final authorization succeeds, the response is
authorized empty Evidence.

Provider score is optional and non-authoritative. A finite present score is
accepted only as a diagnostic hint; fusion uses list rank, not raw score.
Absence of a score does not invalidate an otherwise valid candidate.

Bounded provider text is ignored. Bounded metadata disagreement is ignored for
authority: knowledge-base, document, chunk, content-hash, and provenance
metadata can neither authorize nor deauthorize a valid canonical ID, and the
ID still enters PostgreSQL validation. Oversized text or metadata remains a
whole-response hard-limit violation.

Duplicate IDs are not malformed. The earliest provider rank per source is
retained, later occurrences do not create another Evidence item, and
PostgreSQL remains the identity authority.

### Request, result, and candidate bounds

The first consuming AF-3 slice introduces finite, positive, versioned values
for:

- maximum normalized query characters;
- maximum normalized query UTF-8 bytes;
- maximum requested result count;
- dense over-fetch factor;
- maximum dense candidates;
- maximum keyword candidates;
- maximum provider candidates;
- maximum unique candidate union; and
- SQL candidate validation batch size.

Normalization rejects either an excessive character count or an excessive
UTF-8 byte count before provider work. Requested result count is validated
before arithmetic. These caller-field bound violations use the existing
`422 VALIDATION_ERROR` envelope. Dense request size is:

```text
dense_fetch_count =
    min(MAX_DENSE_CANDIDATES,
        checked_multiply(requested_count, DENSE_OVERFETCH_FACTOR))
```

The multiplication is overflow-safe and the configured ceiling is always
applied. A provider response with more candidates than requested or configured
is fatal rather than truncated. If individually legal bounded source lists
produce more unique identities than the configured candidate-union maximum,
the service discards both lists and produces planned generic
`503 RETRIEVAL_UNAVAILABLE`, with no truncation, partial Evidence, or fallback.

### Keyword retrieval boundary

The exact versioned P0-v1 PostgreSQL keyword-ranking contract uses the
`simple` text-search configuration. The normalized, bounded user query is
passed as a bound parameter to:

```sql
plainto_tsquery('simple', normalized_query)
```

Here `normalized_query` denotes the bound parameter, not interpolated SQL.
User text is not interpreted as PostgreSQL web-search operators or raw
`tsquery` syntax. The authoritative chunk vector is:

```sql
to_tsvector('simple', document_chunks.normalized_text)
```

The match predicate is:

```sql
to_tsvector('simple', document_chunks.normalized_text)
@@ plainto_tsquery('simple', normalized_query)
```

The P0-v1 keyword score is:

```sql
ts_rank_cd(
    to_tsvector('simple', document_chunks.normalized_text),
    plainto_tsquery('simple', normalized_query),
    0
)
```

The score expression is computed from PostgreSQL-authoritative
`document_chunks.normalized_text`. A later generated `tsvector` column or index
may optimize the query only when it preserves these exact observable
tokenization, matching, score, ordering, rank, and limit semantics. A change
that alters any of those semantics requires reviewed contract versioning. If
`plainto_tsquery` produces no lexemes, the keyword candidate list is empty; it
does not become a global match or bypass final authorization.

Before score or rank assignment, rows must already satisfy:

- the live principal;
- exact target knowledge-base ID;
- current membership and read capabilities;
- `Document.status = 'completed'`;
- a non-null, valid persisted `DocumentChunk.content_sha256`; and
- current document/chunk ownership; and
- the matching PostgreSQL text-search predicate above.

Inaccessible or ineligible rows receive no keyword score or rank and cannot
affect an accessible row's rank. Keyword retrieval must not search globally
and filter in Python, expose global hit or document counts, search inaccessible
or ineligible documents, or call unrestricted `_internal` worker repository
methods from HTTP or user-facing services.

The total P0-v1 keyword candidate order is exactly:

1. `keyword_score` descending; then
2. authoritative `document_chunks.id` ascending using PostgreSQL's native UUID
   ordering.

The UUID is not cast to locale-sensitive text. Insertion order, heap order,
index traversal order, planner output order, chunk index, database row-arrival
order, Python set or dictionary iteration, random order, and locale-sensitive
ordering are not source-order or tie-break inputs. The same scoped
authoritative database state and normalized query produce the same total
keyword order.

The one-based keyword source rank has semantics equivalent to:

```sql
row_number() OVER (
    ORDER BY keyword_score DESC, document_chunks.id ASC
)
```

`MAX_KEYWORD_CANDIDATES` is applied using that same total order. The selected
top-N list therefore has ranks 1 through N without gaps or post-limit
reranking. A CTE or equivalent query shape may avoid inconsistent score
recomputation, but observable score, order, rank, and limit semantics remain
exact.

The raw keyword score is used only to create this deterministic keyword source
order. RRF consumes the resulting one-based keyword rank. Raw keyword score is
not added to or multiplied with dense score, used for cross-source
calibration, or used after source-rank assignment as a hidden RRF tie break.

Keyword candidates remain candidates. They enter the same final transaction,
authorization, eligibility, authoritative loading, deduplication, and fusion
boundary as dense candidates. An injected cross-scope keyword candidate is
rejected again by the shared validator.

### Deterministic candidate union and SQL batching

The final validation algorithm is exact:

1. Parse bounded keyword and provider candidates into canonical authoritative
   chunk UUID identities.
2. Preserve rank maps separately: keyword rank by chunk UUID and dense rank by
   chunk UUID.
3. Construct the unique candidate union and enforce its configured ceiling.
4. Sort the unique union by canonical chunk UUID ascending.
5. Partition that ordered list into contiguous batches of exactly the
   configured validation batch size, except the final shorter batch.
6. For `U` unique candidates and batch size `B`:

   ```text
   validation_batch_query_count =
       0             when U = 0
       ceil(U / B)   when U > 0
   ```

7. Account for the initial final-transaction
   session/user/membership/capability statement separately from this batch
   query count.
8. Execute every batch inside the same fixed `REPEATABLE READ` snapshot.
9. Do not trust PostgreSQL row order.
10. Reconstruct validated authoritative records in a map keyed by canonical
    chunk UUID.
11. Only after every batch succeeds, apply the preserved rank maps and
    deterministic RRF ordering.
12. Do not let batch ordering affect final ranking.
13. On any batch or transaction failure, discard every accumulated record and
    return no partial Evidence.
14. Telemetry may report unique candidate count, configured batch size, and
    actual batch query count, but never raw query or Evidence content.

The implementation must not issue N+1 candidate authorization queries or one
unbounded `IN` query.

### Deterministic fusion

P0 fusion is reciprocal rank fusion over at most two bounded normalized lists:
keyword and dense. It uses one-based ranks and fixed `RRF_K = 60`:

```text
rrf_score(chunk) =
    sum(1 / (60 + source_rank) for each source containing the chunk)
```

Raw keyword and vector scores are not added, multiplied, calibrated, or used
to override rank. The earliest occurrence supplies each source rank. One
Evidence item remains per authoritative chunk.

Results sort by:

1. fused score descending;
2. best contributing rank ascending;
3. keyword rank ascending, with absence last;
4. dense rank ascending, with absence last; and
5. canonical authoritative chunk UUID ascending.

Evidence retains contributing source ranks and receives a one-based fused rank.
P0 has no reranker, model-based ordering, or hidden nondeterministic tie-break.
The UUID order used for SQL batching is not the final RRF result order.

### Evidence and citation trust boundary

This documentation change introduces no source-level `Evidence` or `Citation`
type. Future Evidence is constructed only from records loaded in the fixed
final snapshot and carries:

- authoritative chunk, document, and knowledge-base IDs;
- authoritative normalized content;
- the persisted non-null authoritative content hash;
- approved source display identity such as original filename, never a storage
  path;
- page range and character offsets when present;
- keyword and dense ranks when present;
- fused rank and score;
- a stable citation reference; and
- trust classification `untrusted_document_content`.

Evidence and citations never expose host filesystem paths, password hashes,
session or CSRF tokens or digests, database credentials, provider secrets, raw
embeddings, internal exception details, or provider metadata represented as
authority.

### P0 untrusted-evidence boundary and P1 hardening

All document text is untrusted even when an owner uploaded it, ingestion
completed, PostgreSQL stores it, it has a valid citation, or it ranks first.
Examples include fake system/developer messages, scope-widening instructions,
secret requests, tool requests, approval-bypass claims, and encoded or
obfuscated instructions.

AF-3 may return that text only as `untrusted_document_content`. The AF-3
retrieval layer must not create or derive from it:

- a system or developer instruction field;
- identity, membership, capability, or knowledge-base scope;
- provider configuration;
- Tool Policy, a tool name, a tool argument, or an execution object;
- an approval request or decision;
- a secret-access request; or
- citation or provenance authority.

AF-3C tests this retrieval-layer output boundary only. It does not claim to
test prompt construction, RAG, a ChatModel, Agent Runtime, tool execution, or
approvals because those consumers do not exist in AF-3.

When a later RAG, ChatModel, Agent Runtime, or tool-consuming phase is
introduced, that phase must add and pass its own
`future consuming-phase acceptance` cases proving that untrusted Evidence is
not elevated by that consumer. Those later cases are mandatory for the
consumer but are not AF-3C runtime claims.

The P0 boundary is semantic trust separation and adversarial
untrusted-evidence fixtures. It does not claim complete prompt-injection
prevention. P1/AF-2S2 includes advanced prompt-injection detection,
model/runtime-specific consumer guardrails, parser sandboxing, separate worker
and database roles, hostile-document resource containment, quotas and rate
limits, production secrets, TLS, and broader deployment hardening. Deferring
P1 controls does not defer or weaken the P0 semantic boundary.

### Failure, cache, and privacy contract

Public behavior is:

- invalid authentication or inactive user: generic
  `401 AUTHENTICATION_REQUIRED`;
- missing, hidden, unowned, or inaccessible target: generic `404 NOT_FOUND`;
- an authorized request with zero surviving candidates: successful empty
  Evidence;
- required provider, provider-contract, final-transaction, or database failure:
  planned generic `503 RETRIEVAL_UNAVAILABLE`; and
- every private retrieval success or failure:
  `Cache-Control: private, no-store`.

The existing framework's generic `403 FORBIDDEN` remains available, but the
current owner/editor/viewer retrieval role matrix has no executable
member-without-read-capability state. AF-3 has no synthetic current `403`
fixture.

Normal retrieval logs must not contain:

- raw query text;
- chunk or document content;
- candidate, document, knowledge-base, or citation IDs;
- filenames or filesystem paths;
- session/CSRF values or digests, passwords, provider credentials, or database
  secrets;
- raw embeddings; or
- raw provider bodies and internal exception details.

Permitted telemetry is bounded content-free metadata: validated request
correlation ID, provider name, elapsed time, requested result limit, bounded
keyword/dense/unique candidate counts, configured validation batch size,
actual batch query count, rejection count, returned count, and normalized
error classification.

## Consequences

Retrieval performs additional PostgreSQL work after provider calls. A change
committed before the fixed final snapshot can invalidate candidates or access;
a change committed after it governs later requests. This cost and explicit
linearization point prevent derived provider state from becoming authority
without claiming instantaneous revocation of work already in flight.

The final validator and loader are one shared service boundary for keyword and
dense candidates. A query adapter may be introduced only with its first
consumer. Chroma may retain derived indexing fields, but retrieval ignores
them as response authority.

Legacy null-hash chunks remain non-retrievable until an approved pipeline
persists the established lowercase 64-hex content hash. An authorized empty
result remains distinguishable from authentication, scope, provider, and
transaction failures.

## Rejected alternatives

### Use default `READ COMMITTED` wording

Rejected because several statements could observe different snapshots. The
fixed final `REPEATABLE READ` snapshot is normative.

### Hold a transaction across embedding or Chroma

Rejected because external work must not retain a database connection or
transaction. The final transaction begins only after provider work.

### Trust Chroma scope, text, metadata, or provenance

Rejected because derived provider state cannot establish current access,
eligibility, content, revision, or citation authority.

### Search globally and filter in Python

Rejected because it weakens SQL scope and can disclose or amplify
cross-knowledge-base results.

### Authorize candidates one at a time

Rejected because N+1 queries permit provider-controlled database amplification
and do not provide the deterministic batch contract.

### Dynamically invent a legacy chunk revision

Rejected because a runtime hash, timestamp, UUID, or provider value is not the
persisted authoritative revision required for Evidence and citations.

### Truncate or partially accept a fatal provider response

Rejected because structurally invalid or oversized responses have no
deterministic safe partial meaning under this contract.

### Silently fall back to keyword-only retrieval

Rejected because a failed required hybrid component must be explicit rather
than masquerade as successful hybrid retrieval.

### Fuse raw scores or add a P0 reranker

Rejected because source scores are not comparable and a reranker creates a new
model trust boundary outside this decision.

### Treat uploaded instructions as trusted prompt text

Rejected because uploader identity, completed ingestion, relevance, and
citation validity do not grant instruction authority.

## Governance and implementation sequencing

Design review success alone never authorizes AF-3A. The required sequence is:

1. documentation candidate authored;
2. independent read-only review;
3. actionable findings remediated;
4. independent re-review of the exact remediated manifest;
5. separate approval to commit;
6. controlled documentation commit;
7. push to a dedicated remote branch;
8. Draft PR creation;
9. GitHub-hosted CI and documentation checks;
10. independent PR merge-gate review;
11. resolution of any PR or CI findings;
12. separate mark-ready approval;
13. separate merge approval;
14. merge into `main`;
15. local `main` synchronization and branch cleanup;
16. separate explicit AF-3A implementation-start approval; and
17. creation of a new AF-3A implementation branch.

A PASS from a local design review is not commit approval. A committed local
branch is not implementation approval. An open or merged design PR is not
itself AF-3A implementation approval. AF-3A begins only after the design
contract is merged into `main` and an explicit implementation-start
authorization is issued.

Only after that sequence may separately approved slices proceed:

1. AF-3A: bounded one-knowledge-base contracts, SQL-scoped keyword candidates,
   shared validation design, deterministic fakes, and unit/PostgreSQL tests;
2. AF-3B: query embedding, bounded dense adapter with its first consumer,
   response validation, fixed-snapshot final transaction, deterministic
   batching and RRF, and provider-failure tests; and
3. AF-3C: source-level Evidence and citations, authenticated API, cache/error
   integration, privacy telemetry, and executable AF-3 adversarial fixtures.

RAG, prompt construction, ChatModel execution, Agent Runtime, tools, and
approvals remain outside AF-3.

## Acceptance gate

This remediation must stop for a new independent read-only review of the exact
remediated manifest. It does not complete governance steps 4 through 17.

AF-3 remains incomplete until every AF-3 case in
`../retrieval-security-acceptance.md` is implemented at every listed test level
and passes. Later consumers must additionally pass their own consuming-phase
cases. Documentation review supplies no runtime control, no security-
completeness claim, and no production-readiness claim.
