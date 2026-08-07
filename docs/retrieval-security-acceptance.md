# AF-3 retrieval security acceptance specification

## Status and purpose

This is the required executable-test specification for ADR-008. AF-3A-01
through AF-3A-05 are implemented and merged, all 115 AF-3A canonical rows have
closure-compatible executable evidence, and AF-3A is `CLOSED`. The AF-3B entry
gate is satisfied, but AF-3B implementation has not started. AF-3C remains
`BLOCKED` until AF-3B is `CLOSED`. No AF-3B dense retrieval or fusion, or AF-3C
public Evidence, Citation, or HTTP retrieval behavior, is claimed.

The stable-ID inventory is the set of the 118 RET case headings below. It
contains 114 AF-3 runtime IDs and four future consuming-phase IDs. The heading
inventory, canonical ledger, and 27 ADR requirement mappings are parsed
independently; every ledger case ID must resolve to one heading.

| Category | Stable IDs | Count |
| --- | --- | ---: |
| Authentication and request scope | RET-AUTH-001–RET-AUTH-011 | 11 |
| Final transaction and concurrency | RET-CONC-001–RET-CONC-014 | 14 |
| Provider transport, decoding, and taxonomy | RET-PROV-001–RET-PROV-043 | 43 |
| Request, result, union, and SQL bounds | RET-BND-001–RET-BND-015 | 15 |
| Keyword SQL scope | RET-KEY-001–RET-KEY-004 | 4 |
| RRF and result determinism | RET-RANK-001–RET-RANK-005 | 5 |
| Evidence, eligibility, and citations | RET-EVID-001–RET-EVID-010 | 10 |
| AF-3 untrusted-evidence boundary | RET-INJ-001–RET-INJ-006 | 6 |
| Privacy, public errors, and cache behavior | RET-PRIV-001–RET-PRIV-006 | 6 |
| **AF-3 runtime total** | All nine runtime categories | **114** |
| Future consuming-phase obligations | RET-FUT-001–RET-FUT-004 | 4 |
| **Complete inventory** | Runtime plus future | **118** |

### Canonical acceptance identity model

The canonical identity is exactly (Case ID, Variant, Test level). The
canonical ledger below is the sole ownership, execution-boundary, status, and
oracle source of truth. Every row has one finite owner, one finite execution
boundary, one finite status, and one case-local oracle. Case prose and family
summaries describe fixtures but cannot add a level, transfer ownership, merge
oracles, or override a row.

The finite test-level vocabulary is unit, provider-adapter contract,
PostgreSQL integration, deterministic concurrency, fault injection, HTTP
integration, and future consuming-phase acceptance. The finite owner
vocabulary is AF-3A, AF-3B, AF-3C, and FUTURE. The finite status vocabulary is
MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE and
REQUIRED_NOT_YET_IMPLEMENTED.

| Execution boundary | Exact meaning |
| --- | --- |
| PURE_REQUEST_VALIDATOR | Pure request parsing, decoded-query validation, normalization, and scalar/count bounds; no database or external adapter. |
| AF3A_INITIAL_ACCESS | Proof-aware live session, active user, exact target, membership, and capability access before retrieval work. |
| AF3A_KEYWORD | Scoped deterministic PostgreSQL keyword operation, including release before external I/O. |
| AF3A_FINAL_VALIDATOR | First provider-independent final RR/RO validator/loader using zero, keyword, or explicit bounded synthetic candidates. |
| AF3A_CONCURRENCY | Provider-independent clock, barrier, fixed-snapshot, batch, commit, deletion, and concurrency behavior. |
| AF3B_EMBEDDING | One bounded embedding operation and its response/failure contract. |
| AF3B_CHROMA_ADAPTER | Read-only Chroma compatibility/query, bounded Provider response, taxonomy, and adapter lifetime. |
| AF3B_HYBRID_FUSION | Bounded dense/keyword union and deterministic exact fusion. |
| AF3B_HYBRID_REGRESSION | A distinct AF-3B hybrid regression through an AF-3A prerequisite; it never transfers the prerequisite row. |
| AF3C_HTTP | Request wire/media/routes, public errors, cache behavior, HTTP integration, or public all-sink behavior. |
| AF3C_PUBLIC_EVIDENCE | AF-3C-only public Evidence schema, mapping, serialization, or public Evidence privacy. |
| AF3C_PUBLIC_CITATION | AF-3C-only public Citation/CitationReference resolution, mapping, and serialization. |
| FUTURE_CONSUMER | A named later consumer outside AF-3. |

DEFAULT appears only for a stable case that has one unsplit fixture at that
test level and no mixed-phase dependency at that level. A non-DEFAULT Variant
is an explicit parameter identity. The Variant column itself is the complete
executable-label registry: a row binds that label to the named stable case body
and exact boundary. A case-level Planned test level line is only a capability
summary. A level omitted for a particular variant is not declared for that
variant because its oracle cannot be executed meaningfully there; only ledger
rows are required.

Oracle references use the case-local form `O-<level>-<variant>`, where the
level token is `U`, `PAC`, `PG`, `DC`, `FI`, `HTTP`, or `FUTURE`. The reference
is normative rather than opaque: it resolves to exactly the named variant's
fixture and the single observable condition assigned to the row's boundary at
that level in the corresponding case definition. A unit oracle observes only
the pure/service/adapter condition that requires no real database or HTTP
stack; a provider-adapter oracle observes the exact external-adapter contract;
a PostgreSQL oracle observes the stated real-database participation,
non-participation, transaction, bind, snapshot, or release condition; a
deterministic-concurrency oracle observes the named latch-driven state
transition; a fault-injection oracle observes the one named injected branch;
an HTTP oracle observes the exact public status/envelope/header/disclosure
condition; and a future oracle observes only its named later consumer. The
case's forbidden behavior is part of the pass/fail definition only where it
is observable at that same boundary and level. No row imports an assertion
from another boundary merely because the larger fixture traverses it.

ADR-008-R24 is a cross-cutting part of each canonical runtime oracle, not a
second tuple registry. The exact applicability projection is every ledger row
whose Owner is AF-3A, AF-3B, or AF-3C; each such row runs the shared recursive
scanner over the sinks and sentinel-bearing values observable at its own test
level and execution boundary, for success or failure. RET-PRIV-003 and
RET-PRIV-004 supply focused conformance and mutation controls but do not limit
that projection. FUTURE rows acquire R24 only when their named consumer makes
them mandatory.

The final inventory contains 398 explicit (Case ID, Variant) labels, 44
DEFAULT identities, 442 total parameter identities, and 1,064 canonical rows.

| Planned test level | Canonical rows |
| --- | ---: |
| unit | 233 |
| provider-adapter contract | 167 |
| PostgreSQL integration | 328 |
| deterministic concurrency | 9 |
| fault injection | 17 |
| HTTP integration | 306 |
| future consuming-phase acceptance | 4 |

| Owner | Canonical rows |
| --- | ---: |
| AF-3A | 115 |
| AF-3B | 580 |
| AF-3C | 365 |
| FUTURE | 4 |

| Execution boundary | Canonical rows |
| --- | ---: |
| PURE_REQUEST_VALIDATOR | 27 |
| AF3A_INITIAL_ACCESS | 12 |
| AF3A_KEYWORD | 15 |
| AF3A_FINAL_VALIDATOR | 46 |
| AF3A_CONCURRENCY | 15 |
| AF3B_EMBEDDING | 55 |
| AF3B_CHROMA_ADAPTER | 445 |
| AF3B_HYBRID_FUSION | 17 |
| AF3B_HYBRID_REGRESSION | 63 |
| AF3C_HTTP | 261 |
| AF3C_PUBLIC_EVIDENCE | 29 |
| AF3C_PUBLIC_CITATION | 75 |
| FUTURE_CONSUMER | 4 |

| Status | Canonical rows |
| --- | ---: |
| MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | 115 |
| REQUIRED_NOT_YET_IMPLEMENTED | 949 |

| Case family | Canonical rows |
| --- | ---: |
| RET-AUTH | 29 |
| RET-CONC | 73 |
| RET-PROV | 651 |
| RET-BND | 131 |
| RET-KEY | 16 |
| RET-RANK | 12 |
| RET-EVID | 86 |
| RET-INJ | 30 |
| RET-PRIV | 32 |
| RET-FUT | 4 |

There are 1,064 distinct case-local Oracle references and each is referenced
by exactly one canonical row. The enumerated ledger also yields 333 distinct
case-to-level pairs, 261 distinct case-to-owner pairs, and 275 distinct case-
to-boundary pairs. Those relations are not separate prose waivers: their full
membership is exactly the ledger projection. All 27 ADR mapping rows below
resolve to that ledger.

The 27 PURE_REQUEST_VALIDATOR merged markers have complete direct pure-parser
unit oracles. Production evidence for every row in this mapping is
`apps/api/app/retrieval/domain.py`; exact test evidence is
`apps/api/tests/unit/retrieval/test_domain.py` as mapped below. The marker
records merged evidence only; this documentation gate did not rerun the tests
or reopen the approved AF-3A closure decision. The other 88 AF-3A rows retain
their canonical row identities and approved closure-compatible status.

| Canonical implemented identity | Exact production behavior | Exact unit-test assertion |
| --- | --- | --- |
| `RET-BND-001::ADJACENT-U0001-PRESERVATION` | `parse_retrieval_request` rejects U+0000 only and preserves U+0001 through NFC/whitespace processing. | `test_adjacent_control_is_accepted_and_preserved` |
| `RET-BND-001::CASE-SENSITIVE-PRESERVATION` | NFC/ADR-whitespace normalization performs no case fold. | `test_forbidden_transformations_are_not_applied[case]` |
| `RET-BND-001::EACH-WHITESPACE-TRIM-AND-COLLAPSE` | `_normalize_adr_008_whitespace` handles exactly `_ADR_008_WHITESPACE`. | `test_every_adr_008_whitespace_code_point_is_trimmed_and_collapsed` executes the full finite set. |
| `RET-BND-001::EMBEDDED-U0000-REJECTION` | `parse_retrieval_request` rejects any embedded U+0000 before NFC. | `test_null_code_point_is_rejected[embedded]` |
| `RET-BND-001::EXCLUDED-U200B-PRESERVATION` | U+200B is absent from `_ADR_008_WHITESPACE` and remains unchanged. | `test_excluded_whitespace_like_code_point_is_preserved` |
| `RET-BND-001::LONE-SURROGATE-REJECTION` | `_validate_query_scalar_domain` rejects the surrogate range before encoding/normalization. | `test_surrogates_are_rejected` executes high- and low-surrogate parameters. |
| `RET-BND-001::MISSING-QUERY-REJECTION` | Closed mapping validation requires the exact `query` key. | `test_missing_query_is_rejected` |
| `RET-BND-001::NFC-CANONICAL-EQUIVALENCE` | `unicodedata.normalize("NFC", query)` is applied exactly once before whitespace normalization. | `test_canonically_equivalent_queries_produce_equal_nfc_requests` |
| `RET-BND-001::NORMALIZED-SCALAR-EXACT-1` | Post-normalization scalar domain includes 1. | `test_normalized_scalar_boundaries_are_accepted[1]` |
| `RET-BND-001::NORMALIZED-SCALAR-EXACT-2048` | Post-normalization scalar domain includes 2,048. | `test_normalized_scalar_boundaries_are_accepted[2048]` |
| `RET-BND-001::NORMALIZED-SCALAR-PLUS-ONE-2049` | Post-normalization scalar domain rejects 2,049. | `test_normalized_scalar_count_above_maximum_is_rejected` |
| `RET-BND-001::NO-NFKC-COMPATIBILITY-FOLD` | Parser uses NFC, not NFKC/NFKD. | `test_forbidden_transformations_are_not_applied[compatibility-character]` |
| `RET-BND-001::POST-NORMALIZATION-SCALAR-BOUNDARY` | Permitted edge whitespace is removed before the inclusive 2,048-scalar post-normalization bound is applied. | `test_post_normalization_scalar_boundary` |
| `RET-BND-001::QUERY-EXACT-STRING-TYPE` | `type(query) is str` rejects every declared non-string/subclass fixture without coercion. | `test_query_requires_exact_string_type` executes the complete finite parameter list. |
| `RET-BND-001::U0000-ALONE-REJECTION` | `parse_retrieval_request` rejects U+0000 alone before NFC. | `test_null_code_point_is_rejected[single]` |
| `RET-BND-001::WHITESPACE-ONLY-REJECTION` | Exact whitespace normalization produces an empty value, then scalar minimum rejects it. | `test_whitespace_only_query_is_rejected_after_normalization` |
| `RET-BND-002::UTF8-BYTES-EXACT-4096` | Strict UTF-8 count accepts equality 4,096. | `test_4096_utf8_bytes_are_accepted` |
| `RET-BND-002::UTF8-BYTES-PLUS-ONE-4097` | Strict UTF-8 count rejects 4,097. | `test_4097_utf8_bytes_are_rejected` |
| `RET-BND-003::PARSER-DEFAULT-10` | Omitted `requested_count` uses exact integer 10. | `test_requested_count_defaults_to_ten` |
| `RET-BND-003::PARSER-MINIMUM-1` | Exact built-in integer 1 passes the inclusive domain. | `test_requested_count_accepts_inclusive_boundaries[1]` |
| `RET-BND-003::PARSER-MAXIMUM-50` | Exact built-in integer 50 passes the inclusive domain. | `test_requested_count_accepts_inclusive_boundaries[50]` |
| `RET-BND-003::PARSER-NEGATIVE-ONE-REJECTED` | Exact built-in integer -1 fails the inclusive domain. | `test_requested_count_rejects_invalid_values[negative-one]` |
| `RET-BND-003::PARSER-ZERO-REJECTED` | Exact built-in integer 0 fails the inclusive domain. | `test_requested_count_rejects_invalid_values[zero]` |
| `RET-BND-003::PARSER-PLUS-ONE-51-REJECTED` | Exact built-in integer 51 fails the inclusive domain. | `test_requested_count_rejects_invalid_values[fifty-one]` |
| `RET-BND-003::PARSER-BOOLEAN-TRUE-REJECTED` | Exact-type validation rejects boolean `true` before integer range logic. | `test_requested_count_rejects_invalid_values[boolean]` |
| `RET-BND-003::PARSER-FLOAT-1-REJECTED` | Exact-type validation rejects float `1.0`. | `test_requested_count_rejects_invalid_values[float]` |
| `RET-BND-003::PARSER-STRING-1-REJECTED` | Exact-type validation rejects string `"1"`. | `test_requested_count_rejects_invalid_values[string]` |

All 115 AF-3A canonical identities are
`MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE`. Every AF-3B, AF-3C, and
FUTURE tuple remains `REQUIRED_NOT_YET_IMPLEMENTED`; the row-level AF-3A close
does not advance those owners or claim AF-3 as a whole is complete.

### Non-circular phase and fixture rules

Every AF-3A row is provider-independent. It performs no embedding call, Chroma
probe/query, Provider response handling, dense-candidate work, hybrid union,
RRF/fusion, public Evidence/Citation work, or HTTP assertion. AF-3A final and
concurrency rows use keyword candidates, zero candidates, or explicitly
bounded synthetic candidate UUIDs/ranks. Synthetic candidates are never
described as Chroma output. A deterministic provider-independent pause/barrier
may model elapsed external time while every external-adapter call count remains
zero.

AF-3B rows may use embedding, Chroma, dense candidates, bounded hybrid union,
fusion, and distinct regressions through AF-3A controls. Every such regression
has an explicit AF3B-qualified variant identity and is not an AF-3A close
prerequisite. AF-3A owns non-HTTP all-sink assertions for its database and
internal authoritative retrieval record behavior. AF-3B owns non-HTTP
embedding, Provider, and hybrid all-sink regressions. AF-3C alone owns request wire/media,
public routes/errors/cache, public Evidence, public Citation, serialization,
and public HTTP all-sink assertions. All AF-3C rows remain unimplemented.

Within a case body, generic Provider or public-result wording applies only to a
ledger row whose boundary permits it. It never changes an AF-3A row fixture.
The following family allocations make the dependency splits explicit:

| Family | Provider-independent AF-3A identity | AF-3B identity | AF-3C identity |
| --- | --- | --- | --- |
| RET-AUTH-010 | AF3A-INITIAL-ACCESS-ZERO-HIT; AF3A-FINAL-REAUTH-ZERO-CANDIDATES; AF3A-FINAL-SNAPSHOT-ZERO-CANDIDATES | AF3B-PRESENT-EMPTY-PROVIDER; AF3B-HYBRID-AUTHORIZED-EMPTY-REGRESSION | AF3C-AUTHORIZED-EMPTY-HTTP |
| RET-CONC-002/003/005/007/008/009 | Each exact AF3A-KEYWORD label uses a keyword candidate and provider-independent barrier. | Each exact AF3B-HYBRID regression label uses Provider/dense timing. | Each exact AF3C-HTTP label owns public mapping. |
| RET-CONC-004 | Separate AF3A keyword processing and failed labels. | Separate AF3B hybrid processing and failed regression labels. | Separate AF3C HTTP processing and failed labels. |
| RET-CONC-006/010 | Exact AF3A-SYNTHETIC labels use bounded synthetic identities/ranks. | Exact AF3B-HYBRID regression labels use hybrid candidates. | Exact AF3C-HTTP labels own public mapping. |
| RET-CONC-011 | Four AF3A rows independently cover batch-two statement failure, commit failure, connection failure, and statement timeout with keyword/synthetic candidates. | Four distinct AF3B-HYBRID regression rows rerun those failure points after hybrid work. | Four AF3C-HTTP rows own public errors. |
| RET-CONC-012 | AF3A-ZERO-CANDIDATE-ACCESS-LOSS uses zero candidates. | AF3B-HYBRID-ZERO-CANDIDATE-ACCESS-LOSS-REGRESSION uses the present-empty dense path. | AF3C-HTTP-ZERO-CANDIDATE-ACCESS-LOSS owns public behavior. |
| RET-CONC-013 | The three exact clock labels plus AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY are AF-3A. | AF3B-SESSION-EXPIRES-DURING-PROVIDER-REGRESSION is the separate Provider-time regression. | AF3C-HTTP-FINAL-NOW-FRESH-AWARE, AF3C-HTTP-EXPIRES-GREATER-VALID, AF3C-HTTP-EXPIRES-EQUALITY-EXPIRED, and AF3C-HTTP-SESSION-EXPIRES-DURING-PROVIDER own their exact public outcomes. |
| RET-CONC-014 | AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT uses keyword input. | AF3B-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT-REGRESSION uses the stale Chroma ID. | AF3C-HTTP-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT owns authorized-empty public mapping. |
| RET-BND-008 | AF3A-ZERO-SYNTHETIC-CANDIDATES proves final authorization with zero validation batches. | AF3B-PRESENT-EMPTY-DENSE-ZERO-UNION proves Provider parsing and hybrid zero union. | AF3C-HTTP-AUTHORIZED-EMPTY-ZERO-UNION |
| RET-BND-009–015 | Each exact AF3A-SYNTHETIC row owns only unique-input/batch/query bounds. | Each exact AF3B-HYBRID regression row owns dense union/fusion regression. | Each exact AF3C-HTTP row owns public cutoff/serialization. |
| RET-KEY-001–004 | Exact AF3A rows own scoped eligibility, simple bound plainto_tsquery, ts_rank_cd, score/UUID order, cutoff 128, revalidation, bounded counts, and scoped repository use. | Exact AF3B-HYBRID regression rows own only hybrid regressions. | Exact AF3C-HTTP rows own route/repository/public behavior. |
| RET-EVID-001 | AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION uses keyword/synthetic input and the PostgreSQL projection only. | AF3B-FUSED-INTERNAL-RECORD-EXTENSION adds hybrid-derived rank primitives. | AF3C-PUBLIC-EVIDENCE-SERIALIZATION alone exposes public Evidence. |
| RET-EVID-002/010 | Exact AF3A rows own provider-independent eligibility/empty internal authoritative retrieval record sets. | Exact AF3B-HYBRID regression rows own hybrid regressions. | Exact AF3C-HTTP rows own public Evidence mapping. |
| RET-INJ-001–006 | AF3A-KEYWORD-INTERNAL-RECORD uses keyword/synthetic candidates and classifies text only untrusted_document_content. | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION owns hybrid-derived regressions. | AF3C-PUBLIC-EVIDENCE-HTTP owns public serialization. |
| RET-PRIV-004 | KEYWORD-DATABASE-FATAL, FINAL-AUTHORIZATION-STATEMENT-FATAL, LATER-BATCH, and FINAL-COMMIT secrecy rows require no Provider. | EMBEDDING-FATAL, PROVIDER-FATAL, AF3B-HYBRID-FINAL-COMMIT-ALL-SINK-REGRESSION, and AF3B-HYBRID-LATER-BATCH-ALL-SINK-REGRESSION are distinct AF-3B failures. | Corresponding HTTP rows own generic public error/cache/privacy behavior; the two hybrid HTTP rows are explicitly AF3C-qualified. |

RET-BND-010 and RET-BND-011 keep equality 64 and plus-one 65 as different
stable cases and phase-qualified labels. RET-BND-015 separately proves the
exact maximum 192 and three validation queries. RET-BND-002 now has separate
UTF8-BYTES-EXACT-4096 and UTF8-BYTES-PLUS-ONE-4097 identities. Provider
multi-fixture cases similarly use explicit labels instead of combined DEFAULT.

### Canonical ownership ledger

<!-- CANONICAL_LEDGER_BEGIN -->
| Case ID | Variant | Test level | Execution boundary | Owner | Status | Oracle |
| --- | --- | --- | --- | --- | --- | --- |
| RET-AUTH-001 | AUTHENTICATION-FAILURE-CONTROL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AUTHENTICATION-FAILURE-CONTROL |
| RET-AUTH-001 | UNAUTHENTICATED-PRECEDENCE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-UNAUTHENTICATED-PRECEDENCE |
| RET-AUTH-002 | DEFAULT | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-DEFAULT |
| RET-AUTH-002 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-AUTH-003 | DEFAULT | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-DEFAULT |
| RET-AUTH-003 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-AUTH-004 | AF3A-ROLE-MATRIX | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-ROLE-MATRIX |
| RET-AUTH-004 | AF3B-HYBRID-ROLE-MATRIX-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-ROLE-MATRIX-REGRESSION |
| RET-AUTH-004 | AF3C-HTTP-ROLE-MATRIX | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-ROLE-MATRIX |
| RET-AUTH-005 | AF3A-NONMEMBER-INITIAL-ACCESS | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-NONMEMBER-INITIAL-ACCESS |
| RET-AUTH-005 | HIDDEN-TARGET-PRECEDENCE | PostgreSQL integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-HIDDEN-TARGET-PRECEDENCE |
| RET-AUTH-005 | HIDDEN-TARGET-PRECEDENCE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-HIDDEN-TARGET-PRECEDENCE |
| RET-AUTH-006 | DEFAULT | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-DEFAULT |
| RET-AUTH-006 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-AUTH-007 | DEFAULT | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-DEFAULT |
| RET-AUTH-007 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-AUTH-008 | DEFAULT | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-DEFAULT |
| RET-AUTH-008 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-AUTH-009 | AF3A-KEYWORD-EXACT-TARGET | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-EXACT-TARGET |
| RET-AUTH-009 | AF3B-HYBRID-EXACT-TARGET-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-EXACT-TARGET-REGRESSION |
| RET-AUTH-009 | AF3C-HTTP-EXACT-TARGET | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-EXACT-TARGET |
| RET-AUTH-010 | AF3A-FINAL-REAUTH-ZERO-CANDIDATES | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-FINAL-REAUTH-ZERO-CANDIDATES |
| RET-AUTH-010 | AF3A-FINAL-SNAPSHOT-ZERO-CANDIDATES | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-FINAL-SNAPSHOT-ZERO-CANDIDATES |
| RET-AUTH-010 | AF3A-INITIAL-ACCESS-ZERO-HIT | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-INITIAL-ACCESS-ZERO-HIT |
| RET-AUTH-010 | AF3B-HYBRID-AUTHORIZED-EMPTY-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-AUTHORIZED-EMPTY-REGRESSION |
| RET-AUTH-010 | AF3B-PRESENT-EMPTY-PROVIDER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-AF3B-PRESENT-EMPTY-PROVIDER |
| RET-AUTH-010 | AF3C-AUTHORIZED-EMPTY-HTTP | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-AUTHORIZED-EMPTY-HTTP |
| RET-AUTH-011 | DEFAULT | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-DEFAULT |
| RET-AUTH-011 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-BND-001 | ADJACENT-U0001-PRESERVATION | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-ADJACENT-U0001-PRESERVATION |
| RET-BND-001 | AF3A-EMBEDDED-U0000-GATE-ORDER | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-EMBEDDED-U0000-GATE-ORDER |
| RET-BND-001 | AF3A-INITIAL-ACCESS-INVALID-QUERY-GATE-ORDER | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-INITIAL-ACCESS-INVALID-QUERY-GATE-ORDER |
| RET-BND-001 | AF3A-KEYWORD-BIND-CASE-SENSITIVE | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-BIND-CASE-SENSITIVE |
| RET-BND-001 | AF3A-KEYWORD-BIND-EXCLUDED-U200B | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-BIND-EXCLUDED-U200B |
| RET-BND-001 | AF3A-KEYWORD-BIND-NFC-AND-WHITESPACE | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-BIND-NFC-AND-WHITESPACE |
| RET-BND-001 | AF3A-KEYWORD-BIND-NO-NFKC | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-BIND-NO-NFKC |
| RET-BND-001 | AF3A-KEYWORD-BIND-POST-NORMALIZATION-BOUNDARY | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-BIND-POST-NORMALIZATION-BOUNDARY |
| RET-BND-001 | AF3A-U0000-ALONE-GATE-ORDER | PostgreSQL integration | AF3A_INITIAL_ACCESS | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-U0000-ALONE-GATE-ORDER |
| RET-BND-001 | AF3B-HYBRID-QUERY-NORMALIZATION-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-QUERY-NORMALIZATION-REGRESSION |
| RET-BND-001 | AF3C-HTTP-CASE-SENSITIVE-PRESERVATION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-CASE-SENSITIVE-PRESERVATION |
| RET-BND-001 | AF3C-HTTP-EMBEDDED-U0000-REJECTION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-EMBEDDED-U0000-REJECTION |
| RET-BND-001 | AF3C-HTTP-EXCLUDED-U200B-PRESERVATION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-EXCLUDED-U200B-PRESERVATION |
| RET-BND-001 | AF3C-HTTP-INVALID-QUERY-VALIDATION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-INVALID-QUERY-VALIDATION |
| RET-BND-001 | AF3C-HTTP-NO-NFKC-COMPATIBILITY-FOLD | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-NO-NFKC-COMPATIBILITY-FOLD |
| RET-BND-001 | AF3C-HTTP-POST-NORMALIZATION-SCALAR-BOUNDARY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-POST-NORMALIZATION-SCALAR-BOUNDARY |
| RET-BND-001 | AF3C-HTTP-U0000-ALONE-REJECTION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-U0000-ALONE-REJECTION |
| RET-BND-001 | AF3C-HTTP-VALID-NORMALIZED-QUERY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-VALID-NORMALIZED-QUERY |
| RET-BND-001 | CASE-SENSITIVE-PRESERVATION | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-CASE-SENSITIVE-PRESERVATION |
| RET-BND-001 | EACH-WHITESPACE-TRIM-AND-COLLAPSE | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-EACH-WHITESPACE-TRIM-AND-COLLAPSE |
| RET-BND-001 | EMBEDDED-U0000-REJECTION | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-EMBEDDED-U0000-REJECTION |
| RET-BND-001 | EXCLUDED-U200B-PRESERVATION | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-EXCLUDED-U200B-PRESERVATION |
| RET-BND-001 | LONE-SURROGATE-REJECTION | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-LONE-SURROGATE-REJECTION |
| RET-BND-001 | MISSING-QUERY-REJECTION | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-MISSING-QUERY-REJECTION |
| RET-BND-001 | NFC-CANONICAL-EQUIVALENCE | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-NFC-CANONICAL-EQUIVALENCE |
| RET-BND-001 | NORMALIZED-SCALAR-EXACT-1 | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-NORMALIZED-SCALAR-EXACT-1 |
| RET-BND-001 | NORMALIZED-SCALAR-EXACT-2048 | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-NORMALIZED-SCALAR-EXACT-2048 |
| RET-BND-001 | NORMALIZED-SCALAR-PLUS-ONE-2049 | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-NORMALIZED-SCALAR-PLUS-ONE-2049 |
| RET-BND-001 | NO-NFKC-COMPATIBILITY-FOLD | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-NO-NFKC-COMPATIBILITY-FOLD |
| RET-BND-001 | POST-NORMALIZATION-SCALAR-BOUNDARY | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-POST-NORMALIZATION-SCALAR-BOUNDARY |
| RET-BND-001 | QUERY-EXACT-STRING-TYPE | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-QUERY-EXACT-STRING-TYPE |
| RET-BND-001 | U0000-ALONE-REJECTION | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-U0000-ALONE-REJECTION |
| RET-BND-001 | WHITESPACE-ONLY-REJECTION | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-WHITESPACE-ONLY-REJECTION |
| RET-BND-002 | UTF8-BYTES-EXACT-4096 | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-UTF8-BYTES-EXACT-4096 |
| RET-BND-002 | UTF8-BYTES-EXACT-4096 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-UTF8-BYTES-EXACT-4096 |
| RET-BND-002 | UTF8-BYTES-PLUS-ONE-4097 | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-UTF8-BYTES-PLUS-ONE-4097 |
| RET-BND-002 | UTF8-BYTES-PLUS-ONE-4097 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-UTF8-BYTES-PLUS-ONE-4097 |
| RET-BND-003 | AUTHORIZED-BODY-VALIDATION-CONTROL | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AUTHORIZED-BODY-VALIDATION-CONTROL |
| RET-BND-003 | AUTHORIZED-BODY-VALIDATION-CONTROL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AUTHORIZED-BODY-VALIDATION-CONTROL |
| RET-BND-003 | BODY-EXACT-65536 | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-BODY-EXACT-65536 |
| RET-BND-003 | BODY-EXACT-65536 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-BODY-EXACT-65536 |
| RET-BND-003 | BODY-PLUS-ONE-65537 | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-BODY-PLUS-ONE-65537 |
| RET-BND-003 | BODY-PLUS-ONE-65537 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-BODY-PLUS-ONE-65537 |
| RET-BND-003 | CANONICAL-PATH-CONTROL | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CANONICAL-PATH-CONTROL |
| RET-BND-003 | CANONICAL-PATH-CONTROL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CANONICAL-PATH-CONTROL |
| RET-BND-003 | CHUNKED-BODY-PLUS-ONE-65537 | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CHUNKED-BODY-PLUS-ONE-65537 |
| RET-BND-003 | CHUNKED-BODY-PLUS-ONE-65537 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CHUNKED-BODY-PLUS-ONE-65537 |
| RET-BND-003 | ESCAPED-U0000-DOMAIN-HANDOFF | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-ESCAPED-U0000-DOMAIN-HANDOFF |
| RET-BND-003 | ESCAPED-U0000-DOMAIN-HANDOFF | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-ESCAPED-U0000-DOMAIN-HANDOFF |
| RET-BND-003 | LITERAL-NUL-JSON-PARSER-REJECTION | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-LITERAL-NUL-JSON-PARSER-REJECTION |
| RET-BND-003 | LITERAL-NUL-JSON-PARSER-REJECTION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-LITERAL-NUL-JSON-PARSER-REJECTION |
| RET-BND-003 | MEDIA-BEFORE-BODY-PRECEDENCE | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MEDIA-BEFORE-BODY-PRECEDENCE |
| RET-BND-003 | MEDIA-BEFORE-BODY-PRECEDENCE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MEDIA-BEFORE-BODY-PRECEDENCE |
| RET-BND-003 | NONCANONICAL-PATH | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NONCANONICAL-PATH |
| RET-BND-003 | NONCANONICAL-PATH | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NONCANONICAL-PATH |
| RET-BND-003 | AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD |
| RET-BND-003 | AF3A-KEYWORD-CEILING-INDEPENDENT-OF-REQUESTED-COUNT | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-CEILING-INDEPENDENT-OF-REQUESTED-COUNT |
| RET-BND-003 | AF3B-CONFIGURED-PROVIDER-COUNT-FORMULA | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-CONFIGURED-PROVIDER-COUNT-FORMULA |
| RET-BND-003 | AF3B-CONFIGURED-PROVIDER-COUNT-FORMULA | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-AF3B-CONFIGURED-PROVIDER-COUNT-FORMULA |
| RET-BND-003 | AF3B-DENSE-COUNT-BOUNDED-BY-POSITIONS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-DENSE-COUNT-BOUNDED-BY-POSITIONS |
| RET-BND-003 | AF3B-DENSE-COUNT-BOUNDED-BY-POSITIONS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-AF3B-DENSE-COUNT-BOUNDED-BY-POSITIONS |
| RET-BND-003 | AF3C-HTTP-REQUESTED-COUNT-VALIDATION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-REQUESTED-COUNT-VALIDATION |
| RET-BND-003 | AF3C-PUBLIC-RESULT-CUTOFF | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-PUBLIC-RESULT-CUTOFF |
| RET-BND-003 | PARSER-BOOLEAN-TRUE-REJECTED | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-BOOLEAN-TRUE-REJECTED |
| RET-BND-003 | PARSER-DEFAULT-10 | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-DEFAULT-10 |
| RET-BND-003 | PARSER-FLOAT-1-REJECTED | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-FLOAT-1-REJECTED |
| RET-BND-003 | PARSER-MAXIMUM-50 | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-MAXIMUM-50 |
| RET-BND-003 | PARSER-MINIMUM-1 | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-MINIMUM-1 |
| RET-BND-003 | PARSER-NEGATIVE-ONE-REJECTED | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-NEGATIVE-ONE-REJECTED |
| RET-BND-003 | PARSER-PLUS-ONE-51-REJECTED | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-PLUS-ONE-51-REJECTED |
| RET-BND-003 | PARSER-STRING-1-REJECTED | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-STRING-1-REJECTED |
| RET-BND-003 | PARSER-ZERO-REJECTED | unit | PURE_REQUEST_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-PARSER-ZERO-REJECTED |
| RET-BND-003 | SUPPORTED-MEDIA-CONTROL | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SUPPORTED-MEDIA-CONTROL |
| RET-BND-003 | SUPPORTED-MEDIA-CONTROL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SUPPORTED-MEDIA-CONTROL |
| RET-BND-003 | U0000-AUTHENTICATION-PRECEDENCE | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-U0000-AUTHENTICATION-PRECEDENCE |
| RET-BND-003 | U0000-AUTHENTICATION-PRECEDENCE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-U0000-AUTHENTICATION-PRECEDENCE |
| RET-BND-003 | U0000-HIDDEN-TARGET-PRECEDENCE | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-U0000-HIDDEN-TARGET-PRECEDENCE |
| RET-BND-003 | U0000-HIDDEN-TARGET-PRECEDENCE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-U0000-HIDDEN-TARGET-PRECEDENCE |
| RET-BND-003 | UNSUPPORTED-MEDIA | unit | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-UNSUPPORTED-MEDIA |
| RET-BND-003 | UNSUPPORTED-MEDIA | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-UNSUPPORTED-MEDIA |
| RET-BND-004 | DEFAULT | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-BND-004 | DEFAULT | provider-adapter contract | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-BND-004 | DEFAULT | PostgreSQL integration | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-BND-004 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-BND-005 | DEFAULT | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-BND-005 | DEFAULT | provider-adapter contract | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-BND-005 | DEFAULT | PostgreSQL integration | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-BND-005 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-BND-006 | AF3A-KEYWORD-LIMIT-EXACT-128 | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-LIMIT-EXACT-128 |
| RET-BND-006 | AF3B-HYBRID-KEYWORD-LIMIT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-KEYWORD-LIMIT-REGRESSION |
| RET-BND-006 | AF3C-HTTP-KEYWORD-LIMIT | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-KEYWORD-LIMIT |
| RET-BND-007 | DEFAULT | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-BND-007 | DEFAULT | PostgreSQL integration | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-BND-007 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-BND-008 | AF3A-ZERO-SYNTHETIC-CANDIDATES | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-ZERO-SYNTHETIC-CANDIDATES |
| RET-BND-008 | AF3A-ZERO-SYNTHETIC-CANDIDATES | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-ZERO-SYNTHETIC-CANDIDATES |
| RET-BND-008 | AF3B-PRESENT-EMPTY-DENSE-ZERO-UNION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-PRESENT-EMPTY-DENSE-ZERO-UNION |
| RET-BND-008 | AF3B-PRESENT-EMPTY-DENSE-ZERO-UNION | provider-adapter contract | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-AF3B-PRESENT-EMPTY-DENSE-ZERO-UNION |
| RET-BND-008 | AF3B-PRESENT-EMPTY-DENSE-ZERO-UNION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-PRESENT-EMPTY-DENSE-ZERO-UNION |
| RET-BND-008 | AF3C-HTTP-AUTHORIZED-EMPTY-ZERO-UNION | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-AUTHORIZED-EMPTY-ZERO-UNION |
| RET-BND-009 | AF3A-SYNTHETIC-ONE-UNIQUE-CANDIDATE | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-SYNTHETIC-ONE-UNIQUE-CANDIDATE |
| RET-BND-009 | AF3A-SYNTHETIC-ONE-UNIQUE-CANDIDATE | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-ONE-UNIQUE-CANDIDATE |
| RET-BND-009 | AF3B-HYBRID-ONE-UNIQUE-CANDIDATE-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-ONE-UNIQUE-CANDIDATE-REGRESSION |
| RET-BND-009 | AF3B-HYBRID-ONE-UNIQUE-CANDIDATE-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-ONE-UNIQUE-CANDIDATE-REGRESSION |
| RET-BND-009 | AF3C-HTTP-ONE-UNIQUE-CANDIDATE | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-ONE-UNIQUE-CANDIDATE |
| RET-BND-010 | AF3A-SYNTHETIC-EXACT-BATCH-64 | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-SYNTHETIC-EXACT-BATCH-64 |
| RET-BND-010 | AF3A-SYNTHETIC-EXACT-BATCH-64 | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-EXACT-BATCH-64 |
| RET-BND-010 | AF3B-HYBRID-EXACT-BATCH-64-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-EXACT-BATCH-64-REGRESSION |
| RET-BND-010 | AF3B-HYBRID-EXACT-BATCH-64-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-EXACT-BATCH-64-REGRESSION |
| RET-BND-010 | AF3C-HTTP-EXACT-BATCH-64 | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-EXACT-BATCH-64 |
| RET-BND-011 | AF3A-SYNTHETIC-BATCH-PLUS-ONE-65 | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-SYNTHETIC-BATCH-PLUS-ONE-65 |
| RET-BND-011 | AF3A-SYNTHETIC-BATCH-PLUS-ONE-65 | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-BATCH-PLUS-ONE-65 |
| RET-BND-011 | AF3B-HYBRID-BATCH-PLUS-ONE-65-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-BATCH-PLUS-ONE-65-REGRESSION |
| RET-BND-011 | AF3B-HYBRID-BATCH-PLUS-ONE-65-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-BATCH-PLUS-ONE-65-REGRESSION |
| RET-BND-011 | AF3C-HTTP-BATCH-PLUS-ONE-65 | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-BATCH-PLUS-ONE-65 |
| RET-BND-012 | AF3A-SYNTHETIC-THREE-DETERMINISTIC-BATCHES | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-SYNTHETIC-THREE-DETERMINISTIC-BATCHES |
| RET-BND-012 | AF3A-SYNTHETIC-THREE-DETERMINISTIC-BATCHES | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-THREE-DETERMINISTIC-BATCHES |
| RET-BND-012 | AF3B-HYBRID-THREE-DETERMINISTIC-BATCHES-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-THREE-DETERMINISTIC-BATCHES-REGRESSION |
| RET-BND-012 | AF3B-HYBRID-THREE-DETERMINISTIC-BATCHES-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-THREE-DETERMINISTIC-BATCHES-REGRESSION |
| RET-BND-012 | AF3C-HTTP-THREE-DETERMINISTIC-BATCHES | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-THREE-DETERMINISTIC-BATCHES |
| RET-BND-013 | AF3A-SYNTHETIC-DUPLICATES-REDUCE-UNIQUE-INPUT | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-SYNTHETIC-DUPLICATES-REDUCE-UNIQUE-INPUT |
| RET-BND-013 | AF3A-SYNTHETIC-DUPLICATES-REDUCE-UNIQUE-INPUT | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-DUPLICATES-REDUCE-UNIQUE-INPUT |
| RET-BND-013 | AF3B-HYBRID-DUPLICATES-REDUCE-UNIQUE-INPUT-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-DUPLICATES-REDUCE-UNIQUE-INPUT-REGRESSION |
| RET-BND-013 | AF3B-HYBRID-DUPLICATES-REDUCE-UNIQUE-INPUT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-DUPLICATES-REDUCE-UNIQUE-INPUT-REGRESSION |
| RET-BND-013 | AF3C-HTTP-DUPLICATES-REDUCE-UNIQUE-INPUT | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-DUPLICATES-REDUCE-UNIQUE-INPUT |
| RET-BND-014 | AF3A-SYNTHETIC-UNORDERED-POSTGRESQL-ROWS | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-UNORDERED-POSTGRESQL-ROWS |
| RET-BND-014 | AF3B-HYBRID-UNORDERED-POSTGRESQL-ROWS-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-UNORDERED-POSTGRESQL-ROWS-REGRESSION |
| RET-BND-014 | AF3C-HTTP-UNORDERED-POSTGRESQL-ROWS | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-UNORDERED-POSTGRESQL-ROWS |
| RET-BND-015 | AF3A-SYNTHETIC-MAXIMUM-192-THREE-BATCHES | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-MAXIMUM-192-THREE-BATCHES |
| RET-BND-015 | AF3B-HYBRID-MAXIMUM-192-THREE-BATCHES-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-MAXIMUM-192-THREE-BATCHES-REGRESSION |
| RET-BND-015 | AF3C-HTTP-MAXIMUM-192-THREE-BATCHES | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-MAXIMUM-192-THREE-BATCHES |
| RET-CONC-001 | CHROMA-LIFECYCLE-REVOCATION | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CHROMA-LIFECYCLE-REVOCATION |
| RET-CONC-001 | CHROMA-LIFECYCLE-REVOCATION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CHROMA-LIFECYCLE-REVOCATION |
| RET-CONC-001 | EMBEDDING-LIFECYCLE-CANCELLATION | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-EMBEDDING-LIFECYCLE-CANCELLATION |
| RET-CONC-001 | EMBEDDING-LIFECYCLE-CANCELLATION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-EMBEDDING-LIFECYCLE-CANCELLATION |
| RET-CONC-001 | EMBEDDING-LIFECYCLE-FAILURE | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-EMBEDDING-LIFECYCLE-FAILURE |
| RET-CONC-001 | EMBEDDING-LIFECYCLE-FAILURE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-EMBEDDING-LIFECYCLE-FAILURE |
| RET-CONC-001 | EMBEDDING-LIFECYCLE-SUCCESS | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-EMBEDDING-LIFECYCLE-SUCCESS |
| RET-CONC-001 | EMBEDDING-LIFECYCLE-SUCCESS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-EMBEDDING-LIFECYCLE-SUCCESS |
| RET-CONC-002 | AF3A-KEYWORD-SESSION-REVOKED-BEFORE-FINAL-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-SESSION-REVOKED-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-002 | AF3B-HYBRID-SESSION-REVOKED-BEFORE-FINAL-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-SESSION-REVOKED-BEFORE-FINAL-SNAPSHOT-REGRESSION |
| RET-CONC-002 | AF3C-HTTP-SESSION-REVOKED-BEFORE-FINAL-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-SESSION-REVOKED-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-003 | AF3A-KEYWORD-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-003 | AF3B-HYBRID-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT-REGRESSION |
| RET-CONC-003 | AF3C-HTTP-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-USER-INACTIVE-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-004 | AF3A-KEYWORD-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-004 | AF3A-KEYWORD-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-004 | AF3B-HYBRID-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT-REGRESSION |
| RET-CONC-004 | AF3B-HYBRID-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT-REGRESSION |
| RET-CONC-004 | AF3C-HTTP-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-DOCUMENT-FAILED-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-004 | AF3C-HTTP-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-DOCUMENT-PROCESSING-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-005 | AF3A-KEYWORD-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-005 | AF3B-HYBRID-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT-REGRESSION |
| RET-CONC-005 | AF3C-HTTP-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-CHUNK-REPLACED-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-006 | AF3A-SYNTHETIC-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT |
| RET-CONC-006 | AF3B-HYBRID-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT-REGRESSION |
| RET-CONC-006 | AF3C-HTTP-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-MEMBERSHIP-REMOVED-AFTER-SNAPSHOT |
| RET-CONC-007 | AF3A-KEYWORD-DOCUMENT-CHANGED-AFTER-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-DOCUMENT-CHANGED-AFTER-SNAPSHOT |
| RET-CONC-007 | AF3B-HYBRID-DOCUMENT-CHANGED-AFTER-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-DOCUMENT-CHANGED-AFTER-SNAPSHOT-REGRESSION |
| RET-CONC-007 | AF3C-HTTP-DOCUMENT-CHANGED-AFTER-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-DOCUMENT-CHANGED-AFTER-SNAPSHOT |
| RET-CONC-008 | AF3A-KEYWORD-CHUNK-REPLACED-AFTER-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-CHUNK-REPLACED-AFTER-SNAPSHOT |
| RET-CONC-008 | AF3B-HYBRID-CHUNK-REPLACED-AFTER-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-CHUNK-REPLACED-AFTER-SNAPSHOT-REGRESSION |
| RET-CONC-008 | AF3C-HTTP-CHUNK-REPLACED-AFTER-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-CHUNK-REPLACED-AFTER-SNAPSHOT |
| RET-CONC-009 | AF3A-KEYWORD-REVOCATION-AFTER-FINAL-COMMIT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-REVOCATION-AFTER-FINAL-COMMIT |
| RET-CONC-009 | AF3B-HYBRID-REVOCATION-AFTER-FINAL-COMMIT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-REVOCATION-AFTER-FINAL-COMMIT-REGRESSION |
| RET-CONC-009 | AF3C-HTTP-REVOCATION-AFTER-FINAL-COMMIT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-REVOCATION-AFTER-FINAL-COMMIT |
| RET-CONC-010 | AF3A-SYNTHETIC-MULTIBATCH-FIXED-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SYNTHETIC-MULTIBATCH-FIXED-SNAPSHOT |
| RET-CONC-010 | AF3B-HYBRID-MULTIBATCH-FIXED-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-MULTIBATCH-FIXED-SNAPSHOT-REGRESSION |
| RET-CONC-010 | AF3C-HTTP-MULTIBATCH-FIXED-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-MULTIBATCH-FIXED-SNAPSHOT |
| RET-CONC-011 | AF3A-BATCH-TWO-STATEMENT-FAILURE | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-BATCH-TWO-STATEMENT-FAILURE |
| RET-CONC-011 | AF3A-BATCH-TWO-STATEMENT-TIMEOUT | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-BATCH-TWO-STATEMENT-TIMEOUT |
| RET-CONC-011 | AF3A-FINAL-COMMIT-FAILURE | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-FINAL-COMMIT-FAILURE |
| RET-CONC-011 | AF3A-FINAL-CONNECTION-FAILURE | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-FINAL-CONNECTION-FAILURE |
| RET-CONC-011 | AF3B-HYBRID-BATCH-TWO-STATEMENT-FAILURE-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-BATCH-TWO-STATEMENT-FAILURE-REGRESSION |
| RET-CONC-011 | AF3B-HYBRID-BATCH-TWO-STATEMENT-TIMEOUT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-BATCH-TWO-STATEMENT-TIMEOUT-REGRESSION |
| RET-CONC-011 | AF3B-HYBRID-FINAL-COMMIT-FAILURE-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-FINAL-COMMIT-FAILURE-REGRESSION |
| RET-CONC-011 | AF3B-HYBRID-FINAL-CONNECTION-FAILURE-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-FINAL-CONNECTION-FAILURE-REGRESSION |
| RET-CONC-011 | AF3C-HTTP-BATCH-TWO-STATEMENT-FAILURE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-BATCH-TWO-STATEMENT-FAILURE |
| RET-CONC-011 | AF3C-HTTP-BATCH-TWO-STATEMENT-TIMEOUT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-BATCH-TWO-STATEMENT-TIMEOUT |
| RET-CONC-011 | AF3C-HTTP-FINAL-COMMIT-FAILURE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-FINAL-COMMIT-FAILURE |
| RET-CONC-011 | AF3C-HTTP-FINAL-CONNECTION-FAILURE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-FINAL-CONNECTION-FAILURE |
| RET-CONC-012 | AF3A-ZERO-CANDIDATE-ACCESS-LOSS | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-ZERO-CANDIDATE-ACCESS-LOSS |
| RET-CONC-012 | AF3B-HYBRID-ZERO-CANDIDATE-ACCESS-LOSS-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-ZERO-CANDIDATE-ACCESS-LOSS-REGRESSION |
| RET-CONC-012 | AF3C-HTTP-ZERO-CANDIDATE-ACCESS-LOSS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-ZERO-CANDIDATE-ACCESS-LOSS |
| RET-CONC-013 | AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY |
| RET-CONC-013 | AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY | deterministic concurrency | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-DC-AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY |
| RET-CONC-013 | EXPIRES-EQUALITY-EXPIRED | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-EXPIRES-EQUALITY-EXPIRED |
| RET-CONC-013 | EXPIRES-EQUALITY-EXPIRED | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-EXPIRES-EQUALITY-EXPIRED |
| RET-CONC-013 | AF3C-HTTP-EXPIRES-EQUALITY-EXPIRED | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-EXPIRES-EQUALITY-EXPIRED |
| RET-CONC-013 | EXPIRES-GREATER-VALID | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-EXPIRES-GREATER-VALID |
| RET-CONC-013 | EXPIRES-GREATER-VALID | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-EXPIRES-GREATER-VALID |
| RET-CONC-013 | AF3C-HTTP-EXPIRES-GREATER-VALID | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-EXPIRES-GREATER-VALID |
| RET-CONC-013 | FINAL-NOW-FRESH-AWARE | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-FINAL-NOW-FRESH-AWARE |
| RET-CONC-013 | FINAL-NOW-FRESH-AWARE | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-FINAL-NOW-FRESH-AWARE |
| RET-CONC-013 | AF3C-HTTP-FINAL-NOW-FRESH-AWARE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-FINAL-NOW-FRESH-AWARE |
| RET-CONC-013 | AF3B-SESSION-EXPIRES-DURING-PROVIDER-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-SESSION-EXPIRES-DURING-PROVIDER-REGRESSION |
| RET-CONC-013 | AF3B-SESSION-EXPIRES-DURING-PROVIDER-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-SESSION-EXPIRES-DURING-PROVIDER-REGRESSION |
| RET-CONC-013 | AF3B-SESSION-EXPIRES-DURING-PROVIDER-REGRESSION | deterministic concurrency | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-DC-AF3B-SESSION-EXPIRES-DURING-PROVIDER-REGRESSION |
| RET-CONC-013 | AF3C-HTTP-SESSION-EXPIRES-DURING-PROVIDER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-SESSION-EXPIRES-DURING-PROVIDER |
| RET-CONC-014 | AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT | PostgreSQL integration | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-014 | AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT | deterministic concurrency | AF3A_CONCURRENCY | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-DC-AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT |
| RET-CONC-014 | AF3B-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT-REGRESSION |
| RET-CONC-014 | AF3B-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT-REGRESSION | deterministic concurrency | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-DC-AF3B-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT-REGRESSION |
| RET-CONC-014 | AF3C-HTTP-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT |
| RET-EVID-001 | AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION |
| RET-EVID-001 | AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-AUTHORITATIVE-INTERNAL-RECORD-PROJECTION |
| RET-EVID-001 | AF3B-FUSED-INTERNAL-RECORD-EXTENSION | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-FUSED-INTERNAL-RECORD-EXTENSION |
| RET-EVID-001 | AF3B-FUSED-INTERNAL-RECORD-EXTENSION | PostgreSQL integration | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-FUSED-INTERNAL-RECORD-EXTENSION |
| RET-EVID-001 | AF3C-PUBLIC-EVIDENCE-SERIALIZATION | unit | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3C-PUBLIC-EVIDENCE-SERIALIZATION |
| RET-EVID-001 | AF3C-PUBLIC-EVIDENCE-SERIALIZATION | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-PUBLIC-EVIDENCE-SERIALIZATION |
| RET-EVID-002 | AF3A-NULL-HASH-OMISSION | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-NULL-HASH-OMISSION |
| RET-EVID-002 | AF3B-HYBRID-NULL-HASH-OMISSION-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-NULL-HASH-OMISSION-REGRESSION |
| RET-EVID-002 | AF3C-HTTP-NULL-HASH-OMISSION | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-NULL-HASH-OMISSION |
| RET-EVID-003 | CITATION-AUTH-EXPIRED | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-AUTH-EXPIRED |
| RET-EVID-003 | CITATION-AUTH-EXPIRED | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-AUTH-EXPIRED |
| RET-EVID-003 | CITATION-AUTH-INACTIVE-USER | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-AUTH-INACTIVE-USER |
| RET-EVID-003 | CITATION-AUTH-INACTIVE-USER | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-AUTH-INACTIVE-USER |
| RET-EVID-003 | CITATION-AUTH-REVOKED | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-AUTH-REVOKED |
| RET-EVID-003 | CITATION-AUTH-REVOKED | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-AUTH-REVOKED |
| RET-EVID-003 | CITATION-BODY-EXACT-65536 | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-BODY-EXACT-65536 |
| RET-EVID-003 | CITATION-BODY-EXACT-65536 | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-BODY-EXACT-65536 |
| RET-EVID-003 | CITATION-BODY-PLUS-ONE-65537 | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-BODY-PLUS-ONE-65537 |
| RET-EVID-003 | CITATION-BODY-PLUS-ONE-65537 | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-BODY-PLUS-ONE-65537 |
| RET-EVID-003 | CITATION-CHUNKED-BODY-PLUS-ONE-65537 | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-CHUNKED-BODY-PLUS-ONE-65537 |
| RET-EVID-003 | CITATION-CHUNKED-BODY-PLUS-ONE-65537 | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-CHUNKED-BODY-PLUS-ONE-65537 |
| RET-EVID-003 | CITATION-DATABASE-FAILURE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-DATABASE-FAILURE |
| RET-EVID-003 | CITATION-DATABASE-FAILURE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-DATABASE-FAILURE |
| RET-EVID-003 | CITATION-NONCANONICAL-PATH-UNHYPHENATED | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-NONCANONICAL-PATH-UNHYPHENATED |
| RET-EVID-003 | CITATION-NONCANONICAL-PATH-UNHYPHENATED | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-NONCANONICAL-PATH-UNHYPHENATED |
| RET-EVID-003 | CITATION-NONCANONICAL-PATH-UPPERCASE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-NONCANONICAL-PATH-UPPERCASE |
| RET-EVID-003 | CITATION-NONCANONICAL-PATH-UPPERCASE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-NONCANONICAL-PATH-UPPERCASE |
| RET-EVID-003 | CITATION-REFERENCE-MALFORMED-PREFIX | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-REFERENCE-MALFORMED-PREFIX |
| RET-EVID-003 | CITATION-REFERENCE-MALFORMED-PREFIX | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-REFERENCE-MALFORMED-PREFIX |
| RET-EVID-003 | CITATION-REFERENCE-SHORT-HASH | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-REFERENCE-SHORT-HASH |
| RET-EVID-003 | CITATION-REFERENCE-SHORT-HASH | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-REFERENCE-SHORT-HASH |
| RET-EVID-003 | CITATION-REFERENCE-UNHYPHENATED-UUID | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-REFERENCE-UNHYPHENATED-UUID |
| RET-EVID-003 | CITATION-REFERENCE-UNHYPHENATED-UUID | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-REFERENCE-UNHYPHENATED-UUID |
| RET-EVID-003 | CITATION-REFERENCE-UPPERCASE-HASH | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-REFERENCE-UPPERCASE-HASH |
| RET-EVID-003 | CITATION-REFERENCE-UPPERCASE-HASH | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-REFERENCE-UPPERCASE-HASH |
| RET-EVID-003 | CITATION-REFERENCE-UPPERCASE-UUID | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-REFERENCE-UPPERCASE-UUID |
| RET-EVID-003 | CITATION-REFERENCE-UPPERCASE-UUID | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-REFERENCE-UPPERCASE-UUID |
| RET-EVID-003 | CITATION-SCHEMA-ARRAY-VALUE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-ARRAY-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-ARRAY-VALUE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-ARRAY-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-BOOLEAN-VALUE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-BOOLEAN-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-BOOLEAN-VALUE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-BOOLEAN-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-DUPLICATE-FIELD | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-DUPLICATE-FIELD |
| RET-EVID-003 | CITATION-SCHEMA-DUPLICATE-FIELD | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-DUPLICATE-FIELD |
| RET-EVID-003 | CITATION-SCHEMA-EXTRA-FIELD | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-EXTRA-FIELD |
| RET-EVID-003 | CITATION-SCHEMA-EXTRA-FIELD | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-EXTRA-FIELD |
| RET-EVID-003 | CITATION-SCHEMA-MISSING-FIELD | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-MISSING-FIELD |
| RET-EVID-003 | CITATION-SCHEMA-MISSING-FIELD | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-MISSING-FIELD |
| RET-EVID-003 | CITATION-SCHEMA-NONOBJECT-BODY | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-NONOBJECT-BODY |
| RET-EVID-003 | CITATION-SCHEMA-NONOBJECT-BODY | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-NONOBJECT-BODY |
| RET-EVID-003 | CITATION-SCHEMA-NULL-VALUE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-NULL-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-NULL-VALUE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-NULL-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-NUMBER-VALUE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-NUMBER-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-NUMBER-VALUE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-NUMBER-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-OBJECT-VALUE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SCHEMA-OBJECT-VALUE |
| RET-EVID-003 | CITATION-SCHEMA-OBJECT-VALUE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SCHEMA-OBJECT-VALUE |
| RET-EVID-003 | CITATION-SUPPORTED-MEDIA-CONTROL | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-SUPPORTED-MEDIA-CONTROL |
| RET-EVID-003 | CITATION-SUPPORTED-MEDIA-CONTROL | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-SUPPORTED-MEDIA-CONTROL |
| RET-EVID-003 | CITATION-UNAUTHENTICATED-PRECEDENCE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-UNAUTHENTICATED-PRECEDENCE |
| RET-EVID-003 | CITATION-UNAUTHENTICATED-PRECEDENCE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-UNAUTHENTICATED-PRECEDENCE |
| RET-EVID-003 | CITATION-UNSUPPORTED-MEDIA | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-UNSUPPORTED-MEDIA |
| RET-EVID-003 | CITATION-UNSUPPORTED-MEDIA | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-UNSUPPORTED-MEDIA |
| RET-EVID-004 | DEFAULT | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-EVID-004 | DEFAULT | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-EVID-005 | DEFAULT | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-EVID-005 | DEFAULT | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-EVID-006 | CITATION-DOCUMENT-DELETED | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-DOCUMENT-DELETED |
| RET-EVID-006 | CITATION-DOCUMENT-DELETED | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-DOCUMENT-DELETED |
| RET-EVID-006 | CITATION-DOCUMENT-INELIGIBLE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-DOCUMENT-INELIGIBLE |
| RET-EVID-006 | CITATION-DOCUMENT-INELIGIBLE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-DOCUMENT-INELIGIBLE |
| RET-EVID-007 | DEFAULT | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-EVID-007 | DEFAULT | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-EVID-008 | CITATION-HIDDEN-TARGET-PRECEDENCE | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-HIDDEN-TARGET-PRECEDENCE |
| RET-EVID-008 | CITATION-HIDDEN-TARGET-PRECEDENCE | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-HIDDEN-TARGET-PRECEDENCE |
| RET-EVID-008 | CITATION-POSSESSION-NONMEMBER | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-POSSESSION-NONMEMBER |
| RET-EVID-008 | CITATION-POSSESSION-NONMEMBER | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-POSSESSION-NONMEMBER |
| RET-EVID-008 | CITATION-REFERENCE-TARGET-MISMATCH | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-REFERENCE-TARGET-MISMATCH |
| RET-EVID-008 | CITATION-REFERENCE-TARGET-MISMATCH | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-REFERENCE-TARGET-MISMATCH |
| RET-EVID-009 | AUTHORITATIVE-NULL-HASH | unit | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AUTHORITATIVE-NULL-HASH |
| RET-EVID-009 | AUTHORITATIVE-NULL-HASH | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AUTHORITATIVE-NULL-HASH |
| RET-EVID-009 | AUTHORITATIVE-NULL-HASH | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AUTHORITATIVE-NULL-HASH |
| RET-EVID-009 | REFERENCE-MISSING-HASH-COMPONENT | unit | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-U-REFERENCE-MISSING-HASH-COMPONENT |
| RET-EVID-009 | REFERENCE-MISSING-HASH-COMPONENT | PostgreSQL integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-REFERENCE-MISSING-HASH-COMPONENT |
| RET-EVID-009 | REFERENCE-MISSING-HASH-COMPONENT | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-REFERENCE-MISSING-HASH-COMPONENT |
| RET-EVID-010 | AF3A-ALL-INELIGIBLE-AUTHORIZED-EMPTY | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-ALL-INELIGIBLE-AUTHORIZED-EMPTY |
| RET-EVID-010 | AF3B-HYBRID-ALL-INELIGIBLE-AUTHORIZED-EMPTY-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-ALL-INELIGIBLE-AUTHORIZED-EMPTY-REGRESSION |
| RET-EVID-010 | AF3C-HTTP-ALL-INELIGIBLE-AUTHORIZED-EMPTY | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-ALL-INELIGIBLE-AUTHORIZED-EMPTY |
| RET-FUT-001 | DEFAULT | future consuming-phase acceptance | FUTURE_CONSUMER | FUTURE | REQUIRED_NOT_YET_IMPLEMENTED | O-FUTURE-DEFAULT |
| RET-FUT-002 | DEFAULT | future consuming-phase acceptance | FUTURE_CONSUMER | FUTURE | REQUIRED_NOT_YET_IMPLEMENTED | O-FUTURE-DEFAULT |
| RET-FUT-003 | DEFAULT | future consuming-phase acceptance | FUTURE_CONSUMER | FUTURE | REQUIRED_NOT_YET_IMPLEMENTED | O-FUTURE-DEFAULT |
| RET-FUT-004 | DEFAULT | future consuming-phase acceptance | FUTURE_CONSUMER | FUTURE | REQUIRED_NOT_YET_IMPLEMENTED | O-FUTURE-DEFAULT |
| RET-INJ-001 | AF3A-KEYWORD-INTERNAL-RECORD | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-001 | AF3A-KEYWORD-INTERNAL-RECORD | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-001 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-001 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-001 | AF3C-PUBLIC-EVIDENCE-HTTP | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-PUBLIC-EVIDENCE-HTTP |
| RET-INJ-002 | AF3A-KEYWORD-INTERNAL-RECORD | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-002 | AF3A-KEYWORD-INTERNAL-RECORD | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-002 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-002 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-002 | AF3C-PUBLIC-EVIDENCE-HTTP | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-PUBLIC-EVIDENCE-HTTP |
| RET-INJ-003 | AF3A-KEYWORD-INTERNAL-RECORD | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-003 | AF3A-KEYWORD-INTERNAL-RECORD | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-003 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-003 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-003 | AF3C-PUBLIC-EVIDENCE-HTTP | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-PUBLIC-EVIDENCE-HTTP |
| RET-INJ-004 | AF3A-KEYWORD-INTERNAL-RECORD | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-004 | AF3A-KEYWORD-INTERNAL-RECORD | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-004 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-004 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-004 | AF3C-PUBLIC-EVIDENCE-HTTP | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-PUBLIC-EVIDENCE-HTTP |
| RET-INJ-005 | AF3A-KEYWORD-INTERNAL-RECORD | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-005 | AF3A-KEYWORD-INTERNAL-RECORD | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-005 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-005 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-005 | AF3C-PUBLIC-EVIDENCE-HTTP | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-PUBLIC-EVIDENCE-HTTP |
| RET-INJ-006 | AF3A-KEYWORD-INTERNAL-RECORD | unit | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-006 | AF3A-KEYWORD-INTERNAL-RECORD | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-KEYWORD-INTERNAL-RECORD |
| RET-INJ-006 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-006 | AF3B-HYBRID-INTERNAL-RECORD-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-INTERNAL-RECORD-REGRESSION |
| RET-INJ-006 | AF3C-PUBLIC-EVIDENCE-HTTP | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-PUBLIC-EVIDENCE-HTTP |
| RET-KEY-001 | AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF | unit | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF |
| RET-KEY-001 | AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF |
| RET-KEY-001 | AF3B-HYBRID-SCOPED-DETERMINISTIC-ORDER-CUTOFF-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-SCOPED-DETERMINISTIC-ORDER-CUTOFF-REGRESSION |
| RET-KEY-001 | AF3B-HYBRID-SCOPED-DETERMINISTIC-ORDER-CUTOFF-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-SCOPED-DETERMINISTIC-ORDER-CUTOFF-REGRESSION |
| RET-KEY-001 | AF3C-HTTP-SCOPED-DETERMINISTIC-ORDER-CUTOFF | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-SCOPED-DETERMINISTIC-ORDER-CUTOFF |
| RET-KEY-002 | AF3A-CROSS-SCOPE-REVALIDATION | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-CROSS-SCOPE-REVALIDATION |
| RET-KEY-002 | AF3B-HYBRID-CROSS-SCOPE-REVALIDATION-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-CROSS-SCOPE-REVALIDATION-REGRESSION |
| RET-KEY-002 | AF3C-HTTP-CROSS-SCOPE-REVALIDATION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-CROSS-SCOPE-REVALIDATION |
| RET-KEY-003 | AF3A-NO-GLOBAL-RESULT-COUNT | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-NO-GLOBAL-RESULT-COUNT |
| RET-KEY-003 | AF3B-HYBRID-NO-GLOBAL-RESULT-COUNT-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-NO-GLOBAL-RESULT-COUNT-REGRESSION |
| RET-KEY-003 | AF3C-HTTP-NO-GLOBAL-RESULT-COUNT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-NO-GLOBAL-RESULT-COUNT |
| RET-KEY-004 | AF3A-SCOPED-REPOSITORY-ONLY | unit | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-U-AF3A-SCOPED-REPOSITORY-ONLY |
| RET-KEY-004 | AF3A-SCOPED-REPOSITORY-ONLY | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-AF3A-SCOPED-REPOSITORY-ONLY |
| RET-KEY-004 | AF3B-HYBRID-SCOPED-REPOSITORY-ONLY-REGRESSION | unit | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-AF3B-HYBRID-SCOPED-REPOSITORY-ONLY-REGRESSION |
| RET-KEY-004 | AF3B-HYBRID-SCOPED-REPOSITORY-ONLY-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-SCOPED-REPOSITORY-ONLY-REGRESSION |
| RET-KEY-004 | AF3C-HTTP-SCOPED-REPOSITORY-ONLY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-SCOPED-REPOSITORY-ONLY |
| RET-PRIV-001 | DEFAULT | PostgreSQL integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PRIV-001 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PRIV-002 | DEFAULT | PostgreSQL integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PRIV-002 | DEFAULT | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PRIV-003 | CITATION-RESOLUTION-SUCCESS-ALL-SINK-SECRECY | PostgreSQL integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CITATION-RESOLUTION-SUCCESS-ALL-SINK-SECRECY |
| RET-PRIV-003 | CITATION-RESOLUTION-SUCCESS-ALL-SINK-SECRECY | HTTP integration | AF3C_PUBLIC_CITATION | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CITATION-RESOLUTION-SUCCESS-ALL-SINK-SECRECY |
| RET-PRIV-003 | RETRIEVAL-EMPTY-SUCCESS-ALL-SINK-SECRECY | PostgreSQL integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-RETRIEVAL-EMPTY-SUCCESS-ALL-SINK-SECRECY |
| RET-PRIV-003 | RETRIEVAL-EMPTY-SUCCESS-ALL-SINK-SECRECY | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-RETRIEVAL-EMPTY-SUCCESS-ALL-SINK-SECRECY |
| RET-PRIV-003 | RETRIEVAL-EVIDENCE-SUCCESS-ALL-SINK-SECRECY | PostgreSQL integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-RETRIEVAL-EVIDENCE-SUCCESS-ALL-SINK-SECRECY |
| RET-PRIV-003 | RETRIEVAL-EVIDENCE-SUCCESS-ALL-SINK-SECRECY | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-RETRIEVAL-EVIDENCE-SUCCESS-ALL-SINK-SECRECY |
| RET-PRIV-004 | AF3B-HYBRID-FINAL-COMMIT-ALL-SINK-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-FINAL-COMMIT-ALL-SINK-REGRESSION |
| RET-PRIV-004 | AF3B-HYBRID-LATER-BATCH-ALL-SINK-REGRESSION | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-LATER-BATCH-ALL-SINK-REGRESSION |
| RET-PRIV-004 | AF3C-HTTP-HYBRID-FINAL-COMMIT-FAILURE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-HYBRID-FINAL-COMMIT-FAILURE |
| RET-PRIV-004 | AF3C-HTTP-HYBRID-LATER-BATCH-FAILURE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-HYBRID-LATER-BATCH-FAILURE |
| RET-PRIV-004 | EMBEDDING-FATAL-ALL-SINK-SECRECY | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-EMBEDDING-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | EMBEDDING-FATAL-ALL-SINK-SECRECY | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-EMBEDDING-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | EMBEDDING-FATAL-ALL-SINK-SECRECY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-EMBEDDING-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | FINAL-AUTHORIZATION-STATEMENT-FATAL-ALL-SINK-SECRECY | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-FINAL-AUTHORIZATION-STATEMENT-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | FINAL-AUTHORIZATION-STATEMENT-FATAL-ALL-SINK-SECRECY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-FINAL-AUTHORIZATION-STATEMENT-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | FINAL-COMMIT-ALL-SINK-SECRECY | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-FINAL-COMMIT-ALL-SINK-SECRECY |
| RET-PRIV-004 | FINAL-COMMIT-ALL-SINK-SECRECY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-FINAL-COMMIT-ALL-SINK-SECRECY |
| RET-PRIV-004 | KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY | PostgreSQL integration | AF3A_KEYWORD | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | LATER-BATCH-ALL-SINK-SECRECY | PostgreSQL integration | AF3A_FINAL_VALIDATOR | AF-3A | MERGED_IMPLEMENTED_NOT_REVALIDATED_IN_THIS_DOC_GATE | O-PG-LATER-BATCH-ALL-SINK-SECRECY |
| RET-PRIV-004 | LATER-BATCH-ALL-SINK-SECRECY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-LATER-BATCH-ALL-SINK-SECRECY |
| RET-PRIV-004 | PROVIDER-FATAL-ALL-SINK-SECRECY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-PROVIDER-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | PROVIDER-FATAL-ALL-SINK-SECRECY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-PROVIDER-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-004 | PROVIDER-FATAL-ALL-SINK-SECRECY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-PROVIDER-FATAL-ALL-SINK-SECRECY |
| RET-PRIV-005 | PUBLIC-RESPONSE-CACHE-MATRIX | PostgreSQL integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-PUBLIC-RESPONSE-CACHE-MATRIX |
| RET-PRIV-005 | PUBLIC-RESPONSE-CACHE-MATRIX | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-PUBLIC-RESPONSE-CACHE-MATRIX |
| RET-PRIV-006 | AF3B-HYBRID-TELEMETRY-BOUNDS | PostgreSQL integration | AF3B_HYBRID_REGRESSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-AF3B-HYBRID-TELEMETRY-BOUNDS |
| RET-PRIV-006 | AF3C-HTTP-TELEMETRY-BOUNDS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-AF3C-HTTP-TELEMETRY-BOUNDS |
| RET-PROV-001 | CONTENT-ENCODING-ABSENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-ENCODING-ABSENT |
| RET-PROV-001 | CONTENT-ENCODING-ABSENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-ENCODING-ABSENT |
| RET-PROV-001 | CONTENT-ENCODING-ABSENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-ENCODING-ABSENT |
| RET-PROV-001 | CONTENT-ENCODING-ABSENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-ENCODING-ABSENT |
| RET-PROV-001 | CONTENT-ENCODING-GZIP | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-ENCODING-GZIP |
| RET-PROV-001 | CONTENT-ENCODING-GZIP | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-ENCODING-GZIP |
| RET-PROV-001 | CONTENT-ENCODING-GZIP | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-ENCODING-GZIP |
| RET-PROV-001 | CONTENT-ENCODING-GZIP | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-ENCODING-GZIP |
| RET-PROV-001 | CONTENT-ENCODING-IDENTITY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-ENCODING-IDENTITY |
| RET-PROV-001 | CONTENT-ENCODING-IDENTITY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-ENCODING-IDENTITY |
| RET-PROV-001 | CONTENT-ENCODING-IDENTITY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-ENCODING-IDENTITY |
| RET-PROV-001 | CONTENT-ENCODING-IDENTITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-ENCODING-IDENTITY |
| RET-PROV-001 | CONTENT-TYPE-EXPLICIT-UTF8 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-EXPLICIT-UTF8 |
| RET-PROV-001 | CONTENT-TYPE-EXPLICIT-UTF8 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-EXPLICIT-UTF8 |
| RET-PROV-001 | CONTENT-TYPE-EXPLICIT-UTF8 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-EXPLICIT-UTF8 |
| RET-PROV-001 | CONTENT-TYPE-EXPLICIT-UTF8 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-EXPLICIT-UTF8 |
| RET-PROV-001 | CONTENT-TYPE-NO-PARAMETER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-NO-PARAMETER |
| RET-PROV-001 | CONTENT-TYPE-NO-PARAMETER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-NO-PARAMETER |
| RET-PROV-001 | CONTENT-TYPE-NO-PARAMETER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-NO-PARAMETER |
| RET-PROV-001 | CONTENT-TYPE-NO-PARAMETER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-NO-PARAMETER |
| RET-PROV-001 | DOCUMENT-NULL-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENT-NULL-ELEMENT |
| RET-PROV-001 | DOCUMENT-NULL-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENT-NULL-ELEMENT |
| RET-PROV-001 | DOCUMENT-NULL-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENT-NULL-ELEMENT |
| RET-PROV-001 | DOCUMENT-NULL-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENT-NULL-ELEMENT |
| RET-PROV-001 | DOCUMENT-STRING-EXACT-4096 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENT-STRING-EXACT-4096 |
| RET-PROV-001 | DOCUMENT-STRING-EXACT-4096 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENT-STRING-EXACT-4096 |
| RET-PROV-001 | DOCUMENT-STRING-EXACT-4096 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENT-STRING-EXACT-4096 |
| RET-PROV-001 | DOCUMENT-STRING-EXACT-4096 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENT-STRING-EXACT-4096 |
| RET-PROV-001 | DOCUMENTS-NULL-CONTAINER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENTS-NULL-CONTAINER |
| RET-PROV-001 | DOCUMENTS-NULL-CONTAINER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENTS-NULL-CONTAINER |
| RET-PROV-001 | DOCUMENTS-NULL-CONTAINER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENTS-NULL-CONTAINER |
| RET-PROV-001 | DOCUMENTS-NULL-CONTAINER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENTS-NULL-CONTAINER |
| RET-PROV-001 | METADATA-BOOLEAN-FALSE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-BOOLEAN-FALSE |
| RET-PROV-001 | METADATA-BOOLEAN-FALSE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-BOOLEAN-FALSE |
| RET-PROV-001 | METADATA-BOOLEAN-FALSE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-BOOLEAN-FALSE |
| RET-PROV-001 | METADATA-BOOLEAN-FALSE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-BOOLEAN-FALSE |
| RET-PROV-001 | METADATA-BOOLEAN-TRUE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-BOOLEAN-TRUE |
| RET-PROV-001 | METADATA-BOOLEAN-TRUE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-BOOLEAN-TRUE |
| RET-PROV-001 | METADATA-BOOLEAN-TRUE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-BOOLEAN-TRUE |
| RET-PROV-001 | METADATA-BOOLEAN-TRUE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-BOOLEAN-TRUE |
| RET-PROV-001 | METADATA-EMPTY-OBJECT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-EMPTY-OBJECT |
| RET-PROV-001 | METADATA-EMPTY-OBJECT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-EMPTY-OBJECT |
| RET-PROV-001 | METADATA-EMPTY-OBJECT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-EMPTY-OBJECT |
| RET-PROV-001 | METADATA-EMPTY-OBJECT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-EMPTY-OBJECT |
| RET-PROV-001 | METADATA-ENTRIES-EXACT-32 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-ENTRIES-EXACT-32 |
| RET-PROV-001 | METADATA-ENTRIES-EXACT-32 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-ENTRIES-EXACT-32 |
| RET-PROV-001 | METADATA-ENTRIES-EXACT-32 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-ENTRIES-EXACT-32 |
| RET-PROV-001 | METADATA-ENTRIES-EXACT-32 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-ENTRIES-EXACT-32 |
| RET-PROV-001 | METADATA-FINITE-NEGATIVE-NUMBER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-FINITE-NEGATIVE-NUMBER |
| RET-PROV-001 | METADATA-FINITE-NEGATIVE-NUMBER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-FINITE-NEGATIVE-NUMBER |
| RET-PROV-001 | METADATA-FINITE-NEGATIVE-NUMBER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-FINITE-NEGATIVE-NUMBER |
| RET-PROV-001 | METADATA-FINITE-NEGATIVE-NUMBER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-FINITE-NEGATIVE-NUMBER |
| RET-PROV-001 | METADATA-FINITE-POSITIVE-NUMBER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-FINITE-POSITIVE-NUMBER |
| RET-PROV-001 | METADATA-FINITE-POSITIVE-NUMBER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-FINITE-POSITIVE-NUMBER |
| RET-PROV-001 | METADATA-FINITE-POSITIVE-NUMBER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-FINITE-POSITIVE-NUMBER |
| RET-PROV-001 | METADATA-FINITE-POSITIVE-NUMBER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-FINITE-POSITIVE-NUMBER |
| RET-PROV-001 | METADATA-FINITE-ZERO-NUMBER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-FINITE-ZERO-NUMBER |
| RET-PROV-001 | METADATA-FINITE-ZERO-NUMBER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-FINITE-ZERO-NUMBER |
| RET-PROV-001 | METADATA-FINITE-ZERO-NUMBER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-FINITE-ZERO-NUMBER |
| RET-PROV-001 | METADATA-FINITE-ZERO-NUMBER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-FINITE-ZERO-NUMBER |
| RET-PROV-001 | METADATA-KEY-EXACT-128 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-KEY-EXACT-128 |
| RET-PROV-001 | METADATA-KEY-EXACT-128 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-KEY-EXACT-128 |
| RET-PROV-001 | METADATA-KEY-EXACT-128 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-KEY-EXACT-128 |
| RET-PROV-001 | METADATA-KEY-EXACT-128 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-KEY-EXACT-128 |
| RET-PROV-001 | METADATA-NULL-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-NULL-ELEMENT |
| RET-PROV-001 | METADATA-NULL-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-NULL-ELEMENT |
| RET-PROV-001 | METADATA-NULL-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-NULL-ELEMENT |
| RET-PROV-001 | METADATA-NULL-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-NULL-ELEMENT |
| RET-PROV-001 | METADATA-STRING-EXACT-1024 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-STRING-EXACT-1024 |
| RET-PROV-001 | METADATA-STRING-EXACT-1024 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-STRING-EXACT-1024 |
| RET-PROV-001 | METADATA-STRING-EXACT-1024 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-STRING-EXACT-1024 |
| RET-PROV-001 | METADATA-STRING-EXACT-1024 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-STRING-EXACT-1024 |
| RET-PROV-001 | METADATA-STRING-VALUE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-STRING-VALUE |
| RET-PROV-001 | METADATA-STRING-VALUE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-STRING-VALUE |
| RET-PROV-001 | METADATA-STRING-VALUE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-STRING-VALUE |
| RET-PROV-001 | METADATA-STRING-VALUE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-STRING-VALUE |
| RET-PROV-001 | METADATAS-NULL-CONTAINER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATAS-NULL-CONTAINER |
| RET-PROV-001 | METADATAS-NULL-CONTAINER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATAS-NULL-CONTAINER |
| RET-PROV-001 | METADATAS-NULL-CONTAINER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATAS-NULL-CONTAINER |
| RET-PROV-001 | METADATAS-NULL-CONTAINER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATAS-NULL-CONTAINER |
| RET-PROV-002 | CONTENT-LENGTH-EXACT-1048576 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-LENGTH-EXACT-1048576 |
| RET-PROV-002 | CONTENT-LENGTH-EXACT-1048576 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-LENGTH-EXACT-1048576 |
| RET-PROV-002 | CONTENT-LENGTH-EXACT-1048576 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-LENGTH-EXACT-1048576 |
| RET-PROV-002 | STREAMED-NO-LENGTH-EXACT-1048576 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-STREAMED-NO-LENGTH-EXACT-1048576 |
| RET-PROV-002 | STREAMED-NO-LENGTH-EXACT-1048576 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-STREAMED-NO-LENGTH-EXACT-1048576 |
| RET-PROV-002 | STREAMED-NO-LENGTH-EXACT-1048576 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-STREAMED-NO-LENGTH-EXACT-1048576 |
| RET-PROV-003 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-003 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-003 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-004 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-004 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-004 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-005 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-005 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-005 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-006 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-006 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-006 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-007 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-007 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-007 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-008 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-008 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-008 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-008 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-009 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-009 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-009 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-009 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-010 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-010 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-010 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-010 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-011 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-011 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-011 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-011 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-012 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-012 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-012 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-012 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-013 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-013 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-013 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-013 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-014 | DEPTH-16-GUARD-PASS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEPTH-16-GUARD-PASS |
| RET-PROV-014 | DEPTH-16-GUARD-PASS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEPTH-16-GUARD-PASS |
| RET-PROV-014 | DEPTH-16-GUARD-PASS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEPTH-16-GUARD-PASS |
| RET-PROV-014 | DEPTH-16-GUARD-PASS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEPTH-16-GUARD-PASS |
| RET-PROV-014 | DEPTH-17-GUARD-FAIL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEPTH-17-GUARD-FAIL |
| RET-PROV-014 | DEPTH-17-GUARD-FAIL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEPTH-17-GUARD-FAIL |
| RET-PROV-014 | DEPTH-17-GUARD-FAIL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEPTH-17-GUARD-FAIL |
| RET-PROV-014 | DEPTH-17-GUARD-FAIL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEPTH-17-GUARD-FAIL |
| RET-PROV-015 | WIRE-1E400 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-1E400 |
| RET-PROV-015 | WIRE-1E400 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-1E400 |
| RET-PROV-015 | WIRE-1E400 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-1E400 |
| RET-PROV-015 | WIRE-1E400 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-1E400 |
| RET-PROV-015 | WIRE-NAN | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-NAN |
| RET-PROV-015 | WIRE-NAN | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-NAN |
| RET-PROV-015 | WIRE-NAN | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-NAN |
| RET-PROV-015 | WIRE-NAN | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-NAN |
| RET-PROV-015 | WIRE-NEGATIVE-INFINITY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-NEGATIVE-INFINITY |
| RET-PROV-015 | WIRE-NEGATIVE-INFINITY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-NEGATIVE-INFINITY |
| RET-PROV-015 | WIRE-NEGATIVE-INFINITY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-NEGATIVE-INFINITY |
| RET-PROV-015 | WIRE-NEGATIVE-INFINITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-NEGATIVE-INFINITY |
| RET-PROV-015 | WIRE-POSITIVE-INFINITY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-POSITIVE-INFINITY |
| RET-PROV-015 | WIRE-POSITIVE-INFINITY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-POSITIVE-INFINITY |
| RET-PROV-015 | WIRE-POSITIVE-INFINITY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-POSITIVE-INFINITY |
| RET-PROV-015 | WIRE-POSITIVE-INFINITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-POSITIVE-INFINITY |
| RET-PROV-016 | ARRAY-TOP-LEVEL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-ARRAY-TOP-LEVEL |
| RET-PROV-016 | ARRAY-TOP-LEVEL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-ARRAY-TOP-LEVEL |
| RET-PROV-016 | ARRAY-TOP-LEVEL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-ARRAY-TOP-LEVEL |
| RET-PROV-016 | ARRAY-TOP-LEVEL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-ARRAY-TOP-LEVEL |
| RET-PROV-016 | CONTENT-ENCODING-STACKED | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-ENCODING-STACKED |
| RET-PROV-016 | CONTENT-ENCODING-STACKED | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-ENCODING-STACKED |
| RET-PROV-016 | CONTENT-ENCODING-STACKED | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-ENCODING-STACKED |
| RET-PROV-016 | CONTENT-ENCODING-STACKED | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-ENCODING-STACKED |
| RET-PROV-016 | CONTENT-ENCODING-UNSUPPORTED | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-ENCODING-UNSUPPORTED |
| RET-PROV-016 | CONTENT-ENCODING-UNSUPPORTED | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-ENCODING-UNSUPPORTED |
| RET-PROV-016 | CONTENT-ENCODING-UNSUPPORTED | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-ENCODING-UNSUPPORTED |
| RET-PROV-016 | CONTENT-ENCODING-UNSUPPORTED | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-ENCODING-UNSUPPORTED |
| RET-PROV-016 | CONTENT-TYPE-EXTRA-PARAMETER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-EXTRA-PARAMETER |
| RET-PROV-016 | CONTENT-TYPE-EXTRA-PARAMETER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-EXTRA-PARAMETER |
| RET-PROV-016 | CONTENT-TYPE-EXTRA-PARAMETER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-EXTRA-PARAMETER |
| RET-PROV-016 | CONTENT-TYPE-EXTRA-PARAMETER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-EXTRA-PARAMETER |
| RET-PROV-016 | CONTENT-TYPE-FORBIDDEN-CHARSET | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-FORBIDDEN-CHARSET |
| RET-PROV-016 | CONTENT-TYPE-FORBIDDEN-CHARSET | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-FORBIDDEN-CHARSET |
| RET-PROV-016 | CONTENT-TYPE-FORBIDDEN-CHARSET | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-FORBIDDEN-CHARSET |
| RET-PROV-016 | CONTENT-TYPE-FORBIDDEN-CHARSET | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-FORBIDDEN-CHARSET |
| RET-PROV-016 | CONTENT-TYPE-MISSING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-MISSING |
| RET-PROV-016 | CONTENT-TYPE-MISSING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-MISSING |
| RET-PROV-016 | CONTENT-TYPE-MISSING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-MISSING |
| RET-PROV-016 | CONTENT-TYPE-MISSING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-MISSING |
| RET-PROV-016 | CONTENT-TYPE-NONJSON | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-NONJSON |
| RET-PROV-016 | CONTENT-TYPE-NONJSON | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-NONJSON |
| RET-PROV-016 | CONTENT-TYPE-NONJSON | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-NONJSON |
| RET-PROV-016 | CONTENT-TYPE-NONJSON | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-NONJSON |
| RET-PROV-016 | DOCUMENT-ARRAY-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENT-ARRAY-ELEMENT |
| RET-PROV-016 | DOCUMENT-ARRAY-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENT-ARRAY-ELEMENT |
| RET-PROV-016 | DOCUMENT-ARRAY-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENT-ARRAY-ELEMENT |
| RET-PROV-016 | DOCUMENT-ARRAY-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENT-ARRAY-ELEMENT |
| RET-PROV-016 | DOCUMENT-BOOLEAN-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENT-BOOLEAN-ELEMENT |
| RET-PROV-016 | DOCUMENT-BOOLEAN-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENT-BOOLEAN-ELEMENT |
| RET-PROV-016 | DOCUMENT-BOOLEAN-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENT-BOOLEAN-ELEMENT |
| RET-PROV-016 | DOCUMENT-BOOLEAN-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENT-BOOLEAN-ELEMENT |
| RET-PROV-016 | DOCUMENT-NUMBER-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENT-NUMBER-ELEMENT |
| RET-PROV-016 | DOCUMENT-NUMBER-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENT-NUMBER-ELEMENT |
| RET-PROV-016 | DOCUMENT-NUMBER-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENT-NUMBER-ELEMENT |
| RET-PROV-016 | DOCUMENT-NUMBER-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENT-NUMBER-ELEMENT |
| RET-PROV-016 | DOCUMENT-OBJECT-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENT-OBJECT-ELEMENT |
| RET-PROV-016 | DOCUMENT-OBJECT-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENT-OBJECT-ELEMENT |
| RET-PROV-016 | DOCUMENT-OBJECT-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENT-OBJECT-ELEMENT |
| RET-PROV-016 | DOCUMENT-OBJECT-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENT-OBJECT-ELEMENT |
| RET-PROV-016 | DOCUMENTS-INNER-LENGTH | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENTS-INNER-LENGTH |
| RET-PROV-016 | DOCUMENTS-INNER-LENGTH | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENTS-INNER-LENGTH |
| RET-PROV-016 | DOCUMENTS-INNER-LENGTH | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENTS-INNER-LENGTH |
| RET-PROV-016 | DOCUMENTS-INNER-LENGTH | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENTS-INNER-LENGTH |
| RET-PROV-016 | DOCUMENTS-OUTER-CARDINALITY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DOCUMENTS-OUTER-CARDINALITY |
| RET-PROV-016 | DOCUMENTS-OUTER-CARDINALITY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DOCUMENTS-OUTER-CARDINALITY |
| RET-PROV-016 | DOCUMENTS-OUTER-CARDINALITY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENTS-OUTER-CARDINALITY |
| RET-PROV-016 | DOCUMENTS-OUTER-CARDINALITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENTS-OUTER-CARDINALITY |
| RET-PROV-016 | DUPLICATE-TOP-LEVEL-KEY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DUPLICATE-TOP-LEVEL-KEY |
| RET-PROV-016 | DUPLICATE-TOP-LEVEL-KEY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DUPLICATE-TOP-LEVEL-KEY |
| RET-PROV-016 | DUPLICATE-TOP-LEVEL-KEY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DUPLICATE-TOP-LEVEL-KEY |
| RET-PROV-016 | DUPLICATE-TOP-LEVEL-KEY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DUPLICATE-TOP-LEVEL-KEY |
| RET-PROV-016 | INVALID-UTF8 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-INVALID-UTF8 |
| RET-PROV-016 | INVALID-UTF8 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-INVALID-UTF8 |
| RET-PROV-016 | INVALID-UTF8 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-INVALID-UTF8 |
| RET-PROV-016 | INVALID-UTF8 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-INVALID-UTF8 |
| RET-PROV-016 | METADATA-ARRAY-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-ARRAY-ELEMENT |
| RET-PROV-016 | METADATA-ARRAY-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-ARRAY-ELEMENT |
| RET-PROV-016 | METADATA-ARRAY-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-ARRAY-ELEMENT |
| RET-PROV-016 | METADATA-ARRAY-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-ARRAY-ELEMENT |
| RET-PROV-016 | METADATA-BOOLEAN-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-BOOLEAN-ELEMENT |
| RET-PROV-016 | METADATA-BOOLEAN-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-BOOLEAN-ELEMENT |
| RET-PROV-016 | METADATA-BOOLEAN-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-BOOLEAN-ELEMENT |
| RET-PROV-016 | METADATA-BOOLEAN-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-BOOLEAN-ELEMENT |
| RET-PROV-016 | METADATA-NESTED-ARRAY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-NESTED-ARRAY |
| RET-PROV-016 | METADATA-NESTED-ARRAY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-NESTED-ARRAY |
| RET-PROV-016 | METADATA-NESTED-ARRAY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-NESTED-ARRAY |
| RET-PROV-016 | METADATA-NESTED-ARRAY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-NESTED-ARRAY |
| RET-PROV-016 | METADATA-NESTED-OBJECT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-NESTED-OBJECT |
| RET-PROV-016 | METADATA-NESTED-OBJECT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-NESTED-OBJECT |
| RET-PROV-016 | METADATA-NESTED-OBJECT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-NESTED-OBJECT |
| RET-PROV-016 | METADATA-NESTED-OBJECT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-NESTED-OBJECT |
| RET-PROV-016 | METADATA-NONFINITE-LITERAL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-NONFINITE-LITERAL |
| RET-PROV-016 | METADATA-NONFINITE-LITERAL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-NONFINITE-LITERAL |
| RET-PROV-016 | METADATA-NONFINITE-LITERAL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-NONFINITE-LITERAL |
| RET-PROV-016 | METADATA-NONFINITE-LITERAL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-NONFINITE-LITERAL |
| RET-PROV-016 | METADATA-NULL-VALUE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-NULL-VALUE |
| RET-PROV-016 | METADATA-NULL-VALUE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-NULL-VALUE |
| RET-PROV-016 | METADATA-NULL-VALUE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-NULL-VALUE |
| RET-PROV-016 | METADATA-NULL-VALUE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-NULL-VALUE |
| RET-PROV-016 | METADATA-NUMBER-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-NUMBER-ELEMENT |
| RET-PROV-016 | METADATA-NUMBER-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-NUMBER-ELEMENT |
| RET-PROV-016 | METADATA-NUMBER-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-NUMBER-ELEMENT |
| RET-PROV-016 | METADATA-NUMBER-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-NUMBER-ELEMENT |
| RET-PROV-016 | METADATA-STRING-ELEMENT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-STRING-ELEMENT |
| RET-PROV-016 | METADATA-STRING-ELEMENT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-STRING-ELEMENT |
| RET-PROV-016 | METADATA-STRING-ELEMENT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-STRING-ELEMENT |
| RET-PROV-016 | METADATA-STRING-ELEMENT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-STRING-ELEMENT |
| RET-PROV-016 | METADATA-UNSUPPORTED-RANGE-NUMBER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATA-UNSUPPORTED-RANGE-NUMBER |
| RET-PROV-016 | METADATA-UNSUPPORTED-RANGE-NUMBER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATA-UNSUPPORTED-RANGE-NUMBER |
| RET-PROV-016 | METADATA-UNSUPPORTED-RANGE-NUMBER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATA-UNSUPPORTED-RANGE-NUMBER |
| RET-PROV-016 | METADATA-UNSUPPORTED-RANGE-NUMBER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATA-UNSUPPORTED-RANGE-NUMBER |
| RET-PROV-016 | METADATAS-INNER-LENGTH | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATAS-INNER-LENGTH |
| RET-PROV-016 | METADATAS-INNER-LENGTH | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATAS-INNER-LENGTH |
| RET-PROV-016 | METADATAS-INNER-LENGTH | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATAS-INNER-LENGTH |
| RET-PROV-016 | METADATAS-INNER-LENGTH | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATAS-INNER-LENGTH |
| RET-PROV-016 | METADATAS-OUTER-CARDINALITY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-METADATAS-OUTER-CARDINALITY |
| RET-PROV-016 | METADATAS-OUTER-CARDINALITY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-METADATAS-OUTER-CARDINALITY |
| RET-PROV-016 | METADATAS-OUTER-CARDINALITY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-METADATAS-OUTER-CARDINALITY |
| RET-PROV-016 | METADATAS-OUTER-CARDINALITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-METADATAS-OUTER-CARDINALITY |
| RET-PROV-016 | NONCANONICAL-INCLUDE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NONCANONICAL-INCLUDE |
| RET-PROV-016 | NONCANONICAL-INCLUDE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NONCANONICAL-INCLUDE |
| RET-PROV-016 | NONCANONICAL-INCLUDE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NONCANONICAL-INCLUDE |
| RET-PROV-016 | NONCANONICAL-INCLUDE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NONCANONICAL-INCLUDE |
| RET-PROV-016 | NONNULL-DATA | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NONNULL-DATA |
| RET-PROV-016 | NONNULL-DATA | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NONNULL-DATA |
| RET-PROV-016 | NONNULL-DATA | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NONNULL-DATA |
| RET-PROV-016 | NONNULL-DATA | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NONNULL-DATA |
| RET-PROV-016 | NONNULL-EMBEDDINGS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NONNULL-EMBEDDINGS |
| RET-PROV-016 | NONNULL-EMBEDDINGS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NONNULL-EMBEDDINGS |
| RET-PROV-016 | NONNULL-EMBEDDINGS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NONNULL-EMBEDDINGS |
| RET-PROV-016 | NONNULL-EMBEDDINGS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NONNULL-EMBEDDINGS |
| RET-PROV-016 | NONNULL-URIS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NONNULL-URIS |
| RET-PROV-016 | NONNULL-URIS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NONNULL-URIS |
| RET-PROV-016 | NONNULL-URIS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NONNULL-URIS |
| RET-PROV-016 | NONNULL-URIS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NONNULL-URIS |
| RET-PROV-016 | NULL-DISTANCES | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NULL-DISTANCES |
| RET-PROV-016 | NULL-DISTANCES | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NULL-DISTANCES |
| RET-PROV-016 | NULL-DISTANCES | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NULL-DISTANCES |
| RET-PROV-016 | NULL-DISTANCES | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NULL-DISTANCES |
| RET-PROV-016 | NULL-IDS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NULL-IDS |
| RET-PROV-016 | NULL-IDS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NULL-IDS |
| RET-PROV-016 | NULL-IDS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NULL-IDS |
| RET-PROV-016 | NULL-IDS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NULL-IDS |
| RET-PROV-016 | NULL-INCLUDE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NULL-INCLUDE |
| RET-PROV-016 | NULL-INCLUDE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NULL-INCLUDE |
| RET-PROV-016 | NULL-INCLUDE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NULL-INCLUDE |
| RET-PROV-016 | NULL-INCLUDE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NULL-INCLUDE |
| RET-PROV-016 | SCALAR-TOP-LEVEL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SCALAR-TOP-LEVEL |
| RET-PROV-016 | SCALAR-TOP-LEVEL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-SCALAR-TOP-LEVEL |
| RET-PROV-016 | SCALAR-TOP-LEVEL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-SCALAR-TOP-LEVEL |
| RET-PROV-016 | SCALAR-TOP-LEVEL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SCALAR-TOP-LEVEL |
| RET-PROV-016 | UNKNOWN-TOP-LEVEL-KEY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-UNKNOWN-TOP-LEVEL-KEY |
| RET-PROV-016 | UNKNOWN-TOP-LEVEL-KEY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-UNKNOWN-TOP-LEVEL-KEY |
| RET-PROV-016 | UNKNOWN-TOP-LEVEL-KEY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-UNKNOWN-TOP-LEVEL-KEY |
| RET-PROV-016 | UNKNOWN-TOP-LEVEL-KEY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-UNKNOWN-TOP-LEVEL-KEY |
| RET-PROV-016 | UTF8-BOM | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-UTF8-BOM |
| RET-PROV-016 | UTF8-BOM | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-UTF8-BOM |
| RET-PROV-016 | UTF8-BOM | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-UTF8-BOM |
| RET-PROV-016 | UTF8-BOM | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-UTF8-BOM |
| RET-PROV-017 | MISSING-DATA | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-DATA |
| RET-PROV-017 | MISSING-DATA | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-DATA |
| RET-PROV-017 | MISSING-DATA | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-DATA |
| RET-PROV-017 | MISSING-DATA | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-DATA |
| RET-PROV-017 | MISSING-DISTANCES | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-DISTANCES |
| RET-PROV-017 | MISSING-DISTANCES | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-DISTANCES |
| RET-PROV-017 | MISSING-DISTANCES | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-DISTANCES |
| RET-PROV-017 | MISSING-DISTANCES | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-DISTANCES |
| RET-PROV-017 | MISSING-DOCUMENTS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-DOCUMENTS |
| RET-PROV-017 | MISSING-DOCUMENTS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-DOCUMENTS |
| RET-PROV-017 | MISSING-DOCUMENTS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-DOCUMENTS |
| RET-PROV-017 | MISSING-DOCUMENTS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-DOCUMENTS |
| RET-PROV-017 | MISSING-EMBEDDINGS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-EMBEDDINGS |
| RET-PROV-017 | MISSING-EMBEDDINGS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-EMBEDDINGS |
| RET-PROV-017 | MISSING-EMBEDDINGS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-EMBEDDINGS |
| RET-PROV-017 | MISSING-EMBEDDINGS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-EMBEDDINGS |
| RET-PROV-017 | MISSING-IDS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-IDS |
| RET-PROV-017 | MISSING-IDS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-IDS |
| RET-PROV-017 | MISSING-IDS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-IDS |
| RET-PROV-017 | MISSING-IDS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-IDS |
| RET-PROV-017 | MISSING-INCLUDE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-INCLUDE |
| RET-PROV-017 | MISSING-INCLUDE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-INCLUDE |
| RET-PROV-017 | MISSING-INCLUDE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-INCLUDE |
| RET-PROV-017 | MISSING-INCLUDE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-INCLUDE |
| RET-PROV-017 | MISSING-METADATAS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-METADATAS |
| RET-PROV-017 | MISSING-METADATAS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-METADATAS |
| RET-PROV-017 | MISSING-METADATAS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-METADATAS |
| RET-PROV-017 | MISSING-METADATAS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-METADATAS |
| RET-PROV-017 | MISSING-URIS | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-URIS |
| RET-PROV-017 | MISSING-URIS | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-URIS |
| RET-PROV-017 | MISSING-URIS | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-URIS |
| RET-PROV-017 | MISSING-URIS | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-URIS |
| RET-PROV-018 | DISTANCES-OUTER-CARDINALITY-TWO | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DISTANCES-OUTER-CARDINALITY-TWO |
| RET-PROV-018 | DISTANCES-OUTER-CARDINALITY-TWO | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DISTANCES-OUTER-CARDINALITY-TWO |
| RET-PROV-018 | DISTANCES-OUTER-CARDINALITY-TWO | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DISTANCES-OUTER-CARDINALITY-TWO |
| RET-PROV-018 | DISTANCES-OUTER-CARDINALITY-TWO | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DISTANCES-OUTER-CARDINALITY-TWO |
| RET-PROV-018 | IDS-DISTANCES-INNER-LENGTH-MISMATCH | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-IDS-DISTANCES-INNER-LENGTH-MISMATCH |
| RET-PROV-018 | IDS-DISTANCES-INNER-LENGTH-MISMATCH | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-IDS-DISTANCES-INNER-LENGTH-MISMATCH |
| RET-PROV-018 | IDS-DISTANCES-INNER-LENGTH-MISMATCH | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-IDS-DISTANCES-INNER-LENGTH-MISMATCH |
| RET-PROV-018 | IDS-DISTANCES-INNER-LENGTH-MISMATCH | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-IDS-DISTANCES-INNER-LENGTH-MISMATCH |
| RET-PROV-018 | IDS-OUTER-CARDINALITY-ZERO | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-IDS-OUTER-CARDINALITY-ZERO |
| RET-PROV-018 | IDS-OUTER-CARDINALITY-ZERO | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-IDS-OUTER-CARDINALITY-ZERO |
| RET-PROV-018 | IDS-OUTER-CARDINALITY-ZERO | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-IDS-OUTER-CARDINALITY-ZERO |
| RET-PROV-018 | IDS-OUTER-CARDINALITY-ZERO | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-IDS-OUTER-CARDINALITY-ZERO |
| RET-PROV-019 | R10-C40-P40-ACCEPT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-R10-C40-P40-ACCEPT |
| RET-PROV-019 | R10-C40-P40-ACCEPT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-R10-C40-P40-ACCEPT |
| RET-PROV-019 | R10-C40-P40-ACCEPT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-R10-C40-P40-ACCEPT |
| RET-PROV-019 | R10-C40-P40-ACCEPT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-R10-C40-P40-ACCEPT |
| RET-PROV-019 | R10-C40-P41-FATAL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-R10-C40-P41-FATAL |
| RET-PROV-019 | R10-C40-P41-FATAL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-R10-C40-P41-FATAL |
| RET-PROV-019 | R10-C40-P41-FATAL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-R10-C40-P41-FATAL |
| RET-PROV-019 | R10-C40-P41-FATAL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-R10-C40-P41-FATAL |
| RET-PROV-019 | R50-C128-P128-ACCEPT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-R50-C128-P128-ACCEPT |
| RET-PROV-019 | R50-C128-P128-ACCEPT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-R50-C128-P128-ACCEPT |
| RET-PROV-019 | R50-C128-P128-ACCEPT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-R50-C128-P128-ACCEPT |
| RET-PROV-019 | R50-C128-P128-ACCEPT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-R50-C128-P128-ACCEPT |
| RET-PROV-019 | R50-C128-P129-FATAL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-R50-C128-P129-FATAL |
| RET-PROV-019 | R50-C128-P129-FATAL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-R50-C128-P129-FATAL |
| RET-PROV-019 | R50-C128-P129-FATAL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-R50-C128-P129-FATAL |
| RET-PROV-019 | R50-C128-P129-FATAL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-R50-C128-P129-FATAL |
| RET-PROV-020 | CONTENT-TYPE-EXPLICIT-UTF8 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-EXPLICIT-UTF8 |
| RET-PROV-020 | CONTENT-TYPE-EXPLICIT-UTF8 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-EXPLICIT-UTF8 |
| RET-PROV-020 | CONTENT-TYPE-EXPLICIT-UTF8 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-EXPLICIT-UTF8 |
| RET-PROV-020 | CONTENT-TYPE-EXPLICIT-UTF8 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-EXPLICIT-UTF8 |
| RET-PROV-020 | CONTENT-TYPE-EXTRA-PARAMETER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-EXTRA-PARAMETER |
| RET-PROV-020 | CONTENT-TYPE-EXTRA-PARAMETER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-EXTRA-PARAMETER |
| RET-PROV-020 | CONTENT-TYPE-EXTRA-PARAMETER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-EXTRA-PARAMETER |
| RET-PROV-020 | CONTENT-TYPE-EXTRA-PARAMETER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-EXTRA-PARAMETER |
| RET-PROV-020 | CONTENT-TYPE-MISSING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-MISSING |
| RET-PROV-020 | CONTENT-TYPE-MISSING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-MISSING |
| RET-PROV-020 | CONTENT-TYPE-MISSING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-MISSING |
| RET-PROV-020 | CONTENT-TYPE-MISSING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-MISSING |
| RET-PROV-020 | CONTENT-TYPE-NONJSON | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONTENT-TYPE-NONJSON |
| RET-PROV-020 | CONTENT-TYPE-NONJSON | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONTENT-TYPE-NONJSON |
| RET-PROV-020 | CONTENT-TYPE-NONJSON | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONTENT-TYPE-NONJSON |
| RET-PROV-020 | CONTENT-TYPE-NONJSON | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONTENT-TYPE-NONJSON |
| RET-PROV-020 | EXACT-VERSION-CONTROL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-EXACT-VERSION-CONTROL |
| RET-PROV-020 | EXACT-VERSION-CONTROL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-EXACT-VERSION-CONTROL |
| RET-PROV-020 | EXACT-VERSION-CONTROL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-EXACT-VERSION-CONTROL |
| RET-PROV-020 | EXACT-VERSION-CONTROL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-EXACT-VERSION-CONTROL |
| RET-PROV-020 | FORBIDDEN-CHARSET | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-FORBIDDEN-CHARSET |
| RET-PROV-020 | FORBIDDEN-CHARSET | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-FORBIDDEN-CHARSET |
| RET-PROV-020 | FORBIDDEN-CHARSET | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-FORBIDDEN-CHARSET |
| RET-PROV-020 | FORBIDDEN-CHARSET | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-FORBIDDEN-CHARSET |
| RET-PROV-020 | FORBIDDEN-ENCODING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-FORBIDDEN-ENCODING |
| RET-PROV-020 | FORBIDDEN-ENCODING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-FORBIDDEN-ENCODING |
| RET-PROV-020 | FORBIDDEN-ENCODING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-FORBIDDEN-ENCODING |
| RET-PROV-020 | FORBIDDEN-ENCODING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-FORBIDDEN-ENCODING |
| RET-PROV-020 | GZIP-DECODED-EXACT-2097152 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-GZIP-DECODED-EXACT-2097152 |
| RET-PROV-020 | GZIP-DECODED-EXACT-2097152 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-GZIP-DECODED-EXACT-2097152 |
| RET-PROV-020 | GZIP-DECODED-EXACT-2097152 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-GZIP-DECODED-EXACT-2097152 |
| RET-PROV-020 | GZIP-DECODED-EXACT-2097152 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-GZIP-DECODED-EXACT-2097152 |
| RET-PROV-020 | GZIP-DECODED-PLUS-ONE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-GZIP-DECODED-PLUS-ONE |
| RET-PROV-020 | GZIP-DECODED-PLUS-ONE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-GZIP-DECODED-PLUS-ONE |
| RET-PROV-020 | GZIP-DECODED-PLUS-ONE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-GZIP-DECODED-PLUS-ONE |
| RET-PROV-020 | GZIP-DECODED-PLUS-ONE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-GZIP-DECODED-PLUS-ONE |
| RET-PROV-020 | IDENTITY-ENCODING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-IDENTITY-ENCODING |
| RET-PROV-020 | IDENTITY-ENCODING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-IDENTITY-ENCODING |
| RET-PROV-020 | IDENTITY-ENCODING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-IDENTITY-ENCODING |
| RET-PROV-020 | IDENTITY-ENCODING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-IDENTITY-ENCODING |
| RET-PROV-020 | JSON-ARRAY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-JSON-ARRAY |
| RET-PROV-020 | JSON-ARRAY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-JSON-ARRAY |
| RET-PROV-020 | JSON-ARRAY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-JSON-ARRAY |
| RET-PROV-020 | JSON-ARRAY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-JSON-ARRAY |
| RET-PROV-020 | JSON-BOOLEAN | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-JSON-BOOLEAN |
| RET-PROV-020 | JSON-BOOLEAN | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-JSON-BOOLEAN |
| RET-PROV-020 | JSON-BOOLEAN | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-JSON-BOOLEAN |
| RET-PROV-020 | JSON-BOOLEAN | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-JSON-BOOLEAN |
| RET-PROV-020 | JSON-NULL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-JSON-NULL |
| RET-PROV-020 | JSON-NULL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-JSON-NULL |
| RET-PROV-020 | JSON-NULL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-JSON-NULL |
| RET-PROV-020 | JSON-NULL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-JSON-NULL |
| RET-PROV-020 | JSON-NUMBER | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-JSON-NUMBER |
| RET-PROV-020 | JSON-NUMBER | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-JSON-NUMBER |
| RET-PROV-020 | JSON-NUMBER | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-JSON-NUMBER |
| RET-PROV-020 | JSON-NUMBER | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-JSON-NUMBER |
| RET-PROV-020 | JSON-OBJECT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-JSON-OBJECT |
| RET-PROV-020 | JSON-OBJECT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-JSON-OBJECT |
| RET-PROV-020 | JSON-OBJECT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-JSON-OBJECT |
| RET-PROV-020 | JSON-OBJECT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-JSON-OBJECT |
| RET-PROV-020 | MALFORMED-JSON | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MALFORMED-JSON |
| RET-PROV-020 | MALFORMED-JSON | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MALFORMED-JSON |
| RET-PROV-020 | MALFORMED-JSON | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MALFORMED-JSON |
| RET-PROV-020 | MALFORMED-JSON | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MALFORMED-JSON |
| RET-PROV-020 | STACKED-ENCODING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-STACKED-ENCODING |
| RET-PROV-020 | STACKED-ENCODING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-STACKED-ENCODING |
| RET-PROV-020 | STACKED-ENCODING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-STACKED-ENCODING |
| RET-PROV-020 | STACKED-ENCODING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-STACKED-ENCODING |
| RET-PROV-020 | VERSION-MISMATCH | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-VERSION-MISMATCH |
| RET-PROV-020 | VERSION-MISMATCH | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-VERSION-MISMATCH |
| RET-PROV-020 | VERSION-MISMATCH | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-VERSION-MISMATCH |
| RET-PROV-020 | VERSION-MISMATCH | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-VERSION-MISMATCH |
| RET-PROV-020 | WIRE-EXACT-1048576 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-EXACT-1048576 |
| RET-PROV-020 | WIRE-EXACT-1048576 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-EXACT-1048576 |
| RET-PROV-020 | WIRE-EXACT-1048576 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-EXACT-1048576 |
| RET-PROV-020 | WIRE-EXACT-1048576 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-EXACT-1048576 |
| RET-PROV-020 | WIRE-PLUS-ONE-1048577 | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-PLUS-ONE-1048577 |
| RET-PROV-020 | WIRE-PLUS-ONE-1048577 | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-PLUS-ONE-1048577 |
| RET-PROV-020 | WIRE-PLUS-ONE-1048577 | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-PLUS-ONE-1048577 |
| RET-PROV-020 | WIRE-PLUS-ONE-1048577 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-PLUS-ONE-1048577 |
| RET-PROV-020 | WIRE-STREAMED-EXACT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-STREAMED-EXACT |
| RET-PROV-020 | WIRE-STREAMED-EXACT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-STREAMED-EXACT |
| RET-PROV-020 | WIRE-STREAMED-EXACT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-STREAMED-EXACT |
| RET-PROV-020 | WIRE-STREAMED-EXACT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-STREAMED-EXACT |
| RET-PROV-020 | WIRE-STREAMED-PLUS-ONE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-STREAMED-PLUS-ONE |
| RET-PROV-020 | WIRE-STREAMED-PLUS-ONE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-STREAMED-PLUS-ONE |
| RET-PROV-020 | WIRE-STREAMED-PLUS-ONE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-STREAMED-PLUS-ONE |
| RET-PROV-020 | WIRE-STREAMED-PLUS-ONE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-STREAMED-PLUS-ONE |
| RET-PROV-021 | OUTER-RESULT-GROUPS-TWO | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-OUTER-RESULT-GROUPS-TWO |
| RET-PROV-021 | OUTER-RESULT-GROUPS-TWO | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-OUTER-RESULT-GROUPS-TWO |
| RET-PROV-021 | OUTER-RESULT-GROUPS-TWO | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-OUTER-RESULT-GROUPS-TWO |
| RET-PROV-021 | OUTER-RESULT-GROUPS-TWO | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-OUTER-RESULT-GROUPS-TWO |
| RET-PROV-021 | UNORDERED-CANDIDATE-OBJECT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-UNORDERED-CANDIDATE-OBJECT |
| RET-PROV-021 | UNORDERED-CANDIDATE-OBJECT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-UNORDERED-CANDIDATE-OBJECT |
| RET-PROV-021 | UNORDERED-CANDIDATE-OBJECT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-UNORDERED-CANDIDATE-OBJECT |
| RET-PROV-021 | UNORDERED-CANDIDATE-OBJECT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-UNORDERED-CANDIDATE-OBJECT |
| RET-PROV-022 | CONNECTION-ESTABLISHMENT-FAILURE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONNECTION-ESTABLISHMENT-FAILURE |
| RET-PROV-022 | CONNECTION-ESTABLISHMENT-FAILURE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONNECTION-ESTABLISHMENT-FAILURE |
| RET-PROV-022 | CONNECTION-ESTABLISHMENT-FAILURE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONNECTION-ESTABLISHMENT-FAILURE |
| RET-PROV-022 | READ-TIMEOUT-FAILURE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-READ-TIMEOUT-FAILURE |
| RET-PROV-022 | READ-TIMEOUT-FAILURE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-READ-TIMEOUT-FAILURE |
| RET-PROV-022 | READ-TIMEOUT-FAILURE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-READ-TIMEOUT-FAILURE |
| RET-PROV-023 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-023 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-023 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-023 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-024 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-024 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-024 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-024 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-025 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-025 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-025 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-025 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-026 | TYPED-NEGATIVE-INFINITY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-TYPED-NEGATIVE-INFINITY |
| RET-PROV-026 | TYPED-NEGATIVE-INFINITY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-TYPED-NEGATIVE-INFINITY |
| RET-PROV-026 | TYPED-NEGATIVE-INFINITY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-TYPED-NEGATIVE-INFINITY |
| RET-PROV-026 | TYPED-NEGATIVE-INFINITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-TYPED-NEGATIVE-INFINITY |
| RET-PROV-026 | TYPED-POSITIVE-INFINITY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-TYPED-POSITIVE-INFINITY |
| RET-PROV-026 | TYPED-POSITIVE-INFINITY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-TYPED-POSITIVE-INFINITY |
| RET-PROV-026 | TYPED-POSITIVE-INFINITY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-TYPED-POSITIVE-INFINITY |
| RET-PROV-026 | TYPED-POSITIVE-INFINITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-TYPED-POSITIVE-INFINITY |
| RET-PROV-027 | SCORE-ARRAY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SCORE-ARRAY |
| RET-PROV-027 | SCORE-ARRAY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-SCORE-ARRAY |
| RET-PROV-027 | SCORE-ARRAY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-SCORE-ARRAY |
| RET-PROV-027 | SCORE-ARRAY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SCORE-ARRAY |
| RET-PROV-027 | SCORE-BOOLEAN | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SCORE-BOOLEAN |
| RET-PROV-027 | SCORE-BOOLEAN | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-SCORE-BOOLEAN |
| RET-PROV-027 | SCORE-BOOLEAN | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-SCORE-BOOLEAN |
| RET-PROV-027 | SCORE-BOOLEAN | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SCORE-BOOLEAN |
| RET-PROV-027 | SCORE-NULL | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SCORE-NULL |
| RET-PROV-027 | SCORE-NULL | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-SCORE-NULL |
| RET-PROV-027 | SCORE-NULL | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-SCORE-NULL |
| RET-PROV-027 | SCORE-NULL | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SCORE-NULL |
| RET-PROV-027 | SCORE-OBJECT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SCORE-OBJECT |
| RET-PROV-027 | SCORE-OBJECT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-SCORE-OBJECT |
| RET-PROV-027 | SCORE-OBJECT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-SCORE-OBJECT |
| RET-PROV-027 | SCORE-OBJECT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SCORE-OBJECT |
| RET-PROV-027 | SCORE-STRING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SCORE-STRING |
| RET-PROV-027 | SCORE-STRING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-SCORE-STRING |
| RET-PROV-027 | SCORE-STRING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-SCORE-STRING |
| RET-PROV-027 | SCORE-STRING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SCORE-STRING |
| RET-PROV-028 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-028 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-028 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-028 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-029 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-029 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-029 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-030 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-030 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-030 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-031 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-031 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-031 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-032 | INVALID-UUID-SYNTAX | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-INVALID-UUID-SYNTAX |
| RET-PROV-032 | INVALID-UUID-SYNTAX | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-INVALID-UUID-SYNTAX |
| RET-PROV-032 | INVALID-UUID-SYNTAX | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-INVALID-UUID-SYNTAX |
| RET-PROV-032 | INVALID-UUID-SYNTAX | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-INVALID-UUID-SYNTAX |
| RET-PROV-032 | MISSING-CHUNK-PREFIX | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-CHUNK-PREFIX |
| RET-PROV-032 | MISSING-CHUNK-PREFIX | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-CHUNK-PREFIX |
| RET-PROV-032 | MISSING-CHUNK-PREFIX | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-CHUNK-PREFIX |
| RET-PROV-032 | MISSING-CHUNK-PREFIX | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-CHUNK-PREFIX |
| RET-PROV-032 | NONCANONICAL-UUID-SPELLING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NONCANONICAL-UUID-SPELLING |
| RET-PROV-032 | NONCANONICAL-UUID-SPELLING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NONCANONICAL-UUID-SPELLING |
| RET-PROV-032 | NONCANONICAL-UUID-SPELLING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NONCANONICAL-UUID-SPELLING |
| RET-PROV-032 | NONCANONICAL-UUID-SPELLING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NONCANONICAL-UUID-SPELLING |
| RET-PROV-033 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-033 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-034 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-034 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-035 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-035 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-036 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-036 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-037 | DOCUMENT-STATUS-INELIGIBLE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DOCUMENT-STATUS-INELIGIBLE |
| RET-PROV-037 | DOCUMENT-STATUS-INELIGIBLE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DOCUMENT-STATUS-INELIGIBLE |
| RET-PROV-038 | MISSING-CANDIDATE-ID | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-MISSING-CANDIDATE-ID |
| RET-PROV-038 | MISSING-CANDIDATE-ID | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-MISSING-CANDIDATE-ID |
| RET-PROV-038 | MISSING-CANDIDATE-ID | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-MISSING-CANDIDATE-ID |
| RET-PROV-038 | MISSING-CANDIDATE-ID | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-MISSING-CANDIDATE-ID |
| RET-PROV-038 | WRONG-TYPE-CANDIDATE-ID | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WRONG-TYPE-CANDIDATE-ID |
| RET-PROV-038 | WRONG-TYPE-CANDIDATE-ID | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WRONG-TYPE-CANDIDATE-ID |
| RET-PROV-038 | WRONG-TYPE-CANDIDATE-ID | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WRONG-TYPE-CANDIDATE-ID |
| RET-PROV-038 | WRONG-TYPE-CANDIDATE-ID | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WRONG-TYPE-CANDIDATE-ID |
| RET-PROV-039 | DEFAULT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-PROV-039 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-039 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-039 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-040 | DEFAULT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DEFAULT |
| RET-PROV-040 | DEFAULT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-PROV-040 | DEFAULT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-PROV-041 | DECODED-EXACT-2097152 | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DECODED-EXACT-2097152 |
| RET-PROV-041 | DECODED-EXACT-2097152 | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DECODED-EXACT-2097152 |
| RET-PROV-041 | DECODED-EXACT-2097152 | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DECODED-EXACT-2097152 |
| RET-PROV-041 | DECODED-EXACT-2097152 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DECODED-EXACT-2097152 |
| RET-PROV-041 | DECODED-PLUS-ONE-2097153 | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DECODED-PLUS-ONE-2097153 |
| RET-PROV-041 | DECODED-PLUS-ONE-2097153 | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-DECODED-PLUS-ONE-2097153 |
| RET-PROV-041 | DECODED-PLUS-ONE-2097153 | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DECODED-PLUS-ONE-2097153 |
| RET-PROV-041 | DECODED-PLUS-ONE-2097153 | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-DECODED-PLUS-ONE-2097153 |
| RET-PROV-041 | DECODED-PLUS-ONE-2097153 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DECODED-PLUS-ONE-2097153 |
| RET-PROV-041 | NAN | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NAN |
| RET-PROV-041 | NAN | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NAN |
| RET-PROV-041 | NAN | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NAN |
| RET-PROV-041 | NAN | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-NAN |
| RET-PROV-041 | NAN | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NAN |
| RET-PROV-041 | NEGATIVE-INFINITY | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NEGATIVE-INFINITY |
| RET-PROV-041 | NEGATIVE-INFINITY | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NEGATIVE-INFINITY |
| RET-PROV-041 | NEGATIVE-INFINITY | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NEGATIVE-INFINITY |
| RET-PROV-041 | NEGATIVE-INFINITY | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-NEGATIVE-INFINITY |
| RET-PROV-041 | NEGATIVE-INFINITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NEGATIVE-INFINITY |
| RET-PROV-041 | NO-AUTOMATIC-RETRY | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NO-AUTOMATIC-RETRY |
| RET-PROV-041 | NO-AUTOMATIC-RETRY | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NO-AUTOMATIC-RETRY |
| RET-PROV-041 | NO-AUTOMATIC-RETRY | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NO-AUTOMATIC-RETRY |
| RET-PROV-041 | NO-AUTOMATIC-RETRY | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-NO-AUTOMATIC-RETRY |
| RET-PROV-041 | NO-AUTOMATIC-RETRY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NO-AUTOMATIC-RETRY |
| RET-PROV-041 | NORMALIZATION-CONVERSION-OVERFLOW | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NORMALIZATION-CONVERSION-OVERFLOW |
| RET-PROV-041 | NORMALIZATION-CONVERSION-OVERFLOW | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NORMALIZATION-CONVERSION-OVERFLOW |
| RET-PROV-041 | NORMALIZATION-CONVERSION-OVERFLOW | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NORMALIZATION-CONVERSION-OVERFLOW |
| RET-PROV-041 | NORMALIZATION-CONVERSION-OVERFLOW | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-NORMALIZATION-CONVERSION-OVERFLOW |
| RET-PROV-041 | NORMALIZATION-CONVERSION-OVERFLOW | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NORMALIZATION-CONVERSION-OVERFLOW |
| RET-PROV-041 | POSITIVE-INFINITY | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-POSITIVE-INFINITY |
| RET-PROV-041 | POSITIVE-INFINITY | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-POSITIVE-INFINITY |
| RET-PROV-041 | POSITIVE-INFINITY | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-POSITIVE-INFINITY |
| RET-PROV-041 | POSITIVE-INFINITY | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-POSITIVE-INFINITY |
| RET-PROV-041 | POSITIVE-INFINITY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-POSITIVE-INFINITY |
| RET-PROV-041 | TOTAL-DEADLINE | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-TOTAL-DEADLINE |
| RET-PROV-041 | TOTAL-DEADLINE | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-TOTAL-DEADLINE |
| RET-PROV-041 | TOTAL-DEADLINE | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-TOTAL-DEADLINE |
| RET-PROV-041 | TOTAL-DEADLINE | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-TOTAL-DEADLINE |
| RET-PROV-041 | TOTAL-DEADLINE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-TOTAL-DEADLINE |
| RET-PROV-041 | WIRE-EXACT-2097152 | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-EXACT-2097152 |
| RET-PROV-041 | WIRE-EXACT-2097152 | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-EXACT-2097152 |
| RET-PROV-041 | WIRE-EXACT-2097152 | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-EXACT-2097152 |
| RET-PROV-041 | WIRE-EXACT-2097152 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-EXACT-2097152 |
| RET-PROV-041 | WIRE-PLUS-ONE-2097153 | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WIRE-PLUS-ONE-2097153 |
| RET-PROV-041 | WIRE-PLUS-ONE-2097153 | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WIRE-PLUS-ONE-2097153 |
| RET-PROV-041 | WIRE-PLUS-ONE-2097153 | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WIRE-PLUS-ONE-2097153 |
| RET-PROV-041 | WIRE-PLUS-ONE-2097153 | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-WIRE-PLUS-ONE-2097153 |
| RET-PROV-041 | WIRE-PLUS-ONE-2097153 | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WIRE-PLUS-ONE-2097153 |
| RET-PROV-041 | WRONG-DIMENSION | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WRONG-DIMENSION |
| RET-PROV-041 | WRONG-DIMENSION | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WRONG-DIMENSION |
| RET-PROV-041 | WRONG-DIMENSION | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WRONG-DIMENSION |
| RET-PROV-041 | WRONG-DIMENSION | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-WRONG-DIMENSION |
| RET-PROV-041 | WRONG-DIMENSION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WRONG-DIMENSION |
| RET-PROV-041 | WRONG-VALUE-TYPE | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WRONG-VALUE-TYPE |
| RET-PROV-041 | WRONG-VALUE-TYPE | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WRONG-VALUE-TYPE |
| RET-PROV-041 | WRONG-VALUE-TYPE | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WRONG-VALUE-TYPE |
| RET-PROV-041 | WRONG-VALUE-TYPE | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-WRONG-VALUE-TYPE |
| RET-PROV-041 | WRONG-VALUE-TYPE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WRONG-VALUE-TYPE |
| RET-PROV-041 | WRONG-VECTOR-COUNT | unit | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-WRONG-VECTOR-COUNT |
| RET-PROV-041 | WRONG-VECTOR-COUNT | provider-adapter contract | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-WRONG-VECTOR-COUNT |
| RET-PROV-041 | WRONG-VECTOR-COUNT | PostgreSQL integration | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-WRONG-VECTOR-COUNT |
| RET-PROV-041 | WRONG-VECTOR-COUNT | fault injection | AF3B_EMBEDDING | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-WRONG-VECTOR-COUNT |
| RET-PROV-041 | WRONG-VECTOR-COUNT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-WRONG-VECTOR-COUNT |
| RET-PROV-042 | CANCELLATION-WAITERS-AND-STATE-CLEARING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CANCELLATION-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | CANCELLATION-WAITERS-AND-STATE-CLEARING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CANCELLATION-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | CANCELLATION-WAITERS-AND-STATE-CLEARING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CANCELLATION-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | CANCELLATION-WAITERS-AND-STATE-CLEARING | deterministic concurrency | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-DC-CANCELLATION-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | CANCELLATION-WAITERS-AND-STATE-CLEARING | fault injection | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-CANCELLATION-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | CANCELLATION-WAITERS-AND-STATE-CLEARING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CANCELLATION-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | CONCURRENT-FIRST-USE-SINGLE-FLIGHT | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-CONCURRENT-FIRST-USE-SINGLE-FLIGHT |
| RET-PROV-042 | CONCURRENT-FIRST-USE-SINGLE-FLIGHT | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-CONCURRENT-FIRST-USE-SINGLE-FLIGHT |
| RET-PROV-042 | CONCURRENT-FIRST-USE-SINGLE-FLIGHT | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-CONCURRENT-FIRST-USE-SINGLE-FLIGHT |
| RET-PROV-042 | CONCURRENT-FIRST-USE-SINGLE-FLIGHT | deterministic concurrency | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-DC-CONCURRENT-FIRST-USE-SINGLE-FLIGHT |
| RET-PROV-042 | CONCURRENT-FIRST-USE-SINGLE-FLIGHT | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-CONCURRENT-FIRST-USE-SINGLE-FLIGHT |
| RET-PROV-042 | FAILURE-WAITERS-AND-STATE-CLEARING | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-FAILURE-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | FAILURE-WAITERS-AND-STATE-CLEARING | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-FAILURE-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | FAILURE-WAITERS-AND-STATE-CLEARING | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-FAILURE-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | FAILURE-WAITERS-AND-STATE-CLEARING | deterministic concurrency | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-DC-FAILURE-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | FAILURE-WAITERS-AND-STATE-CLEARING | fault injection | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-FAILURE-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | FAILURE-WAITERS-AND-STATE-CLEARING | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-FAILURE-WAITERS-AND-STATE-CLEARING |
| RET-PROV-042 | NO-SAME-REQUEST-PROBE-RETRY | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-NO-SAME-REQUEST-PROBE-RETRY |
| RET-PROV-042 | NO-SAME-REQUEST-PROBE-RETRY | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NO-SAME-REQUEST-PROBE-RETRY |
| RET-PROV-042 | NO-SAME-REQUEST-PROBE-RETRY | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-NO-SAME-REQUEST-PROBE-RETRY |
| RET-PROV-042 | NO-SAME-REQUEST-PROBE-RETRY | deterministic concurrency | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-DC-NO-SAME-REQUEST-PROBE-RETRY |
| RET-PROV-042 | NO-SAME-REQUEST-PROBE-RETRY | fault injection | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-NO-SAME-REQUEST-PROBE-RETRY |
| RET-PROV-042 | NO-SAME-REQUEST-PROBE-RETRY | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NO-SAME-REQUEST-PROBE-RETRY |
| RET-PROV-042 | SUCCESS-CACHED-UNTIL-CLOSE | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SUCCESS-CACHED-UNTIL-CLOSE |
| RET-PROV-042 | SUCCESS-CACHED-UNTIL-CLOSE | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-SUCCESS-CACHED-UNTIL-CLOSE |
| RET-PROV-042 | SUCCESS-CACHED-UNTIL-CLOSE | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-SUCCESS-CACHED-UNTIL-CLOSE |
| RET-PROV-042 | SUCCESS-CACHED-UNTIL-CLOSE | deterministic concurrency | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-DC-SUCCESS-CACHED-UNTIL-CLOSE |
| RET-PROV-042 | SUCCESS-CACHED-UNTIL-CLOSE | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SUCCESS-CACHED-UNTIL-CLOSE |
| RET-PROV-043 | NO-COLLECTION-WRITE-INITIALIZATION | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-NO-COLLECTION-WRITE-INITIALIZATION |
| RET-PROV-043 | NO-COLLECTION-WRITE-INITIALIZATION | fault injection | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-NO-COLLECTION-WRITE-INITIALIZATION |
| RET-PROV-043 | NO-COLLECTION-WRITE-INITIALIZATION | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-NO-COLLECTION-WRITE-INITIALIZATION |
| RET-PROV-043 | ONE-ATTEMPT-NO-FALLBACK | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-ONE-ATTEMPT-NO-FALLBACK |
| RET-PROV-043 | ONE-ATTEMPT-NO-FALLBACK | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-ONE-ATTEMPT-NO-FALLBACK |
| RET-PROV-043 | ONE-ATTEMPT-NO-FALLBACK | PostgreSQL integration | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-ONE-ATTEMPT-NO-FALLBACK |
| RET-PROV-043 | ONE-ATTEMPT-NO-FALLBACK | fault injection | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-ONE-ATTEMPT-NO-FALLBACK |
| RET-PROV-043 | ONE-ATTEMPT-NO-FALLBACK | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-ONE-ATTEMPT-NO-FALLBACK |
| RET-PROV-043 | PROBE-AND-QUERY-TOTAL-DEADLINES | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-PROBE-AND-QUERY-TOTAL-DEADLINES |
| RET-PROV-043 | PROBE-AND-QUERY-TOTAL-DEADLINES | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-PROBE-AND-QUERY-TOTAL-DEADLINES |
| RET-PROV-043 | PROBE-AND-QUERY-TOTAL-DEADLINES | fault injection | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-FI-PROBE-AND-QUERY-TOTAL-DEADLINES |
| RET-PROV-043 | PROBE-AND-QUERY-TOTAL-DEADLINES | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-PROBE-AND-QUERY-TOTAL-DEADLINES |
| RET-PROV-043 | TRUSTED-CONFIGURED-COLLECTION-UUID | unit | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-TRUSTED-CONFIGURED-COLLECTION-UUID |
| RET-PROV-043 | TRUSTED-CONFIGURED-COLLECTION-UUID | provider-adapter contract | AF3B_CHROMA_ADAPTER | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PAC-TRUSTED-CONFIGURED-COLLECTION-UUID |
| RET-PROV-043 | TRUSTED-CONFIGURED-COLLECTION-UUID | HTTP integration | AF3C_HTTP | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-TRUSTED-CONFIGURED-COLLECTION-UUID |
| RET-RANK-001 | SOURCE-RANK-FORMULA-MATRIX | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-SOURCE-RANK-FORMULA-MATRIX |
| RET-RANK-001 | SOURCE-RANK-FORMULA-MATRIX | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-SOURCE-RANK-FORMULA-MATRIX |
| RET-RANK-002 | RAW-SCORE-INVARIANCE | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-RAW-SCORE-INVARIANCE |
| RET-RANK-002 | RAW-SCORE-INVARIANCE | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-RAW-SCORE-INVARIANCE |
| RET-RANK-003 | DEFAULT | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-RANK-003 | DEFAULT | PostgreSQL integration | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-RANK-003 | DEFAULT | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
| RET-RANK-004 | COMPLETE-TIE-COMPARATOR-MATRIX | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-COMPLETE-TIE-COMPARATOR-MATRIX |
| RET-RANK-004 | COMPLETE-TIE-COMPARATOR-MATRIX | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-COMPLETE-TIE-COMPARATOR-MATRIX |
| RET-RANK-005 | DEFAULT | unit | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-U-DEFAULT |
| RET-RANK-005 | DEFAULT | PostgreSQL integration | AF3B_HYBRID_FUSION | AF-3B | REQUIRED_NOT_YET_IMPLEMENTED | O-PG-DEFAULT |
| RET-RANK-005 | DEFAULT | HTTP integration | AF3C_PUBLIC_EVIDENCE | AF-3C | REQUIRED_NOT_YET_IMPLEMENTED | O-HTTP-DEFAULT |
<!-- CANONICAL_LEDGER_END -->

The ledger contains no range, wildcard, shared owner, implicit phase, or
mixed-status row. Every declared case-level test vocabulary value has at least
one exact executable row for the variant when that level can prove its oracle;
incapable levels are not declared. The suite parser rejects duplicate keys,
undefined enums, unresolved case IDs, undeclared body labels, rows without a
stable heading, missing/malformed Oracle references, duplicate case-local
oracles, and any phase-specific mixed fixture. Rows are selected from the
case's exact capable-level matrix, never by taking a Cartesian product of a
case's labels and summary levels.

## Test conventions

- Candidate IDs use `chunk:<canonical UUID>`.
- A valid persisted chunk hash matches `^[0-9a-f]{64}$`.
- Unless a case says otherwise, query, result, candidate, and provider values
  are within configured bounds.
- “Internal authoritative retrieval record” is frozen, slotted, non-public, fully
  materialized before final commit, structurally separates trusted control/
  provenance from text, and classifies text only as
  `untrusted_document_content`. It is not HTTP-serializable and cannot
  serialize as public Evidence.
- “Authorized empty internal authoritative retrieval record set” means final authentication and exact-
  target authorization succeeded but no eligible candidate survived. Public
  Evidence and Citation shapes are AF-3C-only mappings.
- The RET-EVID prefix is retained for historical stable-ID traceability. It
  does not name the AF-3A/AF-3B record type and does not imply that either
  phase exposes public Evidence.
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
  `deterministic concurrency`, `fault injection`, `HTTP integration`, and
  `future consuming-phase acceptance`.
- Unit tests use deterministic fakes and no network. Provider-adapter contract
  tests use bounded mock transports. PostgreSQL integration tests observe SQL,
  transaction isolation, snapshots, and concurrency. HTTP integration tests
  observe public status, envelopes, cache headers, and no-fallback behavior.

The normative non-HTTP lifecycle is exact: preserve
`SessionAuthenticationProof`; run and release one initial live-session,
active-user, exact-target access operation; run the pure validator; run and
release one scoped keyword operation; run exactly one embedding operation;
run the read-only Chroma compatibility/query path; form the bounded union;
open the fresh final transaction; sample one timezone-aware injected UTC
`final_now` immediately before its first authoritative statement; establish
one fixed snapshot and recheck authentication/access/capabilities; validate
and load deterministic batches from that snapshot; materialize immutable
internal authoritative retrieval records; commit and release; and perform no later
authorization-sensitive or lazy load. No connection, transaction, ORM
Session, or SessionTransaction crosses embedding or Chroma I/O.

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
| F1M escaped U+0000 semantic handoff | `RET-BND-003::ESCAPED-U0000-DOMAIN-HANDOFF` | Canonical path; live session; authorized target. | Exact `application/json`; parameterized once with the valid ASCII JSON query escape `"\u0000"` and once with the embedded escape `"a\u0000b"`. | Both parse as strict JSON and hand their decoded values to RET-BND-001's same pre-NFC semantic rejection; each returns generic `422 VALIDATION_ERROR` with zero normalization, retrieval, or public Evidence work and private/no-store. |
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

One adapter instance performs one successful compatibility probe, with
concurrent first uses sharing a single-flight attempt. Success lives only
until adapter close. Failure or cancellation fails current waiters and clears
in-flight state; the same retrieval request does not retry, while a later
independent request may make one new attempt. The canonical collection UUID
comes from trusted configuration. Retrieval performs no collection create,
`get_or_create`, update, upsert, delete, or other write-capable
initialization. Embedding, probe, and query each have one total wall-clock
deadline in the existing validated timeout domain (default 30 seconds,
maximum 600 seconds), exactly one attempt, and no retry, backoff, failover,
stale result, or fallback.

The exact outbound-vector oracle configures embedding dimension `4`; the
deterministic fake returns `[0.25, -0.5, 0.0, 1.0]`; and the POST contains
exactly `"query_embeddings":[[0.25,-0.5,0.0,1.0]]`. The spy compares array
cardinality, every value and its order, and canonical serialized JSON.
Truncation, padding, replacement, normalization or reordering, a duplicate
vector, a second embedding call, or any non-finite value fails.

The embedding adapter invokes exactly
`EmbeddingModel.embed([normalized_query])`. It returns one vector of the exact
configured dimension containing only adapter-normalized built-in finite
floats. The retrieval boundary performs no coercion, truncation, padding, or
second-vector acceptance. Wrong count, dimension, type, an overflow-capable
non-built-in-float coercion sentinel, NaN, or infinity is fatal, discards
completed keyword candidates, and permits no Chroma or final transaction. The
sentinel is rejected by exact-type validation without invoking its conversion
hook. Raw/wire and decoded/decompressed embedding response ceilings are each
inclusive at 2,097,152 bytes; bounded collection precedes strict UTF-8 and
strict JSON materialization.

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
- **Keyword-fatal:** scoped keyword SQL fails before embedding or Chroma. The
  request aborts immediately with generic `503`, zero embedding and Chroma
  calls, no possible dense sentinel, no result, and no fallback.

Source completion order is controlled separately from source ranks. A
positive dense case cannot pass through keyword evidence, and a positive
keyword case cannot pass through dense evidence. These conventions override
any less-specific “may have content” setup below: no Provider-fatal service
variant may use an empty keyword path, and no keyword-fatal variant may perform
embedding or Provider work first.

For the mandatory scanner sidecar on every runtime row, “all observable
sinks” means every sink observable at that row's assigned phase, level, and
boundary. The complete cross-phase vocabulary is
application log messages; access logs; exception/error records and exception
string/`repr` forms; structured log keys and recursively nested values; trace
and span names, attributes, status descriptions, and events; HTTP client and
transport diagnostics; Provider transport records; exposed SQL/database/
driver/transaction diagnostics; response status, headers, metadata, and body;
and every other sink named by ADR-008. AF-3A rows register their observable
non-HTTP pure/service, application, internal authoritative retrieval record,
and PostgreSQL sinks; AF-3B rows register those reachable in the embedding/
Provider/hybrid boundary or regression; AF-3C rows register the observable
response, headers, serialization, access, and public sinks, including unit
serialization and PostgreSQL-backed public mapping where declared. The shared
recursive scanner fails on
exact equality or substring presence for any injected sentinel in any key,
value, sequence member, byte string, or rendered representation. Successful
and failed HTTP cases invoke this scanner too. Only a sentinel at its exact intended
public Evidence or citation-resolution response field is allowlisted; an
entire response object, headers/metadata, extra fields, diagnostics, and all
other sinks remain scanned without exemption.

This scanner is a mandatory assertion sidecar on every canonical ledger row
owned by AF-3A, AF-3B, or AF-3C, at every declared level and for both success
and failure. AF-3A scans its observable non-HTTP pure/service, application,
database, and internal authoritative retrieval record sinks; AF-3B scans its
observable non-HTTP embedding/Provider/hybrid and regression sinks; AF-3C scans
its observable HTTP/serialization/public sinks. Only the exact public Evidence
or citation-resolution field path named by the row may be allowlisted; every
non-public row and every failure row has an empty public-field allowlist. A row
that does not register every reachable sentinel and scan every sink owned by
its exact phase/boundary/level fails even if its functional assertion passes.
The focused RET-PRIV cases test the scanner itself and do not waive it elsewhere.

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
- **Provider or Chroma input:** The AF-3A role-matrix row uses one bounded
  keyword candidate and makes zero embedding/Chroma/Provider calls. The
  separately labelled AF-3B regression may use a dense candidate; AF-3C alone
  asserts public behavior.
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
- **Provider or Chroma input:** The AF-3A row uses bounded keyword candidates
  for A and injected B and makes zero Provider calls. The AF-3B hybrid
  regression separately supplies dense A/B candidates; AF-3C alone asserts
  the public response.
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
- **Provider or Chroma input:** The six exact variants are deliberately split
  by the behavior they prove. `AF3A-INITIAL-ACCESS-ZERO-HIT` stops after the
  provider-independent live-session/target-access operation.
  `AF3A-FINAL-REAUTH-ZERO-CANDIDATES` supplies zero candidates to the fake
  final validator and proves that final authentication/access is not skipped.
  `AF3A-FINAL-SNAPSHOT-ZERO-CANDIDATES` supplies zero candidates to the real
  PostgreSQL final transaction. `AF3B-PRESENT-EMPTY-PROVIDER` proves only that
  the canonical present-empty Provider envelope is a successful adapter
  result. `AF3B-HYBRID-AUTHORIZED-EMPTY-REGRESSION` composes legal empty
  keyword and dense sources and reruns the AF-3A final reauthentication path.
  `AF3C-AUTHORIZED-EMPTY-HTTP` alone asserts the public response.
- **Concurrent state change:** None.
- **Expected public result:** Successful authorized empty Evidence and private/no-store.
- **Expected internal validation result:**

  | Variant | Exact case-local oracle |
  | --- | --- |
  | `AF3A-INITIAL-ACCESS-ZERO-HIT` | The real initial operation observes the live session, active user, exact target membership/capability, releases its database resource, and publishes no retrieval result. |
  | `AF3A-FINAL-REAUTH-ZERO-CANDIDATES` | A fake final-validator unit execution invokes final authentication/access exactly once even though the candidate set is empty and invokes zero validation batches. |
  | `AF3A-FINAL-SNAPSHOT-ZERO-CANDIDATES` | The real first final transaction is `REPEATABLE READ`, `READ ONLY`; its first authoritative statement reauthenticates the session/user/target in that fixed snapshot, executes zero candidate batches, commits, and returns an empty internal authoritative retrieval record set. |
  | `AF3B-PRESENT-EMPTY-PROVIDER` | The adapter accepts the exact canonical present-empty envelope and returns an empty dense candidate list without inventing a missing-collection or Provider failure. |
  | `AF3B-HYBRID-AUTHORIZED-EMPTY-REGRESSION` | Empty keyword and dense maps form an empty union, final reauthentication still runs through the AF-3A boundary, and no partial or synthetic internal authoritative retrieval record is published. |
  | `AF3C-AUTHORIZED-EMPTY-HTTP` | The authorized request returns the existing successful empty public Evidence shape with `Cache-Control: private, no-store`, no identifier/content disclosure, and no partial retrieval result. |
- **Forbidden behavior:** `404`, `503`, a synthetic candidate, a missing-collection error, keyword-only degraded mode, skipped final authorization, or fabricated Evidence.
- **Planned test level:** Unit only for final-reauth invocation;
  provider-adapter contract only for the present-empty envelope; PostgreSQL
  integration separately for initial access, final snapshot, and hybrid
  orchestration; HTTP integration only for the public authorized-empty
  outcome.
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

For RET-CONC-002 through RET-CONC-014, the canonical ledger's exact variant
labels split the common timing property into independent fixtures. Every
AF3A-KEYWORD label uses a bounded keyword candidate; every AF3A-SYNTHETIC
label uses explicit bounded synthetic UUID/rank input; every AF3A-ZERO label
uses no candidate; and AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY uses a
deterministic pause with zero external-adapter calls. Provider barriers,
embedding timing, Chroma candidates, and hybrid unions occur only in the
separate AF3B labels. The processing/failed states in RET-CONC-004 and all
four failure points in RET-CONC-011 remain separate labels and are never
collapsed. Generic “Provider” wording in a case body describes only its AF-3B
regression or AF-3C HTTP execution.

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
- **Expected internal validation result:** Every batch and every internal
  authoritative retrieval record field uses the original fixed snapshot.
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
- **Initial database state:** The final transaction has loaded an eligible
  internal authoritative retrieval record for a current member.
- **Authenticated principal and membership state:** Authorization is valid through final commit.
- **Provider or Chroma input:** One valid candidate.
- **Concurrent state change:** Membership revocation commits after final transaction commit but before response serialization ends.
- **Expected public result:** The current response maps the already-loaded
  immutable internal authoritative retrieval record to public Evidence;
  subsequent requests return hidden `404`.
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
- **Provider or Chroma input:** The same bounded source-isolated candidate
  fixture spans multiple batches in four independently executable variants:
  (A) the second validation-batch statement raises a deterministic database
  error after batch one succeeds; (B) every read succeeds but final
  transaction commit raises a deterministic commit error; (C) final-
  transaction connection acquisition raises a deterministic database
  connection error; (D) the real PostgreSQL `statement_timeout` mechanism is
  set transaction-locally and expires during the second validation-batch
  statement after batch one succeeds. Variant D is mandatory at PostgreSQL
  integration and its separate AF-3B hybrid regression is mandatory at that
  same level; neither may be skipped, waived, or satisfied by a connection-
  failure assertion.
- **Concurrent state change:** None; each variant has exactly its named injected fault and no alternate branch.
- **Expected public result:** Every phase-qualified AF-3C variant returns
  generic planned `503 RETRIEVAL_UNAVAILABLE`, no public Evidence, neither
  content sentinel, no identifier or partial retrieval result, and
  `Cache-Control: private, no-store`.
- **Expected internal validation result:** Variant A discards the successful first-batch records; Variant B publishes nothing before commit success and discards all loaded records; Variant C never begins validation; Variant D rolls back and discards all prior records. Each path has an independently asserted normalized failure classification.
- **Forbidden behavior:** Treating one variant as coverage for another, partial Evidence, dense-only or keyword-only fallback, commit/publication of an earlier batch, either candidate content sentinel in the error, or an ambiguous “database error” assertion that does not prove the injected branch.
- **Planned test level:** All four AF-3A variants and all four AF-3B hybrid
  regressions are mandatory PostgreSQL integration rows. The four
  phase-qualified public mappings are mandatory HTTP integration rows.
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

### RET-CONC-013 — Fresh final authentication clock and Provider-time expiry

- **Category:** Final transaction and concurrency. This case owns nine
  independently executable, phase-qualified variant identities:
  `RET-CONC-013::FINAL-NOW-FRESH-AWARE`,
  `RET-CONC-013::EXPIRES-GREATER-VALID`,
  `RET-CONC-013::EXPIRES-EQUALITY-EXPIRED`,
  `RET-CONC-013::AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY`,
  `RET-CONC-013::AF3B-SESSION-EXPIRES-DURING-PROVIDER-REGRESSION`,
  `RET-CONC-013::AF3C-HTTP-FINAL-NOW-FRESH-AWARE`,
  `RET-CONC-013::AF3C-HTTP-EXPIRES-GREATER-VALID`,
  `RET-CONC-013::AF3C-HTTP-EXPIRES-EQUALITY-EXPIRED`, and
  `RET-CONC-013::AF3C-HTTP-SESSION-EXPIRES-DURING-PROVIDER`.
- **Initial database state:** A live session, active user, target membership,
  and eligible content exist. An injected UTC clock exposes separately
  controlled initial and final values; Provider timestamps use distinct
  sentinels and cannot satisfy the clock call.
- **Authenticated principal and membership state:** Initial proof-aware access
  succeeds and preserves `SessionAuthenticationProof`.
- **Provider or Chroma input:** The first three variants use deterministic
  non-HTTP controls. The
  `RET-CONC-013::AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY` row uses a
  deterministic pause/barrier between initial and final authentication, with
  zero embedding/Chroma/Provider calls. In the Provider-time variant, keyword succeeds, embedding
  succeeds, and Chroma blocks while the session advances from live at initial
  authentication to expired before the final transaction.
- **Concurrent state change:** The Provider-time variant releases Chroma only
  after the injected clock reaches session expiry. Other variants have none.
- **Expected public result:** AF-3A and AF-3B rows have no public oracle. The
  four AF-3C outcomes are exact:

  | AF-3C variant | Exact HTTP oracle |
  | --- | --- |
  | `AF3C-HTTP-FINAL-NOW-FRESH-AWARE` | With a timezone-aware fresh injected final clock and a still-live session, return the existing successful retrieval response and `Cache-Control: private, no-store`; expose no clock value. |
  | `AF3C-HTTP-EXPIRES-GREATER-VALID` | When `expires_at > final_now`, return the existing successful retrieval response and private/no-store; do not classify the session expired. |
  | `AF3C-HTTP-EXPIRES-EQUALITY-EXPIRED` | When `expires_at == final_now`, return generic `401 AUTHENTICATION_REQUIRED`, private/no-store, no content or identifier disclosure, and no partial retrieval result. |
  | `AF3C-HTTP-SESSION-EXPIRES-DURING-PROVIDER` | When Provider work succeeds but the session expires before the final snapshot, return generic `401 AUTHENTICATION_REQUIRED`, private/no-store, no Provider detail, content, identifier, keyword/dense candidate, or partial retrieval result. |
- **Expected internal validation result:** `final_now` is freshly sampled
  exactly once, is timezone-aware UTC, and is sampled immediately before the
  first final authoritative statement. The same bound value governs the
  complete final authentication check. `expires_at > final_now` is valid;
  equality is expired. Initial or Provider time is never reused. The
  Provider-time row proves expiry during Provider work is observed at final
  recheck.
- **Forbidden behavior:** A naive clock value; multiple final samples; an
  earlier sample; reusing initial or Provider time; accepting equality;
  returning accumulated keyword/dense candidates after expiry; or mapping
  authentication loss to empty success or `404`.
- **Planned test level:** Unit and PostgreSQL rows prove the three exact AF-3A
  clock predicates. PostgreSQL plus deterministic concurrency prove the
  provider-independent AF-3A elapsed-barrier expiry. Unit, PostgreSQL, and
  deterministic concurrency prove the separate AF-3B Provider-time
  regression. Only the four phase-qualified rows above execute at HTTP
  integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-CONC-014 — Physical deletion before final snapshot with stale Chroma ID

- **Category:** Final transaction and concurrency. The AF-3B regression is
  `RET-CONC-014::AF3B-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT-REGRESSION`; the
  AF-3C public variant is
  `RET-CONC-014::AF3C-HTTP-PHYSICAL-DELETE-BEFORE-FINAL-SNAPSHOT`; the provider-
  independent prerequisite is
  `RET-CONC-014::AF3A-PHYSICAL-DELETE-KEYWORD-BEFORE-FINAL-SNAPSHOT`.
- **Initial database state:** Real PostgreSQL contains one completed document
  and eligible chunk with unique content, provenance, identity, and existence
  sentinels. Chroma's rebuildable index contains that canonical chunk ID.
- **Authenticated principal and membership state:** A live target member
  passes proof-aware initial access and remains authorized.
- **Provider or Chroma input:** The AF-3A row uses the scoped keyword candidate
  and zero embedding/Chroma/Provider calls. In the separate AF-3B regression,
  scoped keyword completes and the read-only Chroma query returns the stale
  canonical ID after a separate actor physically deletes the PostgreSQL
  document and chunk.
- **Concurrent state change:** The physical PostgreSQL deletion commits before
  the request opens its final transaction and acquires its snapshot.
- **Expected public result:** The AF-3A and AF-3B non-HTTP legs each produce an
  authorized-empty internal authoritative retrieval record set. The later
  AF-3C HTTP leg maps that to authorized empty
  public Evidence. Neither reveals deleted text, provenance, identity, or an
  existence distinction.
- **Expected internal validation result:** The real final snapshot finds no
  authoritative row, omits the stale candidate, fully materializes an empty
  internal authoritative retrieval record set, commits, releases, and performs
  no lazy reload.
- **Forbidden behavior:** A fake-only substitute; soft deletion when physical
  deletion is required; trusting stale Chroma text/metadata; deleted content,
  provenance, ID, count, or existence-detail disclosure; candidate-specific
  `404`; or nonempty output.
- **Planned test level:** PostgreSQL integration, deterministic concurrency,
  HTTP integration. The exact AF-3A and AF-3B deletion/MVCC rows are mandatory
  real PostgreSQL; AF-3C owns only HTTP/public mapping.
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
- **Expected public result:** Every variant returns the expected authoritative
  public Evidence item and private/no-store.
- **Expected internal validation result:** Every named grammar branch is
  accepted independently. Every comparison uses `value <= ceiling`; equality
  is accepted without truncation or omission, bounded parsing succeeds, all
  unsolicited values are discarded as authority, and ordinary PostgreSQL
  candidate validation and internal authoritative retrieval record loading
  continue.
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
- **Initial database state:** Target has eligible hashed chunks A, C, E, and G;
  invalid-position records cannot contribute an internal authoritative
  retrieval record.
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
- **Expected internal validation result:** Only the malformed record is
  omitted; it produces no internal authoritative retrieval record and cannot
  authorize or widen scope. The valid candidate continues through PostgreSQL
  validation at its original provider position and source rank; existing
  deterministic rank, RRF, and tie-breaking rules remain intact. No keyword-
  only fallback occurs.
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
- **Expected internal validation result:** Dense absolute rank 2 is preserved;
  its exact RRF contribution is `1/62`; rank 5 adds neither contribution nor a
  duplicate internal authoritative retrieval record.
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

### RET-PROV-041 — Embedding response bounds and exact vector validation

- **Category:** Provider transport, decoding, and taxonomy. Every label is an
  independently executable row:
  `RET-PROV-041::WRONG-VECTOR-COUNT`,
  `RET-PROV-041::WRONG-DIMENSION`,
  `RET-PROV-041::WRONG-VALUE-TYPE`,
  `RET-PROV-041::NORMALIZATION-CONVERSION-OVERFLOW`,
  `RET-PROV-041::NAN`, `RET-PROV-041::POSITIVE-INFINITY`,
  `RET-PROV-041::NEGATIVE-INFINITY`,
  `RET-PROV-041::WIRE-EXACT-2097152`,
  `RET-PROV-041::WIRE-PLUS-ONE-2097153`,
  `RET-PROV-041::DECODED-EXACT-2097152`,
  `RET-PROV-041::DECODED-PLUS-ONE-2097153`,
  `RET-PROV-041::TOTAL-DEADLINE`, and
  `RET-PROV-041::NO-AUTOMATIC-RETRY`.
- **Initial database state:** Initial access and scoped keyword retrieval have
  completed; a known eligible keyword sentinel makes discard observable.
- **Authenticated principal and membership state:** Live target member with a
  preserved proof and no retained database resource.
- **Provider or Chroma input:** Exactly one
  `EmbeddingModel.embed([normalized_query])` call. The valid control returns
  one configured-dimension list of built-in finite floats. Each row changes
  only its named condition. Wrong value type executes every declared type
  parameter (integer, boolean, string, decimal/float-like object, and numeric
  subclass) without sampling. The legacy-labelled
  `NORMALIZATION-CONVERSION-OVERFLOW` row supplies a deliberately
  non-built-in-float float-like sentinel whose observable `__float__` hook
  would raise `OverflowError` if invoked. The byte rows use bounded streaming
  before strict UTF-8/JSON materialization. Deadline covers the complete
  operation.
- **Concurrent state change:** None.
- **Expected public result:** Every fatal row produces the generic planned
  unavailable outcome at AF-3C, with no keyword sentinel, partial output, or
  fallback. Inclusive byte-equality controls proceed to the valid-vector
  result.
- **Expected internal validation result:** Exactly one vector and exact
  configured dimension are required. Only adapter-normalized built-in finite
  floats pass. No coercion, truncation, padding, duplicate/second vector, or
  retrieval-boundary conversion is permitted. Count, dimension, type, the
  overflow-capable coercion sentinel, NaN, and either infinity discard keyword
  candidates and permit zero Chroma probes/queries and zero final transactions.
  Raw and decoded ceilings each accept 2,097,152 and reject the first byte
  above it. One total-deadline attempt is made.

  The label-specific oracle is exact: `WRONG-VECTOR-COUNT` rejects zero or
  more than one vector; `WRONG-DIMENSION` rejects any length other than the
  configured dimension; `WRONG-VALUE-TYPE` executes and rejects integer,
  boolean, string, decimal/float-like, and numeric-subclass parameters without
  sampling; `NORMALIZATION-CONVERSION-OVERFLOW` rejects its deliberately
  non-built-in-float float-like sentinel as an invalid value type before any
  numeric normalization or coercive conversion, proves the sentinel's
  overflow-raising conversion hook was not invoked, and requires no
  conversion-triggered `OverflowError` to occur; `NAN`, `POSITIVE-INFINITY`,
  and `NEGATIVE-INFINITY` independently reject their named value;
  `WIRE-EXACT-2097152` and `DECODED-EXACT-2097152` independently accept their
  inclusive byte equality with an otherwise valid vector;
  `WIRE-PLUS-ONE-2097153` and `DECODED-PLUS-ONE-2097153` independently reject
  their first excess byte; `TOTAL-DEADLINE` times out the one total operation;
  and `NO-AUTOMATIC-RETRY` records exactly one attempted call after failure.
  The legacy overflow label is retained solely for canonical tuple identity;
  adding `float(value)` or any other coercive conversion to make it raise is a
  contract failure. It remains a fatal embedding-validation row with the same
  boundary-specific no-retry, no-fallback, no-partial-result, no-Provider-
  authority, and disclosure constraints as the corresponding fatal row.

  | Level | Distinct level-specific oracle for every retained label |
  | --- | --- |
  | unit | Observe only the exact local vector/count/dimension/type/finite/byte/deadline/attempt decision named by the label; for the overflow sentinel, observe invalid-type rejection and zero conversion-hook calls; no database claim is made. |
  | provider-adapter contract | Observe the exact bounded embedding request/response transport and decoded adapter validation outcome for the named label; for the overflow sentinel, observe rejection before numeric normalization/conversion and zero conversion-hook calls; no orchestration or PostgreSQL claim is imported. |
  | PostgreSQL integration | Complete real scoped keyword SQL and release its transaction/connection before embedding. For each fatal label, reject the exact result, discard the completed keyword sentinel, retain no database resource across embedding, begin zero Chroma queries and zero final-validator transactions, and publish no success/partial internal authoritative retrieval record. For either exact-byte equality label, retain no database resource across embedding, accept the valid vector, use the present-empty Chroma control, and begin the later final transaction only through a newly acquired database resource. |
  | fault injection | For every row actually enumerated at this level, inject only the named fault and observe one fatal branch. The overflow-sentinel row injects the sentinel, not an `OverflowError`, and observes invalid-type rejection with zero conversion-hook calls; the other rows inject only their named non-finite/plus-one/deadline/attempt fault. Exact-byte equality controls have no fault-injection row. |
  | HTTP integration | Either exact-byte equality control returns the existing successful authorized response and private/no-store; every fatal label returns generic `503 RETRIEVAL_UNAVAILABLE`, private/no-store, no content/identifier/Provider detail, and no partial retrieval result. |
- **Forbidden behavior:** Sampling a value-type or non-finite row; accepting a
  second vector; coercion; padding/truncation; retry, backoff, failover,
  alternate model, cached vector, keyword-only fallback, Chroma work, or final
  SQL after fatal validation.
- **Planned test level:** All thirteen labels execute at unit,
  provider-adapter contract, PostgreSQL integration, and HTTP integration.
  Fault injection executes the eleven fatal/fault labels and deliberately has
  no exact-byte-equality row. The PostgreSQL row for every label is mandatory
  and proves the real database lifecycle consequence above rather than
  duplicating the adapter assertion.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-042 — Compatibility-probe single-flight and instance lifetime

- **Category:** Provider transport, decoding, and taxonomy. This case owns
  `RET-PROV-042::CONCURRENT-FIRST-USE-SINGLE-FLIGHT`,
  `RET-PROV-042::SUCCESS-CACHED-UNTIL-CLOSE`,
  `RET-PROV-042::FAILURE-WAITERS-AND-STATE-CLEARING`,
  `RET-PROV-042::CANCELLATION-WAITERS-AND-STATE-CLEARING`, and
  `RET-PROV-042::NO-SAME-REQUEST-PROBE-RETRY`.
- **Initial database state:** Authorized requests have valid keyword
  candidates; deterministic adapter instances expose probe/query call ledgers
  and close state.
- **Authenticated principal and membership state:** Each request is a live
  target member and owns no database resource at probe entry.
- **Provider or Chroma input:** Barrier-driven concurrent first uses join one
  bounded version probe. Separate rows release it with success, failure, or
  cancellation, close the adapter where required, and start a later
  independent request after cleared failure state.
- **Concurrent state change:** Deterministic latches coordinate waiters; no
  sleeps, polling, or race-dependent assertions are permitted.
- **Expected public result:** Success proceeds normally. Failure/cancellation
  fails every current waiter with no partial result; cancellation publishes no
  fabricated response for a cancelled task. A later independent request may
  perform one new probe.
- **Expected internal validation result:** Concurrent first uses produce
  exactly one probe. Success is cached only for that adapter until close;
  post-close use cannot reuse it. Failure/cancellation clears in-flight state.
  No failed request retries its probe.

  | Variant | Exact deterministic-concurrency oracle |
  | --- | --- |
  | `CONCURRENT-FIRST-USE-SINGLE-FLIGHT` | A barrier holds the first probe while all first-use callers arrive; the call ledger contains exactly one probe and every waiter observes the same successful compatibility result. |
  | `SUCCESS-CACHED-UNTIL-CLOSE` | After the one shared successful probe, all current waiters and later uses of that adapter observe the cached success with no second probe; close invalidates only that instance, and a distinct/new adapter performs exactly one independent probe. |
  | `FAILURE-WAITERS-AND-STATE-CLEARING` | One shared probe fails; every current waiter observes the same normalized failure, the in-flight state is cleared, no waiter queries, and one later independent request may issue exactly one new probe. |
  | `CANCELLATION-WAITERS-AND-STATE-CLEARING` | The shared probe task is cancelled; every current waiter terminates without a fabricated success, the in-flight state is cleared, no waiter queries, and one later independent request may issue exactly one new probe. |
  | `NO-SAME-REQUEST-PROBE-RETRY` | Across the shared failure/cancellation release, every affected request records one joined probe attempt and zero same-request retries; a later independent request's one new attempt is not counted as a retry. |

  At PostgreSQL integration, every variant first completes real keyword work,
  releases every database resource before the shared probe, and observes no
  retained resource across the wait. Failure, cancellation, and no-retry rows
  discard keyword candidates and begin zero final transactions; success rows
  may proceed only after the probe/query path and acquire a new final-
  transaction resource. This real database lifecycle observation is distinct
  from the provider-adapter and deterministic-concurrency oracles.
- **Forbidden behavior:** One probe per waiter; process-global or post-close
  success cache; a stuck failed future; waiter disagreement; same-request
  retry; automatic retry loop; sleeps/polling; partial query; or fallback.
- **Planned test level:** Every label has an exact unit, provider-adapter
  contract, PostgreSQL integration, deterministic-concurrency, and HTTP row.
  Fault injection is retained only for failure, cancellation, and no-same-
  request-retry; shared-success and adapter-lifetime caching have no injected-
  fault property and therefore no fault-injection row. All five deterministic-
  concurrency rows are mandatory and use latches, never sleeps or polling.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-043 — Trusted collection UUID and read-only bounded operations

- **Category:** Provider transport, decoding, and taxonomy. This case owns
  `RET-PROV-043::TRUSTED-CONFIGURED-COLLECTION-UUID`,
  `RET-PROV-043::NO-COLLECTION-WRITE-INITIALIZATION`,
  `RET-PROV-043::PROBE-AND-QUERY-TOTAL-DEADLINES`, and
  `RET-PROV-043::ONE-ATTEMPT-NO-FALLBACK`.
- **Initial database state:** Authorized target and eligible keyword candidate
  exist; trusted configuration supplies tenant, database, canonical collection
  UUID, and validated timeouts.
- **Authenticated principal and membership state:** Live target member; all
  prior database operations are released.
- **Provider or Chroma input:** A transport spy captures every method/path and
  a fault injector blocks independently in probe and query. Timeout parameters
  cover default 30 seconds, valid configured maximum 600 seconds, and
  configuration rejection above 600.
- **Concurrent state change:** None.
- **Expected public result:** Valid read-only probe/query succeeds. Each
  timeout/failure is generic unavailable with no partial output or fallback.
- **Expected internal validation result:** The exact trusted collection UUID,
  never Provider-discovered or caller-supplied identity, appears in the one
  query path. Retrieval issues only the specified version `GET` and query
  `POST`; creation, `get_or_create`, update, upsert, delete, and other write-
  capable initialization calls remain zero on success and every failure.
  Probe and query each get one bounded total wall-clock deadline and exactly
  one attempt; RET-PROV-041 separately owns embedding deadlines and attempts.
- **Exact tuple oracles:** The ledger retains only the 15 tuples below. Each
  case-local Oracle reference resolves to the single independently observable
  condition in this table; a level omitted for a label has no distinct
  executable oracle and is not declared.

  | Variant | Test level | Exact executable oracle |
  | --- | --- | --- |
  | `TRUSTED-CONFIGURED-COLLECTION-UUID` | unit | With canonical configured UUID A and distinct caller/Provider decoy UUID B, the pure request-target construction selects A; B cannot enter the target, and a noncanonical configured value fails before transport. No database or HTTP stack is present. |
  | `TRUSTED-CONFIGURED-COLLECTION-UUID` | provider-adapter contract | The transport ledger records the exact version `GET` followed by the one query `POST` whose path contains configured UUID A; there is no discovery/get-collection call and decoy UUID B never appears in a target path. |
  | `TRUSTED-CONFIGURED-COLLECTION-UUID` | HTTP integration | One authenticated successful retrieval traverses the real HTTP route with a transport spy; the only Chroma query path uses configured UUID A, a distinct untrusted decoy cannot substitute it, and neither collection UUID is exposed publicly. |
  | `NO-COLLECTION-WRITE-INITIALIZATION` | provider-adapter contract | First-use success, missing-collection response, probe failure, and query failure each leave the transport method/path ledger free of create, `get_or_create`, update, upsert, delete, or any other write-capable initialization call. |
  | `NO-COLLECTION-WRITE-INITIALIZATION` | fault injection | Probe and query faults are injected independently; a probe fault prevents query, both branches make zero write-capable calls, and neither branch starts recovery initialization. |
  | `NO-COLLECTION-WRITE-INITIALIZATION` | HTTP integration | Separate successful and Provider-fatal authenticated requests produce only their specified public result while the shared transport spy proves zero write-capable collection calls on both paths. |
  | `PROBE-AND-QUERY-TOTAL-DEADLINES` | unit | A fake monotonic clock proves that probe and query each receive one total 30-second default or configured-at-most-600-second budget that is not reset across operation substeps; configuration above 600 fails before transport. |
  | `PROBE-AND-QUERY-TOTAL-DEADLINES` | provider-adapter contract | The transport records one end-to-end deadline for the complete version operation and one for the complete query operation, covering connection, upload, response streaming, decode, and validation without a per-read or per-substep reset. |
  | `PROBE-AND-QUERY-TOTAL-DEADLINES` | fault injection | Latches block probe and query in separate executions while the fake clock reaches that operation's total deadline; the named operation aborts once, later stages do not run, and there is no retry or fallback. |
  | `PROBE-AND-QUERY-TOTAL-DEADLINES` | HTTP integration | Separate authenticated requests whose probe or query reaches its total deadline each return only generic private/no-store `503 RETRIEVAL_UNAVAILABLE`, with no Evidence, partial result, retry, or fallback. |
  | `ONE-ATTEMPT-NO-FALLBACK` | unit | Deterministic fake probe and query failures each produce an exact call count of one and zero retry, backoff, alternate Provider/collection, stale result, keyword-only result, or final-validator call. |
  | `ONE-ATTEMPT-NO-FALLBACK` | provider-adapter contract | For each failure point, the transport ledger contains one attempted operation and no repeated or alternate method/path; a probe failure has zero query calls and a query failure has exactly one query call. |
  | `ONE-ATTEMPT-NO-FALLBACK` | PostgreSQL integration | Real scoped keyword SQL first returns a known eligible candidate, then the one Provider attempt fails; no final-validator transaction or internal authoritative retrieval record is produced and the keyword candidate is not returned as fallback. |
  | `ONE-ATTEMPT-NO-FALLBACK` | fault injection | Independent probe and query failures assert one injected branch, exact attempt count one, zero retry/backoff/failover/stale-result use, and zero continuation beyond the failed boundary. |
  | `ONE-ATTEMPT-NO-FALLBACK` | HTTP integration | With a known nonempty keyword candidate and a failing Provider operation, the authenticated route returns only generic private/no-store `503 RETRIEVAL_UNAVAILABLE`; the Provider attempt count is one and no Evidence or keyword-only fallback is serialized. |

- **Forbidden behavior:** Collection discovery as authority; client/Provider
  UUID substitution; create-on-missing; write-capable initialization; timeout
  reset between substeps; retry, backoff, failover, stale result, alternate
  collection, or keyword-only fallback.
- **Planned test level:** Unit applies only to configured UUID, total deadline,
  and one-attempt logic; provider-adapter contract applies to all four labels;
  PostgreSQL integration applies only to one-attempt/no-fallback; fault
  injection applies only to no-write initialization, total deadlines, and
  one-attempt/no-fallback; HTTP integration applies to all four labels. The
  ledger declares exactly those tuples without Cartesian expansion or
  sampling.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Request, result, union, and SQL bounds

The bounds families use the canonical ledger's phase-qualified fixtures.
RET-BND-006 AF-3A owns only the exact keyword cutoff. For RET-BND-008 through
RET-BND-015, every AF3A row receives zero, keyword, or explicit bounded
synthetic final-validator input and measures only unique-input, batch-size-64,
query-count, reconstruction, and PostgreSQL amplification properties. Every
AF3B-HYBRID row separately supplies dense/hybrid maps and owns union/fusion
regression. Public cutoff, Evidence count, and serialization assertions occur
only in AF3C rows. No AF-3A bounds fixture invokes embedding, Chroma, Provider,
dense union, or RRF.

### RET-BND-001 — Query semantic and scalar domain

- **Category:** Request, result, union, and SQL bounds. ADR-008-R01 is
  decomposed into the exact unit, database-gate, keyword-bind, hybrid-
  regression, and public identities in the canonical ledger; there is no
  composite query-domain oracle.
- **Initial database state:** Authorized target exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Independently executable strict-body variants
  use (A) one ASCII `a` after normalization; (B) 2,048 ASCII `a` values; (C)
  2,049 ASCII `a` values; (D) only members of the exact whitespace set; (E)
  `"\u00a0a\t \n b\u3000"`, which normalizes exactly to `"a b"`; (F)
  canonically decomposed `"e\u0301"` and precomposed `"\u00e9"` subvariants,
  which both normalize exactly to NFC `"\u00e9"`; (G) missing `query`; (H)
  `query` as number, boolean, null, array, or object; and (I) a JSON string
  containing a lone escaped surrogate. A through I resolve to the separately
  named unit identities below rather than one broad tuple. The case-sensitive,
  no-NFKC, U+200B, and post-normalization boundary unit identities prove only
  pure parsing; their separately phase-qualified AF-3A rows prove the real
  keyword bind. The separately labelled
  `RET-BND-001::AF3B-HYBRID-QUERY-NORMALIZATION-REGRESSION` may add a
  downstream embedding fake and dense sentinel after AF-3A is closed.
  The U+0001 row is unit-only because it proves only semantic acceptance and
  preservation. U+0000 database and HTTP identities use their own phase-
  qualified gate-order/public labels.

  | Stable variant label | JSON query fixture and exact gate/downstream value |
  | --- | --- |
  | `RET-BND-001::CASE-SENSITIVE-PRESERVATION` | Raw `"AgentForge agentforge"`; both embedding input and keyword SQL bound value are exactly `"AgentForge agentforge"`. |
  | `RET-BND-001::NO-NFKC-COMPATIBILITY-FOLD` | Raw `"\uFF21gent"`, beginning U+FF21 FULLWIDTH LATIN CAPITAL LETTER A whose NFKC value is ASCII `A`; downstream remains exactly `"\uFF21gent"`. |
  | `RET-BND-001::EXCLUDED-U200B-PRESERVATION` | Raw `"\u200Balpha\u200B\u200Bbeta\u200B"`, using specifically excluded U+200B ZERO WIDTH SPACE at both edges and twice inside; every U+200B remains in the exact downstream value and is neither trimmed nor collapsed. |
  | `RET-BND-001::POST-NORMALIZATION-SCALAR-BOUNDARY` | Raw TAB + 2,048 ASCII `a` values + U+3000 has 2,050 scalars; permitted edge whitespace is removed first, producing exactly 2,048 `a` values, which pass and reach both downstream spies unchanged. |
  | `RET-BND-001::U0000-ALONE-REJECTION` | The valid JSON source escape `"\u0000"` decodes to U+0000 alone; exact string type, Unicode-scalar validity, and strict UTF-8 representability pass, then the query is rejected before NFC. |
  | `RET-BND-001::EMBEDDED-U0000-REJECTION` | The valid JSON source `"a\u0000b"` decodes with embedded U+0000 and follows the same pre-NFC semantic rejection path. |
  | `RET-BND-001::ADJACENT-U0001-PRESERVATION` | The valid JSON source `"a\u0001b"` decodes with embedded U+0001 and passes query semantic validation with the exact sequence preserved. U+0001 is neither deleted, replaced, normalized, collapsed, nor treated as whitespace. This supporting parameter assigns no downstream retrieval or public-result behavior. |

  | Oracle allocation | Exact observable pass/fail condition |
  | --- | --- |
  | Unit `NORMALIZED-SCALAR-EXACT-1`, `NORMALIZED-SCALAR-EXACT-2048`, and `NORMALIZED-SCALAR-PLUS-ONE-2049` | The pure parser respectively accepts normalized scalar equality 1, accepts equality 2,048, or rejects 2,049. Each is a separate execution. |
  | Unit `EACH-WHITESPACE-TRIM-AND-COLLAPSE` | Every code point in the finite ADR whitespace set independently trims at both edges and collapses an interior run to one U+0020, without sampling. |
  | Unit `NFC-CANONICAL-EQUIVALENCE` | The decomposed and precomposed fixtures produce equal requests whose exact normalized query is U+00E9. |
  | Unit `WHITESPACE-ONLY-REJECTION`, `MISSING-QUERY-REJECTION`, `QUERY-EXACT-STRING-TYPE`, and `LONE-SURROGATE-REJECTION` | Each named pure-parser defect independently raises only the fixed validation classification; the exact finite wrong-type and high/low-surrogate parameters all execute. |
  | Unit named preservation/U+0000 identities | Each exact fixture proves only its named parser acceptance, preservation, normalization exclusion, or pre-NFC rejection. `POST-NORMALIZATION-SCALAR-BOUNDARY` has the exact merged TAB + 2,048 `a` + U+3000 assertion mapped above. |
  | PostgreSQL `AF3A-INITIAL-ACCESS-INVALID-QUERY-GATE-ORDER`, `AF3A-U0000-ALONE-GATE-ORDER`, and `AF3A-EMBEDDED-U0000-GATE-ORDER` | The live session/active-user/exact-target access operation may complete, then the named parser defect causes zero keyword statements and zero final transactions; no invalid text is sent to PostgreSQL. |
  | PostgreSQL `AF3A-KEYWORD-BIND-*` identities | After pure parsing, the exact named normalized value is the real keyword query's bound parameter; the keyword resource is released and Provider/final work is outside this oracle. |
  | PostgreSQL `AF3B-HYBRID-QUERY-NORMALIZATION-REGRESSION` | Each accepted case-sensitive, no-NFKC, U+200B, and post-normalization parameter reaches the single embedding input byte-for-byte/code-point-for-code-point and produces only its named hybrid regression result. |
  | HTTP `AF3C-HTTP-VALID-NORMALIZED-QUERY` and the four named preservation/boundary success identities | The authenticated authorized request returns the existing successful response, private/no-store, with only the expected public Evidence field values and no query disclosure. |
  | HTTP `AF3C-HTTP-INVALID-QUERY-VALIDATION` and the two named U+0000 identities | The exact defect returns generic `422 VALIDATION_ERROR`, private/no-store, no content or identifier disclosure, and no partial retrieval result. |
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
  normalization unit rows assert exact code-point equality only at the pure
  validator output. Their phase-qualified AF-3A rows separately assert the
  real keyword SQL bind and database-resource release. The AF-3B regression
  separately asserts the sole embedding input,
  fake-vector/candidate branch, and exact returned sentinel. The U+0001 supporting parameter asserts
  only semantic acceptance and exact preservation; it assigns no keyword,
  embedding, Chroma/Provider, candidate, ranking, or Evidence behavior. For
  either authenticated, initially
  authorized escaped-U+0000 row, initial authentication/target PostgreSQL may
  have completed, but NFC/whitespace-normalization calls, keyword statements,
  embedding calls, Chroma/Provider calls, final authoritative transactions,
  and internal authoritative retrieval record/public Evidence counts are all
  zero. The PostgreSQL integration execution
  observes that ledger and must not send U+0000 to PostgreSQL to manufacture a
  driver or database error.

  Query-derived text is absent from fixed validation classifications,
  exception `str`/`repr`, internal request-value diagnostic representations,
  public responses, and captured sinks; only fixed, non-user-controlled field
  and classification labels are permitted. The future implementation may use
  `field(repr=False)` as one acceptable mechanism, but this case mandates no
  exclusive Python mechanism. AF-3A owns its non-HTTP query/parser/internal
  sink checks, AF-3B owns the hybrid non-HTTP regression sinks, and AF-3C owns
  only public HTTP response/header/serialization sink behavior.
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
- **Planned test level:** Exact unit identities prove parser behavior;
  PostgreSQL identities prove either live initial-access gate order or an
  exact keyword bind/resource-release oracle; the AF-3B PostgreSQL regression
  proves hybrid propagation; and phase-qualified HTTP identities prove only
  their exact public success or validation outcome. U+0001 has no database or
  HTTP row. No database row uses `PURE_REQUEST_VALIDATOR`.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-002 — Query UTF-8 byte limit

- **Category:** Request, result, union, and SQL bounds. The stable
  execution identities are `RET-BND-002::UTF8-BYTES-EXACT-4096` and
  `RET-BND-002::UTF8-BYTES-PLUS-ONE-4097` for ADR-008-R01.
- **Initial database state:** Authorized target exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** The exact-4096 identity uses 1,024 U+1F642
  scalar values. The plus-one identity uses the same query plus one ASCII `a`
  for exactly 4,097 UTF-8 bytes. Both pure-validator unit rows make zero
  Provider calls; their separate AF-3C HTTP rows own public behavior.
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
  execution only at the levels declared for its exact ledger identity. Controls use source-isolated,
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
  | `RET-BND-003::PARSER-DEFAULT-10` | The pure parser receives `{"query":"a"}` and returns exact integer count 10. |
  | `RET-BND-003::PARSER-MINIMUM-1` | The pure parser accepts exact built-in integer 1. |
  | `RET-BND-003::PARSER-MAXIMUM-50` | The pure parser accepts exact built-in integer 50. |
  | `RET-BND-003::PARSER-ZERO-REJECTED` | The pure parser rejects exact built-in integer 0. |
  | `RET-BND-003::PARSER-NEGATIVE-ONE-REJECTED` | The pure parser rejects exact built-in integer -1; its exact merged unit assertion is mapped above. |
  | `RET-BND-003::PARSER-PLUS-ONE-51-REJECTED` | The pure parser rejects exact built-in integer 51. |
  | `RET-BND-003::PARSER-BOOLEAN-TRUE-REJECTED` | The pure parser rejects exact boolean `true` and does not accept it as integer 1. |
  | `RET-BND-003::PARSER-FLOAT-1-REJECTED` | The pure parser rejects exact float `1.0` without coercion. |
  | `RET-BND-003::PARSER-STRING-1-REJECTED` | The pure parser rejects exact string `"1"` without coercion. |

  The downstream requested-count obligations are different canonical
  identities. `AF3A-INVALID-COUNT-STOPS-BEFORE-KEYWORD` proves real keyword
  and final-database non-participation after any rejected parser count.
  `AF3A-KEYWORD-CEILING-INDEPENDENT-OF-REQUESTED-COUNT` proves with real
  PostgreSQL that accepted count 1, default 10, and count 50 never widen the
  deterministic keyword cutoff above 128. At AF-3B,
  `AF3B-CONFIGURED-PROVIDER-COUNT-FORMULA` proves exact `C = min(128, 128,
  checked_multiply(R, 4))` both in the service calculation and outbound
  adapter request, while `AF3B-DENSE-COUNT-BOUNDED-BY-POSITIONS` proves only
  `D <= P <= C` after exact response validation. At AF-3C,
  `AF3C-HTTP-REQUESTED-COUNT-VALIDATION` owns generic public validation for
  invalid counts and `AF3C-PUBLIC-RESULT-CUTOFF` owns only exact public result
  counts 1, 10, and 50.

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
  count values `0`, `-1`, `51`, `true`, `1.0`, and `"1"` in the
  `AF3C-HTTP-REQUESTED-COUNT-VALIDATION` execution each return exactly
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
  zero final authoritative transactions, and zero internal authoritative
  retrieval record or public Evidence construction/publication. The literal-
  NUL parser row and escaped-U+0000 semantic rows
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
  embedding, Provider, or final-transaction work. The nine pure requested-
  count identities observe only parser output or fixed validation failure.
  The negative-one identity remains unimplemented because no exact merged
  unit assertion supplies `-1`. AF-3A database rows separately observe zero
  repository participation for invalid counts and the fixed keyword ceiling
  for valid counts. AF-3B rows separately observe configured outbound count
  and retained dense count. Neither downstream property is inferred from the
  parser. AF-3C rows separately observe public validation and final result
  cutoff.
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
- **Planned test level:** The nine parser-count identities are unit-only.
  AF-3A gate/repository identities are PostgreSQL integration only. AF-3B
  configured-count and dense-count identities execute independently at unit
  and provider-adapter contract levels. AF-3C validation and public-cutoff
  identities are HTTP integration only. The remaining request-wire variants
  retain only the exact unit/HTTP rows enumerated in the ledger; no count
  identity is expanded across levels by Cartesian product.
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
- **Provider or Chroma input:** The AF-3A row has no Provider input and
  measures the exact keyword cutoff. The separate AF-3B regression adds a
  bounded dense response; AF-3C owns the public result limit.
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
- **Expected internal validation result:** The same UUID sort produces the same contiguous 64/64/remainder partitions, exactly `ceil(U / 64) = 3` validation queries, identical absolute rank maps, exact RRF values, and byte-identical internal authoritative retrieval records.
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

Each RET-KEY case has an exact AF3A keyword identity, a separate
AF3B-HYBRID regression identity, and an AF3C-HTTP identity in the canonical
ledger. The AF-3A fixtures exercise only exact target scoping before score,
completed/current/valid-hash eligibility, bound
`plainto_tsquery('simple', normalized_query)`, `ts_rank_cd(..., 0)`, exact
score-descending/native-UUID-ascending order, the 128 cutoff, shared final
revalidation, bounded scoped counts, and the user-scoped repository boundary.
They use keyword candidates and make zero embedding/Chroma/Provider/fusion
calls. Provider-empty, dense, mixed-source, RRF, public Evidence, and HTTP
route assertions belong only to the separate AF-3B or AF-3C rows.

### RET-KEY-001 — Scoped deterministic PostgreSQL keyword ranking

- **Category:** Keyword SQL scope.
- **Initial database state:** Knowledge base A contains exactly `MAX_KEYWORD_CANDIDATES + 1 = 129` eligible matching chunks. Controlled text produces known `ts_rank_cd` score groups, including at least two equal-score rows whose native UUID order places one at normative rank 128 and the other at rank 129. UUIDs and insertion order are chosen so insertion/heap order disagrees with the full `keyword_score DESC, chunk UUID ASC` order. Knowledge base B contains identical and additional matches but is outside A's scope.
- **Authenticated principal and membership state:** A live member requests exactly A; B is excluded by current SQL authorization and scope predicates before keyword score or rank assignment.
- **Provider or Chroma input:** The AF-3A row has no Provider input and proves
  the exact keyword list directly. The AF-3B regression uses the canonical
  present-empty Provider response to prove keyword-only hybrid success; no
  dense identity can satisfy that regression.
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
- **Provider or Chroma input:** The AF-3A scoped repository test double injects
  B only after keyword generation and therefore after the keyword-query
  boundary; it makes zero Provider calls. The
  separate AF-3B regression adds an explicitly empty dense list.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty A Evidence when no legal A candidate exists.
- **Expected internal validation result:** The
  `AF3A-CROSS-SCOPE-REVALIDATION` PostgreSQL oracle belongs exclusively to
  `AF3A_FINAL_VALIDATOR`: the shared fixed-snapshot validator rejects injected
  B by exact target and access predicates. `RET-KEY-001::AF3A-SCOPED-DETERMINISTIC-ORDER-CUTOFF`
  separately owns real SQL scope-before-score at
  `AF3A_KEYWORD`.
  The AF-3B hybrid row proves only the hybrid regression through that final
  validator, and the AF-3C row proves only the authorized-empty public outcome.
- **Forbidden behavior:** Trusting keyword origin as authority, B disclosure, or bypassing shared validation.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-KEY-003 — No global keyword result count

- **Category:** Keyword SQL scope.
- **Initial database state:** Inaccessible B has many matches; authorized A has none.
- **Authenticated principal and membership state:** Live A member with no B membership.
- **Provider or Chroma input:** The AF-3A row has no Provider input. The
  separate AF-3B regression adds a valid empty dense collection.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty A Evidence with no global or B count.
- **Expected internal validation result:** SQL and telemetry expose only bounded A-scoped counts.
- **Forbidden behavior:** Total-match count, timing branch based on B count, B identifier, or global query.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-KEY-004 — User-facing retrieval cannot use worker/internal repository

- **Category:** Keyword SQL scope.
- **Initial database state:** Internal repository could see multiple private knowledge bases; user repository sees only target A.
- **Authenticated principal and membership state:** Live A member.
- **Provider or Chroma input:** The AF-3A scoped-repository row makes zero
  Provider calls. The AF-3B regression adds a bounded valid Provider response;
  AF-3C alone drives the HTTP route.
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

### RET-EVID-001 — Internal authoritative retrieval record and authoritative projection

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Eligible chunk has authoritative IDs, text, persisted hash, display filename, offsets, and optional page range; document storage key contains a sentinel path.
- **Authenticated principal and membership state:** Live target member with current read capabilities.
- **Provider or Chroma input:** The AF-3A projection row uses a keyword
  candidate or an explicit bounded synthetic candidate and makes zero
  embedding/Chroma/Provider calls. The AF-3B fused-extension row uses a valid
  dense ID plus disagreeing bounded text and provenance metadata. AF-3C maps
  only the already-materialized internal values.
- **Concurrent state change:** None.
- **Expected public result:** The AF-3A/AF-3B non-HTTP leg exposes no public
  Evidence. AF-3C later maps only the allowlisted authoritative and derived
  primitives into its public schema.
- **Expected internal validation result:** The internal authoritative retrieval
  record type is frozen, slotted,
  non-public, has no lazy ORM state, is fully materialized before final commit,
  and fails closed when passed to the public Evidence serializer. Its trusted
  control/provenance member contains only authoritative IDs, persisted hash,
  approved display identity, persisted page/character provenance, and bounded
  derived rank/fusion primitives only in the AF-3B extension. Its separate
  document-text member contains
  `normalized_text` and only the fixed classification
  `untrusted_document_content`. Each authoritative value loads from one
  allowlisted projection in the fixed snapshot; each derived value proves its
  sole permitted input.
- **Forbidden behavior:** Naming the internal type public `Evidence`; generic
  public serialization before AF-3C; a `__dict__` or lazy load; text sharing a
  trusted-control field; claiming every field is loaded from PostgreSQL;
  deriving authoritative fields from ranks; Provider authority; storage path,
  secret, raw embedding, internal exception, or post-commit reload.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-002 — Completed legacy chunk with null content hash

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Completed legacy document has a chunk whose authoritative `content_sha256` is null.
- **Authenticated principal and membership state:** Live target member otherwise retains full read access.
- **Provider or Chroma input:** The AF-3A row supplies the legacy ID as a
  bounded keyword or synthetic final-validator candidate with zero Provider
  calls. The separate AF-3B regression supplies the canonical dense ID with
  bounded untrusted text/metadata.
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
- **Provider or Chroma input:** The AF-3A row uses structurally valid bounded
  keyword or synthetic canonical IDs with zero Provider calls. The separate
  AF-3B regression uses bounded hybrid IDs.
- **Concurrent state change:** Ineligibility is committed before snapshot acquisition.
- **Expected public result:** Authorized empty Evidence and private/no-store.
- **Expected internal validation result:** Final PostgreSQL validation returns no eligible authoritative record without public reasons.
- **Forbidden behavior:** `404` for candidate state, `503`, provider content, or invented revisions.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## AF-3 untrusted-evidence boundary

For each RET-INJ case, AF3A-KEYWORD-INTERNAL-RECORD uses a keyword candidate
or explicit bounded synthetic final-validator candidate and produces only a
non-public internal authoritative retrieval record whose text classification
is `untrusted_document_content`. AF3B-HYBRID-INTERNAL-RECORD-REGRESSION is a
separate dense/fusion regression and cannot close AF-3A. AF3C-PUBLIC-EVIDENCE-
HTTP alone owns public Evidence and HTTP serialization. Generic “valid
candidate” wording below never implies Provider work in the AF-3A row.

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
  their intended public Evidence fields; empty retrieval returns the exact
  empty Evidence shape with no sensitive sentinel; citation resolution exposes
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
  internal authoritative retrieval record text;
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
  variant has every applicable non-Provider sensitive class in live request/
  client context and has loaded the internal authoritative retrieval record
  and identifying classes into accumulated batch-1 state
  before batch 2 fails. Earlier fatal variants retain their sentinels only in
  inputs and context reachable before their named failure; they do not claim
  that a final internal authoritative retrieval record loaded before the
  Provider or keyword stage.
- **Authenticated principal and membership state:** Every execution has a live
  active target member and current session. AF-3A and AF-3B non-HTTP rows begin
  at their owned service/database boundary after their applicable non-HTTP
  proof, membership, and exact-target prerequisites; they do not traverse or
  assert any HTTP route, path, media, body, response, header, or serialization
  gate. Each corresponding AF-3C HTTP row separately traverses its public
  route/path, authentication/authorization, exact request-media, and strict
  body gates according to that public operation's precedence contract before
  reaching the named downstream fatal branch.
- **Provider or Chroma input:** The eight variants below expand to exactly ten
  canonical non-HTTP rows at their capable levels and are separate
  constructible executions. Every AF-3A row uses only keyword or explicit
  bounded synthetic candidates, configures embedding/Chroma/Provider spies to
  prove zero calls, and has no dense or Provider-response sentinel. AF-3B
  failure rows use the exact external boundary named by their label. Only the
  two AF-3B hybrid database regressions carry previously successful bounded
  Provider work into their distinct final-database failures.

  | Stable variant label | Exact failure fixture and execution stage |
  | --- | --- |
  | `RET-PRIV-004::EMBEDDING-FATAL-ALL-SINK-SECRECY` | Scoped keyword SQL first returns a known eligible nonempty keyword sentinel. The one embedding operation fails; the keyword sentinel is discarded and Chroma/final-transaction calls are zero. |
  | `RET-PRIV-004::PROVIDER-FATAL-ALL-SINK-SECRECY` | Scoped keyword SQL and embedding succeed. The bounded Chroma/provider branch raises its injected Provider-fatal exception containing the Provider-detail sentinel; keyword candidates are discarded and final-transaction calls are zero. |
  | `RET-PRIV-004::KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY` | Scoped keyword SQL raises its injected database exception containing the database and exposed driver diagnostics before embedding or Chroma begins. Embedding, compatibility-probe, query, dense-candidate, union, and final-transaction calls are all zero; no dense sentinel can exist. |
  | `RET-PRIV-004::FINAL-AUTHORIZATION-STATEMENT-FATAL-ALL-SINK-SECRECY` | Keyword or zero-candidate setup reaches the first final authoritative statement, which alone raises the injected database exception. No Provider work or validation batch occurs. |
  | `RET-PRIV-004::FINAL-COMMIT-ALL-SINK-SECRECY` | Bounded keyword or synthetic candidates drive final authorization and every required validation batch. The actual final transaction commit raises its injected commit exception; every accumulated internal authoritative retrieval record is discarded. |
  | `RET-PRIV-004::LATER-BATCH-ALL-SINK-SECRECY` | Exactly 129 bounded synthetic candidate identities give `U = 129`, batch size `B = 64`, and `Q = 3` without Provider work. Batch 1 loads 64 PostgreSQL-authoritative internal authoritative retrieval records; batch 2 alone fails. Batch 3 and commit each have zero calls, and all accumulated records are discarded. |
  | `RET-PRIV-004::AF3B-HYBRID-FINAL-COMMIT-ALL-SINK-REGRESSION` | Scoped keyword work, the one embedding operation, bounded successful Provider work, hybrid union/fusion, final authorization, and every required validation batch succeed. The real final transaction reaches commit and commit alone fails. No result, candidate, query, content, identifier, Provider detail, or partial state appears in any allowed non-HTTP sink. This regression does not transfer AF-3A ownership of the commit contract. |
  | `RET-PRIV-004::AF3B-HYBRID-LATER-BATCH-ALL-SINK-REGRESSION` | Scoped keyword work, the one embedding operation, and bounded successful Provider work produce enough valid hybrid candidates for at least two validation batches. Batch one accumulates internal authoritative retrieval records; a later batch alone fails; every accumulated record is discarded, no later batch/commit/publication occurs, and no result, candidate, query, content, identifier, Provider detail, or partial state appears in any allowed non-HTTP sink. This regression does not transfer AF-3A ownership of the batch contract. |

- **Concurrent state change:** None. Each execution has exactly one injected
  fatal branch. The later-batch execution uses deterministic statement
  ordinals and call ledgers, with no timing race and no concurrent mutation.
- **Expected public result:** Every corresponding AF-3C HTTP row returns exactly the byte-stable
  generic planned `503 RETRIEVAL_UNAVAILABLE` envelope and
  `Cache-Control: private, no-store`. The response contains zero Evidence,
  zero citation content, zero partial result, zero fallback result, zero
  Provider raw body, zero Provider exception detail, zero database exception
  detail, and none of the query, ID, path, credential, secret/token, content,
  driver, or transaction sentinels.
  `AF3C-HTTP-HYBRID-FINAL-COMMIT-FAILURE` maps only the successful-Provider/
  failed-final-commit regression, and
  `AF3C-HTTP-HYBRID-LATER-BATCH-FAILURE` maps only the successful-Provider/
  failed-later-batch regression; neither public row substitutes for the other.
- **Expected internal validation result:** Before each non-HTTP execution, the
  owning phase invokes the shared scanner from Test conventions over the
  sinks it can actually observe: AF-3A captures its application/log/trace,
  exception, SQL/database-client/driver/transaction, and internal
  authoritative retrieval record sinks; AF-3B captures those plus embedding/
  Provider transport/client and
  hybrid-state sinks. AF-3C separately runs the scanner over HTTP response,
  header, serialization, access-log, and public sink behavior. The scanner
  walks every nested key,
  value, sequence member, byte string, exception representation, and larger
  rendered string. For every sink and every sentinel, both exact equality and
  substring presence are deterministic failures. Only the normalized
  content-free failure classification is permitted. The embedding-fatal and
  Provider-fatal executions each discard the keyword sentinel at their exact
  boundary. The keyword/database-fatal
  execution aborts immediately with zero embedding/Chroma work and therefore
  no dense sentinel. The final-authorization, final-commit, and later-batch
  AF-3A executions perform zero Provider work. The final-commit execution publishes
  nothing before commit success, then discards all loaded records. The
  later-batch execution proves batch 1 loaded sensitive authoritative state,
  records batch 2 as the sole failure, rolls back the final transaction,
  discards every accumulated record, makes zero batch-3 calls, makes zero
  commit calls, performs no fusion or response publication, and never
  continues with the 64 earlier records. The two AF-3B regressions separately
  prove final-commit and later-batch discard/all-sink properties after
  successful Provider/hybrid work without changing AF-3A ownership.
- **Forbidden behavior:** Treating success-path secrecy as fatal-path
  coverage; using the broad parent case without executing each stable label;
  omitting a sentinel class, sink class, structured key, nested value,
  exception representation, response metadata field, or substring scan; any
  sentinel, stack trace, SQL/Provider/database detail, raw payload, partial
  Evidence, citation, stale cache, or alternate successful response;
  keyword-only fallback after Provider failure; any embedding/Provider work or
  dense-only fallback after keyword/database failure; publication before final commit; retaining batch
  1 records after the later-batch failure; running batch 3; running final
  commit; or requiring Provider failure and later-batch database failure to be
  the same trigger.
- **Planned test level:** Embedding-fatal and Provider-fatal secrecy are each
  independently executable at provider-adapter contract, PostgreSQL
  integration, and HTTP integration. Keyword/database-fatal, final-
  authorization-statement, final-commit, and later-batch are independently
  executable at PostgreSQL integration with separately owned HTTP mappings.
  Both AF-3B hybrid final-commit and hybrid later-batch regressions are
  independent PostgreSQL integration obligations with their own phase-
  qualified AF-3C HTTP mappings.
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

- **Category:** Privacy, public errors, and cache behavior. The non-HTTP
  regression is `RET-PRIV-006::AF3B-HYBRID-TELEMETRY-BOUNDS`; the public row
  is `RET-PRIV-006::AF3C-HTTP-TELEMETRY-BOUNDS`.
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
| ADR-008-R02 — Exact proof/initial-release/pure-validation/keyword-release/embedding/Chroma/union/final-transaction lifecycle and resource barriers | RET-AUTH-001, RET-AUTH-011; all RET-CONC-001 lifecycle variants; the separate AF3A and AF3B identities in RET-CONC-002 through RET-CONC-003; RET-KEY-001 through RET-KEY-004; RET-PRIV-004 keyword-, embedding-, and Provider-fatal identities |
| ADR-008-R03 — Fresh timezone-aware final clock, strict expiry boundary, and actual fixed `REPEATABLE READ`, `READ ONLY` first-statement reauthorization | RET-CONC-001 (actual request settings), RET-CONC-002 through RET-CONC-003, RET-CONC-012, every RET-CONC-013 clock/expiry variant, and RET-EVID-003 citation final-transaction rows; never a helper, mutation actor, unrelated session, initial time, or Provider timestamp |
| ADR-008-R04 — Same snapshot for all batches and every internal authoritative retrieval record/public-citation field | Provider-independent AF3A identities and separate AF3B regression identities in RET-CONC-006 through RET-CONC-010; RET-EVID-001 internal authoritative retrieval record identities; RET-EVID-003 public Citation identities |
| ADR-008-R05 — Request linearization, revocation/deletion timing, and stale derived IDs | RET-CONC-001 through RET-CONC-010, RET-CONC-012 through RET-CONC-014 |
| ADR-008-R06 — All-or-nothing transaction failure | The four AF3A failure identities and four distinct AF3B hybrid regressions in RET-CONC-011; RET-PRIV-004's AF3A final-authorization, final-commit, and later-batch identities plus the separate `AF3B-HYBRID-FINAL-COMMIT-ALL-SINK-REGRESSION` and `AF3B-HYBRID-LATER-BATCH-ALL-SINK-REGRESSION` identities |
| ADR-008-R07 — PostgreSQL authority for identity, scope, state, content, hash, source/provenance, and every citation-resolution field | RET-AUTH-007 through RET-AUTH-009, RET-PROV-030 through RET-PROV-031, RET-PROV-033 through RET-PROV-037, RET-KEY-001 through RET-KEY-004, RET-EVID-001 through RET-EVID-010, especially the exact public citation operation and current authoritative resolution in RET-EVID-003 through RET-EVID-009 |
| ADR-008-R08 — Completed status plus persisted non-null valid hash | RET-KEY-001, RET-EVID-002, RET-EVID-009, RET-EVID-010 |
| ADR-008-R09 — Exact citation operation, current reauthentication/target authorization, authoritative revision binding, and non-bearer reference | RET-EVID-003 through RET-EVID-009, including each named citation HTTP precedence/body/schema variant |
| ADR-008-R10 — Exact bounded single embedding operation, exact vector validation, and no Provider authority | RET-CONC-001 embedding variants; RET-PROV-040 exact payload oracle; every RET-PROV-041 embedding count/dimension/type/no-coercion-overflow-sentinel/non-finite/byte/deadline/attempt variant including its distinct real-PostgreSQL lifecycle oracle; RET-PROV-023 through RET-PROV-031; RET-KEY-002; RET-EVID-001 |
| ADR-008-R11 — Version/query inclusive wire/decode ceilings, exact field/metadata grammar and bounds, and exact depth counting | All named positive grammar variants in RET-PROV-001 paired with RET-PROV-010 through RET-PROV-013 and every named negative grammar branch in RET-PROV-016; RET-PROV-002 through RET-PROV-009; RET-PROV-014; every bounded version variant in RET-PROV-020 |
| ADR-008-R12 — Strict UTF-8/RFC 8259 and unsupported-range numeric failures, canonical response-fatal taxonomy, version/missing-field fatality, independent Provider outage branches, and no fallback | RET-PROV-003 through RET-PROV-006, RET-PROV-009 through RET-PROV-014, RET-PROV-015 (fully canonical literal `NaN`, `Infinity`, and `-Infinity` wire failures plus valid-JSON `1e400` finite-domain failure), RET-PROV-016 (encoding/unknown/duplicate/null/return-field policy), RET-PROV-017 (every missing required key), RET-PROV-018 through RET-PROV-022 (configured count, version probe, position, connection, timeout), RET-BND-007, RET-CONC-011, RET-PRIV-004 |
| ADR-008-R13 — Position-preserving candidate-local taxonomy and authorized empty | RET-PROV-008, RET-PROV-025 through RET-PROV-038 (including missing and non-string ID variants), RET-EVID-010 |
| ADR-008-R14 — Finite wire-distance domain, typed diagnostic `None`, post-decoder typed non-finite/wrong-type omission, absolute-position preservation, and ignored bounded disagreement | RET-PROV-015, RET-PROV-023 through RET-PROV-024, RET-PROV-025 through RET-PROV-026 (`float("nan")`, `float("inf")`, and `float("-inf")` at exact rank 2 with valid ranks 1/3), RET-PROV-027 (string/object/boolean/null/array matrix at exact rank 2), RET-PROV-028 (mixed absolute ranks), RET-PROV-030 through RET-PROV-031, RET-PROV-038 |
| ADR-008-R15 — Duplicate earliest-rank behavior | RET-PROV-039, RET-BND-013, RET-RANK-003 |
| ADR-008-R16 — Exact body/decoded-query/request/configured-Provider/raw-position/dense/keyword/union/batch/final-result domains and bounded SQL work | RET-BND-001 through RET-BND-003, including the U+0000 exclusion, adjacent-U+0001 control, distinct raw/escaped JSON paths, and 65,536/65,537 body rows; RET-EVID-003 citation body rows; RET-BND-004 through RET-BND-015; RET-PROV-002 through RET-PROV-007; all four RET-PROV-019 C40/C128 equality/plus-one rows; RET-KEY-001 |
| ADR-008-R17 — Scoped deterministic PostgreSQL keyword rank generation and internal-path exclusion | The exact AF3A keyword identities in RET-KEY-001 through RET-KEY-004; their separately labelled AF3B hybrid regressions; AF3C HTTP/internal-repository assertions only in the exact AF3C rows |
| ADR-008-R18 — Deterministic union, batching, non-rank-bearing permutations, query count, reconstruction, and independent failure branches | Provider-independent AF3A synthetic-input identities and separate AF3B hybrid regressions in RET-BND-008 through RET-BND-015; the separate AF3A/AF3B identities in RET-CONC-010 and RET-CONC-011 |
| ADR-008-R19 — Exact rational RRF, absolute source-rank prerequisites, earliest-rank preservation, display serialization, and tie-breaking | RET-KEY-001 (deterministic keyword source ranks), RET-PROV-025 through RET-PROV-028 (dense invalid-position ranks remain 1/3 and 1/3/5/7), RET-PROV-038 (valid companion retains original position), RET-PROV-039 (earliest dense rank/contribution), RET-BND-013 (earliest ranks across duplicates), RET-RANK-001 through RET-RANK-005 (exact rational formula, mixed sources, collision, full tie order) |
| ADR-008-R20 — Frozen/slotted/non-public internal authoritative retrieval record, structural trust separation, complete pre-commit materialization, and AF-3C-only public schemas | RET-CONC-007 through RET-CONC-010, RET-CONC-014, RET-EVID-001, RET-EVID-002, RET-EVID-010, RET-RANK-001 through RET-RANK-005, RET-INJ-001 through RET-INJ-006; AF-3C public mapping in RET-EVID-003 through RET-EVID-009 and RET-PRIV-002 through RET-PRIV-003 |
| ADR-008-R21 — P0 AF-3 semantic injection boundary | RET-INJ-001 through RET-INJ-006 |
| ADR-008-R22 — Later consumer-specific acceptance | RET-FUT-001 through RET-FUT-004 |
| ADR-008-R23 — Public errors, valid present-empty behavior, authorized empty, no synthetic `403`, and cache | RET-AUTH-004, RET-AUTH-005, RET-AUTH-010 (present-empty provider response), RET-AUTH-011, RET-CONC-011, RET-BND-008 (present-empty dense source and zero union), RET-PRIV-004, RET-PRIV-005 |
| ADR-008-R24 — Same recursive exact/substring all-sink scanner on success/failure with field-specific public allowlists and bounded telemetry | Exact ledger projection: every canonical row whose Owner is AF-3A, AF-3B, or AF-3C, at that row's declared level and execution boundary. RET-PRIV-001/002/003/004/006 provide focused sentinel, allowlist, mutation, fatal-path, and telemetry conformance controls but do not narrow the projection; FUTURE rows are excluded until their named consumer activates them. |
| ADR-008-R25 — P0 response/trust controls remain distinct from P1 hardening | RET-PROV-006, RET-PROV-010, RET-INJ-001 through RET-INJ-006, RET-FUT-001 through RET-FUT-004 |
| ADR-008-R26 — Per-instance single-flight compatibility, state clearing, trusted collection UUID, read-only retrieval, bounded total deadlines, and one-attempt/no-fallback policy | RET-PROV-020 version-contract variants, all RET-PROV-042 single-flight/lifetime/failure/cancellation/no-retry variants, and exactly the 15 level-qualified RET-PROV-043 tuples retained by its executable oracle matrix |
| ADR-008-R27 — No security-correctness migration/index dependency and semantics-preserving optional performance work | RET-KEY-001 exact unindexed semantic oracle and its future indexed implementation regression at real PostgreSQL level |

This matrix covers initial authorization, final snapshot authorization,
revocation timing, fixed snapshots, candidate parsing, cross-scope rejection,
provider body limits and taxonomy, request/result limits, SQL batch bounds,
keyword SQL scope, null-hash exclusion, internal authoritative retrieval record and public Evidence trust classification,
citation reauthorization, RRF determinism, provider outage, no fallback, cache
control, privacy logging, and P0 injection-evidence handling.

## Suite acceptance rule

AF-3 completes only when every canonical row owned by AF-3A, AF-3B, or AF-3C
is implemented and passing. A status on one row never marks its stable ID or a
different level implemented. The four FUTURE rows become mandatory only with
their named consumers and are not AF-3C runtime claims.

For every such runtime row, passing includes the ADR-008-R24 scanner sidecar at
the same boundary and level. Functional success without its owned sink scan is
a row failure; no phase close may sample, defer, or replace that sidecar with a
RET-PRIV case-level result.

### AF-3A close gate

**Gate status:** `SATISFIED`. All 115 AF-3A-owned canonical rows have the
approved closure-compatible implemented/merged status, so AF-3A is `CLOSED`.

AF-3A closes only when every canonical row whose Owner is AF-3A is implemented
and passing at its exact level. Its permitted execution boundaries are only
PURE_REQUEST_VALIDATOR, AF3A_INITIAL_ACCESS, AF3A_KEYWORD,
AF3A_FINAL_VALIDATOR, and AF3A_CONCURRENCY. The gate rejects any AF-3A row
that performs embedding, Chroma/Provider, dense, hybrid union, fusion, public
Evidence/Citation, or HTTP work. No AF-3B or AF-3C row can satisfy or block the
AF-3A close classification.

### AF-3B entry gate

**Gate status:** `SATISFIED`. AF-3B is ready to begin under a separately
authorized implementation gate; AF-3B implementation has not started.

AF-3B may enter only after the AF-3A close gate above is satisfied. Entry is
derived from AF-3A-owned provider-independent rows only. No unsplit mixed
fixture, AF-3B regression, Provider-time row, or public row is an AF-3A
prerequisite, so the dependency is non-circular.

### AF-3B close gate

After entry, AF-3B closes only when every canonical row whose Owner is AF-3B
is implemented and passing. AF3B_HYBRID_REGRESSION rows are explicit
phase-qualified reruns of AF-3A controls after dense/hybrid extension; they do
not change the ownership or status of the underlying AF-3A prerequisite row.
In addition, AF-3B close reruns the following exact AF-3A-owned rows without
transferring them or changing their status:

- `RET-AUTH-010::AF3A-FINAL-SNAPSHOT-ZERO-CANDIDATES` at PostgreSQL integration;
- `RET-CONC-011::AF3A-BATCH-TWO-STATEMENT-FAILURE` at PostgreSQL integration;
- `RET-CONC-011::AF3A-BATCH-TWO-STATEMENT-TIMEOUT` at PostgreSQL integration;
- `RET-CONC-011::AF3A-FINAL-COMMIT-FAILURE` at PostgreSQL integration;
- `RET-CONC-011::AF3A-FINAL-CONNECTION-FAILURE` at PostgreSQL integration;
- `RET-CONC-013::AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY` at PostgreSQL integration;
- `RET-CONC-013::AF3A-PROVIDER-INDEPENDENT-ELAPSED-BARRIER-EXPIRY` at deterministic concurrency;
- `RET-KEY-002::AF3A-CROSS-SCOPE-REVALIDATION` at PostgreSQL integration;
- `RET-PRIV-004::KEYWORD-DATABASE-FATAL-ALL-SINK-SECRECY` at PostgreSQL integration;
- `RET-PRIV-004::FINAL-AUTHORIZATION-STATEMENT-FATAL-ALL-SINK-SECRECY` at PostgreSQL integration;
- `RET-PRIV-004::FINAL-COMMIT-ALL-SINK-SECRECY` at PostgreSQL integration; and
- `RET-PRIV-004::LATER-BATCH-ALL-SINK-SECRECY` at PostgreSQL integration.

No sampling, skip, waiver, global case status, or single-level surrogate
satisfies the AF-3B close gate.

### AF-3C public gate

**Gate status:** `BLOCKED` until AF-3B is `CLOSED`.

HTTP, request-wire, media, public-error, cache, serialization, public Evidence,
Citation, and public all-sink rows are owned only by AF-3C. They remain
REQUIRED_NOT_YET_IMPLEMENTED and cannot become passing through AF-3A close,
AF-3B entry, or AF-3B close. They still block AF-3 as a whole.

A documentation review does not satisfy a runtime case. Any change to a stable
ID, expected result, trust decision, limit profile, taxonomy, transaction
linearization rule, test level, or trace mapping requires explicit review.
Passing this suite would complete AF-3's defined retrieval gate only; it would
not establish complete security, complete prompt-injection prevention,
complete hostile-document containment, or production readiness.
