"""Embedding boundary, deterministic test adapter, and Ollama implementation."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from typing import Protocol

import httpx

type EmbeddingVector = tuple[float, ...]


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
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise EmbeddingResponseError(
                    f"Embedding at index {vector_index} contains a non-numeric value."
                )
            converted = float(value)
            if not math.isfinite(converted):
                raise EmbeddingResponseError(
                    f"Embedding at index {vector_index} contains a non-finite value."
                )
            vector.append(converted)
        validated.append(tuple(vector))
    return validated


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
            try:
                response = await self._client.post(
                    self._endpoint,
                    json=payload,
                    timeout=self._timeout,
                )
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                raise EmbeddingRequestError("Ollama embedding request timed out.") from exc
            except httpx.HTTPStatusError as exc:
                raise EmbeddingRequestError(
                    f"Ollama embedding request failed with HTTP {exc.response.status_code}."
                ) from exc
            except httpx.HTTPError as exc:
                raise EmbeddingRequestError("Ollama embedding request failed.") from exc

            try:
                body: object = response.json()
            except json.JSONDecodeError as exc:
                raise EmbeddingResponseError("Ollama returned malformed JSON.") from exc
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
            vectors.extend(batch_vectors)
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
