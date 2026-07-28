"""Deterministic, network-free tests for the AF-2B vector-store boundary."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import replace
from uuid import UUID, uuid4, uuid5

import httpx
import pytest

from app.ingestion.vector_store import (
    ChromaVectorStore,
    InMemoryVectorStore,
    VectorRecord,
    VectorStoreConfigurationError,
    VectorStoreInputError,
    VectorStoreNotInitializedError,
    VectorStoreRequestError,
    VectorStoreResponseError,
    stable_vector_id,
)

_NAMESPACE = UUID("74d4295f-4931-4653-8480-1b0ad8101a23")


def _record(
    name: str,
    *,
    knowledge_base_id: UUID | None = None,
    document_id: UUID | None = None,
    chunk_index: int = 0,
    dimension: int = 3,
) -> VectorRecord:
    resolved_document_id = document_id or uuid5(_NAMESPACE, f"document:{name}")
    chunk_id = uuid5(resolved_document_id, f"{chunk_index}:{name}")
    text = f"Normalized {name}"
    return VectorRecord(
        vector_id=stable_vector_id(chunk_id),
        embedding=tuple(float(index + len(name)) for index in range(dimension)),
        knowledge_base_id=knowledge_base_id or uuid5(_NAMESPACE, "knowledge-base"),
        document_id=resolved_document_id,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        normalized_text=text,
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )


def _chroma_store(
    client: httpx.AsyncClient,
    *,
    batch_size: int = 2,
) -> ChromaVectorStore:
    return ChromaVectorStore(
        host="chroma",
        http_port=8000,
        ssl=False,
        collection_name="agentforge_chunks",
        batch_size=batch_size,
        timeout_seconds=0.5,
        client=client,
    )


def _collection_response(
    *,
    collection_id: str = "4f145893-c6bf-4768-9900-8cd933bcc94d",
    name: str = "agentforge_chunks",
    metadata: object | None = None,
    dimension: int | None = None,
) -> dict[str, object]:
    return {
        "id": collection_id,
        "name": name,
        "metadata": metadata
        if metadata is not None
        else {
            "embedding_model": "embed-model",
            "embedding_dimension": 3,
            "source_of_truth": "postgresql",
        },
        "dimension": dimension,
    }


def test_vector_record_uses_stable_chunk_identity() -> None:
    record = _record("first")

    assert record.vector_id == f"chunk:{record.chunk_id}"
    assert stable_vector_id(record.chunk_id) == record.vector_id


@pytest.mark.parametrize(
    ("update", "message"),
    [
        ({"vector_id": "random"}, "durable chunk"),
        ({"chunk_index": -1}, "non-negative"),
        ({"normalized_text": " \n "}, "must not be empty"),
        ({"content_hash": "A" * 64}, "lowercase SHA-256"),
        ({"content_hash": "short"}, "lowercase SHA-256"),
        ({"embedding": ()}, "must not be empty"),
        ({"embedding": (1.0, float("inf"), 3.0)}, "finite"),
    ],
)
def test_vector_record_rejects_invalid_values(
    update: dict[str, object],
    message: str,
) -> None:
    values: dict[str, object] = {
        "vector_id": stable_vector_id(uuid5(_NAMESPACE, "chunk")),
        "embedding": (1.0, 2.0, 3.0),
        "knowledge_base_id": uuid4(),
        "document_id": uuid4(),
        "chunk_id": uuid5(_NAMESPACE, "chunk"),
        "chunk_index": 0,
        "normalized_text": "text",
        "content_hash": hashlib.sha256(b"text").hexdigest(),
    }
    values.update(update)

    with pytest.raises(VectorStoreInputError, match=message):
        VectorRecord(**values)


async def test_in_memory_store_upsert_is_idempotent_and_ordered() -> None:
    store = InMemoryVectorStore()
    later = _record("later", chunk_index=1)
    earlier = _record("earlier", document_id=later.document_id)

    await store.initialize(model_id="embed-model", dimension=3)
    await store.initialize(model_id="embed-model", dimension=3)
    await store.upsert([later, earlier])
    await store.upsert([later])

    assert len(store.records) == 2
    assert store.records == tuple(sorted((later, earlier), key=lambda item: item.vector_id))
    replacement = replace(later, embedding=(9.0, 8.0, 7.0))
    await store.upsert([replacement])
    assert replacement in store.records
    assert later not in store.records
    await store.close()


async def test_in_memory_store_deletes_only_requested_document_and_chunks() -> None:
    store = InMemoryVectorStore()
    first_document = uuid4()
    second_document = uuid4()
    first = _record("first", document_id=first_document)
    second = _record("second", document_id=first_document, chunk_index=1)
    unrelated = _record("unrelated", document_id=second_document)
    await store.initialize(model_id="embed-model", dimension=3)
    await store.upsert([first, second, unrelated])

    await store.delete_by_chunk_ids([first.chunk_id, uuid4()])
    assert store.records == tuple(sorted((second, unrelated), key=lambda item: item.vector_id))

    await store.delete_by_document(first_document)
    assert store.records == (unrelated,)

    await store.delete_by_document(first_document)
    await store.delete_by_chunk_ids([])
    assert store.records == (unrelated,)


async def test_in_memory_store_requires_compatible_initialization() -> None:
    store = InMemoryVectorStore()
    record = _record("first")

    with pytest.raises(VectorStoreNotInitializedError):
        await store.upsert([record])
    with pytest.raises(VectorStoreNotInitializedError):
        await store.delete_by_document(record.document_id)
    with pytest.raises(VectorStoreNotInitializedError):
        await store.delete_by_chunk_ids([record.chunk_id])

    await store.initialize(model_id="embed-model", dimension=3)
    with pytest.raises(VectorStoreConfigurationError):
        await store.initialize(model_id="other-model", dimension=3)
    with pytest.raises(VectorStoreConfigurationError):
        await store.initialize(model_id="embed-model", dimension=4)


async def test_vector_store_rejects_wrong_dimensions_and_duplicate_batch_ids() -> None:
    store = InMemoryVectorStore()
    record = _record("first")
    await store.initialize(model_id="embed-model", dimension=3)

    with pytest.raises(VectorStoreInputError, match="dimension"):
        await store.upsert([_record("wide", dimension=4)])
    with pytest.raises(VectorStoreInputError, match="duplicate ID"):
        await store.upsert([record, record])


@pytest.mark.parametrize(
    ("model_id", "dimension", "message"),
    [
        (" ", 3, "identity"),
        ("model", 0, "positive"),
    ],
)
async def test_vector_store_rejects_invalid_initialization(
    model_id: str,
    dimension: int,
    message: str,
) -> None:
    with pytest.raises(VectorStoreInputError, match=message):
        await InMemoryVectorStore().initialize(model_id=model_id, dimension=dimension)


async def test_chroma_adapter_uses_v2_idempotent_upsert_and_scoped_deletes() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/collections"):
            return httpx.Response(200, json=_collection_response())
        if request.url.path.endswith("/delete"):
            return httpx.Response(200, json={"deleted": 1})
        return httpx.Response(200, json={})

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    store = _chroma_store(client)
    document_id = uuid4()
    records = [
        _record(f"chunk-{index}", document_id=document_id, chunk_index=index) for index in range(3)
    ]
    try:
        await store.initialize(model_id="embed-model", dimension=3)
        await store.initialize(model_id="embed-model", dimension=3)
        await store.upsert(records)
        await store.upsert([])
        await store.delete_by_document(document_id)
        await store.delete_by_chunk_ids([record.chunk_id for record in records])
        await store.delete_by_chunk_ids([])
        await store.close()

        assert not client.is_closed
        assert requests[0].url.path == (
            "/api/v2/tenants/default_tenant/databases/default_database/collections"
        )
        create_payload = json.loads(requests[0].content)
        assert create_payload == {
            "name": "agentforge_chunks",
            "get_or_create": True,
            "metadata": {
                "embedding_model": "embed-model",
                "embedding_dimension": 3,
                "source_of_truth": "postgresql",
            },
        }
        upserts = [request for request in requests if request.url.path.endswith("/upsert")]
        assert len(upserts) == 2
        assert [json.loads(request.content)["ids"] for request in upserts] == [
            [records[0].vector_id, records[1].vector_id],
            [records[2].vector_id],
        ]
        assert json.loads(upserts[0].content)["documents"] == [
            records[0].normalized_text,
            records[1].normalized_text,
        ]
        assert json.loads(upserts[0].content)["metadatas"][0] == {
            "knowledge_base_id": str(records[0].knowledge_base_id),
            "document_id": str(document_id),
            "chunk_id": str(records[0].chunk_id),
            "chunk_index": 0,
            "content_hash": records[0].content_hash,
        }
        deletes = [
            json.loads(request.content)
            for request in requests
            if request.url.path.endswith("/delete")
        ]
        assert deletes == [
            {"where": {"document_id": {"$eq": str(document_id)}}},
            {"ids": [records[0].vector_id, records[1].vector_id]},
            {"ids": [records[2].vector_id]},
        ]
        assert all(request.url.scheme == "http" for request in requests)
        assert all(request.url.host == "chroma" for request in requests)
        assert all(request.extensions["timeout"]["read"] == 0.5 for request in requests)
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    ("body", "error_type", "message"),
    [
        ([], VectorStoreResponseError, "must be an object"),
        (
            _collection_response(collection_id="not-a-uuid"),
            VectorStoreResponseError,
            "valid ID",
        ),
        (
            {key: value for key, value in _collection_response().items() if key != "id"},
            VectorStoreResponseError,
            "valid ID",
        ),
        (
            _collection_response(name="other"),
            VectorStoreResponseError,
            "name does not match",
        ),
        (
            _collection_response(metadata={"embedding_model": "wrong"}),
            VectorStoreConfigurationError,
            "metadata does not match",
        ),
        (
            _collection_response(dimension=4),
            VectorStoreConfigurationError,
            "dimension does not match",
        ),
    ],
)
async def test_chroma_adapter_rejects_incompatible_collection_response(
    body: object,
    error_type: type[Exception],
    message: str,
) -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )
    store = _chroma_store(client)
    try:
        with pytest.raises(error_type, match=message):
            await store.initialize(model_id="embed-model", dimension=3)
    finally:
        await client.aclose()


async def test_chroma_adapter_rejects_malformed_json() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b"not json"))
    )
    store = _chroma_store(client)
    try:
        with pytest.raises(VectorStoreResponseError, match="malformed JSON"):
            await store.initialize(model_id="embed-model", dimension=3)
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    ("response_factory", "message"),
    [
        (lambda request: httpx.Response(503), "HTTP 503"),
        (
            lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("timeout")),
            "timed out",
        ),
        (
            lambda request: (_ for _ in ()).throw(httpx.ConnectError("failure")),
            "request failed",
        ),
    ],
)
async def test_chroma_adapter_normalizes_request_failures(
    response_factory: Callable[[httpx.Request], httpx.Response],
    message: str,
) -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(response_factory))
    store = _chroma_store(client)
    try:
        with pytest.raises(VectorStoreRequestError, match=message):
            await store.initialize(model_id="embed-model", dimension=3)
    finally:
        await client.aclose()


async def test_chroma_adapter_requires_initialization_and_rejects_reconfiguration() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=_collection_response())
        )
    )
    store = _chroma_store(client)
    record = _record("first")
    try:
        with pytest.raises(VectorStoreNotInitializedError):
            await store.upsert([record])

        await store.initialize(model_id="embed-model", dimension=3)
        with pytest.raises(VectorStoreConfigurationError):
            await store.initialize(model_id="other-model", dimension=3)
    finally:
        await client.aclose()


async def test_closed_chroma_adapter_rejects_requests() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=_collection_response())
        )
    )
    store = _chroma_store(client)
    try:
        await store.close()
        await store.close()

        with pytest.raises(VectorStoreRequestError, match="closed"):
            await store.initialize(model_id="embed-model", dimension=3)
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"host": "http://chroma"}, "without a URL scheme"),
        ({"host": "bad/host"}, "hostname"),
        ({"host": "bad host"}, "hostname"),
        ({"http_port": 0}, "between 1 and 65535"),
        ({"collection_name": "ab"}, "3-512"),
        ({"collection_name": "a" * 513}, "3-512"),
        ({"collection_name": "Uppercase"}, "3-512"),
        ({"collection_name": "-invalid"}, "start and end"),
        ({"collection_name": "invalid-"}, "start and end"),
        ({"collection_name": "bad name"}, "3-512"),
        ({"batch_size": 0}, "batch size"),
        ({"timeout_seconds": 0}, "timeout"),
        ({"tenant": " "}, "tenant and database"),
        ({"database": " "}, "tenant and database"),
    ],
)
def test_chroma_adapter_rejects_invalid_configuration(
    overrides: dict[str, object],
    message: str,
) -> None:
    options: dict[str, object] = {
        "host": "chroma",
        "http_port": 8000,
        "ssl": False,
        "collection_name": "agentforge_chunks",
    }
    options.update(overrides)

    with pytest.raises(VectorStoreInputError, match=message):
        ChromaVectorStore(**options)
