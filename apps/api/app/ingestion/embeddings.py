"""Embedding boundary, deterministic test adapter, and Ollama implementation."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import zlib
from collections.abc import AsyncIterator, Sequence
from typing import Protocol, cast

import httpx

type EmbeddingVector = tuple[float, ...]

MAX_EMBEDDING_WIRE_BYTES = 2_097_152
MAX_EMBEDDING_DECODED_BYTES = 2_097_152


def _deadline_expired(deadline: float) -> bool:
    return asyncio.get_running_loop().time() >= deadline


class EmbeddingError(Exception):
    """Base class for explicit embedding failures."""


class EmbeddingInputError(EmbeddingError):
    """Embedding input or configuration is invalid."""


class EmbeddingRequestError(EmbeddingError):
    """The configured embedding provider could not complete a request."""


class EmbeddingResponseError(EmbeddingError):
    """The embedding provider returned an invalid response."""


class EmbeddingModel(Protocol):
    """Provider-independent batch embedding behavior."""

    @property
    def model_id(self) -> str:
        """Return the explicit provider model identity."""
        ...

    @property
    def dimension(self) -> int:
        """Return the exact number of values in every embedding."""
        ...

    async def embed(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        """Embed text in bounded provider batches while preserving order."""
        ...

    async def close(self) -> None:
        """Release resources owned by the adapter."""
        ...


def _validate_texts(texts: Sequence[str]) -> list[str]:
    validated = list(texts)
    for index, text in enumerate(validated):
        if not text.strip():
            raise EmbeddingInputError(f"Embedding input at index {index} is empty.")
    return validated


def validate_embedding_batch(
    texts: Sequence[str],
    vectors: object,
    *,
    dimension: int,
) -> list[EmbeddingVector]:
    """Validate provider output without truncating, padding, or accepting NaN values."""
    if dimension <= 0:
        raise EmbeddingInputError("Embedding dimension must be positive.")
    if not isinstance(vectors, (list, tuple)):
        raise EmbeddingResponseError("Embedding response must contain a vector list.")
    if len(vectors) != len(texts):
        raise EmbeddingResponseError(
            f"Embedding response count {len(vectors)} does not match input count {len(texts)}."
        )

    validated: list[EmbeddingVector] = []
    for vector_index, raw_vector in enumerate(vectors):
        if not isinstance(raw_vector, (list, tuple)):
            raise EmbeddingResponseError(
                f"Embedding at index {vector_index} is not a numeric vector."
            )
        if len(raw_vector) != dimension:
            raise EmbeddingResponseError(
                f"Embedding at index {vector_index} has dimension {len(raw_vector)}; "
                f"expected {dimension}."
            )

        vector: list[float] = []
        for value in raw_vector:
            if type(value) is not float:
                raise EmbeddingResponseError(
                    f"Embedding at index {vector_index} contains a non-numeric value."
                )
            if not math.isfinite(value):
                raise EmbeddingResponseError(
                    f"Embedding at index {vector_index} contains a non-finite value."
                )
            vector.append(value)
        validated.append(tuple(vector))
    return validated


def _embedding_content_encoding(response: httpx.Response) -> str:
    raw = response.headers.get("content-encoding")
    if raw is None or not raw.strip():
        return "identity"
    encoding = raw.strip().lower()
    if "," in encoding or encoding not in {"identity", "gzip"}:
        raise EmbeddingResponseError("Ollama returned an unsupported content encoding.")
    return cast(str, encoding)


async def _embedding_raw_parts(response: httpx.Response) -> AsyncIterator[bytes]:
    if response.is_stream_consumed:
        yield response.content
        return
    async for raw_part in response.aiter_raw():
        yield raw_part


async def _bounded_embedding_json(response: httpx.Response) -> object:
    declared_length = response.headers.get("content-length")
    if declared_length is not None:
        try:
            parsed_length = int(declared_length, 10)
        except ValueError:
            raise EmbeddingResponseError("Ollama returned an invalid content length.") from None
        if parsed_length < 0 or parsed_length > MAX_EMBEDDING_WIRE_BYTES:
            raise EmbeddingResponseError("Ollama embedding response exceeded its byte limit.")

    encoding = _embedding_content_encoding(response)
    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS) if encoding == "gzip" else None
    wire_count = 0
    decoded_count = 0
    decoded_parts: list[bytes] = []
    try:
        async for raw_part in _embedding_raw_parts(response):
            wire_count += len(raw_part)
            if wire_count > MAX_EMBEDDING_WIRE_BYTES:
                raise EmbeddingResponseError("Ollama embedding response exceeded its byte limit.")
            if decompressor is None:
                decoded_part = raw_part
                decoded_count += len(decoded_part)
                if decoded_count > MAX_EMBEDDING_DECODED_BYTES:
                    raise EmbeddingResponseError(
                        "Ollama embedding response exceeded its decoded byte limit."
                    )
                decoded_parts.append(decoded_part)
                continue

            compressed_part = raw_part
            while compressed_part:
                remaining = MAX_EMBEDDING_DECODED_BYTES - decoded_count
                decoded_part = decompressor.decompress(compressed_part, remaining + 1)
                if len(decoded_part) > remaining:
                    raise EmbeddingResponseError(
                        "Ollama embedding response exceeded its decoded byte limit."
                    )
                decoded_count += len(decoded_part)
                decoded_parts.append(decoded_part)
                next_part = decompressor.unconsumed_tail
                if next_part == compressed_part and not decoded_part:
                    raise EmbeddingResponseError("Ollama returned invalid gzip content.")
                compressed_part = next_part
        if decompressor is not None:
            remaining = MAX_EMBEDDING_DECODED_BYTES - decoded_count
            decoded_part = decompressor.flush(remaining + 1)
            if len(decoded_part) > remaining:
                raise EmbeddingResponseError(
                    "Ollama embedding response exceeded its decoded byte limit."
                )
            if not decompressor.eof or decompressor.unused_data:
                raise EmbeddingResponseError("Ollama returned invalid gzip content.")
            decoded_count += len(decoded_part)
            decoded_parts.append(decoded_part)
        decoded = b"".join(decoded_parts).decode("utf-8", errors="strict")
        return json.loads(
            decoded,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"Unsupported JSON constant: {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, zlib.error):
        raise EmbeddingResponseError("Ollama returned malformed JSON.") from None


class DeterministicEmbeddingModel:
    """Infrastructure-free fake embedding model for ordinary tests."""

    def __init__(
        self,
        *,
        model_id: str = "deterministic-test-embedding",
        dimension: int = 8,
        batch_size: int = 32,
    ) -> None:
        if not model_id.strip():
            raise EmbeddingInputError("Embedding model identity must not be blank.")
        if dimension <= 0:
            raise EmbeddingInputError("Embedding dimension must be positive.")
        if batch_size <= 0:
            raise EmbeddingInputError("Embedding batch size must be positive.")
        self._model_id = model_id
        self._dimension = dimension
        self._batch_size = batch_size

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        validated = _validate_texts(texts)
        vectors: list[EmbeddingVector] = []
        for batch_start in range(0, len(validated), self._batch_size):
            batch = validated[batch_start : batch_start + self._batch_size]
            for text in batch:
                seed = f"{self._model_id}\0{text}".encode()
                values = []
                for index in range(self._dimension):
                    digest = hashlib.sha256(seed + index.to_bytes(8, "big")).digest()
                    unsigned = int.from_bytes(digest[:8], "big")
                    values.append((unsigned / ((1 << 64) - 1)) * 2.0 - 1.0)
                vectors.append(tuple(values))
        return validate_embedding_batch(validated, vectors, dimension=self._dimension)

    async def close(self) -> None:
        """The deterministic adapter owns no external resources."""


class OllamaEmbeddingModel:
    """Ollama ``/api/embed`` adapter with bounded batches and timeouts."""

    def __init__(
        self,
        *,
        base_url: str,
        model_id: str,
        dimension: int,
        batch_size: int,
        timeout_seconds: float,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not model_id.strip():
            raise EmbeddingInputError("Embedding model identity must not be blank.")
        if dimension <= 0:
            raise EmbeddingInputError("Embedding dimension must be positive.")
        if batch_size <= 0:
            raise EmbeddingInputError("Embedding batch size must be positive.")
        if timeout_seconds <= 0:
            raise EmbeddingInputError("Embedding request timeout must be positive.")
        parsed_url = httpx.URL(base_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.host:
            raise EmbeddingInputError("Ollama base URL must be an absolute HTTP(S) URL.")

        self._endpoint = f"{str(parsed_url).rstrip('/')}/api/embed"
        self._model_id = model_id
        self._dimension = dimension
        self._batch_size = batch_size
        self._timeout_seconds = float(timeout_seconds)
        self._timeout = httpx.Timeout(timeout_seconds)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient()
        self._closed = False

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        if self._closed:
            raise EmbeddingRequestError("The Ollama embedding adapter is closed.")
        validated = _validate_texts(texts)
        vectors: list[EmbeddingVector] = []
        for batch_start in range(0, len(validated), self._batch_size):
            batch = validated[batch_start : batch_start + self._batch_size]
            payload = {
                "model": self._model_id,
                "input": batch,
                "truncate": False,
            }
            normalized_failure: str | None = None
            try:
                loop = asyncio.get_running_loop()
                deadline = loop.time() + self._timeout_seconds
                async with asyncio.timeout_at(deadline):
                    async with self._client.stream(
                        "POST",
                        self._endpoint,
                        json=payload,
                        timeout=self._timeout,
                    ) as response:
                        if response.is_error:
                            raise EmbeddingRequestError(
                                f"Ollama embedding request failed with HTTP {response.status_code}."
                            )
                        body = await _bounded_embedding_json(response)
                    if not isinstance(body, dict):
                        raise EmbeddingResponseError("Ollama embedding response must be an object.")
                    response_model = body.get("model")
                    if response_model != self._model_id:
                        raise EmbeddingResponseError(
                            "Ollama embedding response model does not match the configured model."
                        )
                    batch_vectors = validate_embedding_batch(
                        batch,
                        body.get("embeddings"),
                        dimension=self._dimension,
                    )
                    if _deadline_expired(deadline):
                        raise TimeoutError
                    vectors.extend(batch_vectors)
            except TimeoutError:
                normalized_failure = "Ollama embedding request timed out."
            except httpx.TimeoutException:
                normalized_failure = "Ollama embedding request timed out."
            except httpx.HTTPError:
                normalized_failure = "Ollama embedding request failed."
            if normalized_failure is not None:
                raise EmbeddingRequestError(normalized_failure)
        return vectors

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> OllamaEmbeddingModel:
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        await self.close()
