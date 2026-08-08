"""Bounded read-only Chroma candidate retrieval for AF-3B."""

from __future__ import annotations

import asyncio
import codecs
import json
import math
import zlib
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Final, Protocol, cast
from urllib.parse import quote
from uuid import UUID

import httpx

from app.ingestion.embeddings import EmbeddingVector

CHROMA_COMPATIBILITY_ID: Final = "chroma-http-v2-1.5.9"
CHROMA_VERSION: Final = "1.5.9"
MAX_PROVIDER_WIRE_BYTES: Final = 1_048_576
MAX_PROVIDER_DECODED_BYTES: Final = 2_097_152
MAX_CANDIDATE_ID_BYTES: Final = 128
MAX_UNTRUSTED_STRING_BYTES: Final = 4_096
MAX_METADATA_ENTRIES: Final = 32
MAX_METADATA_KEY_BYTES: Final = 128
MAX_METADATA_VALUE_BYTES: Final = 1_024
MAX_JSON_DEPTH: Final = 16
MAX_PROVIDER_CANDIDATES: Final = 128
DEFAULT_PROVIDER_TIMEOUT_SECONDS: Final = 30.0
MAX_PROVIDER_TIMEOUT_SECONDS: Final = 600.0

_CANONICAL_RESPONSE_KEYS = frozenset(
    {
        "ids",
        "embeddings",
        "documents",
        "uris",
        "data",
        "metadatas",
        "distances",
        "include",
    }
)


def _deadline_expired(deadline: float) -> bool:
    return asyncio.get_running_loop().time() >= deadline


class DenseProviderError(Exception):
    """Privacy-safe required-Provider failure."""

    def __init__(self) -> None:
        super().__init__("Dense retrieval provider is unavailable.")


def _parse_canonical_vector_id(value: object) -> UUID | None:
    if type(value) is not str or not value.startswith("chunk:"):
        return None
    raw_uuid = value.removeprefix("chunk:")
    try:
        chunk_id = UUID(raw_uuid)
    except ValueError:
        return None
    if value != f"chunk:{chunk_id}":
        return None
    return chunk_id


@dataclass(frozen=True, slots=True, repr=False, init=False)
class _DenseProviderResult:
    """Bounded accepted ranks with rejected Provider identifiers discarded."""

    position_count: int
    _ranked_chunk_ids: tuple[tuple[UUID, int], ...] = field(repr=False)

    def __init__(
        self,
        *,
        position_count: int,
        candidates: Sequence[tuple[object, object, int]],
    ) -> None:
        if (
            type(position_count) is not int
            or not 0 <= position_count <= MAX_PROVIDER_CANDIDATES
            or len(candidates) != position_count
        ):
            raise DenseProviderError

        positions: set[int] = set()
        ranks: dict[UUID, int] = {}
        for candidate in candidates:
            if type(candidate) is not tuple or len(candidate) != 3:
                raise DenseProviderError
            vector_id, provider_score, absolute_position = candidate
            if (
                type(absolute_position) is not int
                or not 0 <= absolute_position < position_count
                or absolute_position in positions
            ):
                raise DenseProviderError
            positions.add(absolute_position)
            if type(vector_id) is str and len(vector_id.encode("utf-8")) > MAX_CANDIDATE_ID_BYTES:
                raise DenseProviderError
            if provider_score is not None and (
                type(provider_score) is not float or not math.isfinite(provider_score)
            ):
                continue
            chunk_id = _parse_canonical_vector_id(vector_id)
            if chunk_id is None:
                continue
            rank = absolute_position + 1
            previous = ranks.get(chunk_id)
            if previous is None or rank < previous:
                ranks[chunk_id] = rank

        if positions != set(range(position_count)):
            raise DenseProviderError
        object.__setattr__(self, "position_count", position_count)
        object.__setattr__(
            self,
            "_ranked_chunk_ids",
            tuple(sorted(ranks.items(), key=lambda item: item[1])),
        )

    @property
    def accepted_count(self) -> int:
        """Return a non-identifying count of candidates that survived local checks."""
        return len(self._ranked_chunk_ids)


class DenseRetrievalPort(Protocol):
    """Provider-neutral read-only dense candidate operation."""

    async def query(
        self,
        *,
        embedding: EmbeddingVector,
        knowledge_base_id: UUID,
        candidate_count: int,
    ) -> _DenseProviderResult: ...


class _DuplicateKeyError(ValueError):
    pass


class _JsonNumber(str):
    """Preserve a bounded JSON number's exact lexical byte representation."""


@dataclass(slots=True)
class _JsonDepthScanner:
    """Track JSON container depth without materializing the response."""

    depth: int = 0
    in_string: bool = False
    escaped: bool = False

    def feed(self, text: str) -> None:
        for character in text:
            if self.in_string:
                if self.escaped:
                    self.escaped = False
                elif character == "\\":
                    self.escaped = True
                elif character == '"':
                    self.in_string = False
                continue
            if character == '"':
                self.in_string = True
            elif character in "[{":
                next_depth = self.depth + 1
                if next_depth > MAX_JSON_DEPTH:
                    raise DenseProviderError
                self.depth = next_depth
            elif character in "]}":
                self.depth -= 1

    def finish(self) -> None:
        if self.depth != 0 or self.in_string:
            raise DenseProviderError


class _CandidateLocalInvalidScore:
    """Non-identifying marker for a raw wrong-type candidate-local score."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<candidate-local-invalid-score>"


_CANDIDATE_LOCAL_INVALID_SCORE = _CandidateLocalInvalidScore()


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"Unsupported JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _validate_json_depth(text: str) -> None:
    scanner = _JsonDepthScanner()
    scanner.feed(text)
    scanner.finish()


def _strict_json(body: bytes) -> object:
    if body.startswith(b"\xef\xbb\xbf"):
        raise DenseProviderError
    try:
        text = body.decode("utf-8", errors="strict")
        _validate_json_depth(text)
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=_JsonNumber,
            parse_int=_JsonNumber,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise DenseProviderError from None


def _validate_content_type(response: httpx.Response) -> None:
    raw = response.headers.get("content-type")
    if raw is None:
        raise DenseProviderError
    parts = [part.strip() for part in raw.split(";")]
    if parts[0].lower() != "application/json" or len(parts) > 2:
        raise DenseProviderError
    if len(parts) == 2:
        parameter = parts[1].split("=", 1)
        if len(parameter) != 2 or parameter[0].strip().lower() != "charset":
            raise DenseProviderError
        if parameter[1].strip().strip('"').lower() != "utf-8":
            raise DenseProviderError


def _content_encoding(response: httpx.Response) -> str:
    raw = response.headers.get("content-encoding")
    if raw is None or not raw.strip():
        return "identity"
    encoding = raw.strip().lower()
    if "," in encoding or encoding not in {"identity", "gzip"}:
        raise DenseProviderError
    return cast(str, encoding)


def _validate_content_length(response: httpx.Response) -> None:
    raw = response.headers.get("content-length")
    if raw is None:
        return
    try:
        declared = int(raw, 10)
    except ValueError:
        raise DenseProviderError from None
    if declared < 0 or declared > MAX_PROVIDER_WIRE_BYTES:
        raise DenseProviderError


async def _provider_raw_parts(response: httpx.Response) -> AsyncIterator[bytes]:
    if response.is_stream_consumed:
        yield response.content
        return
    async for raw_part in response.aiter_raw():
        yield raw_part


async def _bounded_json_body(response: httpx.Response) -> object:
    _validate_content_type(response)
    encoding = _content_encoding(response)
    _validate_content_length(response)
    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS) if encoding == "gzip" else None
    wire_count = 0
    decoded_count = 0
    decoded_parts: list[bytes] = []
    utf8_decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
    depth_scanner = _JsonDepthScanner()

    def accept_decoded_part(decoded_part: bytes) -> None:
        depth_scanner.feed(utf8_decoder.decode(decoded_part, final=False))
        decoded_parts.append(decoded_part)

    try:
        async for raw_part in _provider_raw_parts(response):
            wire_count += len(raw_part)
            if wire_count > MAX_PROVIDER_WIRE_BYTES:
                raise DenseProviderError
            if decompressor is None:
                decoded_part = raw_part
                decoded_count += len(decoded_part)
                if decoded_count > MAX_PROVIDER_DECODED_BYTES:
                    raise DenseProviderError
                accept_decoded_part(decoded_part)
                continue

            compressed_part = raw_part
            while compressed_part:
                remaining = MAX_PROVIDER_DECODED_BYTES - decoded_count
                decoded_part = decompressor.decompress(compressed_part, remaining + 1)
                if len(decoded_part) > remaining:
                    raise DenseProviderError
                decoded_count += len(decoded_part)
                accept_decoded_part(decoded_part)
                next_part = decompressor.unconsumed_tail
                if next_part == compressed_part and not decoded_part:
                    raise DenseProviderError
                compressed_part = next_part
        if decompressor is not None:
            remaining = MAX_PROVIDER_DECODED_BYTES - decoded_count
            decoded_part = decompressor.flush(remaining + 1)
            if len(decoded_part) > remaining:
                raise DenseProviderError
            if not decompressor.eof or decompressor.unused_data:
                raise DenseProviderError
            decoded_count += len(decoded_part)
            accept_decoded_part(decoded_part)
        depth_scanner.feed(utf8_decoder.decode(b"", final=True))
        depth_scanner.finish()
    except (UnicodeDecodeError, zlib.error, httpx.HTTPError):
        raise DenseProviderError from None
    return _strict_json(b"".join(decoded_parts))


def _finite_binary64(value: object) -> float:
    if type(value) is not _JsonNumber:
        raise TypeError
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        raise DenseProviderError from None
    if not math.isfinite(converted):
        raise DenseProviderError
    return converted


def _validate_optional_documents(value: object, *, position_count: int) -> None:
    if value is None:
        return
    if type(value) is not list or len(value) != 1 or type(value[0]) is not list:
        raise DenseProviderError
    documents = value[0]
    if len(documents) != position_count:
        raise DenseProviderError
    for document in documents:
        if document is None:
            continue
        if type(document) is not str:
            raise DenseProviderError
        if len(document.encode("utf-8")) > MAX_UNTRUSTED_STRING_BYTES:
            raise DenseProviderError


def _validate_optional_metadatas(value: object, *, position_count: int) -> None:
    if value is None:
        return
    if type(value) is not list or len(value) != 1 or type(value[0]) is not list:
        raise DenseProviderError
    metadatas = value[0]
    if len(metadatas) != position_count:
        raise DenseProviderError
    for metadata in metadatas:
        if metadata is None:
            continue
        if type(metadata) is not dict or len(metadata) > MAX_METADATA_ENTRIES:
            raise DenseProviderError
        for key, scalar in metadata.items():
            if type(key) is not str or len(key.encode("utf-8")) > MAX_METADATA_KEY_BYTES:
                raise DenseProviderError
            if type(scalar) is str:
                if len(scalar.encode("utf-8")) > MAX_METADATA_VALUE_BYTES:
                    raise DenseProviderError
            elif type(scalar) is bool:
                continue
            elif type(scalar) is _JsonNumber:
                if len(scalar.encode("utf-8")) > MAX_METADATA_VALUE_BYTES:
                    raise DenseProviderError
                _finite_binary64(scalar)
            else:
                raise DenseProviderError


def _typed_result(body: object, *, configured_count: int) -> _DenseProviderResult:
    if type(body) is not dict or set(body) != _CANONICAL_RESPONSE_KEYS:
        raise DenseProviderError
    if body["embeddings"] is not None or body["uris"] is not None or body["data"] is not None:
        raise DenseProviderError
    if body["include"] != ["distances"]:
        raise DenseProviderError
    ids_outer = body["ids"]
    distances_outer = body["distances"]
    if (
        type(ids_outer) is not list
        or len(ids_outer) != 1
        or type(ids_outer[0]) is not list
        or type(distances_outer) is not list
        or len(distances_outer) != 1
        or type(distances_outer[0]) is not list
    ):
        raise DenseProviderError
    ids = ids_outer[0]
    distances = distances_outer[0]
    position_count = len(ids)
    if (
        len(distances) != position_count
        or position_count > configured_count
        or position_count > MAX_PROVIDER_CANDIDATES
    ):
        raise DenseProviderError
    _validate_optional_documents(body["documents"], position_count=position_count)
    _validate_optional_metadatas(body["metadatas"], position_count=position_count)

    normalized_distances: list[object] = []
    for distance in distances:
        if type(distance) is _JsonNumber:
            normalized_distances.append(_finite_binary64(distance))
        else:
            normalized_distances.append(_CANDIDATE_LOCAL_INVALID_SCORE)
    for vector_id in ids:
        if type(vector_id) is str and len(vector_id.encode("utf-8")) > MAX_CANDIDATE_ID_BYTES:
            raise DenseProviderError

    return _DenseProviderResult(
        position_count=position_count,
        candidates=tuple(
            (vector_id, normalized_distances[position], position)
            for position, vector_id in enumerate(ids)
        ),
    )


class ChromaDenseRetrievalAdapter:
    """Pinned raw-HTTP Chroma query adapter with no write-capable operation."""

    _DEFAULT_TENANT = "default_tenant"
    _DEFAULT_DATABASE = "default_database"

    def __init__(
        self,
        *,
        host: str,
        http_port: int,
        ssl: bool,
        collection_uuid: UUID,
        timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
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
            raise ValueError("Invalid Chroma retrieval host configuration.")
        if not 1 <= http_port <= 65_535:
            raise ValueError("Invalid Chroma retrieval port configuration.")
        if not isinstance(collection_uuid, UUID):
            raise ValueError("A canonical Chroma collection UUID is required.")
        if not 0 < timeout_seconds <= MAX_PROVIDER_TIMEOUT_SECONDS:
            raise ValueError("Invalid Chroma retrieval timeout configuration.")
        if not tenant.strip() or not database.strip():
            raise ValueError("Chroma tenant and database must not be blank.")

        scheme = "https" if ssl else "http"
        self._base_url = f"{scheme}://{host}:{http_port}"
        tenant_path = quote(tenant, safe="")
        database_path = quote(database, safe="")
        collection_path = quote(str(collection_uuid), safe="")
        self._query_path = (
            f"/api/v2/tenants/{tenant_path}/databases/{database_path}"
            f"/collections/{collection_path}/query"
        )
        self._timeout_seconds = float(timeout_seconds)
        self._timeout = httpx.Timeout(timeout_seconds)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient()
        self._closed = False
        self._compatible = False
        self._probe_lock = asyncio.Lock()
        self._probe_task: asyncio.Task[None] | None = None

    @property
    def compatibility_id(self) -> str:
        return CHROMA_COMPATIBILITY_ID

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, object] | None = None,
        validate: Callable[[object], object],
    ) -> object:
        if self._closed:
            raise DenseProviderError
        try:
            loop = asyncio.get_running_loop()
            deadline = loop.time() + self._timeout_seconds
            async with asyncio.timeout_at(deadline):
                async with self._client.stream(
                    method,
                    f"{self._base_url}{path}",
                    json=payload,
                    timeout=self._timeout,
                ) as response:
                    if response.status_code != 200:
                        raise DenseProviderError
                    body = await _bounded_json_body(response)
                result = validate(body)
                if _deadline_expired(deadline):
                    raise TimeoutError
                return result
        except (TimeoutError, httpx.HTTPError):
            pass
        raise DenseProviderError

    async def _probe(self) -> None:
        def validate_version(body: object) -> object:
            if body != CHROMA_VERSION:
                raise DenseProviderError
            return None

        await self._request_json(
            "GET",
            "/api/v2/version",
            validate=validate_version,
        )

    async def _ensure_compatible(self) -> None:
        async with self._probe_lock:
            if self._closed:
                raise DenseProviderError
            if self._compatible:
                return
            task = self._probe_task
            if task is None:
                task = asyncio.create_task(self._probe())
                self._probe_task = task
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            if task.cancelled():
                async with self._probe_lock:
                    if self._probe_task is task:
                        self._probe_task = None
            raise
        except DenseProviderError:
            async with self._probe_lock:
                if self._probe_task is task:
                    self._probe_task = None
            raise
        else:
            async with self._probe_lock:
                if self._probe_task is task:
                    self._probe_task = None
                    self._compatible = True

    async def query(
        self,
        *,
        embedding: EmbeddingVector,
        knowledge_base_id: UUID,
        candidate_count: int,
    ) -> _DenseProviderResult:
        if not 1 <= candidate_count <= MAX_PROVIDER_CANDIDATES:
            raise ValueError("Dense candidate count is outside the configured bound.")
        if not embedding or any(
            type(value) is not float or not math.isfinite(value) for value in embedding
        ):
            raise ValueError("Dense query embedding must contain built-in finite floats.")
        await self._ensure_compatible()
        result = await self._request_json(
            "POST",
            self._query_path,
            payload={
                "query_embeddings": [list(embedding)],
                "n_results": candidate_count,
                "where": {"knowledge_base_id": {"$eq": str(knowledge_base_id)}},
                "include": ["distances"],
            },
            validate=lambda body: _typed_result(body, configured_count=candidate_count),
        )
        if not isinstance(result, _DenseProviderResult):
            raise DenseProviderError
        return result

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._compatible = False
        task = self._probe_task
        self._probe_task = None
        if task is not None and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError, DenseProviderError):
                await task
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> ChromaDenseRetrievalAdapter:
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        await self.close()
