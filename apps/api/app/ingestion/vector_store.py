"""Rebuildable vector-index boundary with in-memory and Chroma adapters."""

from __future__ import annotations

import asyncio
import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote
from uuid import UUID

import httpx

from app.ingestion.embeddings import EmbeddingVector

_LOWER_HEX = frozenset("0123456789abcdef")
_COLLECTION_NAME_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{1,510}[a-z0-9]\Z")


class VectorStoreError(Exception):
    """Base class for explicit vector-index failures."""


class VectorStoreInputError(VectorStoreError):
    """Vector record or adapter configuration is invalid."""


class VectorStoreNotInitializedError(VectorStoreError):
    """A vector operation was attempted before collection initialization."""


class VectorStoreConfigurationError(VectorStoreError):
    """An existing index is incompatible with the requested model configuration."""


class VectorStoreRequestError(VectorStoreError):
    """The configured vector service could not complete a request."""


class VectorStoreResponseError(VectorStoreError):
    """The vector service returned an invalid response."""


def stable_vector_id(chunk_id: UUID) -> str:
    """Derive a stable index identifier from a PostgreSQL-authoritative chunk ID."""
    return f"chunk:{chunk_id}"


@dataclass(frozen=True, slots=True)
class VectorRecord:
    """One derived vector record backed by a durable PostgreSQL chunk."""

    vector_id: str
    embedding: EmbeddingVector
    knowledge_base_id: UUID
    document_id: UUID
    chunk_id: UUID
    chunk_index: int
    normalized_text: str
    content_hash: str

    def __post_init__(self) -> None:
        if self.vector_id != stable_vector_id(self.chunk_id):
            raise VectorStoreInputError(
                "Vector ID must be derived from the durable chunk identity."
            )
        if self.chunk_index < 0:
            raise VectorStoreInputError("Chunk index must be non-negative.")
        if not self.normalized_text.strip():
            raise VectorStoreInputError("Vector document text must not be empty.")
        if len(self.content_hash) != 64 or any(
            character not in _LOWER_HEX for character in self.content_hash
        ):
            raise VectorStoreInputError("Chunk content hash must be lowercase SHA-256 hex.")
        if not self.embedding:
            raise VectorStoreInputError("Vector embedding must not be empty.")
        if any(not math.isfinite(value) for value in self.embedding):
            raise VectorStoreInputError("Vector embedding values must be finite.")


class VectorStore(Protocol):
    """Provider-independent behavior for a rebuildable derived vector index."""

    async def initialize(self, *, model_id: str, dimension: int) -> None:
        """Idempotently initialize a collection for one embedding configuration."""
        ...

    async def upsert(self, records: Sequence[VectorRecord]) -> None:
        """Idempotently create or replace stable chunk vector records."""
        ...

    async def delete_by_document(self, document_id: UUID) -> None:
        """Delete only vector records derived from one document."""
        ...

    async def delete_by_chunk_ids(self, chunk_ids: Sequence[UUID]) -> None:
        """Delete vector records by their durable chunk identities."""
        ...

    async def close(self) -> None:
        """Release resources owned by the adapter."""
        ...


def _validate_initialization(model_id: str, dimension: int) -> None:
    if not model_id.strip():
        raise VectorStoreInputError("Embedding model identity must not be blank.")
    if dimension <= 0:
        raise VectorStoreInputError("Embedding dimension must be positive.")


def _validate_records(
    records: Sequence[VectorRecord],
    *,
    expected_dimension: int,
) -> list[VectorRecord]:
    validated = list(records)
    seen_ids: set[str] = set()
    for record in validated:
        if record.vector_id in seen_ids:
            raise VectorStoreInputError(f"Vector batch contains duplicate ID {record.vector_id!r}.")
        seen_ids.add(record.vector_id)
        if len(record.embedding) != expected_dimension:
            raise VectorStoreInputError(
                f"Vector {record.vector_id!r} has dimension {len(record.embedding)}; "
                f"expected {expected_dimension}."
            )
    return validated


class InMemoryVectorStore:
    """Deterministic, infrastructure-free vector-store fake for tests."""

    def __init__(self) -> None:
        self._model_id: str | None = None
        self._dimension: int | None = None
        self._records: dict[str, VectorRecord] = {}
        self._lock = asyncio.Lock()

    @property
    def records(self) -> tuple[VectorRecord, ...]:
        """Return an immutable snapshot in stable vector-ID order."""
        return tuple(self._records[key] for key in sorted(self._records))

    async def initialize(self, *, model_id: str, dimension: int) -> None:
        _validate_initialization(model_id, dimension)
        async with self._lock:
            if self._model_id is None:
                self._model_id = model_id
                self._dimension = dimension
                return
            if self._model_id != model_id or self._dimension != dimension:
                raise VectorStoreConfigurationError(
                    "Vector index is initialized for a different embedding configuration."
                )

    def _required_dimension(self) -> int:
        if self._dimension is None:
            raise VectorStoreNotInitializedError("Vector index is not initialized.")
        return self._dimension

    async def upsert(self, records: Sequence[VectorRecord]) -> None:
        async with self._lock:
            validated = _validate_records(
                records,
                expected_dimension=self._required_dimension(),
            )
            for record in validated:
                self._records[record.vector_id] = record

    async def delete_by_document(self, document_id: UUID) -> None:
        async with self._lock:
            self._required_dimension()
            self._records = {
                vector_id: record
                for vector_id, record in self._records.items()
                if record.document_id != document_id
            }

    async def delete_by_chunk_ids(self, chunk_ids: Sequence[UUID]) -> None:
        async with self._lock:
            self._required_dimension()
            for chunk_id in chunk_ids:
                self._records.pop(stable_vector_id(chunk_id), None)

    async def close(self) -> None:
        """The deterministic adapter owns no external resources."""


class ChromaVectorStore:
    """Async Chroma 1.5 HTTP v2 adapter using caller-supplied embeddings."""

    _DEFAULT_TENANT = "default_tenant"
    _DEFAULT_DATABASE = "default_database"

    def __init__(
        self,
        *,
        host: str,
        http_port: int,
        ssl: bool,
        collection_name: str,
        batch_size: int = 100,
        timeout_seconds: float = 10.0,
        tenant: str = _DEFAULT_TENANT,
        database: str = _DEFAULT_DATABASE,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if (
            not host.strip()
            or "://" in host
            or "/" in host
            or "@" in host
            or any(character.isspace() for character in host)
        ):
            raise VectorStoreInputError("Chroma host must be a hostname without a URL scheme.")
        if not 1 <= http_port <= 65535:
            raise VectorStoreInputError("Chroma HTTP port must be between 1 and 65535.")
        if _COLLECTION_NAME_PATTERN.fullmatch(collection_name) is None:
            raise VectorStoreInputError(
                "Chroma collection name must be 3-512 characters, use only lowercase "
                "letters, digits, dots, dashes, or underscores, and start and end with "
                "a letter or digit."
            )
        if batch_size <= 0:
            raise VectorStoreInputError("Chroma batch size must be positive.")
        if timeout_seconds <= 0:
            raise VectorStoreInputError("Chroma request timeout must be positive.")
        if not tenant.strip() or not database.strip():
            raise VectorStoreInputError("Chroma tenant and database must not be blank.")

        scheme = "https" if ssl else "http"
        self._base_url = f"{scheme}://{host}:{http_port}"
        tenant_path = quote(tenant, safe="")
        database_path = quote(database, safe="")
        self._collections_path = (
            f"/api/v2/tenants/{tenant_path}/databases/{database_path}/collections"
        )
        self._collection_name = collection_name
        self._batch_size = batch_size
        self._timeout = httpx.Timeout(timeout_seconds)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient()
        self._collection_id: str | None = None
        self._model_id: str | None = None
        self._dimension: int | None = None
        self._closed = False
        self._initialize_lock = asyncio.Lock()

    async def _post_json(self, path: str, payload: dict[str, object]) -> object:
        if self._closed:
            raise VectorStoreRequestError("The Chroma vector-store adapter is closed.")
        try:
            response = await self._client.post(
                f"{self._base_url}{path}",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise VectorStoreRequestError("Chroma request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise VectorStoreRequestError(
                f"Chroma request failed with HTTP {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise VectorStoreRequestError("Chroma request failed.") from exc
        try:
            body: object = response.json()
        except json.JSONDecodeError as exc:
            raise VectorStoreResponseError("Chroma returned malformed JSON.") from exc
        return body

    async def initialize(self, *, model_id: str, dimension: int) -> None:
        _validate_initialization(model_id, dimension)
        async with self._initialize_lock:
            if self._collection_id is not None:
                if self._model_id != model_id or self._dimension != dimension:
                    raise VectorStoreConfigurationError(
                        "Vector index is initialized for a different embedding configuration."
                    )
                return

            expected_metadata = {
                "embedding_model": model_id,
                "embedding_dimension": dimension,
                "source_of_truth": "postgresql",
            }
            body = await self._post_json(
                self._collections_path,
                {
                    "name": self._collection_name,
                    "get_or_create": True,
                    "metadata": expected_metadata,
                },
            )
            if not isinstance(body, dict):
                raise VectorStoreResponseError("Chroma collection response must be an object.")
            collection_id = body.get("id")
            if not isinstance(collection_id, str):
                raise VectorStoreResponseError("Chroma collection response has no valid ID.")
            try:
                UUID(collection_id)
            except ValueError as exc:
                raise VectorStoreResponseError(
                    "Chroma collection response has no valid ID."
                ) from exc
            if body.get("name") != self._collection_name:
                raise VectorStoreResponseError(
                    "Chroma collection response name does not match the configured collection."
                )
            metadata = body.get("metadata")
            if not isinstance(metadata, dict) or any(
                metadata.get(key) != value for key, value in expected_metadata.items()
            ):
                raise VectorStoreConfigurationError(
                    "Chroma collection metadata does not match the embedding configuration."
                )
            existing_dimension = body.get("dimension")
            if existing_dimension is not None and existing_dimension != dimension:
                raise VectorStoreConfigurationError(
                    "Chroma collection dimension does not match the embedding configuration."
                )

            self._collection_id = collection_id
            self._model_id = model_id
            self._dimension = dimension

    def _required_collection(self) -> tuple[str, int]:
        if self._collection_id is None or self._dimension is None:
            raise VectorStoreNotInitializedError("Vector index is not initialized.")
        return self._collection_id, self._dimension

    def _records_path(self, action: str) -> tuple[str, int]:
        collection_id, dimension = self._required_collection()
        path = f"{self._collections_path}/{quote(collection_id, safe='')}/{action}"
        return path, dimension

    async def upsert(self, records: Sequence[VectorRecord]) -> None:
        path, dimension = self._records_path("upsert")
        validated = _validate_records(records, expected_dimension=dimension)
        for batch_start in range(0, len(validated), self._batch_size):
            batch = validated[batch_start : batch_start + self._batch_size]
            await self._post_json(
                path,
                {
                    "ids": [record.vector_id for record in batch],
                    "embeddings": [list(record.embedding) for record in batch],
                    "documents": [record.normalized_text for record in batch],
                    "metadatas": [
                        {
                            "knowledge_base_id": str(record.knowledge_base_id),
                            "document_id": str(record.document_id),
                            "chunk_id": str(record.chunk_id),
                            "chunk_index": record.chunk_index,
                            "content_hash": record.content_hash,
                        }
                        for record in batch
                    ],
                },
            )

    async def delete_by_document(self, document_id: UUID) -> None:
        path, _ = self._records_path("delete")
        await self._post_json(
            path,
            {"where": {"document_id": {"$eq": str(document_id)}}},
        )

    async def delete_by_chunk_ids(self, chunk_ids: Sequence[UUID]) -> None:
        path, _ = self._records_path("delete")
        vector_ids = [stable_vector_id(chunk_id) for chunk_id in chunk_ids]
        for batch_start in range(0, len(vector_ids), self._batch_size):
            batch = vector_ids[batch_start : batch_start + self._batch_size]
            await self._post_json(path, {"ids": batch})

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> ChromaVectorStore:
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        await self.close()
