"""CLI worker for durable ingestion jobs and bounded vector-index rebuilds."""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import socket
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol
from uuid import UUID, uuid4

import structlog
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import async_session_maker, dispose_engine
from app.ingestion.chunking import ChunkingConfig, DeterministicChunker
from app.ingestion.document_parsing import create_default_parser_registry
from app.ingestion.embeddings import EmbeddingError, OllamaEmbeddingModel
from app.ingestion.storage import LocalFileStorage, StorageError
from app.ingestion.text_normalization import TextNormalizer
from app.ingestion.vector_store import ChromaVectorStore, VectorStoreError
from app.services.ingestion_processing import (
    IngestionProcessingError,
    IngestionProcessingService,
    RebuildResult,
)

logger = structlog.get_logger(__name__)

_DEFAULT_DOCUMENT_CHUNK_LIMIT = 10_000
_MAX_DOCUMENT_CHUNK_LIMIT = 100_000
_DEFAULT_KNOWLEDGE_BASE_DOCUMENT_LIMIT = 1_000
_MAX_KNOWLEDGE_BASE_DOCUMENT_LIMIT = 10_000
_RECOVERY_LIMIT = 32


class ProcessingService(Protocol):
    """Worker-facing ingestion operations."""

    async def process_next(self, *, recovery_limit: int = 32) -> bool:
        """Process at most one durable job and report whether one was claimed."""
        ...

    async def rebuild_document(self, document_id: UUID, *, max_chunks: int) -> RebuildResult:
        """Rebuild vectors for one PostgreSQL-authoritative document."""
        ...

    async def rebuild_knowledge_base(
        self,
        knowledge_base_id: UUID,
        *,
        max_documents: int,
        max_chunks_per_document: int,
    ) -> RebuildResult:
        """Rebuild vectors for one bounded knowledge base."""
        ...


@dataclass(frozen=True, slots=True)
class WorkerRuntime:
    """Initialized dependencies owned for the lifetime of one CLI command."""

    service: ProcessingService
    worker_id: str


@dataclass(frozen=True, slots=True)
class WorkerArguments:
    """Validated CLI arguments independent from argparse internals."""

    once: bool
    rebuild_document_id: UUID | None
    rebuild_knowledge_base_id: UUID | None
    max_chunks: int
    max_documents: int
    max_chunks_per_document: int


IdleWait = Callable[[asyncio.Event, float], Awaitable[None]]
RuntimeFactory = Callable[[Settings], AbstractAsyncContextManager[WorkerRuntime]]


def _bounded_positive_int(*, maximum: int) -> Callable[[str], int]:
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("must be an integer") from exc
        if not 1 <= parsed <= maximum:
            raise argparse.ArgumentTypeError(f"must be between 1 and {maximum}")
        return parsed

    return parse


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Process durable ingestion jobs or rebuild the derived vector index.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="check for at most one ingestion job, process it if present, and exit",
    )
    subcommands = parser.add_subparsers(dest="command")
    rebuild = subcommands.add_parser(
        "rebuild",
        help="rebuild derived vectors from PostgreSQL-authoritative chunks",
    )
    target = rebuild.add_mutually_exclusive_group(required=True)
    target.add_argument("--document-id", type=UUID)
    target.add_argument("--knowledge-base-id", type=UUID)
    rebuild.add_argument(
        "--max-chunks",
        type=_bounded_positive_int(maximum=_MAX_DOCUMENT_CHUNK_LIMIT),
        default=_DEFAULT_DOCUMENT_CHUNK_LIMIT,
        help=f"document chunk limit (default: {_DEFAULT_DOCUMENT_CHUNK_LIMIT})",
    )
    rebuild.add_argument(
        "--max-documents",
        type=_bounded_positive_int(maximum=_MAX_KNOWLEDGE_BASE_DOCUMENT_LIMIT),
        default=_DEFAULT_KNOWLEDGE_BASE_DOCUMENT_LIMIT,
        help=(f"knowledge-base document limit (default: {_DEFAULT_KNOWLEDGE_BASE_DOCUMENT_LIMIT})"),
    )
    rebuild.add_argument(
        "--max-chunks-per-document",
        type=_bounded_positive_int(maximum=_MAX_DOCUMENT_CHUNK_LIMIT),
        default=_DEFAULT_DOCUMENT_CHUNK_LIMIT,
        help=(
            "per-document chunk limit for knowledge-base rebuilds "
            f"(default: {_DEFAULT_DOCUMENT_CHUNK_LIMIT})"
        ),
    )
    return parser


def parse_arguments(argv: Sequence[str] | None = None) -> WorkerArguments:
    """Parse and validate one worker command."""
    namespace = _build_parser().parse_args(argv)
    command = namespace.command
    once = bool(namespace.once)
    if command == "rebuild" and once:
        _build_parser().error("--once cannot be combined with rebuild")
    if command != "rebuild":
        return WorkerArguments(
            once=once,
            rebuild_document_id=None,
            rebuild_knowledge_base_id=None,
            max_chunks=_DEFAULT_DOCUMENT_CHUNK_LIMIT,
            max_documents=_DEFAULT_KNOWLEDGE_BASE_DOCUMENT_LIMIT,
            max_chunks_per_document=_DEFAULT_DOCUMENT_CHUNK_LIMIT,
        )
    return WorkerArguments(
        once=False,
        rebuild_document_id=namespace.document_id,
        rebuild_knowledge_base_id=namespace.knowledge_base_id,
        max_chunks=namespace.max_chunks,
        max_documents=namespace.max_documents,
        max_chunks_per_document=namespace.max_chunks_per_document,
    )


def _worker_id() -> str:
    """Create an operational identity without using document data."""
    raw_hostname = socket.gethostname() or "unknown-host"
    hostname = "".join(
        character if character.isascii() and (character.isalnum() or character in ".-") else "_"
        for character in raw_hostname
    )
    suffix = f":{os.getpid()}:{uuid4().hex[:12]}"
    return f"{hostname[: 255 - len(suffix)]}{suffix}"


@asynccontextmanager
async def production_runtime(settings: Settings) -> AsyncIterator[WorkerRuntime]:
    """Create external adapters and close every resource on all exit paths."""
    embedding_model = OllamaEmbeddingModel(
        base_url=settings.ollama_base_url,
        model_id=settings.ollama_embed_model,
        dimension=settings.embedding_dimension,
        batch_size=settings.embedding_batch_size,
        timeout_seconds=settings.embedding_request_timeout_seconds,
    )
    vector_store: ChromaVectorStore | None = None
    service: IngestionProcessingService | None = None
    try:
        vector_store = ChromaVectorStore(
            host=settings.chroma_host,
            http_port=settings.chroma_http_port,
            ssl=settings.chroma_ssl,
            collection_name=settings.chroma_collection_name,
            batch_size=settings.ingestion_rebuild_batch_size,
            timeout_seconds=settings.embedding_request_timeout_seconds,
        )
        worker_id = _worker_id()
        service = IngestionProcessingService(
            session_factory=async_session_maker,
            storage=LocalFileStorage(settings.upload_root),
            parser_registry=create_default_parser_registry(),
            normalizer=TextNormalizer(),
            chunker=DeterministicChunker(
                ChunkingConfig(
                    chunk_size=settings.chunk_size_chars,
                    overlap=settings.chunk_overlap_chars,
                )
            ),
            embedding_model=embedding_model,
            vector_store=vector_store,
            worker_id=worker_id,
            lease_duration=timedelta(seconds=settings.ingestion_lease_seconds),
            retry_delay=timedelta(seconds=settings.ingestion_retry_delay_seconds),
            source_max_bytes=settings.max_upload_size_bytes,
            rebuild_batch_size=settings.ingestion_rebuild_batch_size,
        )
        await service.initialize()
        yield WorkerRuntime(service=service, worker_id=worker_id)
    finally:
        try:
            if service is not None:
                await service.close()
            else:
                await embedding_model.close()
        finally:
            try:
                if service is None and vector_store is not None:
                    await vector_store.close()
            finally:
                await dispose_engine()


async def _wait_for_next_poll(stop_event: asyncio.Event, interval_seconds: float) -> None:
    with suppress(TimeoutError):
        await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)


async def _await_until_stopped[ResultT](
    operation: Awaitable[ResultT],
    stop_event: asyncio.Event,
) -> ResultT | None:
    """Await one operation, cancelling and joining it when a stop is requested."""
    processing = asyncio.ensure_future(operation)
    stopping = asyncio.create_task(stop_event.wait())
    try:
        done, _ = await asyncio.wait(
            (processing, stopping),
            return_when=asyncio.FIRST_COMPLETED,
        )
        if processing in done:
            return await processing

        processing.cancel()
        with suppress(asyncio.CancelledError):
            await processing
        return None
    except asyncio.CancelledError:
        processing.cancel()
        with suppress(asyncio.CancelledError):
            await processing
        raise
    finally:
        stopping.cancel()
        with suppress(asyncio.CancelledError):
            await stopping


async def run_worker(
    service: ProcessingService,
    *,
    once: bool,
    stop_event: asyncio.Event,
    poll_interval_seconds: float,
    idle_wait: IdleWait = _wait_for_next_poll,
) -> int:
    """Process durable work, waiting on the stop event whenever the queue is idle."""
    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be positive")

    processed = 0
    while not stop_event.is_set():
        did_process = await _await_until_stopped(
            service.process_next(recovery_limit=_RECOVERY_LIMIT),
            stop_event,
        )
        if did_process is None:
            break
        processed += int(did_process)
        if once:
            break
        if not did_process:
            await idle_wait(stop_event, poll_interval_seconds)
    return processed


def _install_signal_handlers(stop_event: asyncio.Event) -> Callable[[], None]:
    loop = asyncio.get_running_loop()
    installed: list[signal.Signals] = []

    def request_stop(received_signal: signal.Signals) -> None:
        logger.info("ingestion_worker_stop_requested", signal=received_signal.name)
        stop_event.set()

    for received_signal in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(received_signal, request_stop, received_signal)
        except (NotImplementedError, RuntimeError):
            continue
        installed.append(received_signal)

    def remove_handlers() -> None:
        for received_signal in installed:
            loop.remove_signal_handler(received_signal)

    return remove_handlers


def _result_has_failures(result: RebuildResult) -> bool:
    return bool(result.failures)


async def run_command(
    arguments: WorkerArguments,
    *,
    settings: Settings,
    runtime_factory: RuntimeFactory = production_runtime,
    stop_event: asyncio.Event | None = None,
    install_signal_handlers: bool = True,
    idle_wait: IdleWait = _wait_for_next_poll,
) -> int:
    """Execute a parsed CLI command and return its process exit code."""
    async with runtime_factory(settings) as runtime:
        worker_stop = stop_event or asyncio.Event()
        remove_handlers = (
            _install_signal_handlers(worker_stop) if install_signal_handlers else lambda: None
        )
        try:
            if arguments.rebuild_document_id is not None:
                result = await _await_until_stopped(
                    runtime.service.rebuild_document(
                        arguments.rebuild_document_id,
                        max_chunks=arguments.max_chunks,
                    ),
                    worker_stop,
                )
                if result is None:
                    return 130
                logger.info(
                    "document_vector_rebuild_finished",
                    document_id=str(arguments.rebuild_document_id),
                    documents_seen=result.documents_seen,
                    documents_indexed=result.documents_indexed,
                    chunks_indexed=result.chunks_indexed,
                    failures=len(result.failures),
                )
                return int(_result_has_failures(result))

            if arguments.rebuild_knowledge_base_id is not None:
                result = await _await_until_stopped(
                    runtime.service.rebuild_knowledge_base(
                        arguments.rebuild_knowledge_base_id,
                        max_documents=arguments.max_documents,
                        max_chunks_per_document=arguments.max_chunks_per_document,
                    ),
                    worker_stop,
                )
                if result is None:
                    return 130
                logger.info(
                    "knowledge_base_vector_rebuild_finished",
                    knowledge_base_id=str(arguments.rebuild_knowledge_base_id),
                    documents_seen=result.documents_seen,
                    documents_indexed=result.documents_indexed,
                    chunks_indexed=result.chunks_indexed,
                    failures=len(result.failures),
                )
                return int(_result_has_failures(result))

            logger.info(
                "ingestion_worker_started",
                worker_id=runtime.worker_id,
                once=arguments.once,
            )
            processed = await run_worker(
                runtime.service,
                once=arguments.once,
                stop_event=worker_stop,
                poll_interval_seconds=settings.ingestion_worker_poll_interval_seconds,
                idle_wait=idle_wait,
            )
        finally:
            remove_handlers()
        logger.info(
            "ingestion_worker_stopped",
            worker_id=runtime.worker_id,
            processed_jobs=processed,
        )
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the worker CLI and normalize startup or command failures."""
    arguments = parse_arguments(argv)
    try:
        settings = get_settings()
        configure_logging(settings)
        return asyncio.run(run_command(arguments, settings=settings))
    except KeyboardInterrupt:
        return 130
    except (
        EmbeddingError,
        IngestionProcessingError,
        SQLAlchemyError,
        StorageError,
        ValidationError,
        VectorStoreError,
    ) as exc:
        logger.error(
            "ingestion_worker_command_failed",
            error_type=type(exc).__name__,
        )
        return 1
    except Exception as exc:
        logger.error(
            "ingestion_worker_unexpected_failure",
            error_type=type(exc).__name__,
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
