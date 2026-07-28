"""Deterministic, network-free tests for the AF-2B embedding boundary."""

import json
import math
from collections.abc import Callable

import httpx
import pytest

from app.ingestion.embeddings import (
    DeterministicEmbeddingModel,
    EmbeddingInputError,
    EmbeddingRequestError,
    EmbeddingResponseError,
    OllamaEmbeddingModel,
    validate_embedding_batch,
)


def _ollama_model(
    client: httpx.AsyncClient,
    *,
    dimension: int = 3,
    batch_size: int = 2,
) -> OllamaEmbeddingModel:
    return OllamaEmbeddingModel(
        base_url="http://ollama:11434",
        model_id="embed-model",
        dimension=dimension,
        batch_size=batch_size,
        timeout_seconds=0.25,
        client=client,
    )


async def test_deterministic_embedding_fake_is_stable_and_model_scoped() -> None:
    model = DeterministicEmbeddingModel(model_id="fake-v1", dimension=5, batch_size=1)
    other_model = DeterministicEmbeddingModel(model_id="fake-v2", dimension=5)

    first = await model.embed(["same text", "other text"])
    second = await model.embed(["same text", "other text"])
    other = await other_model.embed(["same text"])

    assert first == second
    assert first[0] != first[1]
    assert first[0] != other[0]
    assert all(len(vector) == 5 for vector in first)
    assert all(math.isfinite(value) for vector in first for value in vector)
    assert model.model_id == "fake-v1"
    assert model.dimension == 5
    assert await model.embed([]) == []
    await model.close()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"model_id": " ", "dimension": 3, "batch_size": 1}, "identity"),
        ({"model_id": "model", "dimension": 0, "batch_size": 1}, "dimension"),
        ({"model_id": "model", "dimension": 3, "batch_size": 0}, "batch size"),
    ],
)
def test_deterministic_embedding_fake_rejects_invalid_configuration(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(EmbeddingInputError, match=message):
        DeterministicEmbeddingModel(**kwargs)


async def test_embedding_fake_rejects_blank_input() -> None:
    model = DeterministicEmbeddingModel()

    with pytest.raises(EmbeddingInputError, match="index 1"):
        await model.embed(["valid", " \n "])


@pytest.mark.parametrize(
    ("vectors", "dimension", "message"),
    [
        ("not-vectors", 2, "vector list"),
        ([[1.0, 2.0]], 2, "count"),
        ([[1.0], [2.0, 3.0]], 2, "dimension"),
        ([[1.0, "bad"], [2.0, 3.0]], 2, "non-numeric"),
        ([[1.0, float("nan")], [2.0, 3.0]], 2, "non-finite"),
        ([[1.0, True], [2.0, 3.0]], 2, "non-numeric"),
    ],
)
def test_embedding_batch_validation_rejects_malformed_vectors(
    vectors: object,
    dimension: int,
    message: str,
) -> None:
    with pytest.raises(EmbeddingResponseError, match=message):
        validate_embedding_batch(["first", "second"], vectors, dimension=dimension)


def test_embedding_batch_validation_rejects_invalid_expected_dimension() -> None:
    with pytest.raises(EmbeddingInputError, match="positive"):
        validate_embedding_batch([], [], dimension=0)


async def test_ollama_adapter_batches_requests_and_preserves_order() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = json.loads(request.content)
        inputs = payload["input"]
        embeddings = [
            [float(len(text)), float(index), float(len(text) + index)]
            for index, text in enumerate(inputs)
        ]
        return httpx.Response(
            200,
            json={"model": payload["model"], "embeddings": embeddings},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    model = _ollama_model(client)
    try:
        result = await model.embed(["one", "three", "seventeen"])
        await model.close()

        assert result == [
            (3.0, 0.0, 3.0),
            (5.0, 1.0, 6.0),
            (9.0, 0.0, 9.0),
        ]
        assert len(requests) == 2
        assert [json.loads(request.content)["input"] for request in requests] == [
            ["one", "three"],
            ["seventeen"],
        ]
        assert all(json.loads(request.content)["truncate"] is False for request in requests)
        assert all(request.url.path == "/api/embed" for request in requests)
        assert all(request.extensions["timeout"]["read"] == 0.25 for request in requests)
        assert not client.is_closed
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    ("response_factory", "message"),
    [
        (
            lambda request: httpx.Response(200, json=[]),
            "must be an object",
        ),
        (
            lambda request: httpx.Response(
                200,
                json={"model": "wrong-model", "embeddings": [[1.0, 2.0, 3.0]]},
            ),
            "model does not match",
        ),
        (
            lambda request: httpx.Response(
                200,
                json={"model": "embed-model", "embeddings": [[1.0, 2.0]]},
            ),
            "dimension",
        ),
        (
            lambda request: httpx.Response(
                200,
                json={"model": "embed-model", "embeddings": []},
            ),
            "count",
        ),
    ],
)
async def test_ollama_adapter_rejects_malformed_responses(
    response_factory: Callable[[httpx.Request], httpx.Response],
    message: str,
) -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(response_factory))
    model = _ollama_model(client)
    try:
        with pytest.raises(EmbeddingResponseError, match=message):
            await model.embed(["text"])
    finally:
        await client.aclose()


async def test_ollama_adapter_rejects_non_json_response() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b"not json"))
    client = httpx.AsyncClient(transport=transport)
    model = _ollama_model(client)
    try:
        with pytest.raises(EmbeddingResponseError, match="malformed JSON"):
            await model.embed(["text"])
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (httpx.Response(503), "HTTP 503"),
        (httpx.ReadTimeout("synthetic timeout"), "timed out"),
        (httpx.ConnectError("synthetic connection failure"), "request failed"),
    ],
)
async def test_ollama_adapter_normalizes_request_failures(
    response: httpx.Response | httpx.HTTPError,
    message: str,
) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        if isinstance(response, httpx.HTTPError):
            raise response
        return response

    client = httpx.AsyncClient(transport=httpx.MockTransport(fail))
    model = _ollama_model(client)
    try:
        with pytest.raises(EmbeddingRequestError, match=message):
            await model.embed(["text"])
    finally:
        await client.aclose()


async def test_closed_ollama_adapter_rejects_embedding() -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(500)))
    model = _ollama_model(client)
    try:
        await model.close()
        await model.close()

        with pytest.raises(EmbeddingRequestError, match="closed"):
            await model.embed(["text"])
    finally:
        await client.aclose()


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"base_url": "ollama:11434"}, "absolute"),
        ({"model_id": " "}, "identity"),
        ({"dimension": 0}, "dimension"),
        ({"batch_size": 0}, "batch size"),
        ({"timeout_seconds": 0}, "timeout"),
    ],
)
def test_ollama_adapter_rejects_invalid_configuration(
    overrides: dict[str, object],
    message: str,
) -> None:
    options: dict[str, object] = {
        "base_url": "http://ollama:11434",
        "model_id": "embed-model",
        "dimension": 3,
        "batch_size": 2,
        "timeout_seconds": 1.0,
    }
    options.update(overrides)

    with pytest.raises(EmbeddingInputError, match=message):
        OllamaEmbeddingModel(**options)
