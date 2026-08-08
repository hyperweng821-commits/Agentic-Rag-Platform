"""Provider-adapter contract tests for bounded AF-3B Chroma retrieval."""

import asyncio
import gzip
import json
from collections.abc import AsyncIterator, Callable
from copy import deepcopy
from uuid import UUID, uuid4

import httpx
import pytest

from app.retrieval import chroma as chroma_module
from app.retrieval.chroma import (
    CHROMA_COMPATIBILITY_ID,
    ChromaDenseRetrievalAdapter,
    DenseProviderError,
)
from app.retrieval.hybrid import dense_rank_map

_COLLECTION_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_FIRST_CHUNK = UUID("11111111-1111-4111-8111-111111111111")
_SECOND_CHUNK = UUID("22222222-2222-4222-8222-222222222222")


class _BytesStream(httpx.AsyncByteStream):
    def __init__(self, body: bytes) -> None:
        self.body = body

    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield self.body

    async def aclose(self) -> None:
        pass


class _TrackingPartsStream(httpx.AsyncByteStream):
    def __init__(self, *parts: bytes) -> None:
        self.parts = parts
        self.consumed: list[bytes] = []

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for part in self.parts:
            self.consumed.append(part)
            yield part

    async def aclose(self) -> None:
        pass


def _depth_fixture(depth: int) -> bytes:
    fixture = b"0"
    for level in range(1, depth + 1):
        fixture = b'{"v":' + fixture + b"}" if level % 2 else b"[" + fixture + b"]"
    return fixture


def _canonical_body(ids: list[object] | None = None) -> dict[str, object]:
    values = ids if ids is not None else [f"chunk:{_FIRST_CHUNK}", f"chunk:{_SECOND_CHUNK}"]
    return {
        "ids": [values],
        "embeddings": None,
        "documents": None,
        "uris": None,
        "data": None,
        "metadatas": None,
        "distances": [[0.125 + index / 10 for index in range(len(values))]],
        "include": ["distances"],
    }


def _adapter(client: httpx.AsyncClient, **overrides: object) -> ChromaDenseRetrievalAdapter:
    options: dict[str, object] = {
        "host": "chroma",
        "http_port": 8000,
        "ssl": False,
        "collection_uuid": _COLLECTION_ID,
        "timeout_seconds": 5.0,
        "client": client,
    }
    options.update(overrides)
    return ChromaDenseRetrievalAdapter(**options)  # type: ignore[arg-type]


async def test_query_uses_exact_read_only_contract_and_caches_version_success() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/v2/version":
            return httpx.Response(200, json="1.5.9")
        return httpx.Response(200, json=_canonical_body())

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    knowledge_base_id = uuid4()
    try:
        first = await adapter.query(
            embedding=(0.25, -0.5, 0.0, 1.0),
            knowledge_base_id=knowledge_base_id,
            candidate_count=40,
        )
        second = await adapter.query(
            embedding=(0.25, -0.5, 0.0, 1.0),
            knowledge_base_id=knowledge_base_id,
            candidate_count=40,
        )

        assert adapter.compatibility_id == CHROMA_COMPATIBILITY_ID
        assert first == second
        assert first.position_count == 2
        assert dense_rank_map(first, configured_count=40) == {
            _FIRST_CHUNK: 1,
            _SECOND_CHUNK: 2,
        }
        assert [request.method for request in requests] == ["GET", "POST", "POST"]
        query_path = (
            "/api/v2/tenants/default_tenant/databases/default_database"
            f"/collections/{_COLLECTION_ID}/query"
        )
        assert requests[1].url.path == query_path
        assert json.loads(requests[1].content) == {
            "query_embeddings": [[0.25, -0.5, 0.0, 1.0]],
            "n_results": 40,
            "where": {"knowledge_base_id": {"$eq": str(knowledge_base_id)}},
            "include": ["distances"],
        }
        assert all(
            not request.url.path.endswith(
                ("/create", "/get_or_create", "/update", "/upsert", "/delete")
            )
            for request in requests
        )
    finally:
        await adapter.close()
        await client.aclose()


async def test_canonical_present_empty_response_is_not_a_provider_failure() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        body: object = "1.5.9" if request.url.path == "/api/v2/version" else _canonical_body([])
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        result = await adapter.query(
            embedding=(1.0,),
            knowledge_base_id=uuid4(),
            candidate_count=4,
        )
        assert result.position_count == 0
        assert result.accepted_count == 0
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda body: body.pop("ids"),
        lambda body: body.update({"unknown": None}),
        lambda body: body.update({"include": []}),
        lambda body: body.update({"embeddings": []}),
        lambda body: body.update({"ids": [[f"chunk:{_FIRST_CHUNK}"]]}),
        lambda body: body.update({"documents": [["ok", 4]]}),
        lambda body: body.update({"metadatas": [[{"nested": {}}, None]]}),
    ],
)
async def test_noncanonical_envelopes_fail_the_whole_provider_response(
    mutation: Callable[[dict[str, object]], object],
) -> None:
    body = deepcopy(_canonical_body())
    mutation(body)

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json="1.5.9" if request.url.path == "/api/v2/version" else body,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        with pytest.raises(DenseProviderError, match="unavailable"):
            await adapter.query(
                embedding=(1.0,),
                knowledge_base_id=uuid4(),
                candidate_count=4,
            )
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize("distance", ["NaN", "Infinity", "-Infinity", "1e400"])
async def test_non_rfc_or_unsupported_range_wire_distance_is_response_fatal(
    distance: str,
) -> None:
    raw = (
        '{"ids":[["chunk:11111111-1111-4111-8111-111111111111"]],'
        '"embeddings":null,"documents":null,"uris":null,"data":null,'
        f'"metadatas":null,"distances":[[{distance}]],"include":["distances"]}}'
    ).encode()

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/version":
            return httpx.Response(200, json="1.5.9")
        return httpx.Response(200, content=raw, headers={"content-type": "application/json"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        with pytest.raises(DenseProviderError):
            await adapter.query(
                embedding=(1.0,),
                knowledge_base_id=uuid4(),
                candidate_count=4,
            )
    finally:
        await adapter.close()
        await client.aclose()


async def test_raw_null_distance_is_candidate_local_without_becoming_typed_none() -> None:
    middle = uuid4()
    body = _canonical_body([f"chunk:{_FIRST_CHUNK}", f"chunk:{middle}", f"chunk:{_SECOND_CHUNK}"])
    body["distances"] = [[0.125, None, 0.325]]

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json="1.5.9" if request.url.path == "/api/v2/version" else body,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        result = await adapter.query(
            embedding=(1.0,),
            knowledge_base_id=uuid4(),
            candidate_count=4,
        )

        assert dense_rank_map(result, configured_count=4) == {
            _FIRST_CHUNK: 1,
            _SECOND_CHUNK: 3,
        }
    finally:
        await adapter.close()
        await client.aclose()


async def test_version_failure_is_not_cached_and_never_reaches_query() -> None:
    calls: list[str] = []
    versions = iter(("wrong", "1.5.9"))

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/api/v2/version":
            return httpx.Response(200, json=next(versions))
        return httpx.Response(200, json=_canonical_body([]))

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        with pytest.raises(DenseProviderError):
            await adapter.query(
                embedding=(1.0,),
                knowledge_base_id=uuid4(),
                candidate_count=4,
            )
        result = await adapter.query(
            embedding=(1.0,),
            knowledge_base_id=uuid4(),
            candidate_count=4,
        )
        assert result.accepted_count == 0
        assert calls.count("/api/v2/version") == 2
        assert sum(path.endswith("/query") for path in calls) == 1
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize(
    ("wire_bytes", "succeeds"),
    [(1_048_576, True), (1_048_577, False)],
)
async def test_query_wire_ceiling_is_inclusive(wire_bytes: int, succeeds: bool) -> None:
    base = json.dumps(_canonical_body([]), separators=(",", ":")).encode()
    body = base + b" " * (wire_bytes - len(base))

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/version":
            return httpx.Response(200, json="1.5.9")
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            stream=_BytesStream(body),
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        operation = adapter.query(
            embedding=(1.0,),
            knowledge_base_id=uuid4(),
            candidate_count=4,
        )
        if succeeds:
            assert (await operation).accepted_count == 0
        else:
            with pytest.raises(DenseProviderError):
                await operation
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize(
    ("decoded_bytes", "succeeds"),
    [(2_097_152, True), (2_097_153, False)],
)
async def test_query_decoded_gzip_ceiling_is_inclusive(
    decoded_bytes: int,
    succeeds: bool,
) -> None:
    base = json.dumps(_canonical_body([]), separators=(",", ":")).encode()
    decoded = base + b" " * (decoded_bytes - len(base))
    body = gzip.compress(decoded)
    assert len(body) < 1_048_576

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v2/version":
            return httpx.Response(200, json="1.5.9")
        return httpx.Response(
            200,
            headers={
                "content-type": "application/json",
                "content-encoding": "gzip",
                "content-length": str(len(body)),
            },
            stream=_BytesStream(body),
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        operation = adapter.query(
            embedding=(1.0,),
            knowledge_base_id=uuid4(),
            candidate_count=4,
        )
        if succeeds:
            assert (await operation).accepted_count == 0
        else:
            with pytest.raises(DenseProviderError):
                await operation
    finally:
        await adapter.close()
        await client.aclose()


async def test_query_gzip_bomb_uses_first_plus_one_bounded_decompression(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoded_limit = 1_024
    body = gzip.compress(b"{" + b" " * decoded_limit)
    real_factory = chroma_module.zlib.decompressobj
    requested_output_limits: list[int] = []

    class TrackingDecompressor:
        def __init__(self) -> None:
            self._inner = real_factory(16 + chroma_module.zlib.MAX_WBITS)

        @property
        def unconsumed_tail(self) -> bytes:
            return self._inner.unconsumed_tail

        @property
        def eof(self) -> bool:
            return self._inner.eof

        @property
        def unused_data(self) -> bytes:
            return self._inner.unused_data

        def decompress(self, data: bytes, max_length: int) -> bytes:
            requested_output_limits.append(max_length)
            return self._inner.decompress(data, max_length)

        def flush(self, length: int) -> bytes:
            requested_output_limits.append(length)
            return self._inner.flush(length)

    monkeypatch.setattr(chroma_module, "MAX_PROVIDER_DECODED_BYTES", decoded_limit)
    monkeypatch.setattr(
        chroma_module.zlib,
        "decompressobj",
        lambda *args, **kwargs: TrackingDecompressor(),
    )
    response = httpx.Response(
        200,
        headers={"content-type": "application/json", "content-encoding": "gzip"},
        stream=_BytesStream(body),
    )

    with pytest.raises(DenseProviderError):
        await chroma_module._bounded_json_body(response)
    assert requested_output_limits
    assert max(requested_output_limits) <= decoded_limit + 1


async def test_provider_total_deadline_includes_query_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query_validation_completed = False
    original_typed_result = chroma_module._typed_result

    def typed_result(body: object, *, configured_count: int) -> object:
        nonlocal query_validation_completed
        result = original_typed_result(body, configured_count=configured_count)
        query_validation_completed = True
        return result

    monkeypatch.setattr(chroma_module, "_typed_result", typed_result)
    monkeypatch.setattr(
        chroma_module,
        "_deadline_expired",
        lambda deadline: query_validation_completed,
    )

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json="1.5.9" if request.url.path == "/api/v2/version" else _canonical_body([]),
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        with pytest.raises(DenseProviderError):
            await adapter.query(
                embedding=(1.0,),
                knowledge_base_id=uuid4(),
                candidate_count=4,
            )
        assert query_validation_completed
    finally:
        await adapter.close()
        await client.aclose()


async def test_provider_total_deadline_includes_version_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validation_checks = 0

    def expired(deadline: float) -> bool:
        nonlocal validation_checks
        validation_checks += 1
        return True

    monkeypatch.setattr(chroma_module, "_deadline_expired", expired)
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json="1.5.9"))
    )
    adapter = _adapter(client)
    try:
        with pytest.raises(DenseProviderError):
            await adapter.query(
                embedding=(1.0,),
                knowledge_base_id=uuid4(),
                candidate_count=4,
            )
        assert validation_checks == 1
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize(
    ("field", "size", "succeeds"),
    [
        ("document", 4_096, True),
        ("document", 4_097, False),
        ("metadata-value", 1_024, True),
        ("metadata-value", 1_025, False),
    ],
)
async def test_unsolicited_provider_fields_are_bounded_and_ignored(
    field: str,
    size: int,
    succeeds: bool,
) -> None:
    body = _canonical_body([f"chunk:{_FIRST_CHUNK}"])
    if field == "document":
        body["documents"] = [["x" * size]]
    else:
        body["metadatas"] = [[{"hint": "x" * size}]]

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json="1.5.9" if request.url.path == "/api/v2/version" else body,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        operation = adapter.query(
            embedding=(1.0,),
            knowledge_base_id=uuid4(),
            candidate_count=4,
        )
        if succeeds:
            result = await operation
            assert dense_rank_map(result, configured_count=4) == {_FIRST_CHUNK: 1}
        else:
            with pytest.raises(DenseProviderError):
                await operation
    finally:
        await adapter.close()
        await client.aclose()


async def test_concurrent_first_queries_share_one_version_probe() -> None:
    probe_started = asyncio.Event()
    release_probe = asyncio.Event()
    requests: list[str] = []

    async def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request.url.path)
        if request.url.path == "/api/v2/version":
            probe_started.set()
            await release_probe.wait()
            return httpx.Response(200, json="1.5.9")
        return httpx.Response(200, json=_canonical_body([]))

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        tasks = tuple(
            asyncio.create_task(
                adapter.query(
                    embedding=(1.0,),
                    knowledge_base_id=uuid4(),
                    candidate_count=4,
                )
            )
            for _ in range(2)
        )
        await probe_started.wait()
        release_probe.set()
        results = await asyncio.gather(*tasks)

        assert all(result.accepted_count == 0 for result in results)
        assert requests.count("/api/v2/version") == 1
        assert sum(path.endswith("/query") for path in requests) == 2
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize(
    "body",
    [
        b"\xef\xbb\xbf{}",
        b"\xff",
        b'{"duplicate":1,"duplicate":2}',
        b'{"unterminated":"value}',
        ("[" * 17 + "0" + "]" * 17).encode(),
    ],
)
def test_strict_json_rejects_bom_encoding_duplicate_depth_and_shape(body: bytes) -> None:
    with pytest.raises(DenseProviderError):
        chroma_module._strict_json(body)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"content-type": "text/plain"},
        {"content-type": "application/json; profile=x"},
        {"content-type": "application/json; charset=latin-1"},
        {"content-type": "application/json", "content-encoding": "br"},
        {"content-type": "application/json", "content-encoding": "gzip, identity"},
        {"content-type": "application/json", "content-length": "invalid"},
        {"content-type": "application/json", "content-length": "1048577"},
    ],
)
async def test_provider_headers_fail_closed(headers: dict[str, str]) -> None:
    response = httpx.Response(200, headers=headers, stream=_BytesStream(b"{}"))
    with pytest.raises(DenseProviderError):
        await chroma_module._bounded_json_body(response)


async def test_invalid_gzip_fails_before_json_materialization() -> None:
    response = httpx.Response(
        200,
        headers={"content-type": "application/json", "content-encoding": "gzip"},
        stream=_BytesStream(b"not-gzip"),
    )
    with pytest.raises(DenseProviderError):
        await chroma_module._bounded_json_body(response)


async def test_streaming_depth_accepts_d16_for_ordinary_json_parsing() -> None:
    response = httpx.Response(
        200,
        headers={"content-type": "application/json"},
        stream=_TrackingPartsStream(_depth_fixture(16)),
    )

    assert await chroma_module._bounded_json_body(response) is not None


async def test_streaming_depth_rejects_d17_without_consuming_later_chunk() -> None:
    fixture = _depth_fixture(17)
    scalar_offset = fixture.index(b"0")
    late_sentinel = b"late-stream-chunk-must-not-be-consumed"
    stream = _TrackingPartsStream(fixture[:scalar_offset], late_sentinel)
    response = httpx.Response(
        200,
        headers={"content-type": "application/json"},
        stream=stream,
    )

    with pytest.raises(DenseProviderError):
        await chroma_module._bounded_json_body(response)

    assert stream.consumed == [fixture[:scalar_offset]]
    assert late_sentinel not in stream.consumed


async def test_streaming_depth_preserves_string_escape_and_utf8_state_across_chunks() -> None:
    stream = _TrackingPartsStream(
        b'{"value":"prefix' + b"\\",
        b'"[{}] ' + b"\xc3",
        b"\xa9" + b' suffix"}',
    )
    response = httpx.Response(
        200,
        headers={"content-type": "application/json"},
        stream=stream,
    )

    assert await chroma_module._bounded_json_body(response) == {
        "value": 'prefix"[{}] \N{LATIN SMALL LETTER E WITH ACUTE} suffix'
    }
    assert stream.consumed == list(stream.parts)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda body: body.update({"documents": [[]]}),
        lambda body: body.update({"metadatas": [[]]}),
        lambda body: body.update({"metadatas": [[{f"k{i}": True for i in range(33)}]]}),
        lambda body: body.update({"metadatas": [[{"k" * 129: True}]]}),
        lambda body: body.update({"metadatas": [[{"null": None}]]}),
        lambda body: body.update({"ids": [["x" * 129]]}),
        lambda body: body.update({"ids": [[f"chunk:{_FIRST_CHUNK}"] * 5], "distances": [[0] * 5]}),
    ],
)
async def test_additional_field_count_and_cardinality_failures_are_response_fatal(
    mutation: Callable[[dict[str, object]], object],
) -> None:
    body = _canonical_body([f"chunk:{_FIRST_CHUNK}"])
    mutation(body)

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json="1.5.9" if request.url.path == "/api/v2/version" else body,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        with pytest.raises(DenseProviderError):
            await adapter.query(
                embedding=(1.0,),
                knowledge_base_id=uuid4(),
                candidate_count=4,
            )
    finally:
        await adapter.close()
        await client.aclose()


async def test_scalar_metadata_variants_are_valid_but_never_returned() -> None:
    body = _canonical_body([f"chunk:{_FIRST_CHUNK}"])
    body["metadatas"] = [[{"string": "hint", "number": 1.25, "boolean": True}]]
    body["documents"] = [[None]]

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json="1.5.9" if request.url.path == "/api/v2/version" else body,
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        result = await adapter.query(
            embedding=(1.0,),
            knowledge_base_id=uuid4(),
            candidate_count=4,
        )
        assert result.position_count == 1
        assert not hasattr(result, "metadata")
        assert not hasattr(result, "document")
        assert not hasattr(result, "candidates")
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize(
    "embedding",
    [(), (1,), (float("nan"),), (float("inf"),)],
)
async def test_query_rejects_invalid_embedding_before_transport(
    embedding: tuple[object, ...],
) -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(500)))
    adapter = _adapter(client)
    try:
        with pytest.raises(ValueError, match="embedding"):
            await adapter.query(
                embedding=embedding,  # type: ignore[arg-type]
                knowledge_base_id=uuid4(),
                candidate_count=4,
            )
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize("candidate_count", [0, 129])
async def test_query_rejects_invalid_candidate_count_before_transport(candidate_count: int) -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(500)))
    adapter = _adapter(client)
    try:
        with pytest.raises(ValueError, match="candidate count"):
            await adapter.query(
                embedding=(1.0,),
                knowledge_base_id=uuid4(),
                candidate_count=candidate_count,
            )
    finally:
        await adapter.close()
        await client.aclose()


@pytest.mark.parametrize(
    "failure",
    [httpx.Response(503), httpx.ConnectError("private failure")],
)
async def test_transport_failures_are_normalized(failure: object) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if isinstance(failure, Exception):
            raise failure
        return failure  # type: ignore[return-value]

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    adapter = _adapter(client)
    try:
        with pytest.raises(DenseProviderError, match="unavailable"):
            await adapter.query(
                embedding=(1.0,),
                knowledge_base_id=uuid4(),
                candidate_count=4,
            )
    finally:
        await adapter.close()
        await client.aclose()


async def test_owned_client_context_manager_closes_and_rejects_later_use() -> None:
    adapter = ChromaDenseRetrievalAdapter(
        host="chroma",
        http_port=8000,
        ssl=True,
        collection_uuid=_COLLECTION_ID,
        timeout_seconds=0.01,
    )
    async with adapter as entered:
        assert entered is adapter
    await adapter.close()
    with pytest.raises(DenseProviderError):
        await adapter.query(
            embedding=(1.0,),
            knowledge_base_id=uuid4(),
            candidate_count=4,
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"host": "http://chroma"}, "host"),
        ({"http_port": 0}, "port"),
        ({"collection_uuid": "not-a-uuid"}, "UUID"),
        ({"timeout_seconds": 0}, "timeout"),
        ({"timeout_seconds": 601}, "timeout"),
    ],
)
async def test_adapter_rejects_untrusted_or_unbounded_configuration(
    overrides: dict[str, object],
    message: str,
) -> None:
    client = httpx.AsyncClient()
    try:
        with pytest.raises(ValueError, match=message):
            _adapter(client, **overrides)
    finally:
        await client.aclose()
