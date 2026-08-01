# AF-3 retrieval security acceptance specification

## Status and purpose

This is the required future executable-test specification for ADR-008.
AF-3 remains planned and unimplemented. Every case has implementation status
`REQUIRED_NOT_YET_IMPLEMENTED`; no case is passing and no source-level
retrieval behavior is claimed.

Coverage and distinct behavior determine the inventory. This revision contains
exactly 113 cases: 109 AF-3 runtime cases and 4 future consuming-phase
obligations. AF-3 cannot complete until every AF-3 case passes at every listed
level. The separate future consuming-phase cases become executable obligations
only when their named consumer is introduced and are not AF-3C runtime claims.

| Category | Stable IDs | Count |
| --- | --- | ---: |
| Authentication and request scope | RET-AUTH-001–RET-AUTH-011 | 11 |
| Final transaction and concurrency | RET-CONC-001–RET-CONC-012 | 12 |
| Provider transport, decoding, and taxonomy | RET-PROV-001–RET-PROV-040 | 40 |
| Request, result, union, and SQL bounds | RET-BND-001–RET-BND-015 | 15 |
| Keyword SQL scope | RET-KEY-001–RET-KEY-004 | 4 |
| RRF and result determinism | RET-RANK-001–RET-RANK-005 | 5 |
| Evidence, eligibility, and citations | RET-EVID-001–RET-EVID-010 | 10 |
| AF-3 untrusted-evidence boundary | RET-INJ-001–RET-INJ-006 | 6 |
| Privacy, public errors, and cache behavior | RET-PRIV-001–RET-PRIV-006 | 6 |
| **AF-3 runtime total** | All nine AF-3 runtime categories | **109** |
| Future consuming-phase obligations | RET-FUT-001–RET-FUT-004 | 4 |
| **Complete specification total** | AF-3 runtime plus future obligations | **113** |

Test-level counts below count stable IDs assigned to each level; a stable ID
can count at more than one level. Every parameterized variant stated within an
ID is independently executable at every listed applicable level and is not a
new stable ID.

| Planned test level | Stable-ID count |
| --- | ---: |
| `unit` | 51 |
| `provider-adapter contract` | 40 |
| `PostgreSQL integration` | 103 |
| `HTTP integration` | 109 |
| `future consuming-phase acceptance` | 4 |

All 113 stable IDs have status `REQUIRED_NOT_YET_IMPLEMENTED`; zero are
implemented, passing, skipped, or waived.

## Test conventions

- Candidate IDs use `chunk:<canonical UUID>`.
- A valid persisted chunk hash matches `^[0-9a-f]{64}$`.
- Unless a case says otherwise, query, result, candidate, and provider values
  are within configured bounds.
- “Authorized Evidence” is built from the fixed final PostgreSQL snapshot and
  carries `untrusted_document_content`.
- “Authorized empty Evidence” means final authentication and exact-target
  authorization succeeded but no eligible candidate survived.
- Every future private success and error response has
  `Cache-Control: private, no-store`.
- Existing generic public behavior is `401 AUTHENTICATION_REQUIRED` and hidden
  `404 NOT_FOUND`; planned provider/final-transaction failure is
  `503 RETRIEVAL_UNAVAILABLE`. Request-field bound failures use the existing
  `422 VALIDATION_ERROR` envelope.
- Current owner/editor/viewer members all have retrieval read capabilities.
  No case fabricates an unreachable member-without-read `403`. The generic API
  framework retains `403`; a future reachable retrieval policy requires a
  separately approved fixture.
- The fixed final transaction MUST be PostgreSQL `REPEATABLE READ` and
  `READ ONLY`. AF-3A, AF-3B, and AF-3C have no read-write exception. Any future
  exception requires a separately approved ADR change, a new acceptance case,
  and an explicit security and transaction review before implementation. Its
  first authoritative statement fixes the snapshot and revalidates the
  session, active user, exact target, membership, and read capabilities. The
  actual first final authorization query or an equivalent order-preserving
  same-transaction test hook must prove in the real request transaction that
  `current_setting('transaction_isolation') = 'repeatable read'` and
  `current_setting('transaction_read_only') = 'on'` without an earlier
  authorization-sensitive query, earlier snapshot acquisition, a helper
  transaction, the concurrent mutation actor's transaction, or an unrelated
  database session.
- Provider wire responses use strict UTF-8 and RFC 8259 JSON, and Provider JSON
  distances must be representable as finite IEEE-754 binary64 values. Literal
  `NaN`, `Infinity`, and `-Infinity` wire tokens are invalid JSON, and a
  syntactically valid unsupported-range distance such as `1e400` is
  response-fatal before candidate iteration. Each raw numeric fixture is the
  complete canonical Chroma response with only one distance token changed; a
  fragment such as `{"score":1e400}` is not a valid fixture. A permissive
  decoder or infinity-producing conversion cannot make either category
  candidate-local. Candidate-local non-finite fixtures exist only after
  bounded decoding at the typed adapter boundary, use typed values equivalent
  to `float("nan")`, `float("inf")`, or `float("-inf")`, and never serialize
  them as conforming JSON.
- Planned test-level values are deterministic ordered sets drawn from:
  `unit`, `provider-adapter contract`, `PostgreSQL integration`,
  `HTTP integration`, and `future consuming-phase acceptance`.
- Unit tests use deterministic fakes and no network. Provider-adapter contract
  tests use bounded mock transports. PostgreSQL integration tests observe SQL,
  transaction isolation, snapshots, and concurrency. HTTP integration tests
  observe public status, envelopes, cache headers, and no-fallback behavior.

AF-3C has exactly two public operations and no other endpoint:

- `POST /api/v1/knowledge-bases/{knowledge_base_id}/retrieval`, whose strict
  JSON object has required string `query`, optional strict integer
  `requested_count` defaulting to `10`, and no other key or alias; and
- `POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve`, whose
  strict JSON object has exactly one required string field,
  `citation_reference`, containing the existing
  `af3:citation:v1:<canonical-knowledge-base-UUID>:<canonical-chunk-UUID>:<lowercase-64-hex-hash>`
  CitationReference structure, with no default, alias, or extra field.

Both use a lowercase hyphenated canonical route UUID, exact
`Content-Type: application/json`, duplicate-key rejection, no coercion, and
the same shared application-body ceiling. The gate order is current-session
and active-user authentication; canonical target parsing and exact-target
authorization; supported media; bounded body collection; strict JSON;
closed-schema validation; operation semantics; then retrieval or final
authoritative citation resolution. Thus invalid authentication remains
generic `401`, a malformed or hidden target remains generic `404`, and an
authorized caller's invalid media, body, JSON, schema, or semantic value
remains generic `422`.

`MAX_APPLICATION_BODY_BYTES` is exactly 65,536 application-body octets from
ASGI `http.request` events before JSON decoding. The collector is incremental,
stores at most 65,536 bytes, accepts equality, and aborts immediately when it
observes byte 65,537. On overflow, JSON-parser, duplicate-key, schema,
normalization, semantic-validation, keyword, embedding, Provider, and final-
transaction call counts are all zero. An unbounded `body()` followed by a
length check cannot pass. Unauthenticated and hidden-target executions have
zero application-body receive calls; unsupported media has zero body receive
calls after the earlier gates succeed.

The valid retrieval body seed
`R = {"query":"a","requested_count":1}` is exactly 33 ASCII bytes. The
exact-limit fixture is `R` followed by exactly 65,503 U+0020 JSON-whitespace
bytes; the plus-one fixture uses 65,504. The valid citation seed uses the
exact 154-byte CitationReference shown in ADR-008 and is exactly 179 ASCII
bytes as
`C = {"citation_reference":"af3:citation:v1:123e4567-e89b-42d3-a456-426614174000:11111111-1111-4111-8111-111111111111:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}`.
Its exact-limit fixture appends exactly 65,357 U+0020 bytes and its plus-one
fixture appends 65,358. Each padded body remains valid strict JSON for its
operation and differs only at the body ceiling. Each chunked plus-one fixture
delivers the same 65,537-byte body in chunks of exactly 32,768, 32,768, and 1
byte, with the final byte as the sole overflow trigger.

Citation success is HTTP `200` and an exact closed JSON object containing only
`citation_reference`, `knowledge_base_id`, `document_id`, `chunk_id`,
`content`, `content_sha256`, `source_display_name`, `page_start`, `page_end`,
`character_start`, `character_end`, and `trust_classification`. The reference
is reconstructed as
`af3:citation:v1:<authoritative-target-UUID>:<authoritative-chunk-UUID>:<authoritative-persisted-hash>`;
every identity/content/hash/source/provenance value is current PostgreSQL
data, with the four page/character fields permitted integer or null values; and
`trust_classification` is exactly `untrusted_document_content`. No rank, fused
value, Provider field, storage path/key, diagnostic, or extra field exists.
Caller reference components are locators only and are never response
authority. Every citation path performs zero keyword, embedding, Chroma,
other Provider, candidate-union, batch-validation, RRF, storage, filesystem,
dynamic-hash, alternate-token, and cache-fallback work.

The strict-request decision matrix below indexes separate executable
parameter rows. It is not substitute coverage: each stable label is defined
inside the owning ten-field case and is independently executed at that case's
declared capable levels.

| Decision row | Owning stable variant | Path/auth/target fixture | Request-media/body fixture | Exact gate and public oracle |
| --- | --- | --- | --- | --- |
| F1A canonical-path control | `RET-BND-003::CANONICAL-PATH-CONTROL` | Lowercase hyphenated canonical UUID; live session; authorized existing target. | Exact `application/json`; valid strict body. | Path representation passes; later retrieval executes; exact deterministic Evidence success with private/no-store. |
| F1B uppercase equivalent path | `RET-BND-003::NONCANONICAL-PATH` uppercase parameter | Uppercase text for the same UUID value; live session; otherwise authorized existing target. | Exact `application/json`; valid strict body. | Canonical-path gate returns generic hidden `404`; no redirect, target SQL, body processing, or retrieval work; private/no-store. |
| F1B unhyphenated equivalent path | `RET-BND-003::NONCANONICAL-PATH` unhyphenated parameter | Unhyphenated text for the same UUID value; live session; otherwise authorized existing target. | Exact `application/json`; valid strict body. | Canonical-path gate returns generic hidden `404`; no redirect, target SQL, body processing, or retrieval work; private/no-store. |
| F1C supported-media control | `RET-BND-003::SUPPORTED-MEDIA-CONTROL` | Canonical path; live session; authorized existing target. | Exact `application/json`; valid strict body. | Request-media gate passes; later retrieval executes; exact deterministic Evidence success with private/no-store. |
| F1D unsupported-media rejection | `RET-BND-003::UNSUPPORTED-MEDIA` | Canonical path; live session; authorized existing target. | Exact `text/plain`; otherwise valid JSON bytes. | Request-media gate returns generic `422 VALIDATION_ERROR`; body processing and retrieval call counts are zero; private/no-store. |
| F1E unauthenticated precedence | `RET-AUTH-001::UNAUTHENTICATED-PRECEDENCE` | Canonical route form; missing session; target exists. | Exact `text/plain`; malformed/oversized 65,537-byte body. | Authentication gate returns generic `401 AUTHENTICATION_REQUIRED`; target, media, body receive, and retrieval call counts are zero; private/no-store. |
| F1F hidden-target precedence | `RET-AUTH-005::HIDDEN-TARGET-PRECEDENCE` | Canonical path; live session; target is hidden by absent membership. | Exact `text/plain`; malformed/oversized 65,537-byte body. | Exact-target gate returns generic hidden `404 NOT_FOUND`; media, body receive, and retrieval call counts are zero; private/no-store. |
| F1G media-before-body precedence | `RET-BND-003::MEDIA-BEFORE-BODY-PRECEDENCE` | Canonical path; live session; authorized existing target. | Exact `text/plain`; malformed/oversized 65,537-byte body. | Request-media gate returns generic `422 VALIDATION_ERROR`; body-receive/parser and retrieval call counts are zero; private/no-store. |
| F1H authorized body-validation control | `RET-BND-003::AUTHORIZED-BODY-VALIDATION-CONTROL` | Canonical path; live session; authorized existing target. | Exact `application/json`; parseable object with one forbidden extra field. | Body/schema gate returns generic `422 VALIDATION_ERROR`; body/schema validation is observed and retrieval call counts are zero; private/no-store. |
| F1I retrieval body equality | `RET-BND-003::BODY-EXACT-65536` | Canonical retrieval path; live session; authorized target. | Exact `application/json`; constructible valid 65,536-byte `R` fixture above. | Bounded collection accepts equality; JSON/schema/semantics and retrieval each execute once; deterministic Evidence success with private/no-store. |
| F1J retrieval body plus one | `RET-BND-003::BODY-PLUS-ONE-65537` | Same as F1I. | Exact `application/json`; constructible valid 65,537-byte `R` fixture in one body event. | Byte 65,537 produces generic `422`; parser and every later call count are zero; private/no-store. |
| F1K retrieval chunked plus one | `RET-BND-003::CHUNKED-BODY-PLUS-ONE-65537` | Same as F1I. | Same valid 65,537-byte `R` fixture split 32,768/32,768/1. | The final byte aborts immediately; no further receive, parse, schema, normalization, retrieval, or final SQL; generic `422`, private/no-store. |
| F1L literal NUL JSON rejection | `RET-BND-003::LITERAL-NUL-JSON-PARSER-REJECTION` | Canonical path; live session; authorized target. | Exact `application/json`; one literal unescaped byte `0x00` occurs between the quotes of the `query` JSON string. | Strict JSON parsing rejects the unescaped control byte with generic `422 VALIDATION_ERROR`; schema, query-domain, normalization, and retrieval call counts are zero; private/no-store. |
| F1M escaped U+0000 semantic handoff | `RET-BND-003::ESCAPED-U0000-DOMAIN-HANDOFF` | Canonical path; live session; authorized target. | Exact `application/json`; parameterized once with the valid ASCII JSON query escape `"\u0000"` and once with the embedded escape `"a\u0000b"`. | Both parse as strict JSON and hand their decoded values to RET-BND-001's same pre-NFC semantic rejection; each returns generic `422 VALIDATION_ERROR` with zero normalization, retrieval, or Evidence work and private/no-store. |
| F1N U+0000 authentication precedence | `RET-BND-003::U0000-AUTHENTICATION-PRECEDENCE` | Canonical route form; missing session; target exists. | Parameterized once with the F1L literal-NUL body and once with the F1M escaped-U+0000-alone body. | Authentication returns generic `401`; target, media, body receive, parsing, query-domain, normalization, and retrieval call counts are zero; private/no-store. |
| F1O U+0000 hidden-target precedence | `RET-BND-003::U0000-HIDDEN-TARGET-PRECEDENCE` | Canonical path; live session; target hidden by absent membership. | Parameterized once with the F1L literal-NUL body and once with the F1M escaped-U+0000-alone body. | Exact-target authorization returns generic hidden `404`; media, body receive, parsing, query-domain, normalization, and retrieval call counts are zero; private/no-store. |
| F2A citation supported-media control | `RET-EVID-003::CITATION-SUPPORTED-MEDIA-CONTROL` | Canonical citation route; live session; authorized current target. | Exact `application/json`; valid strict body `C`. | Media/body/schema gates and final PostgreSQL resolution each execute once; exact citation object success with private/no-store. |
| F2B citation body equality | `RET-EVID-003::CITATION-BODY-EXACT-65536` | Same as F2A. | Constructible valid 65,536-byte `C` fixture. | Bounded collection accepts equality and exact authoritative resolution succeeds. |
| F2C citation body plus one | `RET-EVID-003::CITATION-BODY-PLUS-ONE-65537` | Same as F2A. | Constructible valid 65,537-byte `C` fixture in one body event. | Byte 65,537 produces generic `422`; parser/schema/reference/final-SQL calls are zero. |
| F2D citation chunked plus one | `RET-EVID-003::CITATION-CHUNKED-BODY-PLUS-ONE-65537` | Same as F2A. | Same valid 65,537-byte `C` fixture split 32,768/32,768/1. | Final byte aborts immediately; no further receive, parser, schema, reference, or final-SQL work; generic `422`. |
| F2E citation unsupported media | `RET-EVID-003::CITATION-UNSUPPORTED-MEDIA` | Canonical citation route; live session; authorized target. | Exact `text/plain`; otherwise valid `C` bytes. | Generic `422`; body receive/parser/schema/resolution counts are zero. |
| F2F citation unauthenticated precedence | `RET-EVID-003::CITATION-UNAUTHENTICATED-PRECEDENCE` | Canonical citation route; missing session; target exists. | `text/plain`; 65,537-byte malformed/oversized body. | Generic `401`; target/media/body/resolution counts are zero. |
| F2G citation hidden-target precedence | `RET-EVID-008::CITATION-HIDDEN-TARGET-PRECEDENCE` | Canonical citation route; live session; target hidden by no membership. | `text/plain`; 65,537-byte malformed/oversized body. | Generic hidden `404`; media/body/resolution counts are zero. |
| F2H citation strict schema | The individually named `CITATION-SCHEMA` and `CITATION-REFERENCE` rows owned by RET-EVID-003 | Canonical citation route; live session; authorized target. | Exact `application/json`; each row has one absent/extra/duplicate/type/body-shape or reference-grammar defect. | Each reaches only its intended JSON/schema/reference gate, returns generic `422`, and performs no final citation SQL or Provider work. |
| F2I citation uppercase target path | `RET-EVID-003::CITATION-NONCANONICAL-PATH-UPPERCASE` | Uppercase text for the same authorized UUID; live session. | Exact `application/json`; valid `C`. | Generic hidden `404`; no redirect, target SQL, media/body, or final resolution. |
| F2J citation unhyphenated target path | `RET-EVID-003::CITATION-NONCANONICAL-PATH-UNHYPHENATED` | Unhyphenated text for the same authorized UUID; live session. | Exact `application/json`; valid `C`. | Generic hidden `404`; no normalization/redirect, target SQL, media/body, or final resolution. |
| F2K citation database failure | `RET-EVID-003::CITATION-DATABASE-FAILURE` | Canonical route; live session; authorized target. | Exact `application/json`; valid `C`. | Injected final authoritative PostgreSQL failure yields generic planned `503`, no citation content, and no fallback. |
| F2L citation/reference target mismatch | `RET-EVID-008::CITATION-REFERENCE-TARGET-MISMATCH` | Caller is authorized for canonical route target A; syntactically valid reference embeds distinct target B. | Exact `application/json`; sole valid reference field. | Final PostgreSQL resolution remains scoped to A, yields generic hidden `404`, and never treats B/reference possession as authority. |

ADR-008 defines only exact request media `application/json` and the generic
unsupported-media branch. It does not define a missing request
`Content-Type`, request-media parameter/charset, malformed request
`Content-Type`, or structured-suffix branch; no matrix row assigns a new
outcome to those inputs.

Query fixtures require the exact JSON string type, strict decoded Unicode
scalars, and strict UTF-8 representability; then reject any U+0000 before NFC
as semantic validation rather than normalization. They next apply NFC exactly
once; trim the exact Unicode whitespace set U+0009–U+000D, U+0020, U+0085,
U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, and U+3000;
collapse each interior run of that set to U+0020; and make no other
transformation. They then validate 1–2,048 normalized Unicode scalar values,
followed by 1–4,096 strict UTF-8 bytes, before retrieval. A literal unescaped
NUL in a JSON string fails strict JSON parsing, while the ASCII escape
`"\u0000"` is valid JSON and fails only after decoding at the query semantic
gate. Boundary fixtures use
one ASCII `a`, 2,048/2,049 ASCII `a` values, 1,024 U+1F642 values with/without
one trailing ASCII `a`, and the U+0000/U+0001 controls defined below, as
appropriate.

The fixed P0-v1 count constants are:

| Constant | Value |
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

For requested count `R`, configured Provider count
`C = min(128, checked_multiply(R, 4))`. Raw Provider positions satisfy
`0 <= P <= C`; the deduplicated post-local-omission dense rank-map count
`D <= P`; keyword count `K <= 128`; unique union count
`U = |dense keys union keyword keys| <= 192`; validation-batch count is `0`
when `U = 0` and otherwise `ceil(U / 64)`; eligible authoritative count
`E <= U`; and final public result count is exactly `min(R, E)`.

Repository truth fixes compatibility identifier
`chroma-http-v2-1.5.9`: raw `httpx` HTTP v2 against the pinned
`chromadb/chroma:1.5.9`, with no Chroma SDK dependency. A first-use
`GET /api/v2/version` must return the exact JSON string `"1.5.9"` after the
same incremental media/content-encoding/raw-byte/decoded-byte profile used by
the query response. Equality and plus-one wire/decoded bounds, streamed
chunks, `identity`/`gzip`, forbidden encoding/expansion, and immediate early
abort are independently executable before equality comparison. The query is
one `POST` to the v2 collection `/query` path with exactly
`query_embeddings`, `n_results`, the one-target
`where.knowledge_base_id.$eq`, and `include: ["distances"]`. It never requests
documents, metadata, embeddings, URIs, data, or document filters.

The exact outbound-vector oracle configures embedding dimension `4`; the
deterministic fake returns `[0.25, -0.5, 0.0, 1.0]`; and the POST contains
exactly `"query_embeddings":[[0.25,-0.5,0.0,1.0]]`. The spy compares array
cardinality, every value and its order, and canonical serialized JSON.
Truncation, padding, replacement, normalization or reordering, a duplicate
vector, a second embedding call, or any non-finite value fails.

Every raw response fixture has parsed media type `application/json` with no
parameter or only case-insensitive `charset=utf-8`, and is one strict UTF-8
JSON object without a BOM. `Content-Encoding` is absent/`identity` or exactly
one `gzip` token; no other/stacked encoding is supported. The object has exactly
`ids`, `embeddings`, `documents`, `uris`, `data`, `metadatas`, `distances`,
and `include`. Unknown/duplicate keys are fatal. `ids` and `distances` are
non-null matrices with outer cardinality one and equal inner lengths;
`include` is exactly `["distances"]`; `embeddings`, `uris`, and `data` are
null. `documents` and `metadatas` are null unless a case deliberately supplies
aligned, bounded unsolicited values, which remain ignored. The canonical
single-candidate and empty fixtures are respectively:

```json
{"ids":[["chunk:11111111-1111-4111-8111-111111111111"]],"embeddings":null,"documents":null,"uris":null,"data":null,"metadatas":null,"distances":[[0.125]],"include":["distances"]}
```

```json
{"ids":[[]],"embeddings":null,"documents":null,"uris":null,"data":null,"metadatas":null,"distances":[[]],"include":["distances"]}
```

The permitted unsolicited grammar is closed. Each aligned document element
is JSON null or a bounded string. Each aligned metadata element is JSON null
or a shallow object whose distinct bounded string keys map only to bounded
strings, supported finite JSON numbers, or booleans. A null value inside a
metadata object, nested object, nested array, non-finite or unsupported-range
number, wrong document element type, or wrong metadata element type is fatal;
no acceptance variant broadens this grammar.

For every candidate at zero-based position `i`, absolute dense rank is fixed
to `i + 1` before local validation. Invalid records never compact surviving
ranks. The provider-neutral typed-candidate diagnostic score may be `None`
only in a typed fake/adapter fixture; a missing or short canonical Chroma
distance array is fatal.

Suite-wide source-isolation fixtures are mandatory:

- **Dense-only success:** keyword SQL returns a proven valid empty list; one
  dense sentinel is the only possible returned identity and has no keyword
  rank.
- **Keyword-only success:** the Provider returns the canonical present-empty
  response; one keyword sentinel is the only possible returned identity and
  has no dense rank.
- **Mixed-source success:** source-distinct keyword-only and dense-only
  sentinels plus a controlled overlap prove both rank maps.
- **Provider-fatal:** keyword SQL has a known eligible nonempty sentinel before
  the Provider failure; the result is still generic `503` with no sentinel,
  Evidence, or fallback.
- **Keyword-fatal:** the Provider has a known eligible nonempty dense sentinel
  before the keyword/database failure; the result is still generic `503` with
  no sentinel, Evidence, or fallback.

Source completion order is controlled separately from source ranks. A
positive dense case cannot pass through keyword evidence, and a positive
keyword case cannot pass through dense evidence. These conventions override
any less-specific “may have content” setup below: no Provider-fatal service
variant may use an empty keyword path, and no keyword-fatal service variant may
use an empty dense path.

Whenever a case requires a secrecy scan, “all observable sinks” means
application log messages; access logs; exception/error records and exception
string/`repr` forms; structured log keys and recursively nested values; trace
and span names, attributes, status descriptions, and events; HTTP client and
transport diagnostics; Provider transport records; exposed SQL/database/
driver/transaction diagnostics; response status, headers, metadata, and body;
and every other sink named by ADR-008. The shared recursive scanner fails on
exact equality or substring presence for any injected sentinel in any key,
value, sequence member, byte string, or rendered representation. Successful
HTTP cases invoke this scanner too. Only a sentinel at its exact intended
public Evidence or citation-resolution response field is allowlisted; an
entire response object, headers/metadata, extra fields, diagnostics, and all
other sinks remain scanned without exemption.

This scanner is a mandatory assertion wrapper around every successful private
HTTP execution in this specification, not only the privacy cases. It runs for
each nonempty retrieval, authorized-empty retrieval, and successful citation
resolution after response capture. A success case that does not register and
scan every sink fails the suite even if its functional assertions pass.

The P0-v1 provider-response hard ceilings used by the cases are:

| Limit | Ceiling |
| --- | ---: |
| Raw/wire response | 1,048,576 bytes |
| Decoded/decompressed response | 2,097,152 bytes |
| Candidate ID | 128 UTF-8 bytes |
| Individual untrusted string | 4,096 UTF-8 bytes |
| Metadata entries per candidate | 32 |
| Metadata key | 128 UTF-8 bytes |
| Metadata scalar/string value | 1,024 UTF-8 bytes |
| JSON nesting depth | 16 |

Every listed Provider ceiling is inclusive: equality is accepted and only a
measured value above the ceiling is a hard-limit violation. A “valid
present-empty Provider envelope” below means the exact canonical empty fixture
above after the supported version probe: outer cardinality one, empty aligned
inner `ids`/`distances` arrays, required null fields, exact `include`, and no
placeholder record.

Canonical depth fixtures use `D0 = 0`; for `n >= 1`, `Dn = {"v": D(n-1)}` when
`n` is odd and `Dn = [D(n-1)]` when `n` is even. Depth counts container nodes
only: scalar `0` has depth 0; `{}`, `[]`, and `{"v": 0}` have depth 1;
`{"v": []}` has depth 2; and `[{"v": [0]}]` has depth 3. Thus D16 has depth 16
and D17 has depth 17 under ADR-008's exact streaming-stack algorithm.

Every case below contains the same required fields. Membership-removal cases
are intentionally separate only where they prove a different layer or timing
point: final-transaction linearization, zero-candidate authorization, or
citation reauthorization.

RRF ordering uses exact positive rationals. One-source rank `r` is
`1/(60+r)`; two-source ranks `(k,d)` are
`(120+k+d)/((60+k)*(60+d))`; missing sources contribute no term. Comparisons
use exact integer cross-multiplication before best-rank, keyword-rank
absent-last, dense-rank absent-last, and UUID tie breaks. Public
`fused_score` is a display-only JSON string with exactly 12 decimal places,
rounded half-to-even from the exact rational after ordering.

## Authentication and request scope

### RET-AUTH-001 — Missing session

- **Category:** Authentication and request scope. The stable executable
  precedence variant is
  `RET-AUTH-001::UNAUTHENTICATED-PRECEDENCE` for ADR-008-R01.
- **Initial database state:** Target has an owner, one completed document, and one eligible hashed chunk.
- **Authenticated principal and membership state:** No session and no principal.
- **Provider or Chroma input:** Two independently executable HTTP variants
  use the canonical route form so the authentication stage executes. Variant
  A uses exact request media `Content-Type: application/json` and the valid
  minimal body `{"query":"a"}`. The
  `RET-AUTH-001::UNAUTHENTICATED-PRECEDENCE` variant uses
  `Content-Type: text/plain` and a deterministic malformed/oversized
  65,537-byte body; media, syntax, and size would be diagnosed only after successful authentication and
  exact-target authorization. Target/membership, request-media, body-parser,
  schema, keyword, embedding, and Provider spies are configured.
- **Concurrent state change:** None.
- **Expected public result:** Each execution returns exactly the generic
  `401 AUTHENTICATION_REQUIRED` envelope, zero Evidence, zero citation
  content, and `Cache-Control: private, no-store`.
- **Expected internal validation result:** Each execution stops at
  current-session authentication. The labeled precedence execution performs
  zero target or membership SQL after authentication fails, zero
  request-media validation, zero application-body receive calls, zero body
  parsing, zero schema validation, and
  zero keyword, embedding, or Provider work.
- **Forbidden behavior:** The labeled execution returning `404`, `422`, a
  path diagnostic, an unsupported-media diagnostic, a body/parser diagnostic,
  target-existence information, private content, or any later-stage call.
- **Planned test level:** HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-002 — Expired session

- **Category:** Authentication and request scope.
- **Initial database state:** The session expiry is at or before the controlled clock; target content is otherwise eligible.
- **Authenticated principal and membership state:** Cookie names the expired session for a current owner.
- **Provider or Chroma input:** Provider spies must receive no call.
- **Concurrent state change:** None.
- **Expected public result:** Generic `401 AUTHENTICATION_REQUIRED`, no Evidence, and private/no-store.
- **Expected internal validation result:** Session resolution rejects expiry before target authorization.
- **Forbidden behavior:** Reconstructing authority from membership or invoking a provider.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-003 — Initially inactive user

- **Category:** Authentication and request scope.
- **Initial database state:** User is inactive; an unexpired unrevoked session, membership, and eligible content exist.
- **Authenticated principal and membership state:** The cookie cannot produce a usable live principal.
- **Provider or Chroma input:** Provider spies must receive no call.
- **Concurrent state change:** None.
- **Expected public result:** Generic `401 AUTHENTICATION_REQUIRED`, no Evidence, and private/no-store.
- **Expected internal validation result:** Active-user validation fails before target or provider work.
- **Forbidden behavior:** Authorizing from session existence or persisted membership alone.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-004 — Reachable owner/editor/viewer read matrix

- **Category:** Authentication and request scope.
- **Initial database state:** Parameterized owner, editor, and viewer memberships each target eligible hashed content.
- **Authenticated principal and membership state:** A live session for the parameterized member role.
- **Provider or Chroma input:** One bounded canonical eligible candidate.
- **Concurrent state change:** None.
- **Expected public result:** Each role receives the same authorized read Evidence contract, never a synthetic retrieval `403`.
- **Expected internal validation result:** Current capability policy grants both retrieval read capabilities to each existing role.
- **Forbidden behavior:** Inventing a fourth role, monkeypatching an impossible denial state, or granting write capability through retrieval.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-005 — Non-member with empty candidate set

- **Category:** Authentication and request scope. The stable executable
  precedence variant is `RET-AUTH-005::HIDDEN-TARGET-PRECEDENCE` for
  ADR-008-R01.
- **Initial database state:** Target exists with eligible content but no caller membership.
- **Authenticated principal and membership state:** Live active user is not a target member.
- **Provider or Chroma input:** Two independently executable variants use the
  lowercase hyphenated canonical target UUID. Variant A uses exact request
  media `Content-Type: application/json` and valid body `{"query":"a"}`.
  The `RET-AUTH-005::HIDDEN-TARGET-PRECEDENCE` variant uses
  `Content-Type: text/plain` and a deterministic malformed/oversized
  65,537-byte body; the request-media, syntax, and size defects would each be diagnosed only for an
  authorized target. Request-media, body-parser, schema, keyword, embedding,
  Provider, final-authorization, and candidate-validation spies are
  configured.
- **Concurrent state change:** None.
- **Expected public result:** Each execution returns exactly the generic
  hidden `404 NOT_FOUND` envelope, zero Evidence, zero citation content, and
  `Cache-Control: private, no-store`.
- **Expected internal validation result:** Current-session and active-user SQL
  may complete. The exact-target membership/capability SQL is the only
  target-dependent SQL permitted and fails closed. The labeled precedence
  execution performs zero request-media validation, zero body parsing, zero
  application-body receive calls, zero schema validation, zero keyword SQL,
  zero final-transaction SQL, and zero
  embedding or Provider work.
- **Forbidden behavior:** The labeled execution returning `401`, `422`, an
  unsupported-media diagnostic, a body/parser diagnostic, `200 []`, `403`,
  target-existence information, global search, candidate processing, or a
  Provider call.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-006 — Unowned legacy knowledge base

- **Category:** Authentication and request scope.
- **Initial database state:** Legacy target and eligible-looking content exist without any membership.
- **Authenticated principal and membership state:** Live active user has no fabricated legacy ownership.
- **Provider or Chroma input:** Provider spies must remain unused.
- **Concurrent state change:** None.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no Evidence, and private/no-store.
- **Expected internal validation result:** User-facing scoped SQL fails closed; internal worker access is not consulted.
- **Forbidden behavior:** Implicit ownership, internal-repository fallback, or authorized empty Evidence.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-007 — Client document IDs cannot authorize

- **Category:** Authentication and request scope.
- **Initial database state:** A private target document belongs to another user's knowledge base.
- **Authenticated principal and membership state:** Live caller has no target membership.
- **Provider or Chroma input:** Request supplies the real private document ID and an otherwise bounded query.
- **Concurrent state change:** None.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no Evidence, and private/no-store.
- **Expected internal validation result:** Exact-target PostgreSQL membership fails before body validation; the unknown `document_id` field is never evaluated as authority. RET-BND-003 separately proves its authorized-target `422` extra-field policy.
- **Forbidden behavior:** Document-ID possession, metadata, existence checks, or validation-order changes widening access.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-008 — Client chunk IDs cannot authorize

- **Category:** Authentication and request scope.
- **Initial database state:** A current eligible chunk belongs to another user's private target.
- **Authenticated principal and membership state:** Live caller has no target membership.
- **Provider or Chroma input:** Request supplies the real canonical chunk ID as a client-controlled field.
- **Concurrent state change:** None.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no Evidence, and private/no-store.
- **Expected internal validation result:** Exact-target PostgreSQL membership fails before body validation; the unknown `chunk_id` field is never evaluated as authority. RET-BND-003 separately proves its authorized-target `422` extra-field policy.
- **Forbidden behavior:** Treating a canonical ID, Provider metadata, citation-like value, or validation-order change as access.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-009 — Exactly one target despite other memberships

- **Category:** Authentication and request scope.
- **Initial database state:** Caller is a member of A and B; each has eligible content.
- **Authenticated principal and membership state:** Live member requests exactly A.
- **Provider or Chroma input:** Valid A candidate plus a B candidate.
- **Concurrent state change:** None.
- **Expected public result:** Only A Evidence is returned.
- **Expected internal validation result:** Request scope and every final predicate remain exactly A despite separate B access.
- **Forbidden behavior:** Widening to all visible knowledge bases or returning B in the A response.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-010 — True authorized zero-hit retrieval

- **Category:** Authentication and request scope.
- **Initial database state:** Target membership and access are current; no eligible content matches.
- **Authenticated principal and membership state:** Live owner, editor, or viewer retains read capability through final snapshot.
- **Provider or Chroma input:** Legal keyword retrieval returns zero; the bounded Provider response is a valid present-empty Provider envelope, including every required parallel collection at length zero, so parsing succeeds with zero deterministic Provider positions and zero dense candidates.
- **Concurrent state change:** None.
- **Expected public result:** Successful authorized empty Evidence and private/no-store.
- **Expected internal validation result:** The adapter returns an empty dense candidate list without error; final authorization still runs; the unique union is empty and validation-batch query count is zero.
- **Forbidden behavior:** `404`, `503`, a synthetic candidate, a missing-collection error, keyword-only degraded mode, skipped final authorization, or fabricated Evidence.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-011 — Session revoked before request begins

- **Category:** Authentication and request scope.
- **Initial database state:** The user exists and is active; the target knowledge base, valid membership, and eligible documents may exist normally; the session exists, has not expired, has otherwise valid fields, and has a non-null `revoked_at` committed before the request begins.
- **Authenticated principal and membership state:** The cookie names the already-revoked session for a user who would otherwise have valid target membership.
- **Provider or Chroma input:** Embedding-provider and Chroma/provider spies are configured and must receive no call; keyword retrieval must not execute.
- **Concurrent state change:** None; revocation is committed before request start.
- **Expected public result:** Generic `401 AUTHENTICATION_REQUIRED`, no Evidence, no citation, no revocation-reason disclosure, and `Cache-Control: private, no-store`.
- **Expected internal validation result:** Initial authentication rejects the already-revoked session before target lookup or candidate validation; no slow provider or retrieval work starts, and the request never relies on the later final-snapshot recheck.
- **Forbidden behavior:** Accepting the session because expiry remains in the future; treating prior revocation as final-validation-only; invoking embedding, Chroma, keyword retrieval, or PostgreSQL candidate validation; authorized empty Evidence; hidden-resource `404`; or revocation-reason disclosure.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Final transaction and concurrency

### RET-CONC-001 — External-work lifecycle barriers retain no database resource

- **Category:** Final transaction and concurrency. This stable case owns four
  independently executable lifecycle variants:
  `RET-CONC-001::EMBEDDING-LIFECYCLE-SUCCESS`,
  `RET-CONC-001::EMBEDDING-LIFECYCLE-FAILURE`,
  `RET-CONC-001::EMBEDDING-LIFECYCLE-CANCELLATION`, and
  `RET-CONC-001::CHROMA-LIFECYCLE-REVOCATION`.
- **Initial database state:** Caller initially has target membership and
  eligible content. A test-only lifecycle harness runs against the real
  PostgreSQL pool at PostgreSQL integration level and surrounds the actual
  authenticated request at HTTP integration level without production
  diagnostics or public API exposure. Distinct correlation tokens separate
  the request, concurrent actor, health checks, and background work. For the
  request token, the harness observes actual pool checkout/checkin events,
  request-scoped Session and `SessionTransaction` begin/end state,
  transaction begin/end state, owned backend identity, and final first-
  statement snapshot acquisition.
- **Authenticated principal and membership state:** A live member passes
  current-session authentication, canonical target authorization, exact
  request-media validation, bounded body collection, strict schema,
  normalization, and semantic count validation. Any permitted initial or
  keyword database operation ends and checks in its connection before either
  external barrier. Only the Chroma-revocation variant removes membership.
- **Provider or Chroma input:** Each row is a distinct deterministic execution
  with event ledgers and `entered`/`release` latches, never sleeps or eventual
  polling.

  | Stable variant label | Exact external fixture |
  | --- | --- |
  | `RET-CONC-001::EMBEDDING-LIFECYCLE-SUCCESS` | The single `EmbeddingModel.embed([normalized_query])` call enters and blocks after all initial/request work. At the barrier, the fake has not returned a vector and Chroma/final-validation calls are zero. Release returns exactly `[0.25, -0.5, 0.0, 1.0]` for configured dimension 4; one Chroma query and final validation then succeed. |
  | `RET-CONC-001::EMBEDDING-LIFECYCLE-FAILURE` | The same embedding barrier raises the injected bounded embedding failure after release. A known eligible keyword sentinel already exists so fallback would be visible. |
  | `RET-CONC-001::EMBEDDING-LIFECYCLE-CANCELLATION` | While embedding is blocked, the harness cancels and joins the actual request task through the supported deterministic cancellation hook; the fake records cancellation cleanup and never returns a vector. |
  | `RET-CONC-001::CHROMA-LIFECYCLE-REVOCATION` | Successful embedding completes first. The Chroma provider then enters and blocks; after the barrier assertions, a separately correlated actor commits membership deletion, and release returns a valid current candidate. |

- **Concurrent state change:** At each embedding or Chroma `entered` event,
  the request owns zero checked-out connections, zero active transactions, no
  open `SessionTransaction`, no connection idle in transaction, and no
  retained initial/keyword Session; the final transaction and snapshot have
  not begun. Only the Chroma-revocation row runs a concurrent actor. That
  actor's own checkout and commit are proved not to wait on a request-owned
  resource rather than inferred from spare pool capacity.
- **Expected public result:** Embedding success returns the exact deterministic
  Evidence success and private/no-store. Embedding failure returns generic
  planned `503 RETRIEVAL_UNAVAILABLE`, no keyword sentinel, no Evidence, and
  private/no-store. Controlled client/request cancellation publishes no HTTP
  response and leaves no server-side retrieval work. Chroma revocation returns
  generic hidden `404 NOT_FOUND`, no Evidence, and private/no-store.
- **Expected internal validation result:** Every row proves all initial
  transaction ends/checkins precede its external `entered` event. Embedding
  starts only after the listed request gates and initial SQL complete. Success
  permits exactly one embedding result and starts Chroma only after embedding
  release. Failure and cancellation each leave zero request-owned database
  resources, zero Chroma calls, and zero final-transaction/snapshot calls;
  failure performs no keyword-only fallback. In the Chroma row, provider
  completion precedes request checkout and final transaction begin. The
  actual first final authorization query or order-preserving same-transaction
  hook proves `transaction_isolation = repeatable read` and
  `transaction_read_only = on` in that request transaction; final
  authorization observes the committed deletion and returns/checks in every
  final resource.
- **Forbidden behavior:** Treating the Chroma barrier as proof of the earlier
  embedding lifecycle; starting embedding before authentication, target,
  bounded-body, schema, normalization, semantic validation, or permitted
  initial SQL completes; retaining any request-owned connection, transaction,
  Session, or SessionTransaction across either barrier or after failure/
  cancellation; opening final validation before external completion; Chroma
  after embedding failure/cancellation; keyword-only fallback after embedding
  failure; a replacement/duplicate/padded/truncated vector; publication after
  cancellation; reusing one transaction across phases; a read-write final
  transaction; inspecting a helper/actor/unrelated transaction for settings;
  inferring release from pool capacity, logs, sleeps, polling, or mocks; or
  claiming cancellation instantly stops arbitrary external work.
- **Planned test level:** PostgreSQL integration, HTTP integration. Every
  stable label executes independently at both levels; the cancellation row's
  HTTP level asserts disconnect/task cleanup rather than a fabricated status.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-002 — Session revoked before final snapshot

- **Category:** Final transaction and concurrency.
- **Initial database state:** Live session, membership, and eligible content exist at request start.
- **Authenticated principal and membership state:** The session passes initial authorization.
- **Provider or Chroma input:** Controlled provider blocks, then returns a valid candidate.
- **Concurrent state change:** Session revocation commits before final snapshot acquisition.
- **Expected public result:** Generic `401 AUTHENTICATION_REQUIRED`, no Evidence, and private/no-store.
- **Expected internal validation result:** First final authoritative statement observes revoked session state.
- **Forbidden behavior:** Returning Evidence from the initial principal or mapping authentication loss to `404` or empty success.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-003 — User becomes inactive before final snapshot

- **Category:** Final transaction and concurrency.
- **Initial database state:** Active user, live session, membership, and eligible content exist initially.
- **Authenticated principal and membership state:** Initial authorization succeeds.
- **Provider or Chroma input:** Controlled provider returns a valid candidate after release.
- **Concurrent state change:** User deactivation commits during provider work and before final snapshot acquisition.
- **Expected public result:** Generic `401 AUTHENTICATION_REQUIRED`, no Evidence, and private/no-store.
- **Expected internal validation result:** Fixed-snapshot authorization observes inactive-user state.
- **Forbidden behavior:** Membership-only authorization, partial Evidence, or asynchronous provider cancellation claims.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-004 — Document state changes before final snapshot

- **Category:** Final transaction and concurrency.
- **Initial database state:** Candidate document is completed with one eligible hashed chunk.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** Provider returns the current canonical candidate.
- **Concurrent state change:** Two independently executable variants commit the document state as (A) `processing` and (B) `failed` before snapshot acquisition.
- **Expected public result:** Authorized empty Evidence when no other candidate survives.
- **Expected internal validation result:** The final snapshot sees current ineligibility and omits the candidate without reason disclosure.
- **Forbidden behavior:** Returning old content, trusting provider status, or changing authorized empty to `503`.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-005 — Chunk replacement before final snapshot

- **Category:** Final transaction and concurrency.
- **Initial database state:** Completed document initially has old eligible chunk O.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** Provider returns O.
- **Concurrent state change:** Transactionally replace O with N and commit before final snapshot acquisition.
- **Expected public result:** O is omitted; authorized empty Evidence results if N is not a candidate.
- **Expected internal validation result:** Final snapshot cannot resolve O as a current eligible authoritative chunk.
- **Forbidden behavior:** Old provider text, chunk-index rebinding, dynamic hash fallback, or stale citation creation.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-006 — Membership removal after snapshot acquisition

- **Category:** Final transaction and concurrency.
- **Initial database state:** Current member and eligible content exist when the final transaction begins.
- **Authenticated principal and membership state:** First final statement succeeds and fixes an authorized snapshot.
- **Provider or Chroma input:** One valid candidate; test barrier pauses after snapshot acquisition.
- **Concurrent state change:** Membership deletion commits in another transaction before the final transaction commits.
- **Expected public result:** Current request returns the already-snapshot-authorized Evidence; the next request returns hidden `404`.
- **Expected internal validation result:** Every batch and Evidence field uses the original fixed snapshot.
- **Forbidden behavior:** Mixed snapshots, mid-transaction reauthorization against newer state, or claims of retroactive cancellation.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-007 — Document state change after snapshot acquisition

- **Category:** Final transaction and concurrency.
- **Initial database state:** Completed document and eligible hashed chunk are visible when the final snapshot is fixed.
- **Authenticated principal and membership state:** Live target member remains authorized in that snapshot.
- **Provider or Chroma input:** Valid current candidate; barrier pauses before its batch.
- **Concurrent state change:** Document becomes ineligible and commits elsewhere before final transaction commit.
- **Expected public result:** Current response uses the snapshot-eligible immutable Evidence; a later request omits it.
- **Expected internal validation result:** Validation and load observe one fixed snapshot, not the newer document state.
- **Forbidden behavior:** Mixed-state response, post-commit reload, or describing the later commit as instant cancellation.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-008 — Chunk replacement after snapshot acquisition

- **Category:** Final transaction and concurrency.
- **Initial database state:** Old eligible chunk O is the single candidate within the public result cutoff when the final snapshot is fixed; its persisted content is `OLD_CONTENT_SENTINEL` and its persisted valid hash is `OLD_HASH`. Replacement N has a distinct identity, content, and hash.
- **Authenticated principal and membership state:** Live target member is authorized in that snapshot.
- **Provider or Chroma input:** O is a valid candidate; barrier pauses before batch validation.
- **Concurrent state change:** Replace O with N and commit elsewhere before final transaction commit.
- **Expected public result:** The current response deterministically contains O, `OLD_CONTENT_SENTINEL`, and `OLD_HASH`. A separately executed later request whose source fixture selects N contains N and its new persisted content/hash and does not contain O.
- **Expected internal validation result:** O is eligible and in-cutoff in the fixed snapshot, so all authoritative O fields load from that snapshot and remain immutable after commit; only the later request acquires a snapshot containing N.
- **Forbidden behavior:** Omitting the in-cutoff O from the current response, returning N in the current response, combining O identity with N content/hash, returning O in the later request, post-commit reload, or Provider-text substitution.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-009 — Revocation after final commit

- **Category:** Final transaction and concurrency.
- **Initial database state:** Final transaction has loaded eligible Evidence for a current member.
- **Authenticated principal and membership state:** Authorization is valid through final commit.
- **Provider or Chroma input:** One valid candidate.
- **Concurrent state change:** Membership revocation commits after final transaction commit but before response serialization ends.
- **Expected public result:** Current response serializes already-loaded immutable Evidence; subsequent requests return hidden `404`.
- **Expected internal validation result:** Serialization performs no authorization-sensitive database read.
- **Forbidden behavior:** A second content/provenance fetch, mixed response, or asynchronous serialization cancellation claim.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-010 — Multiple batches share one fixed snapshot

- **Category:** Final transaction and concurrency.
- **Initial database state:** More than one validation batch of eligible target chunks exists.
- **Authenticated principal and membership state:** Live target member passes the first final statement.
- **Provider or Chroma input:** Bounded candidates span at least three deterministic batches.
- **Concurrent state change:** Between batches, another transaction changes membership and replaces a later-batch chunk.
- **Expected public result:** Current response is wholly consistent with the initially fixed snapshot; later request sees both changes.
- **Expected internal validation result:** Every batch has the same PostgreSQL snapshot identity and exact bounded query count.
- **Forbidden behavior:** Statement-level snapshot drift, partial newer state, or one transaction per batch.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-011 — Batch failure discards earlier records

- **Category:** Final transaction and concurrency.
- **Initial database state:** Several batches contain eligible target chunks with distinct earlier-batch and later-batch content sentinels.
- **Authenticated principal and membership state:** Live target member passes fixed-snapshot authorization.
- **Provider or Chroma input:** The same bounded source-isolated candidate fixture spans multiple batches in four independently executable variants: (A) the second validation-batch statement raises a deterministic database error after batch one succeeds; (B) every read succeeds but final transaction commit raises a deterministic commit error; (C) final-transaction connection acquisition raises a deterministic database connection error; (D) a supported database statement-timeout mechanism expires during the second validation batch. If the selected driver/database boundary cannot distinguish timeout from connection failure, Variant D is explicitly not applicable there but remains required at the first level that exposes a deterministic statement timeout.
- **Concurrent state change:** None; each variant has exactly its named injected fault and no alternate branch.
- **Expected public result:** Every applicable variant returns generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, neither content sentinel, and private/no-store.
- **Expected internal validation result:** Variant A discards the successful first-batch records; Variant B publishes nothing before commit success and discards all loaded records; Variant C never begins validation; Variant D rolls back and discards all prior records. Each path has an independently asserted normalized failure classification.
- **Forbidden behavior:** Treating one variant as coverage for another, partial Evidence, dense-only or keyword-only fallback, commit/publication of an earlier batch, either candidate content sentinel in the error, or an ambiguous “database error” assertion that does not prove the injected branch.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-012 — Access loss with zero provider candidates

- **Category:** Final transaction and concurrency.
- **Initial database state:** Caller initially has target membership; both retrieval paths will yield no candidates.
- **Authenticated principal and membership state:** Live member passes initial authorization.
- **Provider or Chroma input:** Controlled provider returns a structurally valid empty collection.
- **Concurrent state change:** Membership deletion commits before the final snapshot.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, not authorized empty Evidence, and private/no-store.
- **Expected internal validation result:** Final authorization runs before the zero-batch branch and observes access loss.
- **Forbidden behavior:** Skipping final authorization because `U = 0`, `200 []`, or revealing the prior membership.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Provider transport, decoding, and taxonomy

### RET-PROV-001 — Bounded valid response at exact field and metadata ceilings

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible hashed chunk.
- **Authenticated principal and membership state:** Live target member with read capabilities.
- **Provider or Chroma input:** Every row starts with the canonical eight-key
  single-candidate response and changes only its named permitted branch. It
  remains within wire, decoded, candidate-count, and depth limits; every
  non-target bound is below its ceiling unless the row exercises equality.

  | Stable variant label | Exact permitted fixture |
  | --- | --- |
  | `RET-PROV-001::DOCUMENT-STRING-EXACT-4096` | `documents = [[S]]`, where `S` is exactly 4,096 ASCII `a` bytes. |
  | `RET-PROV-001::METADATA-ENTRIES-EXACT-32` | `metadatas = [[M]]`, where `M` has exactly 32 distinct short keys with short string values. |
  | `RET-PROV-001::METADATA-KEY-EXACT-128` | `M` has one key of exactly 128 ASCII bytes and a short string value. |
  | `RET-PROV-001::METADATA-STRING-EXACT-1024` | `M = {"s": S}`, where `S` is exactly 1,024 ASCII bytes. |
  | `RET-PROV-001::DOCUMENT-NULL-ELEMENT` | `documents = [[null]]`; `metadatas` remains top-level JSON null. |
  | `RET-PROV-001::METADATA-NULL-ELEMENT` | `metadatas = [[null]]`; this is a null aligned container element, not a null value inside an object. |
  | `RET-PROV-001::DOCUMENTS-NULL-CONTAINER` | The required top-level `documents` value is JSON null while `metadatas = [[{}]]`. |
  | `RET-PROV-001::METADATAS-NULL-CONTAINER` | The required top-level `metadatas` value is JSON null while `documents = [["bounded"]]`. |
  | `RET-PROV-001::METADATA-EMPTY-OBJECT` | `metadatas = [[{}]]`, the zero-entry shallow-object branch. |
  | `RET-PROV-001::METADATA-STRING-VALUE` | `metadatas = [[{"s":"value"}]]`. |
  | `RET-PROV-001::METADATA-FINITE-NEGATIVE-NUMBER` | `metadatas = [[{"n":-1.25}]]`. |
  | `RET-PROV-001::METADATA-FINITE-ZERO-NUMBER` | `metadatas = [[{"n":0}]]`. |
  | `RET-PROV-001::METADATA-FINITE-POSITIVE-NUMBER` | `metadatas = [[{"n":100.0}]]`. |
  | `RET-PROV-001::METADATA-BOOLEAN-TRUE` | `metadatas = [[{"b":true}]]`; the value is not classified as a number. |
  | `RET-PROV-001::METADATA-BOOLEAN-FALSE` | `metadatas = [[{"b":false}]]`; the value is not classified as a number. |
  | `RET-PROV-001::CONTENT-TYPE-NO-PARAMETER` | `Content-Type: application/json` with no parameter. |
  | `RET-PROV-001::CONTENT-TYPE-EXPLICIT-UTF8` | `Content-Type: application/json; ChArSeT=UTF-8` as the sole parameter. |
  | `RET-PROV-001::CONTENT-ENCODING-ABSENT` | The header is absent and the canonical body is uncompressed. |
  | `RET-PROV-001::CONTENT-ENCODING-IDENTITY` | `Content-Encoding: identity` is the sole token. |
  | `RET-PROV-001::CONTENT-ENCODING-GZIP` | `Content-Encoding: gzip` is the sole token and bounded streaming decode produces the canonical body. |
- **Concurrent state change:** None.
- **Expected public result:** Every variant returns the expected authoritative Evidence item and private/no-store.
- **Expected internal validation result:** Every named grammar branch is
  accepted independently. Every comparison uses `value <= ceiling`; equality
  is accepted without truncation or omission, bounded parsing succeeds, all
  unsolicited values are discarded as authority, and ordinary PostgreSQL
  candidate validation and Evidence loading continue.
- **Forbidden behavior:** Treating one positive branch as coverage for
  another; rejecting with `>= ceiling`; imposing a ceiling one unit lower;
  truncating an at-limit field; confusing a metadata null element with a
  forbidden object value; treating a boolean as numeric; requiring a charset
  or content-encoding header; rejecting permitted `identity`/`gzip`; omitting
  the valid candidate; unbounded decode; or Provider text/metadata authority.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-002 — Exact inclusive wire ceiling is accepted

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible candidate.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Two independently executable transports carry the same canonical response with one eligible aligned ID/distance and legal JSON whitespace padding to exactly 1,048,576 raw/wire bytes while remaining within every other limit: (A) a truthful `Content-Length: 1048576`; (B) no `Content-Length`, with bounded streaming ending exactly at 1,048,576.
- **Concurrent state change:** None.
- **Expected public result:** Both variants return normal authorized Evidence and private/no-store rather than a size failure.
- **Expected internal validation result:** Variant A validates the truthful equality and still streams/counts actual bytes; Variant B proves absent-length streaming equality. Both accept `wire_bytes <= 1,048,576`, then boundedly parse the canonical envelope and continue ordinary candidate processing.
- **Forbidden behavior:** Treating one transport as coverage for the other, rejecting on equality, enforcing an effective 1,048,575-byte maximum, trusting the header without actual-byte accounting, unbounded buffering, or bypassing decoded, field, count, or depth bounds.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-003 — Declared Content-Length above wire ceiling

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have valid keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** A truthful `Content-Length: 1048577` declares the canonical response's actual 1,048,577-byte wire size.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** The truthful header plus-one branch rejects before reading any response body byte.
- **Forbidden behavior:** Body read, truncation, partial dense result, or keyword-only fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-004 — Missing Content-Length streams above wire ceiling

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have valid keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** No `Content-Length`; a canonical response stream supplies exactly 1,048,577 raw/wire bytes.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** The absent-header streaming plus-one branch aborts immediately upon byte 1,048,577.
- **Forbidden behavior:** Full-body materialization, truncation, partial result, or fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-005 — Dishonest smaller Content-Length

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Header declares a small legal body but transport supplies exactly 1,048,577 raw/wire bytes.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Actual cumulative bytes, not the header alone, trigger response-fatal rejection.
- **Forbidden behavior:** Trusting the false length, unbounded read, truncation, or fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-006 — Compressed body exceeds decoded ceiling

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have legal keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** A single-token `Content-Encoding: gzip` response stays within 1,048,576 wire bytes but expands to 2,097,153 decoded bytes.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Independent bounded decoded-byte accounting aborts immediately when decoded bytes reach 2,097,153, before JSON materialization.
- **Forbidden behavior:** Decompression bomb materialization, partial result, or keyword-only fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-007 — Compressed body exactly at decoded ceiling

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible hashed chunk referenced by the valid candidate.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** A single-token `Content-Encoding: gzip` response uses at most 1,048,576 cumulative raw/wire bytes and decodes to exactly 2,097,152 bytes of valid JSON. Candidate count, every candidate ID and individual field, metadata count, keys and values, and nesting depth at most 16 remain within their hard limits. The exact decoded size uses legal compressible JSON whitespace or another schema-valid bounded construction, never an unbounded string field.
- **Concurrent state change:** None.
- **Expected public result:** Normal authorized Evidence for the valid candidate and private/no-store, not a size failure.
- **Expected internal validation result:** The wire-size check passes; streaming decompression remains bounded; the `decoded_bytes <= 2,097,152` check accepts the exact inclusive ceiling; bounded JSON parsing proceeds; and ordinary PostgreSQL candidate validation continues.
- **Forbidden behavior:** Rejecting merely because decoded size equals the ceiling, accepting any above-limit body, using an unbounded string solely as padding, unbounded decompression or parsing, partial Evidence, or keyword-only fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-008 — Candidate ID exactly at field ceiling

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target exists but no ID in this fixture is canonical.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** One candidate ID is a bounded string of exactly 128 UTF-8 bytes and is non-canonical.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence and private/no-store.
- **Expected internal validation result:** Field limit passes; canonical parsing then omits the record locally.
- **Forbidden behavior:** Treating the at-limit value as response-fatal or using metadata as a replacement ID.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-009 — Candidate ID above field ceiling

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have other valid content.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** One candidate ID is 129 UTF-8 bytes.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Per-field hard-limit violation rejects the whole response before candidate processing.
- **Forbidden behavior:** Candidate-local omission, truncation, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-010 — Oversized ignored provider text

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has a valid canonical chunk.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** The canonical eight-key response has one valid aligned ID/distance, while unsolicited aligned `documents[0][0]` is 4,097 UTF-8 bytes; every other field and limit is valid.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Ignored authority does not mean unbounded; string ceiling rejects the whole response.
- **Forbidden behavior:** Ignoring the size violation, returning PostgreSQL Evidence anyway, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-011 — Too many metadata entries

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has a valid candidate.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** The canonical eight-key response has one valid aligned ID/distance, while unsolicited aligned `metadatas[0][0]` contains 33 distinct entries; every other field and limit is valid.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Metadata-entry ceiling is a whole-response hard-limit failure.
- **Forbidden behavior:** Dropping entry 33, candidate-local omission, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-012 — Oversized metadata key

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has a valid candidate.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** The canonical eight-key response has one valid aligned ID/distance, while unsolicited aligned `metadatas[0][0]` has exactly one 129-byte UTF-8 key; every other field and limit is valid.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Metadata-key ceiling rejects the whole response.
- **Forbidden behavior:** Key truncation, partial acceptance, candidate-local omission, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-013 — Oversized metadata scalar or string value

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has a valid candidate.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** The canonical eight-key response has one valid aligned ID/distance, while unsolicited aligned `metadatas[0][0]` contains exactly one scalar/string representation of 1,025 UTF-8 bytes; every other field and limit is valid.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Metadata-value ceiling rejects the whole response.
- **Forbidden behavior:** Truncation, candidate-local omission, partial Evidence, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-014 — Exact JSON depth boundary

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Two independently executable canonical parser fixtures remain within wire and decoded limits:
  1. **Variant A — exact depth ceiling:** Canonical D16 reaches depth 16. The depth guard accepts it and passes control to subsequent structural validation. Because canonical D16 is not itself a valid Provider envelope, its later wrong-shape classification remains separate and is never labeled `DEPTH_LIMIT_EXCEEDED`.
  2. **Variant B — depth ceiling plus one:** Canonical D17 would reach depth 17. The parser rejects it before full materialization, envelope validation, or candidate processing.
- **Concurrent state change:** None.
- **Expected public result:** Both variants produce generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, no partial dense list, no fallback, and private/no-store; the public envelope does not disclose which guard failed.
- **Expected internal validation result:** Unit and Provider-adapter fixtures distinguish D16 passing the depth guard from D17 failing it; PostgreSQL and HTTP fixtures exercise the response-fatal D17 service path and confirm `503`, no Evidence, and no keyword-only fallback.
- **Forbidden behavior:** Counting the root container as depth 0, counting a scalar as an added depth, failing to count an empty container, accepting D17, rejecting D16 as a depth violation, letting D17 reach envelope or candidate processing, recursive unbounded decode, partial result, fallback, or parser-dependent classification.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-015 — Strict JSON and unsupported-range distances are response-fatal

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have valid keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Four independently executable byte-bounded raw fixtures begin with the complete canonical single-candidate eight-key response. The sole mutation replaces `distances[0][0]` value `0.125` with respectively `NaN`, `Infinity`, `-Infinity`, and `1e400`; the aligned ID, all keys, cardinalities, null fields, and exact `include` remain canonical. The first three contain non-RFC 8259 literal tokens; the fourth is valid JSON syntax but its numeric token is outside finite IEEE-754 binary64.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** The bounded strict decoder rejects the first three fixtures as invalid JSON; numeric-domain conversion rejects `1e400`, including when a lower-level decoder maps it to infinity. Because every other envelope element is canonical, each fixture can fail only at its intended numeric branch. Every fixture is response-fatal before candidate iteration and normalized without payload details.
- **Forbidden behavior:** Using a noncanonical fragment such as `{"score":1e400}`; passing because the top-level envelope is wrong; permissive decoding that accepts the first three literal constants; treating decoder-produced infinity from `1e400` as a candidate value; converting any fixture to candidate-local behavior; reaching candidate iteration; heuristic recovery; partial result; exception disclosure; or keyword-only fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-016 — Wire encoding and canonical top-level schema

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Each independently executable fixture changes
  only its named property in the canonical single-candidate response. Stable
  labels and exact mutations are:

  | Stable variant label | Sole mutation |
  | --- | --- |
  | `RET-PROV-016::INVALID-UTF8` | One invalid UTF-8 sequence in the body. |
  | `RET-PROV-016::UTF8-BOM` | A leading UTF-8 BOM. |
  | `RET-PROV-016::CONTENT-TYPE-MISSING` | No `Content-Type` header. |
  | `RET-PROV-016::CONTENT-TYPE-NONJSON` | `Content-Type: text/plain`. |
  | `RET-PROV-016::CONTENT-TYPE-EXTRA-PARAMETER` | `application/json; charset=utf-8; profile=x`. |
  | `RET-PROV-016::CONTENT-TYPE-FORBIDDEN-CHARSET` | `application/json; charset=utf-16`. |
  | `RET-PROV-016::CONTENT-ENCODING-UNSUPPORTED` | Sole token `br`. |
  | `RET-PROV-016::CONTENT-ENCODING-STACKED` | Tokens `gzip, identity`. |
  | `RET-PROV-016::SCALAR-TOP-LEVEL` | Top-level JSON string. |
  | `RET-PROV-016::ARRAY-TOP-LEVEL` | Top-level JSON array. |
  | `RET-PROV-016::UNKNOWN-TOP-LEVEL-KEY` | One ninth top-level key. |
  | `RET-PROV-016::DUPLICATE-TOP-LEVEL-KEY` | A second `ids` key. |
  | `RET-PROV-016::NONNULL-EMBEDDINGS` | `embeddings = []`. |
  | `RET-PROV-016::NONNULL-URIS` | `uris = []`. |
  | `RET-PROV-016::NONNULL-DATA` | `data = []`. |
  | `RET-PROV-016::NONCANONICAL-INCLUDE` | `include = []`. |
  | `RET-PROV-016::NULL-IDS` | `ids = null`. |
  | `RET-PROV-016::NULL-DISTANCES` | `distances = null`. |
  | `RET-PROV-016::NULL-INCLUDE` | `include = null`. |
  | `RET-PROV-016::DOCUMENTS-OUTER-CARDINALITY` | `documents` has two outer arrays. |
  | `RET-PROV-016::METADATAS-OUTER-CARDINALITY` | `metadatas` has two outer arrays. |
  | `RET-PROV-016::DOCUMENTS-INNER-LENGTH` | Aligned `ids[0]` length is one but `documents[0]` is empty. |
  | `RET-PROV-016::METADATAS-INNER-LENGTH` | Aligned `ids[0]` length is one but `metadatas[0]` is empty. |
  | `RET-PROV-016::DOCUMENT-BOOLEAN-ELEMENT` | `documents = [[true]]`. |
  | `RET-PROV-016::DOCUMENT-NUMBER-ELEMENT` | `documents = [[1]]`. |
  | `RET-PROV-016::DOCUMENT-OBJECT-ELEMENT` | `documents = [[{}]]`. |
  | `RET-PROV-016::DOCUMENT-ARRAY-ELEMENT` | `documents = [[[]]]`. |
  | `RET-PROV-016::METADATA-STRING-ELEMENT` | `metadatas = [["x"]]`. |
  | `RET-PROV-016::METADATA-NUMBER-ELEMENT` | `metadatas = [[1]]`. |
  | `RET-PROV-016::METADATA-BOOLEAN-ELEMENT` | `metadatas = [[true]]`. |
  | `RET-PROV-016::METADATA-ARRAY-ELEMENT` | `metadatas = [[[]]]`. |
  | `RET-PROV-016::METADATA-NESTED-OBJECT` | `metadatas = [[{"k":{}}]]`. |
  | `RET-PROV-016::METADATA-NESTED-ARRAY` | `metadatas = [[{"k":[]}]]`. |
  | `RET-PROV-016::METADATA-NULL-VALUE` | `metadatas = [[{"k":null}]]`; the element itself is an object, so this is distinct from the permitted null element. |
  | `RET-PROV-016::METADATA-NONFINITE-LITERAL` | The otherwise canonical metadata number token is literal `NaN`, invalid under RFC 8259. |
  | `RET-PROV-016::METADATA-UNSUPPORTED-RANGE-NUMBER` | The otherwise canonical metadata value is syntactically valid `1e400`, outside the supported finite binary64 domain. |
- **Concurrent state change:** None.
- **Expected public result:** Every fixture produces generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Each fixture reaches and proves its
  named UTF-8, media, content-encoding, strict-JSON, finite-number, top-level,
  null/cardinality, or shallow-element guard and is whole-response fatal; no
  other mutation is present.
- **Forbidden behavior:** Treating one label as coverage for another;
  BOM/charset/encoding guessing; unknown-field tolerance; last-key-wins;
  null/shape coercion; accepting a forbidden element or nested/value branch;
  confusing permitted metadata null elements with forbidden null object
  values; mapping non-finite values to candidate-local behavior; partial
  extraction; or keyword-only fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-017 — Missing required candidate collection

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Eight independently executable fixtures each begin with the canonical single-candidate response and omit exactly one required top-level key: `ids`, `embeddings`, `documents`, `uris`, `data`, `metadatas`, `distances`, or `include`. The `ids`-omitted fixture is distinct from the canonical present-empty response.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Exact required-key validation makes each omission whole-response fatal and identifies the intended missing-key branch internally without exposing it publicly.
- **Forbidden behavior:** Treating omission as zero hits, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-018 — Mismatched parallel-array lengths

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Independently executable canonical-key fixtures use (A) `ids[0]` length two with `distances[0]` length one; (B) `ids` outer cardinality zero; (C) `distances` outer cardinality two. Optional non-null aligned documents/metadata are absent so only the named position/cardinality defect remains.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Position ambiguity is response-fatal.
- **Forbidden behavior:** Zip-to-shortest behavior, guessed positions, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-019 — Candidate count above configured maximum

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has at least 129 eligible chunks in known UUID and absolute-rank order.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Four independently executable canonical
  responses keep every other bound and field valid:

  | Stable variant label | Exact count fixture |
  | --- | --- |
  | `RET-PROV-019::R10-C40-P40-ACCEPT` | Public `R = 10`, captured `n_results = C = min(128, 10 * 4) = 40`, exactly `P = 40` aligned eligible raw positions. |
  | `RET-PROV-019::R10-C40-P41-FATAL` | Public `R = 10`, captured `C = 40`, exactly `P = 41` aligned positions. |
  | `RET-PROV-019::R50-C128-P128-ACCEPT` | Public `R = 50`, captured `C = min(128, 50 * 4) = 128`, exactly `P = 128` aligned eligible positions. |
  | `RET-PROV-019::R50-C128-P129-FATAL` | Public `R = 50`, captured `C = 128`, exactly `P = 129` aligned positions. |
- **Concurrent state change:** None.
- **Expected public result:** `P = C` returns exactly the first `R` Evidence
  items from the known dense order: 10 for the C40 row and 50 for C128. Each
  `P = C + 1` row returns generic planned
  `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Equality assigns absolute positions
  1–40 or 1–128. Each plus-one row rejects the whole response before
  candidate-local processing. The C40 plus-one rejection occurs even though
  `P = 41` is below the global 128 ceiling.
- **Forbidden behavior:** Checking only `P <= 128`; treating C40 and C128 as
  one execution; treating equality and plus one as one branch; rejecting an
  equality row; accepting, clamping, or truncating a plus-one row; partial
  dense acceptance; or keyword-only fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-020 — Bounded exact Provider compatibility version

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible keyword sentinel and one distinct eligible indexed dense sentinel.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Before the first query, each independently
  executable row applies the Provider response profile directly to
  `GET /api/v2/version`. The exact JSON seed `V = "1.5.9"` is 7 UTF-8 bytes;
  JSON-whitespace padding leaves its parsed value unchanged.

  | Stable variant label | Exact version-response fixture |
  | --- | --- |
  | `RET-PROV-020::EXACT-VERSION-CONTROL` | HTTP `200`, `Content-Type: application/json`, absent `Content-Encoding`, body exactly `V`; `/query` then returns the canonical dense sentinel. |
  | `RET-PROV-020::WIRE-EXACT-1048576` | `V` plus exactly 1,048,569 U+0020 bytes, truthful `Content-Length: 1048576`; decoded value is exact. |
  | `RET-PROV-020::WIRE-STREAMED-EXACT` | The same exact 1,048,576-byte body has no length and arrives in two 524,288-byte chunks. |
  | `RET-PROV-020::WIRE-PLUS-ONE-1048577` | `V` plus 1,048,570 U+0020 bytes, truthful length 1,048,577. |
  | `RET-PROV-020::WIRE-STREAMED-PLUS-ONE` | The same 1,048,577-byte body has no length and arrives in chunks 524,288, 524,288, and 1. |
  | `RET-PROV-020::IDENTITY-ENCODING` | Nominal exact `V` with sole `Content-Encoding: identity`. |
  | `RET-PROV-020::CONTENT-TYPE-EXPLICIT-UTF8` | Nominal exact `V` with `Content-Type: application/json; ChArSeT=UTF-8` as the sole parameter. |
  | `RET-PROV-020::GZIP-DECODED-EXACT-2097152` | Sole `gzip`; bounded compressed bytes inflate to `V` plus exactly 2,097,145 U+0020 bytes. |
  | `RET-PROV-020::GZIP-DECODED-PLUS-ONE` | Sole `gzip`; bounded compressed bytes would inflate to `V` plus 2,097,146 U+0020 bytes, and the decoded counter observes byte 2,097,153. |
  | `RET-PROV-020::FORBIDDEN-ENCODING` | Sole `Content-Encoding: br`. |
  | `RET-PROV-020::STACKED-ENCODING` | `Content-Encoding: gzip, identity`. |
  | `RET-PROV-020::CONTENT-TYPE-MISSING` | No `Content-Type` header with otherwise exact `V`. |
  | `RET-PROV-020::CONTENT-TYPE-NONJSON` | `Content-Type: text/plain` with otherwise exact `V`. |
  | `RET-PROV-020::CONTENT-TYPE-EXTRA-PARAMETER` | `application/json; charset=utf-8; profile=x` with otherwise exact `V`. |
  | `RET-PROV-020::FORBIDDEN-CHARSET` | `Content-Type: application/json; charset=utf-16` with otherwise exact `V`. |
  | `RET-PROV-020::VERSION-MISMATCH` | Bounded exact JSON string `"1.5.8"`. |
  | `RET-PROV-020::MALFORMED-JSON` | Bounded bytes `{"version":` do not form JSON. |
  | `RET-PROV-020::JSON-NULL` | Bounded JSON null. |
  | `RET-PROV-020::JSON-OBJECT` | Bounded empty JSON object. |
  | `RET-PROV-020::JSON-ARRAY` | Bounded empty JSON array. |
  | `RET-PROV-020::JSON-NUMBER` | Bounded JSON number `1.5`. |
  | `RET-PROV-020::JSON-BOOLEAN` | Bounded JSON `true`. |

  No query-response envelope invents a version field. Every failure row keeps
  the known eligible keyword sentinel live so fallback is observable.
- **Concurrent state change:** None.
- **Expected public result:** The exact-version control, both wire-equality,
  identity, explicit-UTF-8, and decoded equality rows each reach `/query` and return exactly
  the keyword and dense sentinels. Every other row returns the byte-stable
  generic planned `503 RETRIEVAL_UNAVAILABLE`, neither sentinel, no Evidence,
  and private/no-store.
- **Expected internal validation result:** The adapter records compatibility
  identifier `chroma-http-v2-1.5.9`. Equality rows use inclusive counters and
  exact parsed-string comparison. A truthful raw plus-one rejects before a
  body read; streamed raw plus-one stops on its final byte; decoded plus-one
  stops the decompressor on byte 2,097,153. Each plus-one has zero full-body
  materializations, JSON-parser/equality calls, and `/query` calls.
  Encoding failures stop before body decode; mismatch/type failures stop after
  bounded parsing and before `/query`.
- **Forbidden behavior:** An unbounded special-case version read; fully
  buffering an oversized raw or expanded response; reading after the first
  over-limit byte; treating one limit/encoding row as another; allowing an
  unsupported/stacked encoding; skipping exact equality; inventing or trusting
  a query-envelope version key; image-tag-only compatibility; best-effort
  parsing; downgrade guessing; query after failure; partial result; or
  keyword-only fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-021 — Candidate positions cannot be reconstructed

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Two independently executable bounded fixtures use (A) two aligned `ids`/`distances` outer result groups even though exactly one query embedding was sent and (B) an object keyed by candidate ID in place of each ordered inner array, which loses the Provider list order required for absolute ranks. Every other top-level key is present and bounded.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Variant A rejects outer cardinality two; Variant B rejects unordered keyed candidates. Both fail before assigning any source rank.
- **Forbidden behavior:** Treating one shape as coverage for the other, choosing one outer group, object iteration as rank, arbitrary ordering, guessed rank, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-022 — Independent Provider connection and timeout failures

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has a known eligible nonempty keyword sentinel that would be returned if fallback occurred.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Two independently executable bounded mock transports use (A) a deterministic connection-establishment error before response headers and (B) a deterministic configured read timeout after request dispatch. Each spy proves its exact branch.
- **Concurrent state change:** None.
- **Expected public result:** Both variants return generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence or keyword sentinel, and private/no-store.
- **Expected internal validation result:** The adapter independently normalizes connection and timeout classifications without raw exception/payload leakage and discards the keyword sentinel.
- **Forbidden behavior:** Treating either branch as coverage for the other, retry without a bound, stale cache, partial result, Provider details, or keyword-only fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-023 — Finite diagnostic distance

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible hashed chunk.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** The canonical response has one aligned ID and finite JSON distance at absolute Provider rank 1.
- **Concurrent state change:** None.
- **Expected public result:** One authorized Evidence item.
- **Expected internal validation result:** Candidate is retained; fusion uses absolute rank 1 and does not arithmetically use the raw distance.
- **Forbidden behavior:** Treating distance as authority or adding it to keyword/RRF score.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-024 — Typed adapter diagnostic score is `None`

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible hashed chunk.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** A deterministic provider-neutral typed adapter enters only at the post-wire step-6 boundary and returns a valid canonical ID at absolute rank 1 with `provider_score = None`. Raw Chroma variants may not obtain this fixture by omitting `distances` or shortening its inner array.
- **Concurrent state change:** None.
- **Expected public result:** One authorized Evidence item.
- **Expected internal validation result:** Typed `None` does not invalidate the candidate; the preserved absolute list rank drives fusion.
- **Forbidden behavior:** Calling a missing/short canonical Chroma distance array optional, bypassing raw envelope validation, response-fatal classification of the typed fixture, local omission, or an invented numeric score.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-025 — Post-decoder typed NaN score is candidate-local

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has eligible companion chunks A and B; the invalid candidate X may also name an eligible chunk but must not survive.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** After successful bounded strict-JSON decoding, a deterministic typed adapter returns the exact ordered list `[A finite at absolute rank 1, X float("nan") at rank 2, B finite at rank 3]`. No non-finite value is serialized into JSON, and the dense-only fixture proves no keyword evidence exists.
- **Concurrent state change:** None.
- **Expected public result:** Evidence contains exactly A and B with dense ranks 1 and 3 and display scores `"0.016393442623"` and `"0.015873015873"` derived from exact `1/61` and `1/63`; X is absent.
- **Expected internal validation result:** Only X is omitted at the post-decoder typed boundary. B retains absolute rank 3 rather than compacted rank 2, and its exact RRF contribution remains `1/63`.
- **Forbidden behavior:** Claiming NaN was transported in conforming JSON, serializing `NaN`, whole-response `503`, non-finite fusion, accepting X, omitting A or B, compacting B to rank 2 or contribution `1/62`, relative-order-only assertions, keyword-assisted success, or treating a Provider score as authority.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-026 — Post-decoder typed infinite score is candidate-local

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has eligible companion chunks A and B; invalid X may name an eligible chunk but must not survive.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** Two independently executable post-decoder typed variants use the exact ordered list `[A finite at absolute rank 1, X invalid at rank 2, B finite at rank 3]`, with X equal to (A) `float("inf")` and (B) `float("-inf")`. Neither value is serialized into JSON, and the dense-only fixture proves no keyword evidence exists.
- **Concurrent state change:** None.
- **Expected public result:** Each variant returns exactly A and B with dense ranks 1 and 3 and display scores `"0.016393442623"` and `"0.015873015873"` derived from exact `1/61` and `1/63`; X is absent.
- **Expected internal validation result:** Each typed infinity candidate is locally omitted; B retains absolute rank 3 and exact contribution `1/63`.
- **Forbidden behavior:** Treating one sign as coverage for the other, claiming infinity was transported in conforming JSON, serializing either literal, whole-response `503`, infinite RRF, accepting X, omitting A/B, compacting B to rank 2 or `1/62`, relative-order-only assertions, keyword-assisted success, or Provider-score authority.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-027 — Wrong-type score is candidate-local

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has eligible companion chunks A and B; invalid X may name an eligible chunk but must not survive.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** Five independently executable canonical-key responses keep `ids[0] = [A, X, B]` byte-identical and place finite distances for A/B at absolute ranks 1/3. Only `distances[0][1]` varies, using exactly (A) string, (B) object, (C) boolean, (D) null, and (E) array. The dense-only convention proves no keyword evidence exists.
- **Concurrent state change:** None.
- **Expected public result:** Every variant returns exactly A and B with exposed dense ranks 1 and 3 and display scores `"0.016393442623"` and `"0.015873015873"` derived from exact `1/61` and `1/63`; X is absent.
- **Expected internal validation result:** Only X is locally omitted while parallel positions remain reconstructable; B retains absolute rank 3 and exact contribution `1/63`.
- **Forbidden behavior:** Treating any wrong type as covered by another, type coercion, response-fatal `503`, accepting X, compacting B to rank 2 or `1/62`, relative-order-only assertions, keyword-assisted success, or raw score use.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-028 — Mixed valid and candidate-local-invalid records

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Target has eligible hashed chunks A, C, E, and G; invalid-position records cannot contribute Evidence.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** After successful bounded strict-JSON decoding, the exact ordered typed list is `[A valid rank 1, malformed-ID rank 2, C valid rank 3, wrong-type-score rank 4, E valid rank 5, typed-NaN rank 6, G valid rank 7]`; no non-finite value is serialized into JSON. The dense-only convention proves no keyword evidence exists.
- **Concurrent state change:** None.
- **Expected public result:** Evidence contains exactly A, C, E, and G with dense ranks 1, 3, 5, and 7; exact contributions `1/61`, `1/63`, `1/65`, and `1/67`; and display scores `"0.016393442623"`, `"0.015873015873"`, `"0.015384615385"`, and `"0.014925373134"`.
- **Expected internal validation result:** Local omissions preserve the complete absolute rank map; this typed post-decoder path is distinct from a fatal wire/decode fixture, which never reaches candidate iteration.
- **Forbidden behavior:** Treating a wire/decode-fatal fixture as this local case, whole-response `503`, invalid Evidence, compacted ranks 1–4, relative-order-only assertions, keyword-assisted success, reordering, or reason disclosure.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-029 — All candidate-local-invalid records

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Target access is current and eligible content may exist.
- **Authenticated principal and membership state:** Live target member remains authorized through final snapshot.
- **Provider or Chroma input:** Structurally valid bounded collection whose every record is locally invalid.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence and private/no-store.
- **Expected internal validation result:** Final authorization succeeds; every record is omitted without a response-fatal error.
- **Forbidden behavior:** `503`, `404`, provider text return, or candidate-specific reasons.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-030 — Metadata mismatch with valid ID

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Canonical ID belongs to an eligible chunk in target A.
- **Authenticated principal and membership state:** Live A member.
- **Provider or Chroma input:** The canonical response has A's aligned valid ID/distance and bounded unsolicited `metadatas[0][0]` falsely naming knowledge base B, another document, hash, and provenance; every other key/cardinality is canonical.
- **Concurrent state change:** None.
- **Expected public result:** Valid A Evidence populated only from PostgreSQL.
- **Expected internal validation result:** Metadata disagreement neither authorizes nor deauthorizes; ID enters exact-A PostgreSQL validation.
- **Forbidden behavior:** Returning provider metadata, rejecting solely for bounded disagreement, or widening scope.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-031 — Provider text mismatch with valid ID

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Canonical ID has authoritative PostgreSQL text P and a valid persisted hash.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** The canonical response has the aligned valid ID/distance and bounded unsolicited `documents[0][0] = Q`, which disagrees with P; every other key/cardinality is canonical.
- **Concurrent state change:** None.
- **Expected public result:** Evidence contains P and its authoritative hash, never Q.
- **Expected internal validation result:** Bounded provider text is ignored while the valid ID is PostgreSQL-validated.
- **Forbidden behavior:** Candidate omission solely for mismatch, Q return, runtime hashing of Q, or provider provenance.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-032 — Non-canonical bounded ID

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has eligible content unrelated to the malformed value.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Three independently executable bounded-string variants use (A) missing `chunk:` prefix, (B) invalid UUID syntax, and (C) a valid UUID in non-canonical spelling.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence when no other candidate is valid.
- **Expected internal validation result:** Canonical parser locally omits each value before building the authoritative UUID union.
- **Forbidden behavior:** Response-fatal `503`, metadata ID substitution, or per-value SQL lookup.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-033 — Unknown canonical ID

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Supplied canonical UUID has never existed; target access is valid.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** One bounded canonical `chunk:<UUID>`.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence.
- **Expected internal validation result:** Bounded batch lookup returns no row and omits the candidate locally.
- **Forbidden behavior:** Candidate-specific `404`, provider-text Evidence, or fabricated chunk.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-034 — Stale canonical ID

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Old chunk was transactionally replaced; only a new identity is current.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Derived index still returns the bounded old canonical ID.
- **Concurrent state change:** Replacement committed before the request.
- **Expected public result:** Authorized empty Evidence.
- **Expected internal validation result:** Final snapshot finds no current eligible old row and omits it.
- **Forbidden behavior:** Chroma text fallback, chunk-index rebinding, or stale citation.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-035 — Cross-knowledge-base candidate

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Request targets A; canonical candidate belongs to eligible B content.
- **Authenticated principal and membership state:** Live A member, optionally also a B member.
- **Provider or Chroma input:** B candidate appears in a bounded A response.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty A Evidence when no A candidate survives.
- **Expected internal validation result:** Exact target predicate locally omits B regardless of separate B access.
- **Forbidden behavior:** Scope widening, B disclosure, or response-fatal classification.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-036 — Candidate from inaccessible object

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Candidate belongs to another user's private knowledge base.
- **Authenticated principal and membership state:** Live caller is authorized only for target A.
- **Provider or Chroma input:** Other user's canonical ID, with optional metadata falsely claiming A.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty A Evidence with no foreign-object disclosure.
- **Expected internal validation result:** Exact target/current membership predicates omit the candidate locally.
- **Forbidden behavior:** Foreign text, filename, citation, count, or distinguishable rejection reason.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-037 — Candidate from ineligible document

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Parameterized candidate document is `pending`, `processing`, or `failed`.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded canonical ID for the ineligible document.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence when it is the only candidate.
- **Expected internal validation result:** Shared final predicate requires completed status and locally omits the candidate.
- **Forbidden behavior:** Provider-status authority, partial processing content, or response-fatal classification.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-038 — Position-preserving missing or wrong-type candidate ID

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has at least one eligible hashed chunk referenced by a separate structurally valid canonical candidate.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Two position-preserving parameterized variants each include a malformed bounded record and the separate valid canonical candidate. Variant A omits the malformed record's ID field. Variant B gives it a non-string JSON ID, with fixtures for `null`, boolean, number, array, and object. Every envelope preserves deterministic record positions and provider ordering.
- **Concurrent state change:** None.
- **Expected public result:** One deterministic authorized result containing Evidence only for the valid canonical candidate and private/no-store; neither variant becomes `503` or an empty result.
- **Expected internal validation result:** Only the malformed record is omitted; it produces no Evidence and cannot authorize or widen scope. The valid candidate continues through PostgreSQL validation at its original provider position and source rank; existing deterministic rank, RRF, and tie-breaking rules remain intact. No keyword-only fallback occurs.
- **Forbidden behavior:** Whole-response failure while positions remain deterministic; ID coercion or substitution; Evidence or authority from the malformed record; omission of the valid candidate; compacting or reordering provider ranks; or keyword-only fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-039 — Duplicate IDs retain earliest provider rank

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible hashed chunk C.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** C appears at dense ranks 2 and 5 in one bounded valid list.
- **Concurrent state change:** None.
- **Expected public result:** Exactly one Evidence item for C.
- **Expected internal validation result:** Dense absolute rank 2 is preserved; its exact RRF contribution is `1/62`; rank 5 adds neither contribution nor duplicate Evidence.
- **Forbidden behavior:** Malformed-response classification, later-rank overwrite, rank compaction, contribution `1/65`, or duplicate output.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-040 — Provider request asks only for candidate handling fields

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target
  `123e4567-e89b-42d3-a456-426614174000` has eligible indexed content; test
  embedding dimension is configured to exactly 4.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** The embedding spy captures exactly one call
  with the one normalized query and returns exactly one vector
  `[0.25, -0.5, 0.0, 1.0]`. The adapter spy then captures exact
  `GET /api/v2/version` returning bounded JSON `"1.5.9"`, followed by exactly
  one POST to
  `/api/v2/tenants/{tenant}/databases/{database}/collections/{collection_uuid}/query`,
  and returns the canonical eight-key response.
- **Concurrent state change:** None.
- **Expected public result:** Normal authorized Evidence from PostgreSQL.
- **Expected internal validation result:** Compatibility is exactly
  `chroma-http-v2-1.5.9`. The captured POST body is exactly the four-key object
  `{"query_embeddings":[[0.25,-0.5,0.0,1.0]],"n_results":<C>,"where":{"knowledge_base_id":{"$eq":"123e4567-e89b-42d3-a456-426614174000"}},"include":["distances"]}`,
  modulo immaterial object-key order. `query_embeddings` has outer cardinality
  one, inner cardinality equal to configured dimension 4, finite values in
  exact fake order, and no other vector. IDs remain implicit and the target
  filter remains a non-authoritative hint.
- **Forbidden behavior:** Zero or multiple embedding calls; zero/multiple,
  truncated, padded, reordered, normalized, replacement, or duplicate query
  vectors; a non-finite value; dimension mismatch; skipping/misreading the
  bounded version probe; an SDK-only or unpinned contract; requesting
  `documents`, `metadatas`, `embeddings`, `uris`, `data`, `where_document`,
  text, or provenance; an extra request key; or Provider content authority.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Request, result, union, and SQL bounds

### RET-BND-001 — Query semantic and scalar domain

- **Category:** Request, result, union, and SQL bounds. The stable
  parameterized execution group is
  `RET-BND-001::QUERY-NORMALIZATION-AND-SCALAR-DOMAIN` for ADR-008-R01.
- **Initial database state:** Authorized target exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Independently executable strict-body variants
  use (A) one ASCII `a` after normalization; (B) 2,048 ASCII `a` values; (C)
  2,049 ASCII `a` values; (D) only members of the exact whitespace set; (E)
  `"\u00a0a\t \n b\u3000"`, which normalizes exactly to `"a b"`; (F)
  canonically decomposed `"e\u0301"` and precomposed `"\u00e9"` subvariants,
  which both normalize exactly to NFC `"\u00e9"`; (G) missing `query`; (H)
  `query` as number, boolean, null, array, or object; and (I) a JSON string
  containing a lone escaped surrogate. The following additional stable
  variants are separately constructible. The case-sensitive, no-NFKC, U+200B,
  and post-normalization boundary variants use a downstream embedding fake
  keyed to the exact expected normalized string plus a keyword-bound-parameter
  ledger; only the expected string produces that row's unique dense Evidence
  sentinel, and a transformed string produces no sentinel.
  The U+0001 row is instead executed at every declared level as a supporting
  semantic-validation observation with no downstream retrieval or result
  oracle. U+0000 rejection variants use the exact stage-call ledger.

  | Stable variant label | JSON query fixture and exact gate/downstream value |
  | --- | --- |
  | `RET-BND-001::CASE-SENSITIVE-PRESERVATION` | Raw `"AgentForge agentforge"`; both embedding input and keyword SQL bound value are exactly `"AgentForge agentforge"`. |
  | `RET-BND-001::NO-NFKC-COMPATIBILITY-FOLD` | Raw `"\uFF21gent"`, beginning U+FF21 FULLWIDTH LATIN CAPITAL LETTER A whose NFKC value is ASCII `A`; downstream remains exactly `"\uFF21gent"`. |
  | `RET-BND-001::EXCLUDED-U200B-PRESERVATION` | Raw `"\u200Balpha\u200B\u200Bbeta\u200B"`, using specifically excluded U+200B ZERO WIDTH SPACE at both edges and twice inside; every U+200B remains in the exact downstream value and is neither trimmed nor collapsed. |
  | `RET-BND-001::POST-NORMALIZATION-SCALAR-BOUNDARY` | Raw TAB + 2,048 ASCII `a` values + U+3000 has 2,050 scalars; permitted edge whitespace is removed first, producing exactly 2,048 `a` values, which pass and reach both downstream spies unchanged. |
  | `RET-BND-001::U0000-ALONE-REJECTION` | The valid JSON source escape `"\u0000"` decodes to U+0000 alone; exact string type, Unicode-scalar validity, and strict UTF-8 representability pass, then the query is rejected before NFC. |
  | `RET-BND-001::EMBEDDED-U0000-REJECTION` | The valid JSON source `"a\u0000b"` decodes with embedded U+0000 and follows the same pre-NFC semantic rejection path. |
  | `RET-BND-001::ADJACENT-U0001-PRESERVATION` | The valid JSON source `"a\u0001b"` decodes with embedded U+0001 and passes query semantic validation with the exact sequence preserved. U+0001 is neither deleted, replaced, normalized, collapsed, nor treated as whitespace. This supporting parameter assigns no downstream retrieval or public-result behavior. |
- **Concurrent state change:** None.
- **Expected public result:** A, B, E, and both F subvariants return authorized
  empty Evidence and private/no-store. The case-sensitive, no-NFKC, U+200B,
  and post-normalization boundary rows return exactly their unique dense
  Evidence sentinels and private/no-store. C, D, G, every H type, I, and both
  U+0000 rejection rows return the existing generic `422 VALIDATION_ERROR`, no
  Evidence, and private/no-store.
  The supporting U+0001 parameter assigns no U+0001-specific public retrieval
  result.
- **Expected internal validation result:** After exact string-type validation,
  the pipeline strictly decodes Unicode scalars, proves strict UTF-8
  representability, rejects any U+0000 before NFC, applies NFC once,
  trims/collapses only the enumerated set, and only then validates the
  normalized scalar bound followed by the strict UTF-8 byte bound. U+0000
  rejection is semantic validation, not normalization. It does not remove,
  replace, collapse, whitespace-map, or U+FFFD-map the value, and it is not
  generalized to all Unicode `Cc` controls. Equality 2,048 passes; plus one
  fails before retrieval work. The case-sensitive, no-NFKC, U+200B, and post-
  normalization boundary rows assert exact code-point equality at the keyword
  SQL bind and sole embedding input, the unique fake-vector/candidate branch,
  and exact returned sentinel, making transformation observable beyond a
  preservation-only prose assertion. The U+0001 supporting parameter asserts
  only semantic acceptance and exact preservation; it assigns no keyword,
  embedding, Chroma/Provider, candidate, ranking, or Evidence behavior. For
  either authenticated, initially
  authorized escaped-U+0000 row, initial authentication/target PostgreSQL may
  have completed, but NFC/whitespace-normalization calls, keyword statements,
  embedding calls, Chroma/Provider calls, final authoritative transactions,
  and Evidence counts are all zero. The PostgreSQL integration execution
  observes that ledger and must not send U+0000 to PostgreSQL to manufacture a
  driver or database error.

  Query-derived text is absent from fixed validation classifications,
  exception `str`/`repr`, internal request-value diagnostic representations,
  public responses, and captured sinks; only fixed, non-user-controlled field
  and classification labels are permitted. The future implementation may use
  `field(repr=False)` as one acceptable mechanism, but this case mandates no
  exclusive Python mechanism. The complete recursive all-sink runtime proof
  remains with the capable AF-3C privacy acceptance layer.
- **Forbidden behavior:** Treating a variant as coverage for another;
  preserving decomposed F rather than NFC; NFKC, NFKD, or compatibility
  normalization; ASCII or Unicode case folding; trimming/collapsing U+200B;
  measuring the raw scalar count before normalization; retaining permitted
  edge whitespace; failing to collapse the permitted interior run; accepting
  empty/missing/wrong-type/surrogate input; truncation; Provider work on a
  failing variant; removing/replacing/collapsing U+0000; treating U+0000 as
  whitespace, U+FFFD, an empty query, or an empty keyword result; sending it to
  PostgreSQL and translating the resulting failure; rejecting or altering the
  positive U+0001 row, treating U+0001 as whitespace, or rejecting all Unicode
  `Cc` controls; disclosing query-derived text in a
  classification, diagnostic, exception, response, or captured sink; raw
  query logging; or byte-only validation.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration. The
  PostgreSQL execution permits the initial authentication/target statements,
  requires zero keyword statements and zero final authoritative transactions,
  and cannot pass by deliberately binding U+0000 and catching a
  driver/database failure.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-002 — Query UTF-8 byte limit

- **Category:** Request, result, union, and SQL bounds. The stable
  parameterized execution group is
  `RET-BND-002::QUERY-UTF8-BYTE-DOMAIN` for ADR-008-R01.
- **Initial database state:** Authorized target exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Two independently executable normalized queries stay within the 2,048-scalar limit: (A) 1,024 U+1F642 scalar values encode to exactly 4,096 UTF-8 bytes; (B) the same query plus one ASCII `a` encodes to exactly 4,097 bytes.
- **Concurrent state change:** None.
- **Expected public result:** Variant A returns authorized empty Evidence and private/no-store; Variant B returns existing `422 VALIDATION_ERROR`, no Evidence, and private/no-store.
- **Expected internal validation result:** Strict UTF-8 byte equality passes and byte plus one independently rejects before Provider or keyword work.
- **Forbidden behavior:** Treating equality and plus one as one assertion, rejecting A, accepting B because its scalar count is legal, character-only acceptance, truncation, Provider calls on B, or query disclosure.
- **Planned test level:** unit, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-003 — Strict request shape and requested result limit

- **Category:** Request, result, union, and SQL bounds. This parent owns the
  independently executable ADR-008-R01 strict-request decision matrix and the
  requested-count domain.
- **Initial database state:** Except for path-rejection and explicit
  precedence executions, the live caller owns one target whose lowercase
  hyphenated canonical UUID is
  `123e4567-e89b-42d3-a456-426614174000`; it contains at least 50 eligible
  chunks in deterministic exact RRF order. Path-rejection executions use that
  same existing authorized target so a hidden or absent target cannot mask the
  textual path defect. U+0000 authentication-precedence executions have an
  existing target; U+0000 hidden-target-precedence executions use that target
  without caller membership.
- **Authenticated principal and membership state:** Every ordinary execution
  has a live, active target member and a current session, so authentication
  succeeds before path, target, request-media, or body processing. The
  U+0000 authentication-precedence parameters have no session. The U+0000
  hidden-target-precedence parameters have a live session but no target
  membership.
- **Provider or Chroma input:** Each row below is a separate deterministic
  execution at every declared capable level. Controls use source-isolated,
  bounded keyword and canonical Provider fixtures that return the exact
  requested Evidence prefix. Provider, request-media, body-parser, schema,
  target-repository, keyword, embedding, and final-validator spies expose the
  executed stage without changing production ordering.

  | Stable variant label | Exact request fixture and trigger |
  | --- | --- |
  | `RET-BND-003::CANONICAL-PATH-CONTROL` | `POST /api/v1/knowledge-bases/123e4567-e89b-42d3-a456-426614174000/retrieval`, `Content-Type: application/json`, and body `{"query":"a","requested_count":1}`. |
  | `RET-BND-003::NONCANONICAL-PATH` — uppercase parameter | The path uses `123E4567-E89B-42D3-A456-426614174000`, which denotes the same UUID value as the authorized target but violates lowercase canonical text. Request media and body equal the canonical-path control. |
  | `RET-BND-003::NONCANONICAL-PATH` — unhyphenated parameter | The path uses `123e4567e89b42d3a456426614174000`, which denotes the same UUID value as the authorized target but violates hyphenated canonical text. Request media and body equal the canonical-path control. |
  | `RET-BND-003::SUPPORTED-MEDIA-CONTROL` | The canonical path, exact `Content-Type: application/json`, and body `{"query":"a","requested_count":1}` exercise successful request-media validation. |
  | `RET-BND-003::UNSUPPORTED-MEDIA` | The canonical path, exact unsupported request media `Content-Type: text/plain`, and otherwise valid JSON bytes `{"query":"a","requested_count":1}` exercise the ADR's unsupported-media branch. |
  | `RET-BND-003::MEDIA-BEFORE-BODY-PRECEDENCE` | The canonical path, `Content-Type: text/plain`, and a deterministic malformed/oversized 65,537-byte body make media, size, and JSON independently defective. |
  | `RET-BND-003::AUTHORIZED-BODY-VALIDATION-CONTROL` | The canonical path, exact `Content-Type: application/json`, and parseable object `{"query":"a","limit":1}` pass the earlier gates and exercise the closed-schema unknown-field rejection. |
  | `RET-BND-003::BODY-EXACT-65536` | The canonical path, exact `Content-Type: application/json`, and the valid exact 65,536-byte `R` fixture defined in Test conventions exercise inclusive body equality. |
  | `RET-BND-003::BODY-PLUS-ONE-65537` | The same path/media and valid 65,537-byte `R` fixture arrive in one ASGI body event. |
  | `RET-BND-003::CHUNKED-BODY-PLUS-ONE-65537` | The identical valid 65,537-byte `R` fixture arrives in ASGI chunks of 32,768, 32,768, and 1 byte. |
  | `RET-BND-003::LITERAL-NUL-JSON-PARSER-REJECTION` | The canonical path and exact media carry a body whose `query` JSON string contains one literal unescaped byte `0x00`; that byte is a strict-JSON defect, not a decoded-query semantic fixture. |
  | `RET-BND-003::ESCAPED-U0000-DOMAIN-HANDOFF` | The canonical path and exact media carry, as separate parameters, exact ASCII JSON bodies `{"query":"\u0000"}` and `{"query":"a\u0000b"}`. Both are syntactically valid strict JSON; parsing must decode them and hand the decoded values to RET-BND-001, which owns the query-domain decision. |
  | `RET-BND-003::U0000-AUTHENTICATION-PRECEDENCE` | With no session, separately execute the literal-NUL body and escaped-U+0000-alone body from the preceding two rows. |
  | `RET-BND-003::U0000-HIDDEN-TARGET-PRECEDENCE` | With a live user but no membership in the existing target, separately execute the same literal-NUL and escaped-U+0000-alone bodies. |
  | `RET-BND-003::REQUESTED-COUNT-DOMAIN` | The canonical path and exact `Content-Type: application/json` parameterize `requested_count` as omitted; integer `1`; integer `0`; integer `-1`; integer `50`; integer `51`; boolean `true`; float `1.0`; and numeric string `"1"`. Each is a separate execution with valid query `"a"`. |

  The authorized body-validation group additionally executes one field at a
  time for `count`, `document_id`, `document_ids`, `chunk_id`, and
  `chunk_ids`; one duplicate JSON key; one non-object body; and one absent
  body. The ADR defines no missing request `Content-Type`, request-media
  parameter/charset, malformed request `Content-Type`, or structured-suffix
  branch, so this case assigns no outcome to those undefined inputs.
- **Concurrent state change:** None. Each execution contains only the defects
  stated in its decision-matrix row.
- **Expected public result:** The canonical-path, supported-media, and exact-
  body controls each return exactly the first deterministic Evidence item with
  `Cache-Control: private, no-store`. Each noncanonical-path parameter returns
  exactly generic hidden `404 NOT_FOUND`, zero Evidence, and
  `Cache-Control: private, no-store`; no redirect response is permitted. The
  unsupported-media execution, media-before-body execution, both body-plus-
  one executions, every authorized-body-validation execution, and requested-
  count values `0`, `-1`, `51`, `true`, `1.0`, and `"1"` each return exactly
  the existing generic
  `422 VALIDATION_ERROR` envelope, zero Evidence, and
  `Cache-Control: private, no-store`. The authorized literal-NUL parser row and
  both escaped-U+0000 semantic-handoff parameters produce that same generic
  `422 VALIDATION_ERROR`, private/no-store envelope through distinct internal
  gates. Each
  U+0000 authentication-precedence parameter returns generic
  `401 AUTHENTICATION_REQUIRED`; each U+0000 hidden-target-precedence parameter
  returns generic hidden `404 NOT_FOUND`; neither precedence group processes
  its body. Omitted count, integer `1`, and integer `50` return exactly the
  first 10, 1, and 50 deterministic Evidence items with
  `Cache-Control: private, no-store`.
- **Expected internal validation result:** The canonical-path control accepts
  the path text, completes exact-target authorization, passes request-media
  and body validation, and reaches keyword, embedding, Provider, and final
  validation exactly once. Each noncanonical-path parameter permits only the
  completed session/active-user authentication read before canonical-path
  rejection; it performs zero exact-target or membership SQL, zero
  request-media validation, zero body parsing, zero schema validation, zero
  keyword SQL, zero embedding or Provider work, and zero final-transaction
  work. The supported-media control records one successful request-media
  decision, one body parse, one schema validation, and later retrieval work.
  The unsupported-media execution permits the completed initial
  authentication and exact-target membership/capability SQL, then records
  request-media rejection before body collection; body-receive, body-parser,
  schema, keyword, embedding, Provider, and final-transaction call counts are
  zero. The
  media-before-body execution has the same allowed SQL and records
  request-media rejection with zero body-receive and body-parser counts despite
  the malformed/oversized bytes. The exact-body row records exactly 65,536 received and retained
  octets, one JSON parse, one schema validation, and later retrieval work. The
  contiguous plus-one row observes byte 65,537 and aborts; the chunked row
  accepts the first two chunks and aborts on the first byte of the final chunk
  without requesting another event. Both overflow rows record zero full-body
  materializations, JSON parses, duplicate-key/schema calls,
  normalization/count calls, keyword queries, embedding/Provider calls, and
  final transactions. The authorized literal-NUL row attempts strict JSON
  parsing and rejects there, with zero completed parses, schema/type/query-
  domain validations, normalizations, or retrieval calls. The authorized
  escaped-U+0000 row records one successful strict parse and successful closed-
  schema validation before handing the decoded value to RET-BND-001. That case
  owns the decoded query-domain decision: both values pass exact query string-
  type, Unicode-scalar, and strict-UTF-8 validity and reach its same pre-NFC
  U+0000 semantic rejection. In particular, the exact ASCII JSON body
  `{"query":"a\u0000b"}` is syntactically valid strict JSON and decodes to
  the string containing `a`, U+0000, and `b`. After the semantic rejection,
  each parameter records zero NFC calls, zero whitespace-normalization calls,
  zero keyword statements, zero embedding calls, zero Chroma/Provider calls,
  zero final authoritative transactions, and zero Evidence construction or
  publication. The literal-NUL parser row and escaped-U+0000 semantic rows
  therefore have different internal gate ledgers even though their public
  outcomes are generic `422 VALIDATION_ERROR`. For both precedence-body
  parameters, the
  authentication-precedence parameters stop at authentication with zero
  target/media/body work, and the
  hidden-target-precedence parameters stop after authentication at exact-
  target authorization with zero media/body work. Every
  authorized-body-validation execution passes authentication,
  exact-target authorization, and request-media validation, then reaches the
  strict body parser/schema stage and rejects there before keyword,
  embedding, Provider, or final-transaction work. Requested-count omission
  applies exact default 10; integer `1` proves the minimum; integer `50`
  proves the inclusive maximum and configured Provider count 128; each
  failing count is rejected without coercion before over-fetch arithmetic or
  retrieval work.
- **Forbidden behavior:** The canonical-path or supported-media control being
  rejected at its named gate. A noncanonical-path parameter being lowercased,
  rehyphenated, redirected, accepted, target-resolved, body-parsed,
  Provider-executed, or mapped to `422`. Unsupported request media being
  treated as JSON, silently coerced, body-parsed, Provider-executed, or mapped
  to a body diagnostic. The media-before-body execution invoking the body
  parser or returning a parser/schema-specific alternative. An
  authorized-body-validation execution bypassing strict schema validation,
  accepting an alias or client ID, using duplicate-key last-wins, or reaching
  retrieval work. Treating the literal unescaped NUL as valid JSON; treating
  the ASCII U+0000 escape as a JSON parse failure; merging the parser and
  semantic ledgers; running NFC or retrieval after decoded U+0000; exposing
  query content in either generic `422 VALIDATION_ERROR`; allowing either
  defective body to supersede required `401` or hidden `404` precedence.
  Rejecting body equality;
  accepting or truncating body plus one; using unbounded `body()` or complete
  materialization before a length check; parsing or schema-validating after
  overflow; continuing body receive after the first overflow byte. Treating
  count minimum, equality, maximum, plus-one, or
  wrong JSON types as one execution; accepting booleans as integers; silently
  clamping; overflow arithmetic; partial Evidence; fallback Evidence; or a
  Provider call on any failing `422` execution.
- **Planned test level:** unit, HTTP integration. Every stable variant label
  and every parameter row is independently executable at both levels; unit
  executions use deterministic gate/repository spies and HTTP executions
  assert the public envelope, headers, routing, and downstream call ledger.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-004 — Dense over-fetch arithmetic below ceiling

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target has exactly one eligible dense-only sentinel and no keyword match.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Public `requested_count = 10`; the adapter spy captures exact integer `n_results = min(128, checked_multiply(10, 4)) = 40` and returns the canonical single-candidate response for the dense sentinel.
- **Concurrent state change:** None.
- **Expected public result:** Exactly one Evidence item for the dense sentinel, with no keyword rank and private/no-store.
- **Expected internal validation result:** Configured Provider count `C` equals checked `10 * 4 = 40`; raw positions `P <= 40`, and no floating or display-domain arithmetic participates.
- **Forbidden behavior:** Floating arithmetic, unchecked overflow, off-by-one count, or unbounded provider request.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-005 — Dense over-fetch ceiling

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target has exactly one eligible dense-only sentinel and no keyword match.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Public `requested_count = 50`; checked product `50 * 4 = 200` exceeds both dense/Provider ceilings, the adapter spy captures exact `n_results = 128`, and it returns the canonical single-candidate response for the dense sentinel.
- **Concurrent state change:** None.
- **Expected public result:** Exactly one Evidence item for the dense sentinel, with no keyword rank and private/no-store.
- **Expected internal validation result:** Overflow-safe calculation yields exactly `min(128, 128, 200) = 128` in the outbound request.
- **Forbidden behavior:** Request above ceiling, arithmetic wrap, or post-response-only truncation.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-006 — Keyword candidate maximum

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** More than `MAX_KEYWORD_CANDIDATES` eligible target chunks match.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Dense response is bounded and valid.
- **Concurrent state change:** None.
- **Expected public result:** After all 128 keyword candidates are validated and exactly ranked, final public count is `F = min(R, E)` and never exceeds the accepted requested count.
- **Expected internal validation result:** Legal scoped keyword SQL returns at most exactly 128 rows; `K <= 128`, union/validation operate before the public cutoff, and only final exact RRF order is cut to `R`.
- **Forbidden behavior:** Unbounded SQL result materialization, global count exposure, Python-only source limiting, pre-validation public cutoff, or `F > R`.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-007 — Candidate union above configured maximum

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target has enough eligible identities for disjoint bounded source lists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Individually legal source maps, each at most 128 keys, are disjoint enough to create exactly `MAX_UNIQUE_CANDIDATES + 1 = 193` unique UUIDs.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** The exact `U = 193` plus-one branch rejects before SQL partition allocation and discards both source rank maps.
- **Forbidden behavior:** Arbitrary truncation, partial Evidence, unbounded allocation, or fallback.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-008 — Zero unique candidates

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target remains current.
- **Authenticated principal and membership state:** Live target member passes final authorization.
- **Provider or Chroma input:** Both source lists are empty; the dense empty list comes from the same valid present-empty Provider envelope, which parses successfully to zero deterministic Provider positions and zero dense candidates.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence and private/no-store.
- **Expected internal validation result:** The adapter returns the empty dense list; `U = 0`; validation-batch query count is zero; and the separate first final-authorization statement still runs.
- **Forbidden behavior:** Empty `IN` query, synthetic or placeholder candidate, missing-collection error, keyword-only degraded mode, skipped final authorization, or `503`.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-009 — One unique candidate

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** One eligible target chunk exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Source maps yield one unique canonical UUID.
- **Concurrent state change:** None.
- **Expected public result:** One authorized Evidence item.
- **Expected internal validation result:** One single-item batch and exactly `ceil(1 / B) = 1` validation query.
- **Forbidden behavior:** N+1 authorization, zero queries, or padding the batch.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-010 — Exactly one full batch

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Exactly `B` eligible target chunks exist.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Source maps yield exactly `B` unique canonical UUIDs.
- **Concurrent state change:** None.
- **Expected public result:** Deterministically ranked authorized Evidence within the requested result limit.
- **Expected internal validation result:** UUID-ascending partition has size `B` and exactly one validation query.
- **Forbidden behavior:** Extra query, smaller arbitrary partitions, or reliance on provider order for batching.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-011 — One more than a full batch

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** `B + 1` eligible target chunks exist.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Source maps yield `B + 1` unique canonical UUIDs.
- **Concurrent state change:** None.
- **Expected public result:** Deterministically ranked authorized Evidence within result bounds.
- **Expected internal validation result:** Contiguous UUID-ascending partitions have sizes `B` and `1`; query count is 2.
- **Forbidden behavior:** One unbounded `IN`, three queries, or provider-order partitioning.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-012 — Several deterministic batches

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** More than 128 eligible target chunks create three validation batches at `B = 64`.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Across every repetition, the ordered keyword list, ordered dense list, and their serialized UUID-to-absolute-rank maps are byte-identical. Independently executable repetitions vary only non-rank-bearing factors: keyword/dense completion order, unique-union insertion order, dictionary/map iteration order, validation-batch result arrival order, and PostgreSQL row-return order before UUID-keyed reconstruction.
- **Concurrent state change:** None.
- **Expected public result:** Every repetition returns identical final Evidence ordering.
- **Expected internal validation result:** The same UUID sort produces the same contiguous 64/64/remainder partitions, exactly `ceil(U / 64) = 3` validation queries, identical absolute rank maps, exact RRF values, and byte-identical Evidence.
- **Forbidden behavior:** Permuting an ordered source list such as dense `[A, B]` into `[B, A]` and calling it non-rank-bearing; changing any source rank map; hash/set iteration ordering, completion/arrival-order partitions, SQL row-order reconstruction, N+1 queries, or unstable results.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-013 — Duplicate source candidates reduce unique union

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Eligible chunks appear repeatedly within and across sources.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded keyword and dense lists contain duplicates with known earliest ranks.
- **Concurrent state change:** None.
- **Expected public result:** At most one Evidence item per chunk.
- **Expected internal validation result:** `U` counts unique UUIDs only; partitions and `ceil(U / 64)` use that count while source rank maps retain each identity's earliest unchanged absolute rank and therefore its exact original RRF contribution.
- **Forbidden behavior:** Duplicate SQL parameters, duplicate Evidence, lost/compacted earliest rank, changed contribution, or counting source occurrences as `U`.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-014 — Unordered PostgreSQL rows

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Eligible candidate rows are returned in a deliberately different order from requested UUIDs.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Known keyword/dense rank maps cover several candidates.
- **Concurrent state change:** None.
- **Expected public result:** Evidence follows deterministic RRF order, not database row order.
- **Expected internal validation result:** Authoritative records are reconstructed by a UUID-keyed map after all batches succeed.
- **Forbidden behavior:** Positional zip with SQL rows, row-order ranking, or provenance misassociation.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-015 — Exact maximum validation-batch query count

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Exactly `MAX_UNIQUE_CANDIDATES = 192` eligible rows exist.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded source lists yield that exact unique maximum.
- **Concurrent state change:** None.
- **Expected public result:** Bounded authorized Evidence.
- **Expected internal validation result:** Actual validation queries equal exactly `ceil(192 / 64) = 3`; the first final-authorization statement is separately counted as one and never included in the three.
- **Forbidden behavior:** Hidden per-row queries, an unbounded `IN`, or counting authorization as a validation batch.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Keyword SQL scope

### RET-KEY-001 — Scoped deterministic PostgreSQL keyword ranking

- **Category:** Keyword SQL scope.
- **Initial database state:** Knowledge base A contains exactly `MAX_KEYWORD_CANDIDATES + 1 = 129` eligible matching chunks. Controlled text produces known `ts_rank_cd` score groups, including at least two equal-score rows whose native UUID order places one at normative rank 128 and the other at rank 129. UUIDs and insertion order are chosen so insertion/heap order disagrees with the full `keyword_score DESC, chunk UUID ASC` order. Knowledge base B contains identical and additional matches but is outside A's scope.
- **Authenticated principal and membership state:** A live member requests exactly A; B is excluded by current SQL authorization and scope predicates before keyword score or rank assignment.
- **Provider or Chroma input:** The Provider returns the canonical present-empty response, proving keyword-only success; no dense identity can satisfy the result.
- **Concurrent state change:** Rebuild/repeat the fixture with varied insertion order and deliberately varied physical/row-return order, including an execution shape that would expose a pre-order `LIMIT`.
- **Expected public result:** Every repetition returns the same requested prefix of the exact A-only top-128 UUID set; returned items expose the same one-based keyword ranks, have no dense ranks, and B never appears.
- **Expected internal validation result:** Unit assertions fix `simple`, bound `plainto_tsquery`, `ts_rank_cd(..., 0)`, and the expected full total order. PostgreSQL assertions compute the oracle independently, prove A scoping before scoring, prove the rank-128/rank-129 tie and native UUID cutoff, and require exactly the first 128 UUIDs with ranks 1–128 in every repetition. RRF receives those ranks unchanged.
- **Forbidden behavior:** Applying `LIMIT 128` before the normative deterministic order; including the tied rank-129 UUID or excluding rank 128; B influencing A ranks; ordering only by score; insertion-, row-, heap-, index-, planner-, random-, or locale-sensitive UUID-text order; Python post-hoc ranking after an unordered/unbounded query; B count exposure; dense-assisted success; or raw keyword score used in fusion/tie breaks.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-KEY-002 — Injected cross-scope keyword candidate is revalidated

- **Category:** Keyword SQL scope.
- **Initial database state:** Target A is authorized; injected canonical candidate belongs to B.
- **Authenticated principal and membership state:** Live A member.
- **Provider or Chroma input:** Keyword repository test double injects B after the scoped-query boundary; dense list is empty.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty A Evidence when no legal A candidate exists.
- **Expected internal validation result:** Shared fixed-snapshot validator rejects B again by exact target and access predicates.
- **Forbidden behavior:** Trusting keyword origin as authority, B disclosure, or bypassing shared validation.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-KEY-003 — No global keyword result count

- **Category:** Keyword SQL scope.
- **Initial database state:** Inaccessible B has many matches; authorized A has none.
- **Authenticated principal and membership state:** Live A member with no B membership.
- **Provider or Chroma input:** Dense response is a valid empty collection.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty A Evidence with no global or B count.
- **Expected internal validation result:** SQL and telemetry expose only bounded A-scoped counts.
- **Forbidden behavior:** Total-match count, timing branch based on B count, B identifier, or global query.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-KEY-004 — HTTP retrieval cannot use worker/internal repository

- **Category:** Keyword SQL scope.
- **Initial database state:** Internal repository could see multiple private knowledge bases; user repository sees only target A.
- **Authenticated principal and membership state:** Live A member.
- **Provider or Chroma input:** Bounded valid provider response.
- **Concurrent state change:** None.
- **Expected public result:** Only authorized A Evidence.
- **Expected internal validation result:** Dependency/spy proves user-facing service calls only the scoped repository path.
- **Forbidden behavior:** `_internal` worker call, fabricated principal, unscoped SQL, or post-hoc global filtering.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## RRF and result determinism

### RET-RANK-001 — Exact RRF formula

- **Category:** RRF and result determinism.
- **Initial database state:** Several authoritative eligible chunk identities are supplied to pure fusion.
- **Authenticated principal and membership state:** Authorized principal context is already validated.
- **Provider or Chroma input:** Independently executable fixtures cover (A) keyword-only rank `k`; (B) dense-only rank `d`; (C) both ranks `(k,d)`; (D) a missing keyword source; (E) a missing dense source. Absolute ranks are fixed before fusion.
- **Concurrent state change:** None.
- **Expected public result:** Evidence exposes the exact source-rank nullability, one-based fused rank, and a display-only `fused_score` string with exactly 12 decimal places rounded half-to-even.
- **Expected internal validation result:** One-source candidates use exact `1/(60+r)`; two-source candidates use exact `(120+k+d)/((60+k)*(60+d))`; a missing source contributes no term. Ordering compares exact integer cross-products before serialization.
- **Forbidden behavior:** Treating one/missing/two-source variants as equivalent, zero-based or compacted ranks, another constant, a sentinel missing-rank contribution, raw-score arithmetic, binary64/display values as the sort key, another precision/rounding mode, or rounding-dependent ordering.
- **Planned test level:** unit, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-RANK-002 — Raw score scales cannot override rank

- **Category:** RRF and result determinism.
- **Initial database state:** Two eligible authoritative chunks exist.
- **Authenticated principal and membership state:** Authorized principal context is already validated.
- **Provider or Chroma input:** Repeat fixtures with identical ranks but radically different finite keyword/vector raw scores.
- **Concurrent state change:** None.
- **Expected public result:** Both repetitions have identical Evidence ordering and fused scores.
- **Expected internal validation result:** Fusion consumes only preserved one-based source ranks.
- **Forbidden behavior:** Adding, multiplying, calibrating, or tie-breaking with raw scores.
- **Planned test level:** unit, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-RANK-003 — Cross-source duplicate becomes one Evidence item

- **Category:** RRF and result determinism.
- **Initial database state:** Eligible chunks K, D, and O are distinct; K appears keyword-only, D dense-only, and O in both source maps.
- **Authenticated principal and membership state:** Authorized target context.
- **Provider or Chroma input:** Source-distinct sentinels and known absolute ranks form the suite-wide mixed-source fixture.
- **Concurrent state change:** None.
- **Expected public result:** Exactly one Evidence item each for K, D, and O; K has only keyword rank, D only dense rank, and O both ranks.
- **Expected internal validation result:** Both source maps are independently observed; O's exact rational sums both rank contributions once and identity deduplication remains authoritative.
- **Forbidden behavior:** Passing without either source-distinct sentinel, assigning K a dense rank or D a keyword rank, two O items, lost contribution, or raw-score merge.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-RANK-004 — Complete deterministic tie order

- **Category:** RRF and result determinism.
- **Initial database state:** Eligible UUID fixtures are chosen to exercise every tie level and include the exact-rational collision `(keyword=3,dense=80)` versus `(keyword=24,dense=30)`.
- **Authenticated principal and membership state:** Authorized target context.
- **Provider or Chroma input:** Parameterized rank maps exercise exact-rational, best-rank, keyword-rank absent-last, dense-rank absent-last, and UUID comparators. The collision pair is mathematically `29/1260` for both even though direct binary64 sums can be `0.023015873015873014` and `0.023015873015873017`.
- **Concurrent state change:** None.
- **Expected public result:** Order is exact rational descending, best rank ascending, keyword rank ascending absent-last, dense rank ascending absent-last, UUID ascending. Both collision items serialize as `"0.023015873016"`, and `(3,80)` precedes `(24,30)` by best rank.
- **Expected internal validation result:** Integer cross-products classify the collision as exactly equal before the next comparator; separate fixtures prove every later comparator.
- **Forbidden behavior:** Binary64 or serialized-decimal ordering (which would rank `(24,30)` first), epsilon comparison, treating displayed equality as the authority, Provider arrival, SQL row order, raw score, random value, or locale-sensitive UUID order.
- **Planned test level:** unit, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-RANK-005 — SQL batch order cannot affect RRF order

- **Category:** RRF and result determinism.
- **Initial database state:** Eligible UUID order differs deliberately from final rank order.
- **Authenticated principal and membership state:** Live authorized target member.
- **Provider or Chroma input:** Rank maps produce a known RRF order across several UUID-sorted batches.
- **Concurrent state change:** None.
- **Expected public result:** Evidence follows RRF order and requested result limit.
- **Expected internal validation result:** Batch reconstruction completes before rank maps and RRF are applied.
- **Forbidden behavior:** UUID batch order as response order, per-batch ranking, or early result truncation.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Evidence, eligibility, and citations

### RET-EVID-001 — Authoritative Evidence projection

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Eligible chunk has authoritative IDs, text, persisted hash, display filename, offsets, and optional page range; document storage key contains a sentinel path.
- **Authenticated principal and membership state:** Live target member with current read capabilities.
- **Provider or Chroma input:** Valid ID plus disagreeing bounded text and provenance metadata.
- **Concurrent state change:** None.
- **Expected public result:** The PostgreSQL-authoritative partition contains only target/document/chunk IDs, `normalized_text` as content, persisted valid hash, approved source display name, and persisted optional page/character ranges. The derived partition contains only preserved keyword/dense ranks, display-only fused score, fused rank, deterministic citation reference, and fixed `untrusted_document_content`.
- **Expected internal validation result:** The authoritative partition loads from one allowlisted projection in the fixed snapshot. Each derived field proves its sole input: validated absolute rank maps; exact RRF; the authoritative target/chunk IDs and hash in `af3:citation:v1:<knowledge_base_uuid>:<chunk_uuid>:<content_sha256>`; or the fixed trust literal.
- **Forbidden behavior:** Claiming every Evidence field is loaded from PostgreSQL; deriving authoritative fields from rank maps; deriving ranks/score/trust from PostgreSQL row order or content; Provider authority; storage path, secret, raw embedding, internal exception, or post-commit reload.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-002 — Completed legacy chunk with null content hash

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Completed legacy document has a chunk whose authoritative `content_sha256` is null.
- **Authenticated principal and membership state:** Live target member otherwise retains full read access.
- **Provider or Chroma input:** Valid canonical ID for the legacy chunk with bounded text, UUID, timestamp, and metadata.
- **Concurrent state change:** None.
- **Expected public result:** No Evidence for that chunk, no citation, and authorized empty Evidence if it is the only candidate.
- **Expected internal validation result:** Persisted-null hash makes the chunk ineligible and omission is non-disclosing.
- **Forbidden behavior:** Dynamic text hash, `updated_at`, UUID, Chroma/provider metadata, or another invented revision.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-003 — Citation resolver reauthenticates and resolves authoritatively

- **Category:** Evidence, eligibility, and citations. This stable case owns the
  citation supported-media, body-boundary, authentication-precedence, and
  strict-schema variants named below.
- **Initial database state:** Canonical route target
  `123e4567-e89b-42d3-a456-426614174000` has current completed document
  `22222222-2222-4222-8222-222222222222`, eligible chunk
  `11111111-1111-4111-8111-111111111111`, persisted hash of 64 lowercase
  `a` characters, authoritative normalized text, approved display source, and
  persisted nullable page/character provenance. The CitationReference is the
  exact value in body seed `C`.
- **Authenticated principal and membership state:** Success/media/body/schema
  rows use a current live target member. Separate authentication rows use no
  session, an expired session, an already-revoked session, and an unexpired/
  unrevoked session whose user is inactive. A deliberately cached/prebuilt
  Principal exists in every failing-auth row and must not be trusted.
- **Provider or Chroma input:** Every row invokes `POST` on the citation route
  family. Unless a named path-rejection row changes only the target text, the
  exact route is
  `/api/v1/knowledge-bases/123e4567-e89b-42d3-a456-426614174000/citations/resolve`.
  Provider, embedding, keyword, candidate, RRF, storage, and filesystem spies
  must remain unused in every row.

  | Stable variant label | Exact media/body and trigger |
  | --- | --- |
  | `RET-EVID-003::CITATION-SUPPORTED-MEDIA-CONTROL` | Exact `Content-Type: application/json` and unpadded valid body `C`; every gate and final authoritative resolution succeeds. |
  | `RET-EVID-003::CITATION-BODY-EXACT-65536` | Exact media and the valid 65,536-byte padded `C` fixture; only body equality differs from the control. |
  | `RET-EVID-003::CITATION-BODY-PLUS-ONE-65537` | Exact media and the valid 65,537-byte padded `C` fixture in one ASGI event. |
  | `RET-EVID-003::CITATION-CHUNKED-BODY-PLUS-ONE-65537` | The same 65,537 bytes in chunks 32,768/32,768/1. |
  | `RET-EVID-003::CITATION-UNSUPPORTED-MEDIA` | Exact `Content-Type: text/plain` and otherwise valid `C`. |
  | `RET-EVID-003::CITATION-UNAUTHENTICATED-PRECEDENCE` | Missing session, `Content-Type: text/plain`, and a 65,537-byte malformed/oversized body. |
  | `RET-EVID-003::CITATION-AUTH-EXPIRED` | Expired session, exact media, and valid `C`. |
  | `RET-EVID-003::CITATION-AUTH-REVOKED` | Already-revoked session, exact media, and valid `C`. |
  | `RET-EVID-003::CITATION-AUTH-INACTIVE-USER` | Inactive user, exact media, and valid `C`. |
  | `RET-EVID-003::CITATION-SCHEMA-MISSING-FIELD` | Exact empty object `{}`. |
  | `RET-EVID-003::CITATION-SCHEMA-EXTRA-FIELD` | Valid reference plus one `extra` field. |
  | `RET-EVID-003::CITATION-SCHEMA-DUPLICATE-FIELD` | Two `citation_reference` keys in the raw JSON object. |
  | `RET-EVID-003::CITATION-SCHEMA-NUMBER-VALUE` | Sole value is JSON number `1`. |
  | `RET-EVID-003::CITATION-SCHEMA-BOOLEAN-VALUE` | Sole value is JSON `true`. |
  | `RET-EVID-003::CITATION-SCHEMA-NULL-VALUE` | Sole value is JSON null. |
  | `RET-EVID-003::CITATION-SCHEMA-ARRAY-VALUE` | Sole value is JSON array `[]`. |
  | `RET-EVID-003::CITATION-SCHEMA-OBJECT-VALUE` | Sole value is JSON object `{}`. |
  | `RET-EVID-003::CITATION-SCHEMA-NONOBJECT-BODY` | Top-level JSON array containing one otherwise valid reference. |
  | `RET-EVID-003::CITATION-REFERENCE-MALFORMED-PREFIX` | Valid components follow prefix `citation:v1:` instead of exact `af3:citation:v1:`. |
  | `RET-EVID-003::CITATION-REFERENCE-UPPERCASE-UUID` | Only the embedded knowledge-base UUID contains uppercase hexadecimal. |
  | `RET-EVID-003::CITATION-REFERENCE-UNHYPHENATED-UUID` | Only the embedded chunk UUID omits hyphens. |
  | `RET-EVID-003::CITATION-REFERENCE-UPPERCASE-HASH` | Only the 64-hex hash uses uppercase `A`. |
  | `RET-EVID-003::CITATION-REFERENCE-SHORT-HASH` | Only the hash has 63 lowercase hexadecimal characters. |
  | `RET-EVID-003::CITATION-NONCANONICAL-PATH-UPPERCASE` | The route uses `123E4567-E89B-42D3-A456-426614174000`; exact media and body `C` are otherwise valid. |
  | `RET-EVID-003::CITATION-NONCANONICAL-PATH-UNHYPHENATED` | The route uses `123e4567e89b42d3a456426614174000`; exact media and body `C` are otherwise valid. |
  | `RET-EVID-003::CITATION-DATABASE-FAILURE` | All gates pass with valid `C`; the final authoritative PostgreSQL statement raises one injected database exception before any response value is published. |
- **Concurrent state change:** None.
- **Expected public result:** The supported-media and body-equality rows return
  HTTP `200`, the exact closed citation-resolution object from Test
  conventions, and private/no-store. Every authentication row returns the
  byte-identical generic `401 AUTHENTICATION_REQUIRED`, no citation/Evidence
  content, and private/no-store. Unsupported media, both overflow rows, and
  every strict-schema/reference row return the same generic
  `422 VALIDATION_ERROR`, no citation/Evidence content, and private/no-store.
  Both noncanonical-path rows return generic hidden `404 NOT_FOUND`, no
  citation content, and private/no-store. The database-failure row returns the
  byte-stable planned generic `503 RETRIEVAL_UNAVAILABLE`, no citation content,
  and private/no-store.
- **Expected internal validation result:** Success resolves the opaque cookie,
  authorizes the exact route target, incrementally bounds and validates the
  body, then starts one final `REPEATABLE READ`, `READ ONLY` PostgreSQL
  transaction. Its first statement fixes the snapshot, rechecks current
  session/user/target/access, compares exact current identity and persisted
  hash, and loads every response field. The body-equality row records 65,536
  octets and no truncation. Each auth failure has zero target/media/body/final-
  resolution calls after authentication. Unsupported media has zero body
  receive calls. Each overflow aborts on byte 65,537 with zero JSON/parser/
  schema/reference/final-SQL calls; the chunked row requests no event after
  its final one-byte chunk. Strict-schema rows reach only their named gate and
  have zero final-resolution SQL. Each noncanonical path stops after current
  authentication with zero exact-target SQL, redirect, media/body, or final-
  resolution work. The database-failure row rolls back the final transaction,
  publishes no partial field, exposes no exception detail, and performs no
  fallback. All rows have zero prohibited-work calls.
- **Forbidden behavior:** A second citation endpoint or token format; implicit
  request shape; trusting a cached/prebuilt Principal or any reference field
  as authentication, authorization, content, revision, or provenance;
  returning `404` for an initial auth row; target SQL, media validation, or
  body processing after failed authentication; body processing for
  unsupported media; rejecting equality; accepting/truncating plus one;
  unbounded materialization; JSON/schema work after overflow; coercion,
  aliases, extras, duplicate-key last-wins, or reference repair; a read-write
  or mixed-snapshot final resolution; echoing caller fields as authority;
  canonicalizing or redirecting a noncanonical path; leaking database failure
  detail or publishing a partial citation object;
  Provider/Chroma/embedding/keyword/candidate/RRF/storage/filesystem/cache
  fallback; dynamic hash; extra response field; missing private/no-store; or a
  general response-object secrecy exemption.
- **Planned test level:** PostgreSQL integration, HTTP integration.
  Every named row executes at both levels: the PostgreSQL level uses the
  request-gate harness against the real pool, and the HTTP level drives the
  actual ASGI route and receive stream.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-004 — Citation fails after stale hash

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation expects hash H1; current same-identity row has a different persisted hash H2.
- **Authenticated principal and membership state:** Live target member retains access.
- **Provider or Chroma input:** Exact HTTP request is
  `POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve`, where
  the canonical lowercase route UUID is the currently authorized target,
  `Content-Type: application/json`, and the strict sole-field body is
  `{"citation_reference":"af3:citation:v1:<route-target-UUID>:<current-chunk-UUID>:<H1>"}`.
  Authentication, target, media, bounded-body, JSON, schema, and syntax gates
  pass. All prohibited-work spies remain unused.
- **Concurrent state change:** Hash-changing authoritative update committed before resolution.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no old content, and private/no-store.
- **Expected internal validation result:** Final PostgreSQL resolution rechecks
  current session/user and exact-target access, then compares the current
  persisted H2 with H1 in one fixed read-only snapshot and fails closed. The
  caller's H1 supplies no revision authority.
- **Forbidden behavior:** Another method/route or request shape; resolving
  before the ordered gates; caller-reference authority; dynamic H1 recovery;
  silent rebinding to H2; current content or mismatch disclosure; Provider,
  embedding, keyword, candidate, RRF, storage, filesystem, cache, or alternate-
  token fallback; any response other than generic hidden `404`; or missing
  private/no-store.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-005 — Citation fails after chunk replacement

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation names old chunk O; current document contains replacement N.
- **Authenticated principal and membership state:** Live target member retains access.
- **Provider or Chroma input:** Exact HTTP request is
  `POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve` with O's
  canonical target as the lowercase route UUID, exact
  `Content-Type: application/json`, and strict sole-field body
  `{"citation_reference":"af3:citation:v1:<route-target-UUID>:<O-UUID>:<O-persisted-hash>"}`.
  Every pre-resolution gate passes; all prohibited-work spies remain unused.
- **Concurrent state change:** Transactional replacement committed before resolution.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no O content, and private/no-store.
- **Expected internal validation result:** Final fixed-snapshot PostgreSQL
  reauthorization succeeds, but the exact current eligible O identity/hash
  predicate returns no row; no caller field or N row supplies a response.
- **Forbidden behavior:** Another method/route/body; chunk-index rebinding;
  returning N under O's citation; returning O or replacement details;
  Provider/embedding/keyword/candidate/RRF/storage/filesystem/cache fallback;
  alternate token or hash repair; non-`404` public behavior; or missing
  private/no-store.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-006 — Citation fails after document deletion or ineligibility

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation initially points to a current eligible chunk.
- **Authenticated principal and membership state:** Live target member retains membership.
- **Provider or Chroma input:** Each parameter row calls exactly
  `POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve` with the
  canonical lowercase authorized target UUID, exact
  `Content-Type: application/json`, and a strict sole-field body whose
  `citation_reference` value is the prior syntactically canonical
  CitationReference. Every earlier gate passes; all prohibited-work spies
  remain unused.
- **Concurrent state change:** Parameterized document deletion or transition away from `completed` commits before resolution.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no citation content, and private/no-store.
- **Expected internal validation result:** In the final PostgreSQL snapshot,
  current session/user/target access reauthorization succeeds and the current
  document-existence/completed-state plus exact chunk/hash predicate fails
  closed for the named deletion or state transition.
- **Forbidden behavior:** Another method/route/body; stale cached resolution;
  deleted text or status disclosure; caller-reference authority; Provider,
  embedding, keyword, candidate, RRF, storage, filesystem, or alternate-token
  fallback; dynamic hashing; non-`404` public behavior; or missing private/no-
  store.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-007 — Citation reauthorization after membership revocation

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation target remains current and hashed; prior member has lost target membership.
- **Authenticated principal and membership state:** Live active user has no current target membership.
- **Provider or Chroma input:** The caller sends exactly
  `POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve`, using
  the citation's canonical lowercase target UUID in the route,
  `Content-Type: application/json`, and the strict sole-field body whose
  `citation_reference` value is the previously valid canonical
  CitationReference. All prohibited-work spies remain unused.
- **Concurrent state change:** Membership removal committed before citation resolution.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no citation content, and private/no-store.
- **Expected internal validation result:** Authentication remains current, but
  the exact-target authorization gate observes the committed membership loss
  and stops before media validation or body processing; body receive, parser,
  schema, final-resolution SQL, and prohibited-work call counts are zero.
- **Forbidden behavior:** Reading/parsing the body before hidden-target
  rejection; using prior access, citation possession, cache, or Provider state
  as authorization; distinguishable revocation detail; any public result other
  than generic hidden `404`; Provider/embedding/keyword/candidate/RRF/storage/
  filesystem/alternate-token work; or missing private/no-store.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-008 — Citation possession never authorizes a non-member

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Target B has a valid current citation and belongs
  to another user's private knowledge base. Target A is a distinct current
  knowledge base used only by the target-mismatch row.
- **Authenticated principal and membership state:** In the ordinary and hidden-
  precedence rows, the live caller has never had B membership. In
  `RET-EVID-008::CITATION-REFERENCE-TARGET-MISMATCH`, the live caller is a
  current member of route target A but has no B membership.
- **Provider or Chroma input:** Three independently executable HTTP rows use
  exactly `POST
  /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve`. The ordinary
  row uses B's canonical lowercase route UUID, exact
  `Content-Type: application/json` and a strict sole-field body whose
  `citation_reference` value is the exact B CitationReference. The
  `RET-EVID-008::CITATION-HIDDEN-TARGET-PRECEDENCE` row instead uses
  `Content-Type: text/plain` plus a malformed/oversized 65,537-byte body, so
  later media and body defects are independently observable if reached.
  `RET-EVID-008::CITATION-REFERENCE-TARGET-MISMATCH` uses A's canonical route,
  exact `Content-Type: application/json`, and a syntactically valid sole-field
  body whose `citation_reference` value is the B CitationReference.
  Provider, embedding, keyword, candidate, RRF, storage, and filesystem spies
  are configured and must remain unused.
- **Concurrent state change:** None.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no existence disclosure, and private/no-store.
- **Expected internal validation result:** In the first two rows, current
  authentication succeeds and exact-target B authorization fails before media
  validation or any application-body receive; both record zero media, body,
  parser, schema, final-resolution SQL, and prohibited-work calls. In the
  mismatch row, A authorization and bounded request validation succeed, but
  final PostgreSQL resolution remains exactly scoped to A, treats the embedded
  B values only as assertions, finds no match, and loads no B row or response
  field.
- **Forbidden behavior:** Reading or validating either body before exact-target
  rejection; returning `422` for the precedence row; switching final scope
  from route A to embedded target B; bearer-token semantics;
  foreign content; a distinguishable “valid but forbidden” response;
  Provider/embedding/keyword/candidate/RRF/storage/filesystem/cache/alternate-
  token work; any result other than generic hidden `404`; or missing private/
  no-store.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-009 — Citation expected hash is absent

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Two independently executable variants use
  `RET-EVID-009::AUTHORITATIVE-NULL-HASH`, a current legacy chunk whose
  persisted hash is null, and
  `RET-EVID-009::REFERENCE-MISSING-HASH-COMPONENT`, a current valid-hash chunk
  whose presented reference omits its required expected hash.
- **Authenticated principal and membership state:** Live target member retains access.
- **Provider or Chroma input:** Each request calls exactly
  `POST /api/v1/knowledge-bases/{knowledge_base_id}/citations/resolve` with the
  canonical lowercase authorized target UUID and exact
  `Content-Type: application/json`. The authoritative-null-hash body's strict
  sole `citation_reference` field contains a syntactically canonical
  CitationReference with the current chunk UUID and an arbitrary valid
  64-lowercase-hex expected hash; no null-hash token or alternate format is
  invented. The missing-component body's sole `citation_reference` field
  contains the otherwise matching reference with the final
  `:<content_sha256>` component omitted. All prohibited-work spies remain
  unused.
- **Concurrent state change:** None.
- **Expected public result:** The authoritative-null-hash row returns generic
  hidden `404 NOT_FOUND`; the missing-component row returns generic
  `422 VALIDATION_ERROR`. Both
  return no citation content and private/no-store.
- **Expected internal validation result:** The authoritative-null-hash row passes request syntax and
  final PostgreSQL resolution finds no eligible row because the authoritative
  hash is null. The missing-component row fails CitationReference syntax after bounded strict
  schema validation and performs zero final-resolution SQL. Neither variant
  creates or repairs a hash.
- **Forbidden behavior:** A null-hash or incomplete alternate token; mapping
  the malformed missing-component row to final `404`; hashing current text; substituting UUID/
  timestamp; returning content; repairing the reference; caller authority;
  Provider/embedding/keyword/candidate/RRF/storage/filesystem/cache fallback;
  an extra response field; or missing private/no-store.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-010 — Valid IDs all become PostgreSQL-ineligible

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Target access is current; canonical candidates are unknown, null-hash, stale, or attached to non-completed documents at final snapshot.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** Structurally valid bounded canonical IDs.
- **Concurrent state change:** Ineligibility is committed before snapshot acquisition.
- **Expected public result:** Authorized empty Evidence and private/no-store.
- **Expected internal validation result:** Final PostgreSQL validation returns no eligible authoritative record without public reasons.
- **Forbidden behavior:** `404` for candidate state, `503`, provider content, or invented revisions.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## AF-3 untrusted-evidence boundary

### RET-INJ-001 — “Ignore previous instructions” remains data

- **Category:** AF-3 untrusted-evidence boundary.
- **Initial database state:** Eligible hashed chunk contains an “ignore previous instructions” directive.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Valid bounded candidate for the chunk.
- **Concurrent state change:** None.
- **Expected public result:** Text appears only inside Evidence labeled `untrusted_document_content`.
- **Expected internal validation result:** Retrieval constructs data fields only and preserves authoritative provenance independently.
- **Forbidden behavior:** Trusted instruction creation, authorization/scope change, provider reconfiguration, or execution object.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-INJ-002 — Fake system and developer messages create no trusted fields

- **Category:** AF-3 untrusted-evidence boundary.
- **Initial database state:** Eligible chunks imitate system and developer messages.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Valid bounded candidates for both chunks.
- **Concurrent state change:** None.
- **Expected public result:** Both contents remain quoted untrusted Evidence with no system/developer field.
- **Expected internal validation result:** AF-3 output schema has only the explicit untrusted-content channel.
- **Forbidden behavior:** Prompt construction, role-message conversion, precedence assignment, or claims about ChatModel behavior.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-INJ-003 — Content cannot alter authorization or target scope

- **Category:** AF-3 untrusted-evidence boundary.
- **Initial database state:** Eligible A chunk instructs retrieval from B and claims extra membership.
- **Authenticated principal and membership state:** Live caller requests A; B is outside this request.
- **Provider or Chroma input:** Valid A candidate plus attempted B scope text.
- **Concurrent state change:** None.
- **Expected public result:** Only A-scoped untrusted Evidence.
- **Expected internal validation result:** Principal, exact target, SQL predicates, and provider request scope derive independently of content.
- **Forbidden behavior:** Querying B, changing membership/capability, accepting B candidates, or content-derived authorization fields.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-INJ-004 — Content creates no tool, approval, or secret-access object

- **Category:** AF-3 untrusted-evidence boundary.
- **Initial database state:** Eligible chunks name tools/arguments, claim approval, and request session/database/provider secrets.
- **Authenticated principal and membership state:** Live target member has retrieval read access only.
- **Provider or Chroma input:** Valid bounded candidates for the adversarial chunks.
- **Concurrent state change:** None.
- **Expected public result:** Quoted untrusted Evidence only; no secret or execution/approval representation.
- **Expected internal validation result:** AF-3 retrieval output contains no Tool Policy, tool name/argument, execution, approval, or secret-access object.
- **Forbidden behavior:** Tool selection/configuration, approval creation/bypass, secret lookup, or claims that nonexistent runtime consumers were tested.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-INJ-005 — Citation and provenance ignore document instructions

- **Category:** AF-3 untrusted-evidence boundary.
- **Initial database state:** Eligible malicious chunk claims a false source, hash, citation, and authority while having current authoritative provenance.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Valid candidate with matching adversarial provider metadata.
- **Concurrent state change:** None.
- **Expected public result:** Evidence contains the claim only as untrusted content; citation/provenance use only PostgreSQL values.
- **Expected internal validation result:** Citation identity, expected hash, display source, and offsets are content-independent.
- **Forbidden behavior:** Content/provider-defined citation, valid-citation-as-instruction-authority, or provenance override.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-INJ-006 — Obfuscated or first-ranked instruction stays untrusted

- **Category:** AF-3 untrusted-evidence boundary.
- **Initial database state:** Eligible hashed chunk contains encoded/confusable instructions and another benign chunk exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded ranks place the adversarial chunk first after deterministic RRF.
- **Concurrent state change:** None.
- **Expected public result:** First item remains `untrusted_document_content`; ordering and provenance remain deterministic.
- **Expected internal validation result:** Trust classification is invariant to content recognition, decoding, citation validity, and rank.
- **Forbidden behavior:** Decoding into trusted instructions, rank-based elevation, policy/scope change, or suppression of provenance.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Privacy, public errors, and cache behavior

### RET-PRIV-001 — Raw query absent from every success sink

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** Authorized target has eligible content and the
  complete shared all-sink capture is active before request entry.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded valid response; query contains a unique high-entropy sentinel.
- **Concurrent state change:** None.
- **Expected public result:** Exact bounded nonempty Evidence success and
  private/no-store; raw and normalized query sentinels are absent from every
  response field, header, and metadata value.
- **Expected internal validation result:** The shared recursive exact-plus-
  substring scanner covers every named sink and permits only bounded content-
  free telemetry. Raw and normalized query values are distinct sentinels and
  have no allowlisted public field.
- **Forbidden behavior:** Either query sentinel in any application/access/
  exception record, structured key or nested value, trace/span name/
  attribute/event, HTTP/Provider transport diagnostic, SQL/database/driver
  diagnostic, response metadata/header/body field, byte string, or rendered
  representation; a partial sink list; or a response-object exemption.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-002 — Evidence content is allowlisted only at its public field

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** Eligible authoritative content contains a unique sentinel.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Valid candidate for the sentinel chunk.
- **Concurrent state change:** None.
- **Expected public result:** Authorized Evidence contains the content
  sentinel exactly at the Evidence `content` field and private/no-store. It
  occurs in no other response path or metadata.
- **Expected internal validation result:** The shared recursive scanner scans
  all sinks including the response, exempts the content sentinel only at the
  exact `content` value path, and rejects its exact or substring occurrence
  everywhere else. A negative-control sink injector places the same sentinel
  in a success-only span event and proves the scanner fails.
- **Forbidden behavior:** Exempting the Evidence object or response body as a
  whole; content in a key, unexpected field, header, diagnostic, log,
  exception, trace/span, transport, SQL/driver record, or Provider dump;
  omitting substring scans; or a scanner that runs only on failure.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-003 — Every private success uses field-specific all-sink secrecy

- **Category:** Privacy, public errors, and cache behavior. This stable case
  owns `RET-PRIV-003::RETRIEVAL-EVIDENCE-SUCCESS-ALL-SINK-SECRECY`,
  `RET-PRIV-003::RETRIEVAL-EMPTY-SUCCESS-ALL-SINK-SECRECY`, and
  `RET-PRIV-003::CITATION-RESOLUTION-SUCCESS-ALL-SINK-SECRECY`.
- **Initial database state:** A deterministic sentinel factory creates
  pairwise-distinct non-containing values for raw/normalized query,
  authoritative content, target/document/chunk/user/session IDs, persisted
  hash, approved display filename, filesystem/object-storage paths,
  session/CSRF digests, database credential, secret/token, exact citation
  reference, raw embedding, bounded raw Provider body, Provider diagnostic,
  and exposed SQL/database/driver/transaction diagnostic. Success-only
  Evidence and citation sentinels are loaded only after final successful
  PostgreSQL authorization so a leak conditional on success is observable.
- **Authenticated principal and membership state:** A live target member uses
  the retrieval route for the first two variants and the exact citation route,
  media, and sole-field body for the third.
- **Provider or Chroma input:** Nonempty retrieval uses a valid bounded
  response containing an ignored raw-body sentinel and the exact fake
  embedding vector. Empty retrieval uses the canonical present-empty response
  and valid empty keyword result. Citation resolution makes zero Provider,
  embedding, or keyword calls.
- **Concurrent state change:** None.
- **Expected public result:** Nonempty retrieval exposes sentinels only at
  their intended Evidence fields; empty retrieval returns the exact empty
  Evidence shape with no sensitive sentinel; citation resolution exposes
  values only in the exact closed success object. Every row is HTTP `200` and
  private/no-store. No path, secret, embedding, raw payload, or diagnostic is
  public.
- **Expected internal validation result:** Before each request, the harness
  registers every sink in Test conventions. The recursive scanner checks
  nested keys and values, bytes, exception forms, and rendered strings for
  exact and substring matches. The field allowlist is exact:

  | Sensitive class | Only permitted retrieval response fields | Only permitted citation response fields |
  | --- | --- | --- |
  | target UUID | `knowledge_base_id`; substring within `citation_reference` | `knowledge_base_id`; substring within `citation_reference` |
  | document UUID | `document_id` | `document_id` |
  | chunk UUID | `chunk_id`; substring within `citation_reference` | `chunk_id`; substring within `citation_reference` |
  | authoritative content | `content` | `content` |
  | persisted hash | `content_sha256`; substring within `citation_reference` | `content_sha256`; substring within `citation_reference` |
  | approved display filename | `source_display_name` | `source_display_name` |
  | page/character provenance | its exact named provenance field | its exact named provenance field |
  | complete CitationReference | `citation_reference` | `citation_reference` |
  | trust literal | `trust_classification` | `trust_classification` |

  No other sentinel has an allowlisted response path. A mutation-control
  matrix injects each success-only sentinel, one sink class at a time, into an
  application log, access log, nested structured key/value, exception record,
  span name/attribute/event, HTTP diagnostic, Provider record, SQL/driver
  diagnostic, response header/metadata, and unexpected response field; every
  injection must make the scanner fail. The unmodified executions pass.
- **Forbidden behavior:** Treating the whole response/Evidence/citation object
  as exempt; allowing a value at the wrong field; exempting headers, metadata,
  diagnostics, or transport state; omitting empty retrieval or citation
  success; running only a normal-log or fatal-path scan; omitting a sentinel,
  sink, structured key, nested value, exception form, exact comparison, or
  substring comparison; any path/secret/embedding/raw-body/diagnostic leak;
  or prohibited work during citation resolution.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-004 — Stable provider/database all-sink error envelope

- **Category:** Privacy, public errors, and cache behavior. This parent owns
  the independently executable ADR-008-R24 fatal-path secrecy variants.
- **Initial database state:** Caller and target pass initial authorization. A
  deterministic sentinel factory constructs pairwise-distinct, high-entropy
  values whose byte strings do not contain one another. The controlled
  fixture inputs, eligible records, and bounded request/client context assign
  one unique sentinel to each sensitive class: raw query; normalized query;
  authoritative Evidence text;
  knowledge-base UUID; document UUID; chunk UUID; user UUID; session ID;
  citation ID; filesystem path; object-storage path; database credential;
  secret/token; bounded raw Provider response body; and bounded Provider
  diagnostic or exception-detail context. UUID sentinels are valid,
  class-distinct UUIDs. The raw-query fixture uses decomposed Unicode and
  repeated exact-set whitespace so its strict input bytes and resulting NFC,
  trimmed, collapsed normalized-query bytes are distinct and neither complete
  sentinel string contains the other. Each database-failure variant also
  constructs distinct later database-exception detail, driver-diagnostic
  detail, and transaction-diagnostic detail sentinels; a diagnostic category
  is captured when that boundary exposes it to the harness. The later-batch
  variant has every sensitive class in live request/client context and has
  loaded the Evidence and identifying classes into accumulated batch-1 state
  before batch 2 fails. Earlier fatal variants retain their sentinels only in
  inputs and context reachable before their named failure; they do not claim
  that final Evidence loaded before the Provider or keyword stage.
- **Authenticated principal and membership state:** A live active target
  member has a current session. Authentication, canonical path parsing,
  exact-target authorization, exact request-media validation, and strict body
  validation succeed before each named fatal branch.
- **Provider or Chroma input:** The four rows below are separate constructible
  executions. All non-Provider-fatal rows use a successful bounded canonical
  Provider response and successful Provider parsing. That response carries
  the raw-body sentinel in one bounded, cardinality-aligned unsolicited
  `documents` string that the adapter must ignore, and the controlled mock
  client places the Provider-diagnostic sentinel in its bounded diagnostic
  context before returning the response. Provider-related sentinels therefore
  remain in the earlier adapter/client context so an unsafe later context dump
  is observable without a simultaneous Provider failure.

  | Stable variant label | Exact failure fixture and execution stage |
  | --- | --- |
  | `RET-PRIV-004::PROVIDER-FATAL-ALL-SINK-SECRECY` | Scoped keyword SQL first returns a known eligible nonempty keyword sentinel. The bounded Provider branch then raises its injected Provider-fatal exception containing the Provider-detail sentinel. |
  | `RET-PRIV-004::KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY` | The canonical Provider first returns a known eligible nonempty dense sentinel. Scoped keyword SQL then raises its injected database exception containing the database and exposed driver diagnostics. |
  | `RET-PRIV-004::FINAL-COMMIT-ALL-SINK-SECRECY` | Keyword and Provider work succeed; final authorization and every required validation batch load known eligible keyword and dense sentinels. The actual final transaction commit then raises its injected commit exception containing the database and exposed transaction diagnostics. |
  | `RET-PRIV-004::LATER-BATCH-ALL-SINK-SECRECY` | Valid bounded source maps contain 65 dense identities and 64 disjoint keyword identities, giving sorted union `U = 129`, batch size `B = 64`, and required query count `Q = 3`. Final connection acquisition and fixed-snapshot authorization succeed. Batch 1 succeeds and loads 64 PostgreSQL-authoritative records, including accumulated Evidence and identifying sentinels. Validation batch 2 raises its injected database exception containing the later-batch database, exposed driver, and exposed transaction diagnostics. A statement-ordinal ledger distinguishes this validation-query failure from initial connection, first-batch, and final-commit failures; planned batch 3 and commit each have zero calls. |

- **Concurrent state change:** None. Each execution has exactly one injected
  fatal branch. The later-batch execution uses deterministic statement
  ordinals and call ledgers, with no timing race and no concurrent mutation.
- **Expected public result:** Every execution returns exactly the byte-stable
  generic planned `503 RETRIEVAL_UNAVAILABLE` envelope and
  `Cache-Control: private, no-store`. The response contains zero Evidence,
  zero citation content, zero partial result, zero fallback result, zero
  Provider raw body, zero Provider exception detail, zero database exception
  detail, and none of the query, ID, path, credential, secret/token, content,
  driver, or transaction sentinels.
- **Expected internal validation result:** Before each execution, the harness
  invokes the same shared success/failure scanner from Test conventions and
  captures ordinary log message text; structured log keys and values; access
  logs; exception and error logs; trace and span names, attributes, events,
  and status descriptions; HTTP client logs; HTTP transport logs; database
  client and driver diagnostics exposed to the harness; captured exception
  objects and their string and `repr` representations; and response status,
  metadata, headers, and body. The scanner walks every nested key,
  value, sequence member, byte string, exception representation, and larger
  rendered string. For every sink and every sentinel, both exact equality and
  substring presence are deterministic failures. Only the normalized
  content-free failure classification is permitted. The Provider-fatal
  execution discards the keyword sentinel. The keyword/database-fatal
  execution discards the dense sentinel. The final-commit execution publishes
  nothing before commit success, then discards all loaded records. The
  later-batch execution proves batch 1 loaded sensitive authoritative state,
  records batch 2 as the sole failure, rolls back the final transaction,
  discards every accumulated record, makes zero batch-3 calls, makes zero
  commit calls, performs no fusion or response publication, and never
  continues with the 64 earlier records.
- **Forbidden behavior:** Treating success-path secrecy as fatal-path
  coverage; using the broad parent case without executing each stable label;
  omitting a sentinel class, sink class, structured key, nested value,
  exception representation, response metadata field, or substring scan; any
  sentinel, stack trace, SQL/Provider/database detail, raw payload, partial
  Evidence, citation, stale cache, or alternate successful response;
  keyword-only fallback after Provider failure; dense-only fallback after
  keyword/database failure; publication before final commit; retaining batch
  1 records after the later-batch failure; running batch 3; running final
  commit; or requiring Provider failure and later-batch database failure to be
  the same trigger.
- **Planned test level:** Provider-fatal secrecy is independently executable
  at provider-adapter contract, PostgreSQL integration, and HTTP integration.
  Keyword/database-fatal, final-commit, and later-batch secrecy are each
  independently executable at PostgreSQL integration and HTTP integration.
  These label-specific capable levels preserve the stable ID's existing level
  classification.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-005 — Every reachable private response is no-store

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** Separate reachable fixtures produce authorized
  Evidence, authorized empty retrieval, successful citation resolution,
  invalid request/body overflow, invalid authentication, hidden target,
  provider failure, and citation database failure.
- **Authenticated principal and membership state:** State varies lawfully per fixture; no impossible retrieval `403` state is invented.
- **Provider or Chroma input:** Valid, empty, or fatal bounded retrieval
  fixture as appropriate; citation rows use the exact public citation request
  and make no Provider call.
- **Concurrent state change:** None.
- **Expected public result:** Each `200`, `401`, `404`, `422`, and planned `503` response has exactly `Cache-Control: private, no-store`.
- **Expected internal validation result:** Central private-response boundary
  covers every future retrieval and citation-resolution path.
- **Forbidden behavior:** Shared/public caching, missing directive, stale private reuse, or a fabricated current `403` fixture.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-006 — Telemetry batching fields are bounded and content-free

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** Authorized target has several batches of eligible chunks.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded keyword/dense candidates span several batches with some local omissions.
- **Concurrent state change:** None.
- **Expected public result:** Normal bounded Evidence.
- **Expected internal validation result:** Telemetry may include provider, elapsed time, requested limit, bounded counts, batch size/query count, rejection/return counts, correlation ID, and normalized status only.
- **Forbidden behavior:** Raw query, Evidence content, IDs, filenames, citation, raw payload, or unbounded labels.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Future consuming-phase obligations

These cases are required when their consumers are introduced. They are not
claims about AF-3C and do not block AF-3 before the named consumer exists. The
consumer's approved phase must refine the fixture without weakening the
forbidden behavior.

### RET-FUT-001 — Later RAG/prompt construction preserves evidence trust

- **Category:** Future consuming-phase obligation.
- **Initial database state:** Eligible authoritative chunk contains adversarial instructions and a valid persisted hash.
- **Authenticated principal and membership state:** Live authorized target member.
- **Provider or Chroma input:** Valid AF-3 Evidence fixture labeled `untrusted_document_content`.
- **Concurrent state change:** None.
- **Expected public result:** The later RAG response does not represent document text as trusted system/developer policy.
- **Expected internal validation result:** Prompt construction uses an explicit untrusted-evidence channel defined by that later phase.
- **Forbidden behavior:** Trusted-role concatenation, scope elevation, or claiming AF-3C already tested this consumer.
- **Planned test level:** future consuming-phase acceptance.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-FUT-002 — Later ChatModel consumer cannot elevate Evidence

- **Category:** Future consuming-phase obligation.
- **Initial database state:** Eligible adversarial Evidence includes secret and policy override requests.
- **Authenticated principal and membership state:** Live authorized target member.
- **Provider or Chroma input:** Valid AF-3 Evidence fixture and deterministic fake ChatModel defined by the later phase.
- **Concurrent state change:** None.
- **Expected public result:** Consumer output cannot establish authorization, secret access, or trusted instruction authority from Evidence.
- **Expected internal validation result:** Later ChatModel boundary preserves trust classification and explicit instruction precedence.
- **Forbidden behavior:** Treating cited/relevant text as policy or claiming current AF-3 ChatModel execution.
- **Planned test level:** future consuming-phase acceptance.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-FUT-003 — Later Agent Runtime cannot derive authority from Evidence

- **Category:** Future consuming-phase obligation.
- **Initial database state:** Eligible Evidence asks the future runtime to widen scope and execute an action.
- **Authenticated principal and membership state:** Live authorized target member with no extra authority.
- **Provider or Chroma input:** Valid AF-3 Evidence fixture passed to a deterministic later runtime.
- **Concurrent state change:** None.
- **Expected public result:** Runtime outcome remains within independently authorized scope and budgets.
- **Expected internal validation result:** Runtime treats Evidence as observation data, never identity, policy, or approval.
- **Forbidden behavior:** Content-derived scope, permission, execution budget, or claim that Agent Runtime exists in AF-3.
- **Planned test level:** future consuming-phase acceptance.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-FUT-004 — Later tool consumer cannot create or approve an action from Evidence

- **Category:** Future consuming-phase obligation.
- **Initial database state:** Eligible Evidence names a future tool, attacker arguments, and a fake approval.
- **Authenticated principal and membership state:** Live authorized target member without content-derived tool authority.
- **Provider or Chroma input:** Valid AF-3 Evidence fixture passed to the later tool-consuming phase.
- **Concurrent state change:** None.
- **Expected public result:** No action executes unless independently resolved, authorized, policy-checked, and approved by that phase.
- **Expected internal validation result:** Tool identity/arguments and approval state originate outside Evidence and traverse the required executor/policy path.
- **Forbidden behavior:** Evidence-created tool call, approval bypass, secret access, or claim that AF-3 tests tool execution.
- **Planned test level:** future consuming-phase acceptance.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## ADR requirement-to-case traceability

The ADR's runtime security requirements map as follows. Governance sequencing
and the no-production-readiness statement are non-runtime review gates in
ADR-008 and `roadmap.md`; they are deliberately not assigned to a test level
that cannot observe them.

| ADR requirement | Stable acceptance cases |
| --- | --- |
| ADR-008-R01 — Exactly two strict public shapes, shared bounded body, decoded-query domain/normalization/count contract, ordered live-session authentication, exact target, and no client-ID authorization | Retrieval matrix `RET-AUTH-001::UNAUTHENTICATED-PRECEDENCE`, `RET-AUTH-005::HIDDEN-TARGET-PRECEDENCE`, and all RET-BND-003 stable variants, including exact/plus-one/chunked body rows and the distinct literal-NUL/escaped-U+0000 gate and precedence rows; every individually named public-operation variant in RET-EVID-003 plus `RET-EVID-008::CITATION-HIDDEN-TARGET-PRECEDENCE` and `RET-EVID-008::CITATION-REFERENCE-TARGET-MISMATCH`; U+0000 rejection, adjacent-U+0001 preservation, and normalization/scalar variants in RET-BND-001; UTF-8 domain in RET-BND-002; RET-AUTH-002 through RET-AUTH-011 for remaining authentication/scope branches |
| ADR-008-R02 — Initial request/database work ends before embedding; no request-owned transaction, connection, Session, or SessionTransaction spans embedding or Chroma; failure/cancellation cleanup precedes final work | RET-AUTH-001, RET-AUTH-011; `RET-CONC-001::EMBEDDING-LIFECYCLE-SUCCESS`; `RET-CONC-001::EMBEDDING-LIFECYCLE-FAILURE`; `RET-CONC-001::EMBEDDING-LIFECYCLE-CANCELLATION`; `RET-CONC-001::CHROMA-LIFECYCLE-REVOCATION`; RET-CONC-002 through RET-CONC-003 |
| ADR-008-R03 — Actual final request transaction is fixed `REPEATABLE READ` and `READ ONLY`, with first-statement reauthorization | RET-CONC-001 (the actual first final retrieval authorization query or order-preserving same-transaction hook proves both settings in the real request), RET-CONC-002 through RET-CONC-003, RET-CONC-012, and RET-EVID-003 success/failure rows for the citation final transaction and first-statement recheck; never a helper, mutation actor, or unrelated session |
| ADR-008-R04 — Same snapshot for all batches and every authoritative Evidence/citation field | RET-CONC-006 through RET-CONC-010, RET-EVID-001, RET-EVID-003 |
| ADR-008-R05 — Request linearization and revocation timing | RET-CONC-001 through RET-CONC-009 |
| ADR-008-R06 — All-or-nothing transaction failure | RET-CONC-011, RET-PRIV-004 |
| ADR-008-R07 — PostgreSQL authority for identity, scope, state, content, hash, source/provenance, and every citation-resolution field | RET-AUTH-007 through RET-AUTH-009, RET-PROV-030 through RET-PROV-031, RET-PROV-033 through RET-PROV-037, RET-KEY-001 through RET-KEY-004, RET-EVID-001 through RET-EVID-010, especially the exact public citation operation and current authoritative resolution in RET-EVID-003 through RET-EVID-009 |
| ADR-008-R08 — Completed status plus persisted non-null valid hash | RET-KEY-001, RET-EVID-002, RET-EVID-009, RET-EVID-010 |
| ADR-008-R09 — Exact citation operation, current reauthentication/target authorization, authoritative revision binding, and non-bearer reference | RET-EVID-003 through RET-EVID-009, including each named citation HTTP precedence/body/schema variant |
| ADR-008-R10 — Canonical pinned bounded Chroma version/query contract, exact single embedding payload, and no Provider authority | RET-AUTH-009, RET-CONC-001 embedding variants, RET-PROV-016 through RET-PROV-022, RET-PROV-023 through RET-PROV-031, RET-PROV-035 through RET-PROV-036, RET-PROV-040 exact configured-dimension vector/payload oracle, RET-KEY-002, RET-EVID-001 |
| ADR-008-R11 — Version/query inclusive wire/decode ceilings, exact field/metadata grammar and bounds, and exact depth counting | All named positive grammar variants in RET-PROV-001 paired with RET-PROV-010 through RET-PROV-013 and every named negative grammar branch in RET-PROV-016; RET-PROV-002 through RET-PROV-009; RET-PROV-014; every bounded version variant in RET-PROV-020 |
| ADR-008-R12 — Strict UTF-8/RFC 8259 and unsupported-range numeric failures, canonical response-fatal taxonomy, version/missing-field fatality, independent Provider outage branches, and no fallback | RET-PROV-003 through RET-PROV-006, RET-PROV-009 through RET-PROV-014, RET-PROV-015 (fully canonical literal `NaN`, `Infinity`, and `-Infinity` wire failures plus valid-JSON `1e400` finite-domain failure), RET-PROV-016 (encoding/unknown/duplicate/null/return-field policy), RET-PROV-017 (every missing required key), RET-PROV-018 through RET-PROV-022 (configured count, version probe, position, connection, timeout), RET-BND-007, RET-CONC-011, RET-PRIV-004 |
| ADR-008-R13 — Position-preserving candidate-local taxonomy and authorized empty | RET-PROV-008, RET-PROV-025 through RET-PROV-038 (including missing and non-string ID variants), RET-EVID-010 |
| ADR-008-R14 — Finite wire-distance domain, typed diagnostic `None`, post-decoder typed non-finite/wrong-type omission, absolute-position preservation, and ignored bounded disagreement | RET-PROV-015, RET-PROV-023 through RET-PROV-024, RET-PROV-025 through RET-PROV-026 (`float("nan")`, `float("inf")`, and `float("-inf")` at exact rank 2 with valid ranks 1/3), RET-PROV-027 (string/object/boolean/null/array matrix at exact rank 2), RET-PROV-028 (mixed absolute ranks), RET-PROV-030 through RET-PROV-031, RET-PROV-038 |
| ADR-008-R15 — Duplicate earliest-rank behavior | RET-PROV-039, RET-BND-013, RET-RANK-003 |
| ADR-008-R16 — Exact body/decoded-query/request/configured-Provider/raw-position/dense/keyword/union/batch/final-result domains and bounded SQL work | RET-BND-001 through RET-BND-003, including the U+0000 exclusion, adjacent-U+0001 control, distinct raw/escaped JSON paths, and 65,536/65,537 body rows; RET-EVID-003 citation body rows; RET-BND-004 through RET-BND-015; RET-PROV-002 through RET-PROV-007; all four RET-PROV-019 C40/C128 equality/plus-one rows; RET-KEY-001 |
| ADR-008-R17 — Scoped deterministic PostgreSQL keyword rank generation and internal-path exclusion | RET-KEY-001 (scoped deterministic score, total order, and one-based ranks), RET-KEY-002 through RET-KEY-004 |
| ADR-008-R18 — Deterministic union, batching, non-rank-bearing permutations, query count, reconstruction, and independent failure branches | RET-BND-008 through RET-BND-015 (especially RET-BND-012's byte-identical source lists/rank maps), RET-CONC-010, RET-CONC-011 |
| ADR-008-R19 — Exact rational RRF, absolute source-rank prerequisites, earliest-rank preservation, display serialization, and tie-breaking | RET-KEY-001 (deterministic keyword source ranks), RET-PROV-025 through RET-PROV-028 (dense invalid-position ranks remain 1/3 and 1/3/5/7), RET-PROV-038 (valid companion retains original position), RET-PROV-039 (earliest dense rank/contribution), RET-BND-013 (earliest ranks across duplicates), RET-RANK-001 through RET-RANK-005 (exact rational formula, mixed sources, collision, full tie order) |
| ADR-008-R20 — Explicit PostgreSQL-authoritative versus deterministic-derived Evidence partitions, trust class, and excluded data | RET-EVID-001 (field-by-field authority/derivation oracle), RET-EVID-002 through RET-EVID-010, RET-RANK-001 through RET-RANK-005, RET-INJ-001 through RET-INJ-006, RET-PRIV-002, RET-PRIV-003 |
| ADR-008-R21 — P0 AF-3 semantic injection boundary | RET-INJ-001 through RET-INJ-006 |
| ADR-008-R22 — Later consumer-specific acceptance | RET-FUT-001 through RET-FUT-004 |
| ADR-008-R23 — Public errors, valid present-empty behavior, authorized empty, no synthetic `403`, and cache | RET-AUTH-004, RET-AUTH-005, RET-AUTH-010 (present-empty provider response), RET-AUTH-011, RET-CONC-011, RET-BND-008 (present-empty dense source and zero union), RET-PRIV-004, RET-PRIV-005 |
| ADR-008-R24 — Same recursive exact/substring all-sink scanner on success/failure with field-specific public allowlists and bounded telemetry | RET-PRIV-001; RET-PRIV-002; all three success-only variants in RET-PRIV-003 plus the mandatory scanner wrapper on every successful HTTP case; all four fatal variants in RET-PRIV-004; RET-PRIV-006 |
| ADR-008-R25 — P0 response/trust controls remain distinct from P1 hardening | RET-PROV-006, RET-PROV-010, RET-INJ-001 through RET-INJ-006, RET-FUT-001 through RET-FUT-004 |

This matrix covers initial authorization, final snapshot authorization,
revocation timing, fixed snapshots, candidate parsing, cross-scope rejection,
provider body limits and taxonomy, request/result limits, SQL batch bounds,
keyword SQL scope, null-hash exclusion, Evidence trust classification,
citation reauthorization, RRF determinism, provider outage, no fallback, cache
control, privacy logging, and P0 injection-evidence handling.

## Suite acceptance rule

All 109 AF-3 runtime cases from `RET-AUTH-001` through `RET-PRIV-006` must be
implemented and pass at every listed level before AF-3 is complete. The four
cases `RET-FUT-001` through `RET-FUT-004` are mandatory additions for their
later consuming phases and are not AF-3C runtime claims.

A documentation review does not satisfy a runtime case. Any change to a stable
ID, expected result, trust decision, limit profile, taxonomy, transaction
linearization rule, test level, or trace mapping requires explicit review.
Passing this suite would complete AF-3's defined retrieval gate only; it would
not establish complete security, complete prompt-injection prevention,
complete hostile-document containment, or production readiness.
