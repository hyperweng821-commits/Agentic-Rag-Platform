# AF-3 retrieval security acceptance specification

## Status and purpose

This is the required future executable-test specification for ADR-008. AF-3
retrieval is planned and unimplemented. Every case has implementation status
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
- The fixed final transaction is `REPEATABLE READ` and normally `READ ONLY`.
  Its first authoritative statement fixes the snapshot and revalidates the
  session, active user, exact target, membership, and read capabilities.
- Planned test-level values are deterministic ordered sets drawn from:
  `unit`, `provider-adapter contract`, `PostgreSQL integration`,
  `HTTP integration`, and `future consuming-phase acceptance`.
- Unit tests use deterministic fakes and no network. Provider-adapter contract
  tests use bounded mock transports. PostgreSQL integration tests observe SQL,
  transaction isolation, snapshots, and concurrency. HTTP integration tests
  observe public status, envelopes, cache headers, and no-fallback behavior.

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

Every case below contains the same required fields. Membership-removal cases
are intentionally separate only where they prove a different layer or timing
point: final-transaction linearization, zero-candidate authorization, or
citation reauthorization.

## Authentication and request scope

### RET-AUTH-001 — Missing session

- **Category:** Authentication and request scope.
- **Initial database state:** Target has an owner, one completed document, and one eligible hashed chunk.
- **Authenticated principal and membership state:** No session and no principal.
- **Provider or Chroma input:** Provider spies are configured but must receive no call.
- **Concurrent state change:** None.
- **Expected public result:** Generic `401 AUTHENTICATION_REQUIRED`, no Evidence, and private/no-store.
- **Expected internal validation result:** Authentication stops before target lookup, keyword SQL, embedding, or Chroma.
- **Forbidden behavior:** Target disclosure, provider work, candidate counting, or private content.
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

- **Category:** Authentication and request scope.
- **Initial database state:** Target exists with eligible content but no caller membership.
- **Authenticated principal and membership state:** Live active user is not a target member.
- **Provider or Chroma input:** Client claims an empty candidate set; provider spies must remain unused.
- **Concurrent state change:** None.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, not authorized empty Evidence, and private/no-store.
- **Expected internal validation result:** Initial exact-target membership SQL fails before any candidate-dependent branch.
- **Forbidden behavior:** `200 []`, `403`, target disclosure, global search, or provider work.
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
- **Expected internal validation result:** Authorization derives only from exact-target PostgreSQL membership; the client document ID grants nothing.
- **Forbidden behavior:** Document-ID possession, metadata, or existence checks widening access.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-AUTH-008 — Client chunk IDs cannot authorize

- **Category:** Authentication and request scope.
- **Initial database state:** A current eligible chunk belongs to another user's private target.
- **Authenticated principal and membership state:** Live caller has no target membership.
- **Provider or Chroma input:** Request supplies the real canonical chunk ID as a client-controlled field.
- **Concurrent state change:** None.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no Evidence, and private/no-store.
- **Expected internal validation result:** Client chunk identity is ignored or rejected as an authorization mechanism before provider work.
- **Forbidden behavior:** Treating a canonical ID, provider metadata, or citation-like value as access.
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
- **Provider or Chroma input:** Legal keyword query returns zero and bounded dense provider returns zero.
- **Concurrent state change:** None.
- **Expected public result:** Successful authorized empty Evidence and private/no-store.
- **Expected internal validation result:** Final authorization statement still runs; validation-batch query count is zero.
- **Forbidden behavior:** `404`, `503`, skipping final authorization, or fabricating a hit.
- **Planned test level:** PostgreSQL integration, HTTP integration.
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

### RET-CONC-001 — Membership revoked before final snapshot

- **Category:** Final transaction and concurrency.
- **Initial database state:** Caller initially has target membership and eligible content.
- **Authenticated principal and membership state:** Live member passes the initial check.
- **Provider or Chroma input:** Controlled provider blocks, then returns a valid current candidate.
- **Concurrent state change:** Membership deletion commits before the final transaction's first authoritative statement.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no Evidence, and private/no-store.
- **Expected internal validation result:** Final snapshot observes access loss and aborts before candidate Evidence survives.
- **Forbidden behavior:** Initial-principal authority, empty success, partial Evidence, or asynchronous-cancellation claims.
- **Planned test level:** PostgreSQL integration, HTTP integration.
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
- **Concurrent state change:** Document changes to `processing` or `failed` and commits before snapshot acquisition.
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
- **Initial database state:** Old eligible chunk O is visible when the final snapshot is fixed.
- **Authenticated principal and membership state:** Live target member is authorized in that snapshot.
- **Provider or Chroma input:** O is a valid candidate; barrier pauses before batch validation.
- **Concurrent state change:** Replace O with N and commit elsewhere before final transaction commit.
- **Expected public result:** Current response may return snapshot-loaded O with O's persisted hash; a later request uses N.
- **Expected internal validation result:** All authoritative O fields load in the original snapshot and remain immutable after commit.
- **Forbidden behavior:** Combining O identity with N content/hash, post-commit reload, or provider-text substitution.
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
- **Initial database state:** Several batches contain eligible target chunks.
- **Authenticated principal and membership state:** Live target member passes fixed-snapshot authorization.
- **Provider or Chroma input:** Bounded candidates span multiple batches; deterministic fault is injected after an earlier batch succeeds.
- **Concurrent state change:** The later batch query or transaction fails before completion.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Transaction rollback/discard removes every accumulated authoritative record.
- **Forbidden behavior:** Partial Evidence, keyword-only fallback, commit of an earlier batch, or candidate content in the error.
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

### RET-PROV-001 — Bounded valid response

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible hashed chunk.
- **Authenticated principal and membership state:** Live target member with read capabilities.
- **Provider or Chroma input:** Version-supported JSON within every byte, field, metadata, count, and depth ceiling contains the canonical ID.
- **Concurrent state change:** None.
- **Expected public result:** One authorized Evidence item and private/no-store.
- **Expected internal validation result:** Transport, bounded decode, structural parsing, canonical parsing, and PostgreSQL validation all succeed.
- **Forbidden behavior:** Requesting or using provider text/provenance as authority or performing unbounded decode.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-002 — Exact inclusive wire ceiling is accepted

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible candidate.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** A structurally valid JSON response totals exactly 1,048,576 raw/wire bytes, remains within the decoded ceiling, candidate-count and every per-field limit, and nesting depth 16, and contains the eligible canonical candidate; legal JSON whitespace or another schema-valid bounded construction supplies any exact-size padding.
- **Concurrent state change:** None.
- **Expected public result:** Normal authorized Evidence and private/no-store rather than a size failure.
- **Expected internal validation result:** The `wire_bytes <= 1,048,576` check accepts the exact inclusive ceiling; bounded parsing and ordinary candidate processing continue.
- **Forbidden behavior:** Rejecting on `wire_bytes >= 1,048,576`, enforcing an effective 1,048,575-byte maximum, unbounded buffering, or bypassing decoded, field, count, or depth bounds.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-003 — Declared Content-Length above wire ceiling

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have valid keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** `Content-Length` declares 1,048,577 bytes.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Adapter rejects before reading the response body.
- **Forbidden behavior:** Body read, truncation, partial dense result, or keyword-only fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-004 — Missing Content-Length streams above wire ceiling

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have valid keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** No `Content-Length`; streamed raw bytes reach 1,048,577.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Streaming aborts immediately when cumulative wire bytes exceed the ceiling.
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
- **Provider or Chroma input:** Compressed response stays within 1,048,576 wire bytes but expands to 2,097,153 decoded bytes.
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
- **Provider or Chroma input:** A compressed response uses at most 1,048,576 cumulative raw/wire bytes and decodes to exactly 2,097,152 bytes of valid JSON. Candidate count, every candidate ID and individual field, metadata count, keys and values, and nesting depth at most 16 remain within their hard limits. The exact decoded size uses legal compressible JSON whitespace or another schema-valid bounded construction, never an unbounded string field.
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
- **Provider or Chroma input:** Canonical ID is valid but an untrusted text field is 4,097 UTF-8 bytes.
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
- **Provider or Chroma input:** Candidate metadata contains 33 entries.
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
- **Provider or Chroma input:** Candidate metadata has a 129-byte UTF-8 key.
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
- **Provider or Chroma input:** Candidate metadata contains a scalar/string representation of 1,025 UTF-8 bytes.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Metadata-value ceiling rejects the whole response.
- **Forbidden behavior:** Truncation, candidate-local omission, partial Evidence, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-014 — Excessive JSON nesting

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Body is within byte limits but reaches nesting depth 17.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Bounded parser rejects depth before normal candidate handling.
- **Forbidden behavior:** Recursive unbounded decode, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-015 — Invalid JSON

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have valid keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Byte-bounded response is syntactically invalid JSON.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Parse failure is response-fatal and normalized without payload details.
- **Forbidden behavior:** Heuristic recovery, partial dense records, exception disclosure, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-016 — Wrong top-level response shape

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Bounded JSON top level has the wrong type or envelope shape.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Envelope validation classifies the entire response as fatal.
- **Forbidden behavior:** Shape coercion, partial extraction, or keyword-only fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-017 — Missing required candidate collection

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Supported bounded envelope omits the required candidate collection.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Required-field validation makes the whole response fatal.
- **Forbidden behavior:** Treating omission as zero hits, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-018 — Mismatched parallel-array lengths

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Candidate IDs, distances, or related parallel arrays have different lengths.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Position ambiguity is response-fatal.
- **Forbidden behavior:** Zip-to-shortest behavior, guessed positions, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-019 — Candidate count above configured maximum

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have valid candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Structurally valid collection contains one more record than requested or configured.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Count validation rejects the whole response before canonical candidate processing.
- **Forbidden behavior:** Truncation, partial dense acceptance, or keyword-only fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-020 — Unsupported envelope version

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Bounded structurally coherent response declares an unsupported version.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Version gate rejects the whole response deterministically.
- **Forbidden behavior:** Best-effort parsing, downgrade guessing, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-021 — Candidate positions cannot be reconstructed

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target may have keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Bounded data structure is structurally ambiguous about candidate order or grouping.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Deterministic-position requirement classifies the whole response as fatal.
- **Forbidden behavior:** Arbitrary ordering, guessed rank, partial result, or fallback.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-022 — Network or timeout failure

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has legal keyword candidates.
- **Authenticated principal and membership state:** Live target member passes initial authorization.
- **Provider or Chroma input:** Deterministic mock raises connection failure or bounded timeout.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Adapter normalizes the failure without raw exception or payload leakage.
- **Forbidden behavior:** Retry without a bound, stale cache, partial result, provider details, or keyword-only fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-023 — Finite optional score

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible hashed chunk.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Canonical ID has a finite numeric score and provider rank 1.
- **Concurrent state change:** None.
- **Expected public result:** One authorized Evidence item.
- **Expected internal validation result:** Candidate is retained; fusion uses rank 1 and does not arithmetically use the raw score.
- **Forbidden behavior:** Treating score as authority or adding it to keyword/RRF score.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-024 — Absent optional score

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has one eligible hashed chunk.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Canonical candidate has no optional score but has deterministic list position.
- **Concurrent state change:** None.
- **Expected public result:** One authorized Evidence item.
- **Expected internal validation result:** Absence does not invalidate the candidate; provider list rank drives fusion.
- **Forbidden behavior:** Response-fatal classification, local omission, or invented numeric score.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-025 — NaN score is candidate-local

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has the referenced eligible chunk.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** Structurally valid bounded record has a present `NaN` score.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence when it is the only candidate.
- **Expected internal validation result:** Only that candidate is omitted; the surrounding response remains valid.
- **Forbidden behavior:** Whole-response `503`, non-finite fusion, or accepting the candidate.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-026 — Infinite score is candidate-local

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has the referenced eligible chunks.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** Parameterized bounded records contain positive or negative infinity.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence when the record is the only candidate.
- **Expected internal validation result:** Each non-finite record is locally omitted with no public reason.
- **Forbidden behavior:** Whole-response `503`, infinite RRF value, or candidate acceptance.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-027 — Wrong-type score is candidate-local

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has the referenced eligible chunk.
- **Authenticated principal and membership state:** Live target member remains authorized.
- **Provider or Chroma input:** Bounded candidate record has a string, object, or boolean in the optional score field.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence when it is the only candidate.
- **Expected internal validation result:** Only that record is omitted while envelope structure remains usable.
- **Forbidden behavior:** Type coercion, response-fatal `503`, or raw score use.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-028 — Mixed valid and candidate-local-invalid records

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Target has two eligible hashed chunks.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Ordered bounded list mixes valid records with malformed IDs and wrong-type/non-finite-score records.
- **Concurrent state change:** None.
- **Expected public result:** Evidence contains only valid candidates in their preserved relative provider order.
- **Expected internal validation result:** Local omissions do not shift the relative rank order of remaining records.
- **Forbidden behavior:** Whole-response `503`, invalid Evidence, reordering, or reason disclosure.
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
- **Provider or Chroma input:** Bounded metadata falsely names knowledge base B, another document, hash, and provenance.
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
- **Provider or Chroma input:** Bounded provider text Q disagrees with P.
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
- **Provider or Chroma input:** Correct bounded string type uses missing prefix, invalid UUID, or non-canonical UUID spelling.
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
- **Expected internal validation result:** Dense rank 2 is preserved; rank 5 adds neither score nor duplicate Evidence.
- **Forbidden behavior:** Malformed-response classification, later-rank overwrite, or duplicate output.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PROV-040 — Provider request asks only for candidate handling fields

- **Category:** Provider transport, decoding, and taxonomy.
- **Initial database state:** Authorized target has eligible indexed content.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Adapter spy captures the outbound dense query and returns a bounded valid ID/rank response.
- **Concurrent state change:** None.
- **Expected public result:** Normal authorized Evidence from PostgreSQL.
- **Expected internal validation result:** Request principally asks for IDs and rank/distance fields, not documents, text, or provenance as response authority.
- **Forbidden behavior:** Requesting provider content for authoritative Evidence or citation construction.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Request, result, union, and SQL bounds

### RET-BND-001 — Query character limit

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Normalized query contains one more character than the configured maximum.
- **Concurrent state change:** None.
- **Expected public result:** Existing `422 VALIDATION_ERROR`, no Evidence, and private/no-store.
- **Expected internal validation result:** Character count rejects before keyword SQL, embedding, or Chroma.
- **Forbidden behavior:** Truncation, provider work, raw query logging, or byte-only validation.
- **Planned test level:** unit, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-002 — Query UTF-8 byte limit

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Multibyte normalized query is within the character limit but one UTF-8 byte above the byte limit.
- **Concurrent state change:** None.
- **Expected public result:** Existing `422 VALIDATION_ERROR`, no Evidence, and private/no-store.
- **Expected internal validation result:** UTF-8 byte count independently rejects before provider or keyword work.
- **Forbidden behavior:** Character-only acceptance, truncation, provider calls, or query disclosure.
- **Planned test level:** unit, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-003 — Requested result limit

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target contains more eligible chunks than the configured result maximum.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Caller requests one more result than the configured maximum.
- **Concurrent state change:** None.
- **Expected public result:** Existing `422 VALIDATION_ERROR`, no Evidence, and private/no-store.
- **Expected internal validation result:** Result-count validation rejects before over-fetch arithmetic or provider work.
- **Forbidden behavior:** Silent clamp, overflow arithmetic, or provider call.
- **Planned test level:** unit, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-004 — Dense over-fetch arithmetic below ceiling

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Valid requested count multiplied by the versioned factor remains below `MAX_DENSE_CANDIDATES`.
- **Concurrent state change:** None.
- **Expected public result:** Normal bounded retrieval behavior.
- **Expected internal validation result:** `dense_fetch_count` equals checked `requested_count * DENSE_OVERFETCH_FACTOR`.
- **Forbidden behavior:** Floating arithmetic, unchecked overflow, off-by-one count, or unbounded provider request.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-005 — Dense over-fetch ceiling

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target exists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Valid requested count times factor exceeds `MAX_DENSE_CANDIDATES`.
- **Concurrent state change:** None.
- **Expected public result:** Normal bounded retrieval behavior.
- **Expected internal validation result:** Overflow-safe calculation yields exactly `MAX_DENSE_CANDIDATES` in the outbound request.
- **Forbidden behavior:** Request above ceiling, arithmetic wrap, or post-response-only truncation.
- **Planned test level:** unit, provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-006 — Keyword candidate maximum

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** More than `MAX_KEYWORD_CANDIDATES` eligible target chunks match.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Dense response is bounded and valid.
- **Concurrent state change:** None.
- **Expected public result:** Result remains within requested Evidence count.
- **Expected internal validation result:** Legal scoped keyword SQL returns at most exactly the configured keyword maximum.
- **Forbidden behavior:** Unbounded SQL result materialization, global count exposure, or Python-only limiting.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-007 — Candidate union above configured maximum

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target has enough eligible identities for disjoint bounded source lists.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Individually legal keyword and dense lists create `MAX_UNIQUE_CANDIDATES + 1` unique IDs.
- **Concurrent state change:** None.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, no Evidence, and private/no-store.
- **Expected internal validation result:** Union ceiling rejects before SQL partition allocation and discards both source lists.
- **Forbidden behavior:** Arbitrary truncation, partial Evidence, unbounded allocation, or fallback.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-008 — Zero unique candidates

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Authorized target remains current.
- **Authenticated principal and membership state:** Live target member passes final authorization.
- **Provider or Chroma input:** Both bounded source lists are empty.
- **Concurrent state change:** None.
- **Expected public result:** Authorized empty Evidence.
- **Expected internal validation result:** `U = 0`, validation-batch query count is 0, and the separate first authorization statement still runs.
- **Forbidden behavior:** Empty `IN` query, skipped authorization, or `503`.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
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
- **Initial database state:** More than two batches of eligible target chunks exist.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Identical bounded keyword/dense fixtures are presented repeatedly in different arrival orders.
- **Concurrent state change:** None.
- **Expected public result:** Every repetition returns identical final Evidence ordering.
- **Expected internal validation result:** Unique UUID sort produces identical contiguous partitions and exactly `ceil(U / B)` queries.
- **Forbidden behavior:** Hash/set iteration ordering, arrival-order partitions, N+1 queries, or unstable results.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-BND-013 — Duplicate source candidates reduce unique union

- **Category:** Request, result, union, and SQL bounds.
- **Initial database state:** Eligible chunks appear repeatedly within and across sources.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded keyword and dense lists contain duplicates with known earliest ranks.
- **Concurrent state change:** None.
- **Expected public result:** At most one Evidence item per chunk.
- **Expected internal validation result:** `U` counts unique UUIDs only; partitions and `ceil(U / B)` use that count while source rank maps remain separate.
- **Forbidden behavior:** Duplicate SQL parameters, duplicate Evidence, lost earliest rank, or counting source occurrences as `U`.
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
- **Initial database state:** Exactly `MAX_UNIQUE_CANDIDATES` eligible rows exist.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded source lists yield that exact unique maximum.
- **Concurrent state change:** None.
- **Expected public result:** Bounded authorized Evidence.
- **Expected internal validation result:** Actual validation queries equal exactly `ceil(MAX_UNIQUE_CANDIDATES / B)`; the first authorization statement is separately counted.
- **Forbidden behavior:** Hidden per-row queries, an unbounded `IN`, or counting authorization as a validation batch.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

## Keyword SQL scope

### RET-KEY-001 — Legal keyword SQL excludes out-of-target chunks

- **Category:** Keyword SQL scope.
- **Initial database state:** A and B contain identical searchable text; caller requests A.
- **Authenticated principal and membership state:** Live A member; B may be visible separately or inaccessible.
- **Provider or Chroma input:** Dense response is empty and valid.
- **Concurrent state change:** None.
- **Expected public result:** Only A Evidence or authorized empty, never B.
- **Expected internal validation result:** First keyword query predicates exact A, current membership/capabilities, completed status, valid hash, and ownership.
- **Forbidden behavior:** Global keyword search, Python post-filter as primary scope, or B hit/count exposure.
- **Planned test level:** PostgreSQL integration, HTTP integration.
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
- **Provider or Chroma input:** Known one-based keyword and dense rank maps.
- **Concurrent state change:** None.
- **Expected public result:** Evidence exposes expected source ranks, fused scores, and one-based fused ranks.
- **Expected internal validation result:** Each score equals `sum(1 / (60 + source_rank))` with `RRF_K = 60`.
- **Forbidden behavior:** Zero-based ranks, another constant, raw-score arithmetic, or rounding-dependent ordering.
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
- **Initial database state:** One eligible chunk appears in both source maps.
- **Authenticated principal and membership state:** Authorized target context.
- **Provider or Chroma input:** Same UUID has known keyword and dense ranks.
- **Concurrent state change:** None.
- **Expected public result:** One Evidence item carries both contributing ranks.
- **Expected internal validation result:** RRF sums both rank contributions once and identity deduplication remains authoritative.
- **Forbidden behavior:** Two Evidence items, lost contribution, or raw-score merge.
- **Planned test level:** unit, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-RANK-004 — Complete deterministic tie order

- **Category:** RRF and result determinism.
- **Initial database state:** Eligible UUID fixtures are chosen to exercise every tie level.
- **Authenticated principal and membership state:** Authorized target context.
- **Provider or Chroma input:** Rank maps create equal fused scores and controlled best/keyword/dense ranks.
- **Concurrent state change:** None.
- **Expected public result:** Order is fused score descending, best rank ascending, keyword rank ascending absent-last, dense rank ascending absent-last, UUID ascending.
- **Expected internal validation result:** Parameterized fixtures reach each successive comparator deterministically.
- **Forbidden behavior:** Provider arrival, SQL row order, raw score, random value, or locale-sensitive UUID order.
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
- **Expected public result:** Evidence contains only approved PostgreSQL values, ranks, citation reference, and `untrusted_document_content`.
- **Expected internal validation result:** Every response field loads within the fixed final snapshot from an allowlisted projection.
- **Forbidden behavior:** Provider authority, storage path, secret, raw embedding, internal exception, or post-commit reload.
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

### RET-EVID-003 — Current citation resolves authoritatively

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation binds current chunk UUID and persisted valid hash; document remains completed and visible.
- **Authenticated principal and membership state:** Live target member with current read capabilities.
- **Provider or Chroma input:** No provider call; caller presents the server-issued stable citation reference.
- **Concurrent state change:** None.
- **Expected public result:** Current PostgreSQL text, approved source display identity, provenance, and untrusted classification.
- **Expected internal validation result:** Resolver reauthenticates, scopes to one knowledge base, and matches document, chunk, and persisted hash.
- **Forbidden behavior:** Citation-as-authorization, Chroma lookup, storage path, or hash recomputation.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-004 — Citation fails after stale hash

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation expects hash H1; current same-identity row has a different persisted hash H2.
- **Authenticated principal and membership state:** Live target member retains access.
- **Provider or Chroma input:** No provider call; caller presents the H1 reference.
- **Concurrent state change:** Hash-changing authoritative update committed before resolution.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no old content, and private/no-store.
- **Expected internal validation result:** Exact current persisted-hash comparison fails closed.
- **Forbidden behavior:** Dynamic H1 recovery, silent rebinding to H2, Chroma fallback, or mismatch disclosure.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-005 — Citation fails after chunk replacement

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation names old chunk O; current document contains replacement N.
- **Authenticated principal and membership state:** Live target member retains access.
- **Provider or Chroma input:** No provider call; caller presents O's reference.
- **Concurrent state change:** Transactional replacement committed before resolution.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no O content, and private/no-store.
- **Expected internal validation result:** Resolver finds no current eligible exact O identity/hash.
- **Forbidden behavior:** Chunk-index rebinding, returning N under O's citation, or provider fallback.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-006 — Citation fails after document deletion or ineligibility

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation initially points to a current eligible chunk.
- **Authenticated principal and membership state:** Live target member retains membership.
- **Provider or Chroma input:** No provider call; caller presents the prior reference.
- **Concurrent state change:** Parameterized document deletion or transition away from `completed` commits before resolution.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no citation content, and private/no-store.
- **Expected internal validation result:** Current document existence and eligibility predicates fail closed.
- **Forbidden behavior:** Stale cached resolution, deleted text, status disclosure, or Chroma fallback.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-007 — Citation reauthorization after membership revocation

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Citation target remains current and hashed; prior member has lost target membership.
- **Authenticated principal and membership state:** Live active user has no current target membership.
- **Provider or Chroma input:** No provider call; caller presents a previously valid citation.
- **Concurrent state change:** Membership removal committed before citation resolution.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no citation content, and private/no-store.
- **Expected internal validation result:** Membership-scoped citation SQL returns no visible target.
- **Forbidden behavior:** Using prior access, citation possession, cache, or provider state as authorization.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-008 — Citation possession never authorizes a non-member

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Valid current citation target belongs to another user's private knowledge base.
- **Authenticated principal and membership state:** Live caller has never had target membership.
- **Provider or Chroma input:** No provider call; caller possesses the exact stable reference.
- **Concurrent state change:** None.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no existence disclosure, and private/no-store.
- **Expected internal validation result:** Exact target membership is required independently of reference validity.
- **Forbidden behavior:** Bearer-token citation semantics, foreign content, or a distinguishable “valid but forbidden” response.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-EVID-009 — Citation expected hash is absent

- **Category:** Evidence, eligibility, and citations.
- **Initial database state:** Current target chunk is legacy null-hash or the presented reference lacks its required expected hash.
- **Authenticated principal and membership state:** Live target member retains access.
- **Provider or Chroma input:** No provider call; caller presents the incomplete or null-hash citation reference.
- **Concurrent state change:** None.
- **Expected public result:** Generic hidden `404 NOT_FOUND`, no citation content, and private/no-store.
- **Expected internal validation result:** Resolver requires a persisted expected non-null valid hash and fails closed.
- **Forbidden behavior:** Hashing current text, substituting UUID/timestamp, returning content, or repairing the reference.
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
- **Expected public result:** Text may appear only inside Evidence labeled `untrusted_document_content`.
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
- **Expected public result:** Evidence may quote the claim but citation/provenance use only PostgreSQL values.
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

### RET-PRIV-001 — Raw query absent from normal logs

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** Authorized target has eligible content and structured log capture is active.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Bounded valid response; query contains a unique high-entropy sentinel.
- **Concurrent state change:** None.
- **Expected public result:** Normal bounded retrieval result.
- **Expected internal validation result:** Permitted telemetry records correlation/timing/count data without the sentinel.
- **Forbidden behavior:** Query in messages, structured fields, access logs, exception logs, traces, or provider payload logs.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-002 — Evidence content absent from normal logs

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** Eligible authoritative content contains a unique sentinel.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Valid candidate for the sentinel chunk.
- **Concurrent state change:** None.
- **Expected public result:** Authorized Evidence may contain the text; normal logs do not.
- **Expected internal validation result:** Content-free telemetry records only allowed bounded fields.
- **Forbidden behavior:** Chunk/document content in normal logs, errors, traces, or provider dumps.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-003 — Identifiers, paths, secrets, and raw payloads absent from logs

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** IDs, filename, storage path, session/CSRF digests, and content each contain traceable sentinels where representable.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Valid response plus a bounded provider-body sentinel.
- **Concurrent state change:** None.
- **Expected public result:** Approved Evidence fields only; no secret/path/internal details.
- **Expected internal validation result:** Normal telemetry excludes candidate/document/KB/citation IDs, filename/path, secrets, raw embedding, and raw body.
- **Forbidden behavior:** Any listed sentinel in normal log fields or error serialization.
- **Planned test level:** PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-004 — Stable provider/final-database error envelope

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** Caller and target pass initial authorization.
- **Authenticated principal and membership state:** Live target member.
- **Provider or Chroma input:** Parameterized provider-contract failure and final-transaction failure with private exception sentinels.
- **Concurrent state change:** None beyond the injected failure.
- **Expected public result:** Generic planned `503 RETRIEVAL_UNAVAILABLE`, stable public envelope, no Evidence, and private/no-store.
- **Expected internal validation result:** Failures normalize to content-free classification and all candidate state is discarded.
- **Forbidden behavior:** Stack trace, SQL/provider details, raw payload, partial Evidence, stale cache, or keyword-only fallback.
- **Planned test level:** provider-adapter contract, PostgreSQL integration, HTTP integration.
- **Implementation status:** `REQUIRED_NOT_YET_IMPLEMENTED`.

### RET-PRIV-005 — Every reachable private response is no-store

- **Category:** Privacy, public errors, and cache behavior.
- **Initial database state:** Separate reachable fixtures produce authorized Evidence, authorized empty, invalid request, invalid authentication, hidden target, and provider failure.
- **Authenticated principal and membership state:** State varies lawfully per fixture; no impossible retrieval `403` state is invented.
- **Provider or Chroma input:** Valid, empty, or fatal bounded fixture appropriate to each path.
- **Concurrent state change:** None.
- **Expected public result:** Each `200`, `401`, `404`, `422`, and planned `503` response has exactly `Cache-Control: private, no-store`.
- **Expected internal validation result:** Central private-response boundary covers every future retrieval path.
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
| ADR-008-R01 — Initial live-session authentication, exact target, and no client-ID authorization | RET-AUTH-001 through RET-AUTH-011 |
| ADR-008-R02 — Initial check and no transaction across provider work | RET-AUTH-001, RET-AUTH-011, RET-CONC-001 through RET-CONC-003 |
| ADR-008-R03 — Final fixed `REPEATABLE READ` authorization statement | RET-CONC-001 through RET-CONC-003, RET-CONC-012 |
| ADR-008-R04 — Same snapshot for all batches and Evidence fields | RET-CONC-006 through RET-CONC-010, RET-EVID-001 |
| ADR-008-R05 — Request linearization and revocation timing | RET-CONC-001 through RET-CONC-009 |
| ADR-008-R06 — All-or-nothing transaction failure | RET-CONC-011, RET-PRIV-004 |
| ADR-008-R07 — PostgreSQL authority | RET-PROV-030, RET-PROV-031, RET-EVID-001 |
| ADR-008-R08 — Completed status plus persisted non-null valid hash | RET-KEY-001, RET-EVID-002, RET-EVID-009, RET-EVID-010 |
| ADR-008-R09 — Citation reauthorization and revision binding | RET-EVID-003 through RET-EVID-009 |
| ADR-008-R10 — Chroma never authorizes or supplies authoritative fields | RET-PROV-030, RET-PROV-031, RET-PROV-040, RET-EVID-001 |
| ADR-008-R11 — Inclusive wire/decode ceilings and P0-v1 field bounds | RET-PROV-002 (wire ceiling), RET-PROV-003 through RET-PROV-005 (wire ceiling plus one), RET-PROV-006 (decoded ceiling plus one), RET-PROV-007 (decoded ceiling), RET-PROV-008 through RET-PROV-014, RET-PROV-019 |
| ADR-008-R12 — Response-fatal taxonomy, provider outage, and no fallback | RET-PROV-003 through RET-PROV-006, RET-PROV-009 through RET-PROV-022, RET-BND-007, RET-PRIV-004 |
| ADR-008-R13 — Position-preserving candidate-local taxonomy and authorized empty | RET-PROV-008, RET-PROV-025 through RET-PROV-038 (including missing and non-string ID variants), RET-EVID-010 |
| ADR-008-R14 — Optional score, provider order, and ignored bounded disagreement | RET-PROV-023 through RET-PROV-031 |
| ADR-008-R15 — Duplicate earliest-rank behavior | RET-PROV-039, RET-BND-013, RET-RANK-003 |
| ADR-008-R16 — Query/result/dense/keyword/provider/union bounds | RET-BND-001 through RET-BND-007, RET-PROV-019 |
| ADR-008-R17 — Keyword SQL scope and internal-path exclusion | RET-KEY-001 through RET-KEY-004 |
| ADR-008-R18 — Deterministic union, batching, query count, and failure | RET-BND-008 through RET-BND-015, RET-CONC-010, RET-CONC-011 |
| ADR-008-R19 — Exact RRF and tie-breaking | RET-RANK-001 through RET-RANK-005 |
| ADR-008-R20 — Evidence allowlist, trust class, and excluded data | RET-EVID-001, RET-PRIV-002, RET-PRIV-003 |
| ADR-008-R21 — P0 AF-3 semantic injection boundary | RET-INJ-001 through RET-INJ-006 |
| ADR-008-R22 — Later consumer-specific acceptance | RET-FUT-001 through RET-FUT-004 |
| ADR-008-R23 — Public errors, authorized empty, no synthetic `403`, and cache | RET-AUTH-004, RET-AUTH-005, RET-AUTH-010, RET-AUTH-011, RET-CONC-011, RET-PRIV-004, RET-PRIV-005 |
| ADR-008-R24 — Privacy logging and bounded telemetry | RET-PRIV-001 through RET-PRIV-003, RET-PRIV-006 |
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
