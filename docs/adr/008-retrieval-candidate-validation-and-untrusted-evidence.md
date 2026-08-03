# ADR-008: Validate retrieval candidates in PostgreSQL and treat evidence as untrusted

- Status: Proposed design gate under remediation. Current `main` contains only
  the pure AF-3A retrieval-request validator and
  `SessionAuthenticationProof`; this decision authorizes no additional runtime
  implementation.
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

AF-3A has merged the pure retrieval-request validator and the internal
`SessionAuthenticationProof`, but has not implemented proof-aware initial
access, keyword retrieval, the final PostgreSQL validator/loader, final
reauthentication, fixed-snapshot validation, or their concurrency controls.
AF-3 will combine PostgreSQL keyword candidates with dense candidates from an
external provider. Provider output may be malformed, oversized, stale,
cross-scope, duplicated, or adversarial. Persisted document text may contain
instructions aimed at later model or tool consumers. This ADR fixes the P0
retrieval security contract before a query adapter, retrieval endpoint,
public `Evidence` schema, or public `Citation` schema is introduced.

## Decision

AF-3 retrieval is a bounded operation over exactly one target knowledge base.
Its normative non-HTTP lifecycle is:

1. obtain and preserve the internal `SessionAuthenticationProof`;
2. run one short initial live-session, active-user, and exact-target access
   operation;
3. close every database connection, ORM session, and transaction resource;
4. validate the pure retrieval request with no retained database resource;
5. run one separate scoped keyword database operation;
6. close every database connection, ORM session, and transaction resource;
7. run embedding;
8. run the read-only Chroma compatibility/query path;
9. construct the bounded candidate union;
10. open a fresh final PostgreSQL transaction;
11. sample and bind the final recheck time immediately before its first
    authoritative statement;
12. establish one fixed snapshot and recheck authentication, exact-target
    access, and capabilities;
13. validate and load candidates in deterministic batches from that snapshot;
14. materialize immutable internal authoritative retrieval records;
15. commit and release the final transaction; and
16. perform no authorization-sensitive or lazy database load afterward.

No database connection, ORM Session, or transaction may cross embedding or
Chroma I/O.

PostgreSQL is authoritative. Chroma output is a bounded untrusted candidate
hint. Keyword and dense identities enter one final validator. Retrieved text is
classified as `untrusted_document_content`: evidence data with no instruction,
policy, authorization, tool, approval, or provenance authority.

For this ADR, **internal authoritative retrieval record** is the single
normative term for the frozen, slotted, non-public AF-3A/AF-3B output loaded at
the final boundary. The capitalized normative term **Evidence** is reserved
exclusively for the AF-3C public schema. An internal authoritative retrieval
record is not HTTP-serializable and is never public Evidence or Citation.

This decision is an implementation prerequisite, not an implementation
record. The two merged AF-3A prerequisites do not make AF-3A complete.

## Normative requirement index

The following identifiers are the complete normative runtime security-
requirement index for this ADR. The detailed sections define their precise
meaning. The acceptance specification maps every identifier to one or more
stable case IDs. Governance approvals and production-readiness disclaimers are
non-runtime review gates and are verified by the governance process rather
than assigned to an incapable test layer.

| ID | Normative requirement |
| --- | --- |
| ADR-008-R01 | Each of the exactly two AF-3C public operations uses its one strict P0-v1 request shape, the shared bounded-body contract, and the fixed gate order; retrieval additionally uses the exact decoded-query domain-validation, normalization, and count contract, including U+0000 rejection before NFC. Every request authenticates a live, active principal from an existing, unexpired, unrevoked session, names exactly one target knowledge base, and authorizes from PostgreSQL; client document or chunk IDs never establish access. |
| ADR-008-R02 | The exact sixteen-step non-HTTP lifecycle above is preserved: proof-aware initial access, resource release, pure validation, a separate scoped keyword operation and release, embedding, read-only Chroma, bounded union, and a fresh final transaction. No PostgreSQL connection, transaction, ORM Session, or SessionTransaction crosses embedding or Chroma I/O. |
| ADR-008-R03 | In AF-3A, AF-3B, and AF-3C, the actual final request transaction MUST be PostgreSQL `REPEATABLE READ` and `READ ONLY`. Immediately before its first authoritative statement, it samples one freshly injected timezone-aware UTC `final_now`, binds that same value for the complete final authentication check, then fixes the snapshot and revalidates session, user, target, membership, and current read capabilities. `expires_at > final_now` is valid and equality is expired; neither the initial authentication time nor a Provider timestamp may be reused. |
| ADR-008-R04 | Every validation batch and every authoritative field of each internal authoritative retrieval record loads within the same fixed final snapshot, with no authorization-sensitive PostgreSQL reload after commit. |
| ADR-008-R05 | The final snapshot is the request linearization point; changes before it are visible, changes after it govern later requests, and no asynchronous cancellation is claimed. |
| ADR-008-R06 | Final validation and internal authoritative retrieval record loading are all-or-nothing; any required batch or transaction failure discards accumulated records and produces the planned generic retrieval failure. |
| ADR-008-R07 | PostgreSQL alone supplies authoritative identity, scope, document/chunk state, text, hash, source identity, provenance, and every field of the public citation-resolution result; caller-provided CitationReference fields are locators only. |
| ADR-008-R08 | A chunk is retrieval- and citation-eligible only when its document is completed and its persisted `content_sha256` is a non-null lowercase 64-hex SHA-256 value; no retrieval-time revision fallback is allowed. |
| ADR-008-R09 | The one public citation-resolution operation reauthenticates, scopes to the canonical route knowledge base, strictly accepts the existing CitationReference wire structure, and requires the same current persisted chunk hash; citation possession and caller-provided reference fields never authorize access. |
| ADR-008-R10 | Exactly one `EmbeddingModel.embed([normalized_query])` operation returns exactly one configured-dimension vector of adapter-normalized built-in finite floats without truncation, padding, coercion, or a second vector. Its raw and decoded bodies are each bounded to an inclusive 2,097,152 bytes under one total deadline and one attempt; any count, dimension, type, overflow, or non-finite defect is fatal before Chroma or final SQL and discards keyword candidates. |
| ADR-008-R11 | Provider-response limit profile P0-v1 applies to both the version probe and query, with inclusive wire and decoded ceilings, streaming content-encoding enforcement, and early abort; query responses additionally apply candidate-ID, string, metadata, and exact container-counting JSON-depth limits before normal candidate processing. |
| ADR-008-R12 | Every response-fatal provider-contract condition, including a version mismatch, non-UTF-8 or non-RFC 8259 wire JSON, a JSON distance outside the supported finite numeric domain, or an absent required canonical collection, prevents candidate iteration and produces no internal authoritative retrieval record, no keyword-only fallback, and no candidate-local continuation; AF-3C maps the failure only to the planned generic `503` with no public Evidence. |
| ADR-008-R13 | Every candidate-local condition omits only that bounded record; an authorized request whose candidates are all locally omitted produces an empty internal authoritative retrieval record set without disclosing reasons, which AF-3C maps to empty public Evidence. |
| ADR-008-R14 | Provider distance/score is non-authoritative; a conforming canonical wire distance must decode into the supported finite domain, while a present wrong-type distance/score or a typed value equivalent to `float("nan")`, `float("inf")`, or `float("-inf")` supplied only at the post-decoder typed adapter boundary omits that candidate without compacting its absolute source position; fusion uses the preserved source rank and ignores bounded provider disagreement. |
| ADR-008-R15 | Duplicate IDs retain the earliest rank per source and produce at most one internal authoritative retrieval record per authoritative chunk; AF-3C may map it to at most one public Evidence item. |
| ADR-008-R16 | Each AF-3 POST body, decoded retrieval-query domain excluding U+0000, normalized query scalar values and UTF-8 bytes, public requested results, configured Provider results, raw Provider positions, dense and keyword rank maps, candidate union, validation batches, and final public results use the exact finite P0-v1 domains and relationships. |
| ADR-008-R17 | P0-v1 keyword SQL is scoped before scoring and deterministically ranks PostgreSQL-authoritative `simple` text-search matches by score then native UUID; HTTP retrieval cannot call unscoped worker/internal paths or expose global counts. |
| ADR-008-R18 | Candidate union ordering, partitioning, validation query count, record reconstruction, and failure behavior follow the deterministic batching contract. |
| ADR-008-R19 | P0 fusion uses fixed `RRF_K = 60`, preserved one-based absolute source ranks, exact rational comparison, the specified tie order, display-only decimal serialization, and no raw-score fusion or reranker. |
| ADR-008-R20 | AF-3A/AF-3B use a minimal frozen, slotted, non-public internal authoritative retrieval record that is fully materialized before final commit, is not HTTP-serializable and cannot serialize as public Evidence, structurally separates trusted control/provenance from document text, and assigns text only `untrusted_document_content`. Public Evidence, Citation, and HTTP schemas belong only to AF-3C. |
| ADR-008-R21 | AF-3 enforces the P0 semantic trust boundary: content cannot create trusted instructions, authorization/scope, provider configuration, tools, approvals, secret requests, or citation authority. |
| ADR-008-R22 | Every later RAG, ChatModel, Agent Runtime, or tool-consuming phase adds its own consuming-phase acceptance cases; AF-3 does not claim to test nonexistent consumers. |
| ADR-008-R23 | Authentication, hidden-resource, provider-failure, valid present-empty provider response, authorized-empty, and private cache behavior are deterministic; current AF-3 roles do not fabricate an unreachable retrieval `403`. |
| ADR-008-R24 | The same recursive exact-and-substring secrecy scanner is a mandatory sidecar on every canonical ledger row owned by AF-3A, AF-3B, or AF-3C, for both success and failure at that row's exact level and boundary. Ownership remains boundary-specific: AF-3A owns its observable non-HTTP pure/service, database, and internal authoritative retrieval record sinks; AF-3B owns its observable non-HTTP embedding/Provider/hybrid and regression sinks; AF-3C exclusively owns its observable HTTP response/header/serialization/public sinks. Only exact field-specific public Evidence or citation-resolution response paths are allowlisted, and telemetry is bounded and content-free. RET-PRIV-003/004 are conformance and mutation controls, not the complete applicability map. |
| ADR-008-R25 | P0 retrieval response bounds and semantic trust controls remain distinct from AF-2S2/P1 parser sandboxing and broader hostile-document, identity, and deployment hardening. |
| ADR-008-R26 | The pinned Chroma compatibility probe is per-adapter-instance single-flight, caches success only until close, clears failed/cancelled in-flight state, permits no same-request retry, and may be attempted once by a later independent request. The configured canonical collection UUID is trusted input and retrieval invokes no collection create, `get_or_create`, update, or write-capable initialization path. Embedding, probe, and query each have one bounded total wall-clock deadline in the existing 30-second default/600-second maximum timeout domain, exactly one attempt, and no retry, backoff, failover, stale result, or fallback. |
| ADR-008-R27 | No migration or index is required for current security correctness. Any generated `tsvector`, GIN, or related index remains optional performance work and preserves identical observable security and ranking semantics. |

## Detailed security contract

### Request and initial authorization boundary

AF-3C exposes exactly two public P0-v1 operations and no others:

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/retrieval
Content-Type: application/json

POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve
Content-Type: application/json
```

For both operations, `knowledge_base_id` is the one target. Its accepted
textual form is a lowercase, hyphenated canonical UUID. The retrieval JSON
body is exactly:

```json
{
  "query": "required JSON string",
  "requested_count": 10
}
```

The body contract is closed:

| Field | Required | Exact JSON type | Default | P0-v1 rule |
| --- | --- | --- | --- | --- |
| `query` | Yes | string | None | Validate its decoded domain, normalize, and measure exactly as specified below. |
| `requested_count` | No | integer | `10` | Accept only `1` through `50`, inclusive. |

No coercion is permitted. In particular, a JSON string or floating-point
number is not an integer, and JSON `true` and `false` are not integers.
Duplicate object keys, an absent body, a non-object body, an unsupported media
type, and every unknown or extra field produce the existing generic
`422 VALIDATION_ERROR` after the authentication and hidden-target ordering
below. `document_id`, `document_ids`, `chunk_id`, `chunk_ids`, `limit`,
`count`, and aliases for either accepted field are not accepted. There is no
second equivalent request shape.

Both POST operations share `MAX_APPLICATION_BODY_BYTES = 65,536`. The
measured value is exactly the cumulative number of application-body octets in
ASGI `http.request` events exposed to the application before JSON decoding;
headers, transfer framing, and any server-private representation are not part
of the count. Body collection MUST read incrementally into a bounded
collector. It MUST NOT call an unbounded `body()` or equivalent full-body
materializer and then check the length. Exactly 65,536 observed octets may
proceed. Observation of byte 65,537 immediately aborts collection without
retaining a byte above the ceiling, parsing the remainder of that event, or
requesting another body event, and returns the existing generic
`422 VALIDATION_ERROR`. No JSON parser, duplicate-key detector, schema
validator, normalization, semantic count validator, keyword query, embedding,
Provider call, or final PostgreSQL transaction may run after overflow.

The common public gate order is exact:

1. Resolve the current opaque session and active user.
2. Parse the canonical route UUID and perform exact-target PostgreSQL
   authorization with hidden `404` behavior.
3. Require the supported request media type `application/json`.
4. Incrementally collect at most 65,536 application-body octets.
5. Parse strict UTF-8 JSON with duplicate-key rejection.
6. Validate the operation's closed request schema without coercion.
7. Apply operation-specific semantic validation and normalization: retrieval
   applies the decoded-query domain, normalization, and count rules below;
   citation resolution validates the canonical CitationReference grammar
   below.
8. Begin retrieval work or final authoritative citation-resolution work.

Thus unauthenticated requests return generic `401` without target lookup,
media validation, or application-body processing; malformed or hidden targets
return generic hidden `404` without media validation or application-body
processing; and unsupported media returns generic `422` before body
collection. Every private response, including all failures at these gates,
uses `Cache-Control: private, no-store`.

PostgreSQL character/text values cannot represent code zero, while the keyword
contract below requires `normalized_query` as a PostgreSQL text bound
parameter. The decoded retrieval-query domain therefore excludes U+0000 before
normalization or retrieval work rather than relying on a database failure.

After closed-schema and exact-type validation, the P0-v1 decoded-query
domain-validation and normalization pipeline is exact and ordered:

1. Validate that the exact decoded JSON string consists of Unicode scalar
   values and can be encoded as strict UTF-8. A lone surrogate or any value
   that cannot be encoded as strict UTF-8 is invalid.
2. Reject the query if any decoded scalar is U+0000. This is semantic
   validation, not normalization, and it occurs before NFC.
3. Apply Unicode Normalization Form C (`NFC`) once.
4. Define whitespace as exactly U+0009 through U+000D, U+0020, U+0085,
   U+00A0, U+1680, U+2000 through U+200A, U+2028, U+2029, U+202F, U+205F,
   and U+3000.
5. Remove every leading and trailing code point in that set.
6. Replace each maximal nonempty interior run of those code points with one
   U+0020 SPACE.
7. Perform no case folding, stemming, punctuation removal, locale mapping,
   NFKC, NFKD, or other transformation.
8. Validate that the normalized query contains 1 through 2,048 Unicode scalar
   values, inclusive.
9. Validate that its strict UTF-8 encoding contains 1 through 4,096 bytes,
   inclusive.
10. Begin retrieval work only after both ordered bounds succeed.

U+0000 is not removed, replaced, collapsed, treated as whitespace, changed to
U+FFFD, converted to an empty query or a zero-keyword-candidate query, or sent
to PostgreSQL so that a driver/database failure can be normalized into request
validation. This specific PostgreSQL-text compatibility rule does not reject
every Unicode `Cc` control.

The result of NFC and whitespace processing is `normalized_query`. An empty
result fails the ordered scalar minimum. Its character count is the number of
Unicode scalar values, not UTF-16 code units, graphemes, or bytes. Its byte
count is the length of its strict UTF-8 encoding. Both inclusive P0-v1 limits
apply independently in the order above:

| Request limit | Minimum | Maximum |
| --- | ---: | ---: |
| `normalized_query` Unicode scalar values | 1 | 2,048 |
| `normalized_query` UTF-8 bytes | 1 | 4,096 |
| `requested_count` | 1 | 50 |

For independently constructible boundary fixtures, one ASCII `a` is the
minimum query; 2,048 ASCII `a` values meet the character maximum and 2,049
exceed it; 1,024 U+1F642 values occupy exactly 4,096 UTF-8 bytes and appending
one ASCII `a` produces 4,097 bytes while remaining below the character
maximum. Whitespace-only input is empty after normalization. Zero, a negative
integer, `51`, a boolean, a float, and a numeric string are invalid
`requested_count` values. A literal unescaped NUL byte inside a JSON string is
rejected by strict JSON parsing. In contrast, the ASCII JSON escape
`"\u0000"` is valid JSON and decodes to U+0000; U+0000 alone or embedded as
`"a\u0000b"` is rejected by the semantic gate before NFC. The adjacent-control
positive fixture `"a\u0001b"` is accepted and preserves U+0001, subject to the
same later normalization and bounds, proving that this is not a blanket
Unicode-`Cc` prohibition. All request-domain failures produce the existing
generic `422 VALIDATION_ERROR`, no public Evidence, and no keyword, embedding,
Provider/Chroma, or final-transaction work.

For an authenticated and initially authorized escaped-U+0000 request, current
session/active-user authentication, canonical-target parsing, exact-target
membership/capability authorization, supported-media validation, bounded-body
collection, strict JSON parsing, closed-schema validation, and exact-type
validation may already have completed. After Unicode-scalar and strict UTF-8
validity succeed, U+0000 rejection performs zero NFC/whitespace-normalization
work, zero keyword statements, zero embedding calls, zero Provider/Chroma
calls, and zero final authoritative transactions, and yields zero public
Evidence.
The public result is the generic `422 VALIDATION_ERROR` with
`Cache-Control: private, no-store`.

For retrieval, authentication obtains and preserves the internal
`SessionAuthenticationProof`. The operation-specific portion of the common
order ends the one initial live-session, active-user, exact-target access
operation and returns every database resource before body collection; it then
parses the bounded JSON and runs the already-pure request validator without a
retained database resource. Only a fully authenticated, initially authorized,
valid bounded request may open the separate scoped keyword operation. That
operation completes and releases every database resource before embedding;
embedding completes before the read-only Chroma compatibility/query path.

This ordering means malformed request fields and oversized bodies cannot
replace a required `401` or reveal a hidden target through `422`. It does not
permit retention of the target-authorization transaction or connection while
reading, parsing, or normalizing the body.

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

The initial check, the SQL-scoped keyword query, and the final transaction are
three separate short operations. The pure request validator runs between the
first and second. No transaction, connection, ORM Session, or
SessionTransaction may be retained while waiting for embedding, Chroma,
network, parser, filesystem, or other external I/O.

Query embedding has its own resource-lifecycle boundary; a later Chroma
barrier is not evidence for it. Authentication, exact-target authorization,
bounded body processing, retrieval schema validation, decoded-query domain
validation, query normalization and count validation, and the separate scoped
keyword database operation must have completed and released every database
resource before the single bounded
`EmbeddingModel.embed([normalized_query])` call begins. At an observable
embedding-entry barrier, the request owns no checked-out PostgreSQL connection,
open transaction, ORM Session with retained connection, or open
SessionTransaction, and the final transaction has neither begun nor acquired
a snapshot. Successful embedding returns exactly one configured-dimension
finite vector under the embedding contract below. Embedding failure is
required-Provider-fatal, discards completed keyword candidates, and permits no
keyword-only fallback; controlled request-task cancellation while the
embedding await is blocked may publish no response but must unwind without a
retained database resource, Chroma call, or final transaction. This cleanup
rule does not claim instantaneous cancellation of arbitrary external work.

The current production role matrix gives owner, editor, and viewer the
retrieval read capabilities. AF-3 therefore has no reachable
member-without-read-capability runtime fixture and must not invent one,
monkeypatch one into an integration test, add a fourth role, or change the
matrix. The generic API framework can represent `403` for a visible member
lacking a requested capability, but a future policy that makes retrieval
`403` reachable requires a separately approved policy change and a new
fixture. Current non-member, missing, and hidden targets use generic `404`.

### Public citation-resolution operation

The one citation operation is exactly:

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve
Content-Type: application/json
```

Its body is a strict JSON object with exactly one required field and no
default, alias, duplicate, coercion, or extra field:

```json
{
  "citation_reference": "af3:citation:v1:123e4567-e89b-42d3-a456-426614174000:11111111-1111-4111-8111-111111111111:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

`citation_reference` is a JSON string containing the already-defined
CitationReference wire structure, exactly
`af3:citation:v1:<knowledge_base_uuid>:<chunk_uuid>:<content_sha256>`. Both
UUID components use lowercase hyphenated canonical text and the hash is
exactly 64 lowercase hexadecimal characters. No signed token, opaque citation
token, alternate identifier, query parameter, path token, or second request
shape exists. A malformed reference or request shape produces the same
generic `422 VALIDATION_ERROR` as other authenticated request-validation
failures. A syntactically valid reference whose embedded target does not equal
the already-authorized route target is not authority and resolves to the same
generic hidden `404 NOT_FOUND` as any absent current authoritative match.

After the common authentication, exact-target, media, bounded-body, JSON,
schema, and CitationReference-syntax gates succeed, final citation resolution
uses one short PostgreSQL `REPEATABLE READ`, `READ ONLY` transaction. Its first
authoritative statement fixes the snapshot and rechecks the current session,
active user, exact route target, membership, and read capabilities. The same
snapshot requires a completed current document, the exact current chunk, and
a persisted non-null valid hash equal to the reference hash, and loads every
response value. Authentication loss at this recheck is generic `401`; target
access loss or any absent, ineligible, replaced, cross-target, null-hash, or
hash-mismatched citation is generic hidden `404`. A database or transaction
failure is the existing planned generic `503 RETRIEVAL_UNAVAILABLE`. No
authorization-sensitive reload follows commit.

Caller-provided reference components are lookup assertions only. They never
supply authorization, content, revision, source identity, or provenance. The
resolver performs no query embedding, keyword retrieval, Chroma or other
Provider call, candidate validation, RRF, storage read, filesystem read,
dynamic content hashing, revision repair, cache fallback, or alternate-token
work on success or failure.

A successful resolution returns HTTP `200` with exactly this JSON object
shape, where every non-literal value is loaded from PostgreSQL in the final
snapshot and `citation_reference` is reconstructed from those authoritative
values rather than echoed as caller authority:

```json
{
  "citation_reference": "af3:citation:v1:123e4567-e89b-42d3-a456-426614174000:11111111-1111-4111-8111-111111111111:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "knowledge_base_id": "123e4567-e89b-42d3-a456-426614174000",
  "document_id": "22222222-2222-4222-8222-222222222222",
  "chunk_id": "11111111-1111-4111-8111-111111111111",
  "content": "PostgreSQL-authoritative normalized text",
  "content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "source_display_name": "approved-display-name.txt",
  "page_start": null,
  "page_end": null,
  "character_start": 0,
  "character_end": 40,
  "trust_classification": "untrusted_document_content"
}
```

The four page/character fields are their persisted permitted integer values or
JSON `null`. No source rank, fused value, storage key/path, Provider field,
secret, diagnostic, alternate citation value, or additional response field is
permitted. Every citation success and failure uses
`Cache-Control: private, no-store`.

### Atomic final PostgreSQL boundary

After all external embedding and Chroma work completes, retrieval enters one
short final PostgreSQL transaction with these normative properties:

- isolation level is `REPEATABLE READ`;
- mode is `READ ONLY`; AF-3A, AF-3B, and AF-3C have no read-write exception;
- no embedding, Chroma, network, parser, filesystem, or other external I/O
  occurs inside it;
- immediately before its first authoritative statement, the service samples
  its injected UTC clock exactly once; the sampled `final_now` MUST be
  timezone-aware and is bound unchanged to the complete final authentication
  check;
- `expires_at > final_now` is valid and `expires_at == final_now` is expired;
  the service MUST NOT reuse the initial authentication time, sample again,
  or use an embedding, Chroma, or other Provider timestamp;
- the first authoritative statement acquires the fixed transaction snapshot
  and atomically revalidates session validity, active-user status, the exact
  target knowledge base, current membership, and current read capabilities;
- the actual first final authorization query or an equivalent order-preserving
  same-transaction test hook proves in the real request transaction that
  `current_setting('transaction_isolation') = 'repeatable read'` and
  `current_setting('transaction_read_only') = 'on'`; this proof may not add an
  earlier authorization-sensitive query, move snapshot acquisition earlier,
  or inspect a helper transaction, the concurrent mutation actor's
  transaction, or an unrelated database session;
- every candidate-validation batch and every authoritative field of each
  internal authoritative retrieval record is read using that same fixed
  snapshot;
- authoritative content, hash, source display identity, and provenance load
  before the transaction completes;
- no second PostgreSQL content or provenance load occurs after commit;
- after commit, the application may use only already-loaded immutable internal
  authoritative retrieval record values and may not perform another
  authorization-sensitive or lazy fetch;
- validation and internal authoritative retrieval record loading are all-or-
  nothing; no record accumulated
  from an earlier batch survives authorization failure, an unvalidated
  required batch, transaction failure, or database failure; and
- transaction or database failure produces the explicit planned generic
  `503 RETRIEVAL_UNAVAILABLE` response and never a partial internal
  authoritative retrieval record or partial public Evidence.

Any future read-write exception requires a separately approved ADR change, a
new acceptance case, and an explicit security and transaction review before
implementation. The current AF-3 contract does not permit such an exception.

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
   response's internal authoritative retrieval records were already loaded
   within the fixed snapshot.

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
chunks must not become internal authoritative retrieval records, public
Evidence, or citations. Retrieval must not substitute a
dynamically calculated hash, `updated_at`, chunk UUID, Chroma metadata,
provider metadata, or another implicit revision token. Legacy content becomes
eligible only after an explicitly approved reprocessing or re-ingestion
pipeline persists the normal authoritative hash.

Citation creation requires the persisted non-null hash. A stable citation
reference binds exactly the authoritative knowledge-base UUID, chunk UUID,
and that hash in the CitationReference wire structure defined above. Citation
resolution is the authenticated, one-knowledge-base PostgreSQL operation
defined above.
The resolver starts from the presented opaque session cookie and
reauthenticates the current session row and active user; it MUST NOT accept a
cached, caller-supplied, or prebuilt `Principal` as proof of current
authentication. Missing, expired, revoked, and inactive-user sessions each
produce the same generic `401`, no citation or public Evidence content, no target,
membership, citation, document, or chunk SQL after the failed authentication,
no Provider call, and private/no-store behavior. Only after successful
reauthentication does it recheck current target membership/access, completed
document state, chunk identity, and the persisted expected hash. It fails
closed with generic `404` when access is absent, the expected hash is absent,
or the current hash no longer matches.

No response text, filename, page range, offsets, content hash, document
identity, knowledge-base identity, or citation identity may be sourced from
Chroma `documents` or `metadatas`.

### Embedding operation boundary

AF-3B performs exactly one
`EmbeddingModel.embed([normalized_query])` operation. The adapter returns
exactly one vector. That vector has exactly the trusted configured dimension
and contains only adapter-normalized values whose runtime type is the built-in
`float` and whose values are finite. The retrieval boundary performs no value
coercion: it does not accept integers, booleans, strings, decimal objects,
numeric subclasses, or other float-like values; it does not truncate, pad,
replace, reorder, duplicate, or request a second vector. Adapter normalization
or conversion failure, including overflow, and any wrong count, wrong
dimension, wrong type, `NaN`, positive infinity, or negative infinity is
fatal. It discards completed keyword candidates and permits no Chroma probe,
Chroma query, final PostgreSQL transaction, partial result, or fallback.

For an HTTP-backed embedding adapter, raw/wire bytes and decoded/decompressed
bytes each have the inclusive ceiling 2,097,152. Collection is bounded before
strict UTF-8 decoding and strict JSON materialization. The operation uses one
bounded total wall-clock deadline, including connection, upload, response,
streaming, decoding, and validation, from the existing validated timeout
domain: 30 seconds by default and no configured value above 600 seconds. It
has exactly one attempt and no automatic retry, backoff, failover, alternate
model, cached stale vector, or fallback.

### Chroma provider request and P0-v1 response limits

Repository truth pins `chromadb/chroma:1.5.9` and uses raw HTTP v2 through
`httpx`; no Chroma SDK is a dependency. AF-3B may add a query operation to the
existing provider-neutral `VectorStore` boundary only alongside its first
retrieval consumer. Its compatibility identifier is exactly
`chroma-http-v2-1.5.9`.

Before its first query, that adapter calls `GET /api/v2/version` and requires
HTTP `200`, JSON media type, strict UTF-8, and the exact JSON string
`"1.5.9"`. A missing, malformed, or different version result is a required-
Provider contract failure. The Provider query response has no invented
version field: the version probe, pinned deployment image, v2 path, and
canonical schema together are the supported-version mechanism. An upgrade
requires a reviewed contract/version change rather than best-effort parsing.

Compatibility state is scoped to one adapter instance. Concurrent first uses
join one single-flight probe and observe its same outcome. Only success is
cached, and only until adapter close. Probe failure or cancellation fails all
current waiters, clears the failed in-flight state, and causes the current
retrieval request to fail without a same-request retry. A later independent
request may initiate one new probe attempt. Probe and query each use one
bounded total wall-clock deadline from the same validated 30-second default/
600-second maximum timeout domain and exactly one attempt; neither permits
retry, backoff, failover, a stale result, or fallback.

The canonical collection UUID is injected from trusted configuration. The
retrieval adapter is read-only: it may issue only the compatibility probe and
query operations specified here. It MUST NOT call collection creation,
`get_or_create`, collection update, upsert, delete, or another write-capable
initialization path, even on first use, missing collection, probe failure, or
query failure.

The version response is not a special unbounded read. The same Provider HTTP
profile defined below applies before equality comparison: parsed media type
`application/json` with no parameter or sole case-insensitive
`charset=utf-8`; absent, `identity`, or single-token `gzip`
`Content-Encoding`; a 1,048,576-byte inclusive raw/wire ceiling; a
2,097,152-byte inclusive decoded/decompressed ceiling; incremental raw and
decoded counters; and immediate abort on the first byte above either ceiling
before complete materialization or JSON parsing. A truthful oversized
`Content-Length`, a streamed plus-one byte, unsupported or stacked encoding,
decoded expansion above the ceiling, invalid UTF-8/JSON, or any result other
than the exact JSON string is one generic required-Provider failure. It stops
before `/query`, returns planned generic `503 RETRIEVAL_UNAVAILABLE`, and
permits no fallback, partial dense list, internal authoritative retrieval
record, or public Evidence. JSON whitespace may pad
an otherwise exact version string to exercise equality at a byte ceiling;
the parsed value must still equal exactly `"1.5.9"`.

The one outbound query operation is:

```text
POST /api/v2/tenants/{tenant}/databases/{database}/collections/{collection_uuid}/query
Content-Type: application/json
```

The adapter emits exactly these request keys:

```json
{
  "query_embeddings": [[0.25, -0.5, 0.0, 1.0]],
  "n_results": 40,
  "where": {
    "knowledge_base_id": {
      "$eq": "00000000-0000-0000-0000-000000000000"
    }
  },
  "include": ["distances"]
}
```

The displayed request is also the exact outbound conformance fixture: its
test configuration fixes embedding dimension `4`, and the deterministic fake
returns the ordered vector `[0.25, -0.5, 0.0, 1.0]`. The captured body must
contain exactly that one vector, preserving all four finite values and their
order. It may not truncate, pad, replace, duplicate, normalize, reorder, or
send a second vector. In every non-fixture configuration,
`query_embeddings` likewise contains exactly one array with exactly the
configured embedding dimension and the one validated embedding result's
finite binary64-compatible JSON numbers in unchanged order.
`n_results` is exactly the configured Provider count defined below. `where`
contains exactly the one target UUID equality as a defense-in-depth hint; it
never authorizes. `include` is exactly `["distances"]`; Chroma returns IDs
unconditionally. The adapter sends no `documents`, `metadatas`, `embeddings`,
`uris`, `data`, `where_document`, or additional request key. Provider text,
metadata, and provenance are therefore not requested at all.

The canonical Chroma 1.5.9 wire response is one JSON object with exactly eight
top-level keys: `ids`, `embeddings`, `documents`, `uris`, `data`,
`metadatas`, `distances`, and `include`. Key order is immaterial, but unknown
keys and duplicate keys are response-fatal. A nonempty canonical fixture is:

```json
{
  "ids": [
    [
      "chunk:11111111-1111-4111-8111-111111111111",
      "chunk:22222222-2222-4222-8222-222222222222"
    ]
  ],
  "embeddings": null,
  "documents": null,
  "uris": null,
  "data": null,
  "metadatas": null,
  "distances": [
    [
      0.125,
      0.25
    ]
  ],
  "include": [
    "distances"
  ]
}
```

The only canonical empty fixture is:

```json
{
  "ids": [
    []
  ],
  "embeddings": null,
  "documents": null,
  "uris": null,
  "data": null,
  "metadatas": null,
  "distances": [
    []
  ],
  "include": [
    "distances"
  ]
}
```

`ids` and `distances` are required, non-null arrays with outer cardinality
exactly one because the request contains one query embedding. Their inner
array lengths must be equal. `include` is required, non-null, and exactly
`["distances"]`. `embeddings`, `uris`, and `data` are required and exactly
JSON `null`; any non-null value is response-fatal.

Although the adapter never requests them, an untrusted Provider may
unsolicitedly populate `documents` or `metadatas`. Each key is therefore
required and may be either JSON `null` or an outer array of cardinality one
whose inner array has the same length as `ids[0]`. A document element is null
or a bounded string. A metadata element is null or an object with bounded
distinct string keys and scalar string, finite JSON number, or boolean values;
nested metadata objects, nested metadata arrays, and metadata null values are
invalid. JSON booleans are the boolean branch and are not numeric values; all
numeric metadata values must be supported finite IEEE-754 binary64 values.
No document element may be a boolean, number, object, or array, and no
metadata element may be a string, number, boolean, or array. These bounded
unsolicited values are ignored after structural/limit validation and never
become authority. This is the only permitted non-null return-field variation,
and it does not alter the required `include` value. No required field may be
missing, and no array, scalar, singleton, or null coercion is allowed. Parsed
`Content-Type` must be `application/json` with either no parameter or the sole
case-insensitive parameter `charset=utf-8`; a missing header, another media
type/parameter/charset, invalid UTF-8, or a UTF-8 byte-order mark is
response-fatal. `Content-Encoding` may be absent, `identity`, or the single
token `gzip`; any other or stacked encoding is response-fatal. Gzip is
streamed through both the raw and decoded counters before JSON
materialization.

The absolute dense source position is the zero-based index `i` in
`ids[0]`/`distances[0]`; its one-based source rank is fixed as `i + 1` before
any candidate-local validation. The parallel arrays are validated for
cardinality before iteration. A wrong-type ID or distance at one otherwise
reconstructable position is candidate-local as defined below. Omitting it
never compacts or renumbers later positions. Missing arrays, unequal lengths,
an outer cardinality other than one, or any shape that prevents this
reconstruction is response-fatal.

The conversion boundary is ordered and explicit:

1. bounded raw wire bytes;
2. bounded decompression, when declared;
3. strict UTF-8 and strict RFC 8259 tokenization with duplicate-key rejection;
4. the decoded generic JSON object, still untrusted;
5. canonical top-level/cardinality/limit validation and absolute-position
   assignment; then
6. typed candidate conversion retaining the immutable absolute rank.

A Provider SDK or deterministic fake may enter only at step 6 through the same
bounded typed-candidate contract. It cannot bypass the byte/structure
requirements for a raw-wire test or reclassify a raw numeric-domain failure.

The versioned initial Provider HTTP response profile is:

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

The Provider wire format is strict RFC 8259 JSON. Literal `NaN`, `Infinity`,
and `-Infinity` tokens are not valid JSON. Each numeric-domain fixture is the
complete canonical nonempty response above with exactly one intended change:
replace the first `0.125` token in `distances[0]` with `NaN`, `Infinity`,
`-Infinity`, or `1e400`. The first three responses are invalid JSON. The
fourth is syntactically valid JSON, but its numeric token cannot be represented
in the supported finite IEEE-754 binary64 distance domain. It is therefore a
response-fatal unsupported Provider numeric representation. A raw fragment
such as `{"score":1e400}` is not a numeric-domain fixture because it would
false-pass through the wrong-envelope branch. A permissive decoder must not
turn a literal non-RFC 8259 constant into a candidate-local value, and a
decoder that maps `1e400` to infinity must not reclassify that wire-fatal
response. These failures occur before candidate iteration and produce the
generic failure, no partial internal authoritative retrieval record, no public
Evidence, no keyword-only fallback, and
no candidate-local continuation.

The adapter enforces the wire/decode portions of this profile for both
`/version` and `/query`, and enforces the query-envelope portions after a
bounded `/query` decode, in this order:

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
6. The bounded parser accepts only strict RFC 8259 JSON and rejects non-standard
   numeric tokens such as `NaN`, `Infinity`, and `-Infinity`.
7. Convert a JSON numeric token in a distance position only into the supported
   finite IEEE-754 binary64 domain; reject an unsupported-range value such as
   `1e400` before candidate iteration even if a decoder maps it to infinity.
8. Enforce ID, individual string, metadata-entry, metadata-key,
   metadata-value, and nesting ceilings during or immediately after bounded
   parsing and before normal candidate processing.
9. Any transport, decode, numeric-domain, body, nesting, or per-field
   hard-limit violation is a whole-response provider-contract failure.

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
fatal and produces planned generic `503 RETRIEVAL_UNAVAILABLE`, no internal
authoritative retrieval record, no public Evidence, no partial result, and no
keyword-only fallback.

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
internal authoritative retrieval record or public Evidence, supplies no
authority, and cannot widen scope. Surrounding
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
- wire data that is not strict RFC 8259 JSON, including literal `NaN`,
  `Infinity`, or `-Infinity` tokens;
- a syntactically valid JSON numeric distance that cannot be represented in the
  supported finite IEEE-754 binary64 domain, such as `1e400`;
- excessive nesting;
- wrong top-level response shape;
- missing required candidate collection;
- mismatched parallel-array lengths;
- candidate count above the configured maximum;
- a missing, malformed, or unsupported Provider version result;
- an unknown/duplicate top-level key, forbidden non-null
  `embeddings`/`uris`/`data`, malformed optional `documents`/`metadatas`, or
  noncanonical `include` value;
- any per-field hard-limit violation; and
- a data structure that prevents deterministic candidate-position
  reconstruction.

Every whole-response fatal condition produces generic planned
`503 RETRIEVAL_UNAVAILABLE`, no partial result, no keyword-only fallback, no
candidate-local continuation, no internal authoritative retrieval record, and
no public Evidence.

Candidate-local non-finite distance/score handling exists only at the explicitly named
post-decoder typed adapter boundary. At that boundary, the wire response has
already been successfully and boundedly decoded, and a provider SDK, adapter,
or deterministic test double returns a typed candidate object whose diagnostic
distance/score is equivalent to `float("nan")`, `float("inf")`, or
`float("-inf")`. The invalid record is placed at a known absolute position;
only that typed candidate is omitted, valid companions before and after it
retain their original absolute ranks, and those ranks supply their unchanged
RRF contributions. These cases do not claim that a non-finite value was
transported in conforming JSON.
PostgreSQL remains the only authorization, internal authoritative retrieval
record, public Evidence, provenance, and citation authority.

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
- a present distance/score at a reconstructable position is a string, object,
  boolean, null, or array; or
- a post-decoder typed adapter candidate has a score equivalent to
  `float("nan")`, `float("inf")`, or `float("-inf")`; or
- the individual candidate record is otherwise invalid without making
  candidate positions ambiguous.

Candidate-local omissions do not disclose their reasons. Remaining candidates
retain their original absolute source ranks and relative Provider order;
positions are never compacted or re-enumerated. RRF uses those unchanged
absolute ranks, not the ordinal positions of the survivors. If every candidate
is locally omitted and final authorization succeeds, AF-3B produces an
authorized empty internal authoritative retrieval record set; AF-3C maps that
set to authorized empty public Evidence.

Provider distance/score is non-authoritative. The canonical Chroma wire
response requires one aligned distance value at every position, and each JSON
number must decode into the supported finite IEEE-754 binary64 domain. The
provider-neutral step-6 `TypedCandidate` may represent its diagnostic
`provider_score` as `float | None`; `None` is valid only for an injected typed
adapter/fake that did not originate from a missing or short canonical Chroma
array. A finite present value is only a diagnostic hint; fusion uses the
preserved absolute list rank, not the raw value. The candidate-local
non-finite cases begin only after bounded wire decoding at the typed adapter
boundary and never represent non-finite JSON transport.

Bounded provider text is ignored. Bounded metadata disagreement is ignored for
authority: knowledge-base, document, chunk, content-hash, and provenance
metadata can neither authorize nor deauthorize a valid canonical ID, and the
ID still enters PostgreSQL validation. Oversized text or metadata remains a
whole-response hard-limit violation.

Duplicate IDs are not malformed. The earliest provider rank per source is
retained, later occurrences do not create another internal authoritative
retrieval record or public Evidence item, and PostgreSQL remains the identity
authority.

### Request, result, and candidate bounds

P0-v1 fixes these positive constants; they are not implementation-selected
defaults:

| Constant | Exact value |
| --- | ---: |
| `MAX_APPLICATION_BODY_BYTES` | 65,536 |
| `DEFAULT_REQUESTED_COUNT` | 10 |
| `MAX_REQUESTED_COUNT` | 50 |
| `DENSE_OVERFETCH_FACTOR` | 4 |
| `MAX_DENSE_CANDIDATES` | 128 |
| `MAX_PROVIDER_CANDIDATES` | 128 |
| `MAX_KEYWORD_CANDIDATES` | 128 |
| `MAX_UNIQUE_CANDIDATES` | 192 |
| `VALIDATION_BATCH_SIZE` (`B`) | 64 |

The query character/byte constants are fixed in the request contract above.
Normalization rejects either an excessive scalar-value count or an excessive
UTF-8 byte count before provider work. `requested_count` is validated before
arithmetic. These caller-field violations use the existing
`422 VALIDATION_ERROR` envelope. For an accepted public requested count `R`,
the configured outbound Provider count `C` is:

```text
C = min(
        MAX_PROVIDER_CANDIDATES,
        MAX_DENSE_CANDIDATES,
        checked_multiply(R, DENSE_OVERFETCH_FACTOR)
    )
```

The count domains and relationships are exact:

| Symbol | Meaning and invariant |
| --- | --- |
| `R` | Validated public `requested_count`; `1 <= R <= 50`. |
| `C` | Configured `n_results` in the one outbound query; `4 <= C <= 128` and it equals the formula above. |
| `P` | Raw canonical Provider position count, `len(ids[0])`; `0 <= P <= C`. `P > C` or `P > MAX_PROVIDER_CANDIDATES` is response-fatal, not truncated. |
| `D` | Dense count, defined as the number of unique UUID keys in the dense absolute-rank map after candidate-local ID/score omission and earliest-rank deduplication; `0 <= D <= P`. |
| `K` | Keyword count, defined as the number of rows/rank-map keys returned after the deterministic SQL top-N cutoff; `0 <= K <= 128`. |
| `U` | Cardinality of the union of the dense and keyword rank-map key sets; `max(D, K) <= U <= D + K`. If `U > 192`, discard both maps and fail generically without SQL validation. |
| `Q` | Candidate-validation batch query count; `0` when `U = 0`, otherwise `ceil(U / 64)`. The final authorization statement is not part of `Q`. |
| `E` | Eligible authoritative record count after every batch succeeds in the fixed snapshot; `0 <= E <= U`. |
| `F` | Final public Evidence count after exact RRF sort and cutoff; `F = min(R, E)`. |

`P` counts original Provider positions, including candidate-local invalid and
duplicate records. `D` counts only retained unique dense identities, while
each retained identity maps to its earliest unchanged absolute rank. `K`
already contains unique authoritative chunk rows with one-based ranks. `U`,
`Q`, and `E` are computed before the public result cutoff; `F` is applied only
after all validation and exact deterministic fusion complete.

The multiplication is checked even though the public P0-v1 range is bounded.
For example, the default `R = 10` produces `C = 40`, while `R = 50` produces
the dense ceiling `C = 128`. At `R = 10`, a canonical response with exactly
`P = 40` raw positions is accepted and one with exactly `P = 41` is
response-fatal even though `41 <= MAX_PROVIDER_CANDIDATES`. At every valid
`R`, a canonical Provider response with exactly `C` positions is accepted for
candidate processing; `C + 1` positions is fatal.
Individually legal disjoint dense and keyword maps can produce `U = 193`,
which exercises the union failure without violating either source maximum.
No count is silently clamped except the explicit calculation of `C`, and no
fatal source or union overflow permits a partial internal authoritative
retrieval record, partial public Evidence, or fallback.

### Keyword retrieval boundary

The exact versioned P0-v1 PostgreSQL keyword-ranking contract uses the
`simple` text-search configuration. The normalized, bounded user query is
passed as a bound parameter only after the decoded-query U+0000 exclusion has
succeeded, to:

```sql
plainto_tsquery('simple', normalized_query)
```

Here `normalized_query` denotes the bound parameter, not interpolated SQL.
User text is not interpreted as PostgreSQL web-search operators or raw
`tsquery` syntax. It is a precondition of this call that `normalized_query`
contains no U+0000; implementations must not deliberately send U+0000 to
PostgreSQL and convert a driver or database failure into validation. The
authoritative chunk vector is:

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
reranking. SQL MUST establish `keyword_score DESC, document_chunks.id ASC` and
the corresponding one-based ranks before applying the `128`-row cutoff; it may
not `LIMIT` an unordered intermediate relation and sort afterward. The
conformance fixture contains 129 eligible rows, including equal-score UUIDs on
both sides of the cutoff, and varies insertion and physical row-return order.
The selected UUID set and ranks 1 through 128 must always equal the normative
total order. A CTE or equivalent query shape may avoid inconsistent score
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
    return no partial internal authoritative retrieval record or public
    Evidence.
14. Telemetry may report unique candidate count, configured batch size, and
    actual batch query count, but never raw query, internal authoritative
    retrieval record content, or public Evidence content.

The implementation must not issue N+1 candidate authorization queries or one
unbounded `IN` query.

### Deterministic fusion

P0 fusion is reciprocal rank fusion over at most two bounded normalized lists:
keyword and dense. It uses preserved one-based absolute source ranks and fixed
`RRF_K = 60`. The authoritative ordering score is an exact rational value,
never a binary64 value:

```text
one source at rank r:
    numerator = 1
    denominator = 60 + r

keyword rank k and dense rank d:
    numerator = 120 + k + d
    denominator = (60 + k) * (60 + d)
```

A missing source contributes no term; it is not rank zero, infinity, or a
configured sentinel contribution. Implementations may reduce the fraction but
need not do so. To compare positive scores `n1/d1` and `n2/d2`, compare the
exact integers `n1 * d2` and `n2 * d1`; bounded checked integers or arbitrary-
precision integers must make overflow impossible. Equal cross-products mean
an exact rational tie and advance to the next comparator. Binary64 conversion,
decimal display text, epsilon comparison, and source-score values are
forbidden as authoritative sort keys.

Operation order is fixed: retain the earliest absolute rank per source,
construct the one- or two-source rational above, compare every candidate by
exact cross-multiplication, apply all tie breakers, assign one-based fused
ranks, apply the public `R` cutoff, and only then serialize display values.
Raw keyword and vector scores are not added, multiplied, calibrated, or used
to override rank. One internal authoritative retrieval record remains per
authoritative chunk; AF-3C may map it to one public Evidence item.

Results sort by:

1. exact fused rational descending;
2. best contributing rank ascending;
3. keyword rank ascending, with absence last;
4. dense rank ascending, with absence last; and
5. canonical authoritative chunk UUID ascending.

The public `fused_score` is a JSON string matching
`^0\.[0-9]{12}$`. It is the exact rational rounded to 12 digits after the
decimal point using decimal round-half-to-even and rendered with all 12
digits. It is display-only: clients and the server may not use the serialized
value to reconstruct ordering or ties. For example, the mathematically equal
rank pairs `(keyword=3, dense=80)` and `(keyword=24, dense=30)` both equal
`29/1260` and serialize as `"0.023015873016"`. Straight binary64 evaluation
can produce respectively `0.023015873015873014` and
`0.023015873015873017`; treating those artifacts as unequal would incorrectly
rank the second candidate first. Exact comparison identifies a tie, after
which best contributing rank correctly places `(3, 80)` first.

The AF-3B internal authoritative retrieval record retains contributing
absolute source ranks and receives a one-based fused rank. P0 has no reranker,
model-based ordering, or hidden
nondeterministic tie-break. The UUID order used for SQL batching is not the
final RRF result order.

### Internal record and public Evidence/Citation trust boundary

AF-3A introduces only a minimal internal authoritative retrieval record. It is
frozen, slotted, non-public, and fully materialized before final commit; it has
no lazy ORM fields and no generic public serializer. Its type and fields MUST
NOT be named or exposed as public `Evidence`. A serialization attempt through
the public Evidence schema fails closed until AF-3C deliberately maps the
record's internal values.

The RET-EVID stable-ID prefix in the acceptance specification is retained for
historical traceability. It does not mean that an AF-3A or AF-3B row exposes
the AF-3C public Evidence schema. AF-3A and AF-3B rows produce only non-public,
non-HTTP-serializable internal authoritative retrieval records; public
Evidence and Citation remain AF-3C-only.

The internal authoritative retrieval record has two disjoint members: trusted
control/provenance primitives and document-derived text. Text is structurally confined to the
document-content member and receives only the fixed classification
`untrusted_document_content`; document text cannot populate or alter a
control/provenance member. AF-3B may extend the internal control member only
with bounded rank/fusion primitives. Public Evidence, Citation, and HTTP
schemas remain AF-3C work.

The future AF-3C public Evidence mapping has two disjoint field partitions.

The PostgreSQL-authoritative internal control/provenance partition is loaded
through one allowlisted projection in the fixed final snapshot; AF-3C may map
it to these public Evidence fields:

| Evidence field | Exact authority |
| --- | --- |
| `knowledge_base_id` | Current PostgreSQL knowledge-base UUID selected by the exact-target predicate. |
| `document_id` | Current PostgreSQL document UUID joined to the eligible chunk. |
| `chunk_id` | Current PostgreSQL chunk UUID. |
| `content` | `DocumentChunk.normalized_text`. |
| `content_sha256` | Persisted non-null valid `DocumentChunk.content_sha256`. |
| `source_display_name` | Approved persisted display identity, such as original filename, never a storage key or path. |
| `page_start`, `page_end` | Persisted permitted page range or null. |
| `character_start`, `character_end` | Persisted permitted character offsets or null. |

The deterministic derived internal partition is not described as loaded from
PostgreSQL; AF-3C may map it to these public Evidence fields:

| Evidence field | Only permitted derivation |
| --- | --- |
| `keyword_rank` | The preserved validated one-based keyword absolute-rank map, or null when absent. |
| `dense_rank` | The preserved validated one-based dense absolute-rank map, or null when absent. |
| internal fused rational | The exact fixed `RRF_K = 60` construction from those rank maps. |
| `fused_score` | The 12-place round-half-even display-only serialization of that exact rational. |
| `fused_rank` | One-based position after the complete exact rational and tie-break ordering. |
| `trust_classification` | The fixed literal `untrusted_document_content`; content does not select it. |
| `citation_reference` | Deterministic construction from the PostgreSQL-authoritative target UUID, chunk UUID, and persisted hash, using exactly `af3:citation:v1:<knowledge_base_uuid>:<chunk_uuid>:<content_sha256>`. |

Every internal authoritative retrieval record value is immutable and fully
materialized before final commit.
Every derived value is computed only after all authoritative rows have loaded
and every required validation batch has succeeded. Provider distance, text,
metadata, completion order, SQL row order, and content semantics cannot supply
or alter either partition. The transparent citation reference is an identity
and revision locator, not a bearer credential; the resolver reauthenticates
and reauthorizes it as specified above.

Public Evidence and citations never expose host filesystem paths, password hashes,
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
`future consuming-phase acceptance` cases proving that untrusted public Evidence is
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

In AF-3B and AF-3C hybrid retrieval, both the scoped keyword path and the
required dense Provider path are required components. Their failure fixtures
follow the normative lifecycle and are intentionally asymmetric. Keyword SQL
runs before embedding or Chroma: a keyword/database failure aborts retrieval
immediately, so that execution has zero embedding calls, zero Chroma work, and
no possible dense result. Embedding or Chroma failure occurs only after
keyword candidates may have been produced and discards all of them. Neither
failure degrades to a single-source result or returns partial output.

Source-isolation tests still prove dense-only success with a valid present-
empty keyword result, keyword-only success with the canonical present-empty
Provider response, and mixed success with source-distinct sentinels. The
Provider-fatal fixture deliberately retains a known eligible nonempty keyword
sentinel and still requires no result. The keyword-fatal fixture has no dense
sentinel because the lifecycle makes one impossible. Completion order or
previously accumulated candidates never creates a fallback mode.

Public behavior is:

- invalid authentication or inactive user: generic
  `401 AUTHENTICATION_REQUIRED`;
- missing, hidden, unowned, or inaccessible target: generic `404 NOT_FOUND`;
- an authenticated, initially authorized request with invalid media, body,
  JSON, schema, type, query domain, query bounds, or count: generic
  `422 VALIDATION_ERROR`;
- an authorized request with zero surviving candidates: successful empty
  public Evidence;
- a current authoritative citation match: the exact citation-resolution
  object defined above;
- required provider, provider-contract, final-transaction, or database failure:
  planned generic `503 RETRIEVAL_UNAVAILABLE`; and
- every private retrieval or citation-resolution success or failure:
  `Cache-Control: private, no-store`.

The existing framework's generic `403 FORBIDDEN` remains available, but the
current owner/editor/viewer retrieval role matrix has no executable
member-without-read-capability state. AF-3 has no synthetic current `403`
fixture.

Observable private-operation sinks must not contain:

- raw query text;
- chunk or document content;
- candidate, document, knowledge-base, or citation IDs;
- filenames or filesystem paths;
- session/CSRF values or digests, passwords, provider credentials, or database
  secrets;
- raw embeddings; or
- raw Provider bodies, Provider exception details, or database exception
  details.

The canonical ledger is also the exact R24 applicability map: every row whose
Owner is AF-3A, AF-3B, or AF-3C incorporates the scanner into its own oracle at
its declared test level and execution boundary. This includes success and
failure rows in every case family; no RET-PRIV row, selected fatal list, HTTP-
success list, sampling rule, or case-level status narrows that projection.
FUTURE rows acquire the sidecar only when their named consuming phase makes
them mandatory. A row scans every sink observable at its assigned boundary
and level and registers every sensitive value reachable by that exact fixture;
an absent sink or unreachable value is proved absent rather than silently
waived. A non-public row has an empty public-field allowlist.

AF-3A owns non-HTTP application/log/trace, exception, pure/service,
SQL/database-client/driver/transaction, and internal authoritative retrieval
record sinks. AF-3B owns non-HTTP embedding/Provider transport/client and
hybrid-state sinks in addition to the AF-3A sinks reachable by its regressions.
AF-3C alone owns HTTP response status, headers, metadata, serialization,
access-log, and public sinks. Across those phase allocations the harness
captures every listed sink; no sink migrates to AF-3C merely because a later
public operation will consume the result. A recursive scanner walks all nested
keys, values, sequence members, byte strings, and rendered representations.
For every pairwise-distinct high-entropy sentinel, both exact equality and
substring presence are failures.

Success executions use success-only sentinels, including values created or
loaded only after successful final authorization, so a leak guarded by a
success branch is observable. Retrieval success separately exercises a
nonempty public Evidence response and authorized-empty public Evidence
response; citation success
exercises the exact resolution object. The response-body allowlist is
field-specific, not object-wide. For retrieval, a sensitive value may occur
only as the value of its intended serialized public Evidence field from this
exact set: `knowledge_base_id`, `document_id`, `chunk_id`, `content`,
`content_sha256`, `source_display_name`, `page_start`, `page_end`,
`character_start`, `character_end`, `keyword_rank`, `dense_rank`,
`fused_score`, `fused_rank`, `trust_classification`, and
`citation_reference`. For citation resolution, a value may occur only as the
value of its intended field in the exact response object defined above. No
allowlist applies to an enclosing response object, response metadata or
headers, an unexpected field, a nested diagnostic, transport state, or any
other sink. Query, session, credential, secret, embedding, raw-body, and
exception/diagnostic sentinels have no public allowlisted field.

Fatal conformance fixtures inject distinct sensitive-class and failure-detail
sentinels appropriate to the boundary reached. The Provider-fatal fixture has
a known eligible nonempty keyword sentinel. The keyword/database-fatal fixture
aborts before embedding or Chroma and therefore has no dense candidate. The
AF-3A final-authorization, final-commit, and later-batch fixtures use only
keyword or explicit bounded synthetic candidates. The two separate AF-3B
hybrid final-commit and hybrid later-batch regressions alone carry successful
bounded Provider work into their named database failure. Each fatal fixture
returns no public Evidence, citation, or fallback and has no response-body
sentinel allowlist.

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

No migration or index is required for security correctness at this point.
Generated `tsvector`, GIN, and related indexes remain optional performance
work. Any later optimization MUST preserve identical observable scoping,
eligibility, tokenization, scoring, total ordering, cutoff, privacy, and
failure semantics.

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
persisted authoritative revision required for public Evidence and citations.

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

Repository-wide role separation, session boundaries, single-writer operation,
baseline hashing, evidence invalidation, risk-based verification, completion
semantics, remediation naming, and gate-output requirements are normative in
`../../AGENTS.md`. Canonical AF-3 phase/slice state is maintained in
`../roadmap.md`; the executable tuple remains canonical only in
`../retrieval-security-acceptance.md`.

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
16. separate explicit approval for the next AF-3A implementation slice; and
17. creation of a new AF-3A implementation branch for that slice.

A PASS from a local design review is not commit approval. A committed local
branch is not implementation approval. An open or merged design PR is not
itself approval for more AF-3A implementation. The next AF-3A runtime slice
begins only after the remediated design contract is merged into `main` and an
explicit implementation-start authorization is issued.

The pure retrieval-request validator and `SessionAuthenticationProof` are the
only merged AF-3A prerequisites. Separately approved remaining slices proceed
under this fixed ownership:

1. AF-3A owns proof-aware initial access, SQL-scoped deterministic keyword
   candidates, the first final `REPEATABLE READ`, `READ ONLY` fixed-snapshot
   authoritative validator/loader, final-clock authentication and access
   classification, the minimal internal authoritative retrieval record,
   deterministic fakes, and the recursive non-HTTP scanner sidecar on every
   AF-3A-owned canonical row at its exact boundary and level,
   and its unit/real-PostgreSQL/concurrency/fault-injection gates;
2. AF-3B cannot begin dense retrieval, Provider querying, or fusion until
   every canonical AF-3A-owned row at a provider-independent execution
   boundary is implemented, tested, reviewed, and merged. An AF-3B hybrid
   regression has its own phase-qualified identity and is never an AF-3A
   close prerequisite.
   It then adds only query embedding, the bounded read-only dense adapter,
   bounded candidate handling, deterministic fusion, the recursive non-HTTP
   scanner sidecar on every AF-3B-owned canonical row, other tests, and
   specified AF-3A regression reruns while reusing the AF-3A controls; and
3. AF-3C owns source-level public Evidence and Citation schemas, exactly the
   retrieval and citation-resolution POST operations with the shared bounded-body gate,
   cache/error integration, real-request transaction-setting proof, public
   success/failure privacy telemetry and HTTP response/header/serialization/
   public all-sink scanning on every AF-3C-owned canonical row at its exact
   boundary and level, and executable AF-3 adversarial fixtures.

RAG, prompt construction, ChatModel execution, Agent Runtime, tools, and
approvals remain outside AF-3.

## Acceptance gate

This remediation must stop for a new independent read-only review of the exact
remediated manifest. It does not complete governance steps 4 through 17.

AF-3 remains incomplete until the canonical `(case ID, variant, test level)`
ledger in `../retrieval-security-acceptance.md` passes. AF-3A closes only from
its provider-independent rows. AF-3B entry depends on that close result, and
AF-3B closes only from its own rows, including separately labelled hybrid
regressions. AF-3C-only obligations are excluded from those non-HTTP gates but
are never marked complete by them.
Later consumers must additionally pass their own consuming-phase cases.
Documentation review supplies no runtime control, no security-completeness
claim, and no production-readiness claim.
