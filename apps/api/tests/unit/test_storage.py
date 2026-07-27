"""Deterministic tests for the AF-1 local file-storage boundary."""

from pathlib import Path

import pytest

from app.ingestion.storage import (
    EmptyFileError,
    FileTooLargeError,
    LocalFileStorage,
    UnsafeStorageKeyError,
)


class MemoryStream:
    """Async byte stream with deterministic chunk behavior."""

    def __init__(self, content: bytes) -> None:
        self._content = content
        self._position = 0

    async def read(self, size: int = -1) -> bytes:
        if self._position >= len(self._content):
            return b""
        end = len(self._content) if size < 0 else self._position + size
        chunk = self._content[self._position : end]
        self._position = end
        return chunk


class FailingStream:
    """Source that fails after one partial chunk."""

    def __init__(self) -> None:
        self._reads = 0

    async def read(self, size: int = -1) -> bytes:
        self._reads += 1
        if self._reads == 1:
            return b"partial"
        raise OSError("synthetic source failure")


def _matches(path: Path, pattern: str) -> list[Path]:
    return list(path.rglob(pattern))


async def test_storage_streams_hashes_and_publishes_beneath_root(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)
    stored = await storage.store(
        MemoryStream(b"private text"),
        storage_key="kb/document.txt",
        max_bytes=100,
    )

    assert stored.size_bytes == 12
    assert stored.sha256 == "66c279b1e928c2dd31a931998f6239872230eb459535a6ae9ccef3b5dcb8c99c"
    assert stored.prefix == b"private text"
    assert (tmp_path / "kb/document.txt").read_bytes() == b"private text"
    assert not _matches(tmp_path, "*.tmp")


async def test_storage_rejects_empty_file_and_cleans_temporary_file(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    with pytest.raises(EmptyFileError):
        await storage.store(MemoryStream(b""), storage_key="kb/empty.txt", max_bytes=100)

    assert not _matches(tmp_path, "*.*")


async def test_storage_rejects_oversized_file_and_cleans_temporary_file(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    with pytest.raises(FileTooLargeError):
        await storage.store(MemoryStream(b"too large"), storage_key="kb/file.txt", max_bytes=3)

    assert not (tmp_path / "kb/file.txt").exists()
    assert not _matches(tmp_path, "*.tmp")


@pytest.mark.parametrize(
    "storage_key",
    ["../outside.txt", "/absolute.txt", "kb/../../outside.txt", "."],
)
async def test_storage_rejects_path_traversal(tmp_path: Path, storage_key: str) -> None:
    storage = LocalFileStorage(tmp_path)

    with pytest.raises(UnsafeStorageKeyError):
        await storage.store(MemoryStream(b"data"), storage_key=storage_key, max_bytes=100)

    assert not (tmp_path.parent / "outside.txt").exists()


async def test_storage_delete_is_idempotent(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)
    await storage.store(MemoryStream(b"data"), storage_key="kb/file.txt", max_bytes=100)

    await storage.delete("kb/file.txt")
    await storage.delete("kb/file.txt")

    assert not (tmp_path / "kb/file.txt").exists()


async def test_source_failure_removes_partial_file(tmp_path: Path) -> None:
    storage = LocalFileStorage(tmp_path)

    with pytest.raises(OSError, match="synthetic"):
        await storage.store(FailingStream(), storage_key="kb/file.txt", max_bytes=100)

    assert not (tmp_path / "kb/file.txt").exists()
    assert not _matches(tmp_path, "*.tmp")
