"""Replaceable AF-1 file-storage boundary and local implementation."""

import asyncio
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol
from uuid import uuid4


class AsyncReadable(Protocol):
    """Minimal internal upload stream required by AF-1."""

    async def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` bytes from the source."""
        ...


@dataclass(frozen=True, slots=True)
class StoredFile:
    """Safe metadata produced while streaming a file into storage."""

    storage_key: str
    size_bytes: int
    sha256: str
    prefix: bytes


class FileStorage(Protocol):
    """Internal storage behavior consumed by the AF-1 application service."""

    async def store(
        self,
        source: AsyncReadable,
        *,
        storage_key: str,
        max_bytes: int,
    ) -> StoredFile:
        """Persist a streamed source beneath a server-controlled key."""
        ...

    async def delete(self, storage_key: str) -> None:
        """Idempotently remove a server-controlled key."""
        ...


class StorageError(Exception):
    """Base class for storage failures safe for service-level translation."""


class EmptyFileError(StorageError):
    """The source stream contained no bytes."""


class FileTooLargeError(StorageError):
    """The source stream exceeded its explicit byte limit."""


class UnsafeStorageKeyError(StorageError):
    """A storage key attempted to escape the configured root."""


class LocalFileStorage:
    """Local storage confined beneath one configured root."""

    _CHUNK_SIZE = 64 * 1024
    _PREFIX_SIZE = 4096

    def __init__(self, root: Path) -> None:
        self._root = root.expanduser().resolve()

    def _resolve_key(self, storage_key: str) -> Path:
        key = PurePosixPath(storage_key)
        if key.is_absolute() or not key.parts or any(part in {"", ".", ".."} for part in key.parts):
            raise UnsafeStorageKeyError
        candidate = self._root.joinpath(*key.parts)
        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise UnsafeStorageKeyError from exc
        return candidate

    async def store(
        self,
        source: AsyncReadable,
        *,
        storage_key: str,
        max_bytes: int,
    ) -> StoredFile:
        """Stream one file atomically while calculating its digest and size."""
        target = self._resolve_key(storage_key)
        await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
        resolved_parent = await asyncio.to_thread(target.parent.resolve)
        try:
            resolved_parent.relative_to(self._root)
        except ValueError as exc:
            raise UnsafeStorageKeyError from exc

        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        digest = hashlib.sha256()
        prefix = bytearray()
        size_bytes = 0
        published = False
        try:
            handle = await asyncio.to_thread(temporary.open, "xb")
            try:
                while chunk := await source.read(self._CHUNK_SIZE):
                    size_bytes += len(chunk)
                    if size_bytes > max_bytes:
                        raise FileTooLargeError
                    digest.update(chunk)
                    if len(prefix) < self._PREFIX_SIZE:
                        prefix.extend(chunk[: self._PREFIX_SIZE - len(prefix)])
                    await asyncio.to_thread(handle.write, chunk)
                if size_bytes == 0:
                    raise EmptyFileError
                await asyncio.to_thread(handle.flush)
                await asyncio.to_thread(os.fsync, handle.fileno())
            finally:
                await asyncio.to_thread(handle.close)
            await asyncio.to_thread(os.replace, temporary, target)
            published = True
        finally:
            if not published:
                await asyncio.to_thread(temporary.unlink, missing_ok=True)

        return StoredFile(
            storage_key=storage_key,
            size_bytes=size_bytes,
            sha256=digest.hexdigest(),
            prefix=bytes(prefix),
        )

    async def delete(self, storage_key: str) -> None:
        """Idempotently remove a stored file without exposing its host path."""
        target = self._resolve_key(storage_key)
        await asyncio.to_thread(target.unlink, missing_ok=True)
