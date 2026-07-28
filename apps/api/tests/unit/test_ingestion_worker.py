"""Deterministic tests for the AF-2B ingestion worker CLI."""

from __future__ import annotations

import asyncio
import os
import signal
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.core.config import Settings
from app.ingestion.vector_store import VectorStoreInputError, VectorStoreRequestError
from app.services.ingestion_processing import RebuildFailure, RebuildResult
from app.workers import ingestion_worker
from app.workers.ingestion_worker import (
    WorkerArguments,
    WorkerRuntime,
    parse_arguments,
    production_runtime,
    run_command,
    run_worker,
)


class StubProcessingService:
    """Small worker-facing fake with explicit call records."""

    def __init__(
        self,
        *,
        process_results: list[bool] | None = None,
        rebuild_result: RebuildResult | None = None,
    ) -> None:
        self.process_results = process_results or []
        self.rebuild_result = rebuild_result or RebuildResult(1, 1, 2)
        self.process_calls: list[int] = []
        self.document_rebuild_calls: list[tuple[UUID, int]] = []
        self.knowledge_base_rebuild_calls: list[tuple[UUID, int, int]] = []

    async def process_next(self, *, recovery_limit: int = 32) -> bool:
        self.process_calls.append(recovery_limit)
        return self.process_results.pop(0) if self.process_results else False

    async def rebuild_document(
        self,
        document_id: UUID,
        *,
        max_chunks: int,
    ) -> RebuildResult:
        self.document_rebuild_calls.append((document_id, max_chunks))
        return self.rebuild_result

    async def rebuild_knowledge_base(
        self,
        knowledge_base_id: UUID,
        *,
        max_documents: int,
        max_chunks_per_document: int,
    ) -> RebuildResult:
        self.knowledge_base_rebuild_calls.append(
            (knowledge_base_id, max_documents, max_chunks_per_document)
        )
        return self.rebuild_result


def _runtime_factory(
    service: StubProcessingService,
    lifecycle: list[str] | None = None,
) -> Any:
    @asynccontextmanager
    async def factory(_: Settings) -> AsyncIterator[WorkerRuntime]:
        if lifecycle is not None:
            lifecycle.append("entered")
        try:
            yield WorkerRuntime(service=service, worker_id="test-worker")
        finally:
            if lifecycle is not None:
                lifecycle.append("closed")

    return factory


def _worker_arguments(*, once: bool = False) -> WorkerArguments:
    return WorkerArguments(
        once=once,
        rebuild_document_id=None,
        rebuild_knowledge_base_id=None,
        max_chunks=10_000,
        max_documents=1_000,
        max_chunks_per_document=10_000,
    )


def test_parse_arguments_supports_default_polling_and_one_shot() -> None:
    continuous = parse_arguments([])
    one_shot = parse_arguments(["--once"])

    assert continuous == _worker_arguments()
    assert one_shot == _worker_arguments(once=True)


def test_parse_arguments_supports_bounded_document_rebuild() -> None:
    document_id = uuid4()

    arguments = parse_arguments(
        ["rebuild", "--document-id", str(document_id), "--max-chunks", "27"]
    )

    assert arguments.rebuild_document_id == document_id
    assert arguments.rebuild_knowledge_base_id is None
    assert arguments.max_chunks == 27
    assert arguments.once is False


def test_parse_arguments_supports_bounded_knowledge_base_rebuild() -> None:
    knowledge_base_id = uuid4()

    arguments = parse_arguments(
        [
            "rebuild",
            "--knowledge-base-id",
            str(knowledge_base_id),
            "--max-documents",
            "12",
            "--max-chunks-per-document",
            "34",
        ]
    )

    assert arguments.rebuild_document_id is None
    assert arguments.rebuild_knowledge_base_id == knowledge_base_id
    assert arguments.max_documents == 12
    assert arguments.max_chunks_per_document == 34


@pytest.mark.parametrize(
    "argv",
    [
        ["rebuild"],
        ["--once", "rebuild", "--document-id", str(uuid4())],
        ["rebuild", "--document-id", str(uuid4()), "--max-chunks", "0"],
        ["rebuild", "--document-id", str(uuid4()), "--max-chunks", "100001"],
        ["rebuild", "--knowledge-base-id", str(uuid4()), "--max-documents", "not-an-int"],
    ],
)
def test_parse_arguments_rejects_ambiguous_or_unbounded_work(argv: list[str]) -> None:
    with pytest.raises(SystemExit, match="2"):
        parse_arguments(argv)


def test_worker_id_is_sanitized_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(socket, "gethostname", lambda: "host name/" * 40)
    monkeypatch.setattr(os, "getpid", lambda: 123456)
    monkeypatch.setattr(
        ingestion_worker,
        "uuid4",
        lambda: UUID("12345678-1234-5678-1234-567812345678"),
    )

    worker_id = ingestion_worker._worker_id()

    assert len(worker_id) == 255
    assert " " not in worker_id
    assert "/" not in worker_id
    assert worker_id.endswith(":123456:123456781234")


@pytest.mark.parametrize(("result", "expected"), [(True, 1), (False, 0)])
async def test_one_shot_checks_exactly_one_job(result: bool, expected: int) -> None:
    service = StubProcessingService(process_results=[result])
    stop_event = asyncio.Event()

    processed = await run_worker(
        service,
        once=True,
        stop_event=stop_event,
        poll_interval_seconds=15.0,
    )

    assert processed == expected
    assert service.process_calls == [32]


async def test_idle_polling_waits_without_busy_loop() -> None:
    service = StubProcessingService(process_results=[False])
    stop_event = asyncio.Event()
    waiting = asyncio.Event()
    release_wait = asyncio.Event()
    observed_intervals: list[float] = []

    async def deterministic_wait(_: asyncio.Event, interval_seconds: float) -> None:
        observed_intervals.append(interval_seconds)
        waiting.set()
        await release_wait.wait()

    worker_task = asyncio.create_task(
        run_worker(
            service,
            once=False,
            stop_event=stop_event,
            poll_interval_seconds=4.25,
            idle_wait=deterministic_wait,
        )
    )
    await waiting.wait()

    assert service.process_calls == [32]
    stop_event.set()
    release_wait.set()

    assert await worker_task == 0
    assert observed_intervals == [4.25]
    assert service.process_calls == [32]


async def test_stop_event_cancels_and_awaits_in_flight_processing() -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()
    stop_event = asyncio.Event()

    class BlockingService(StubProcessingService):
        async def process_next(self, *, recovery_limit: int = 32) -> bool:
            self.process_calls.append(recovery_limit)
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise
            return True

    service = BlockingService()
    worker_task = asyncio.create_task(
        run_worker(
            service,
            once=False,
            stop_event=stop_event,
            poll_interval_seconds=1.0,
        )
    )
    await started.wait()

    stop_event.set()

    assert await worker_task == 0
    assert cancelled.is_set()
    assert service.process_calls == [32]


async def test_external_cancellation_propagates_after_child_is_joined() -> None:
    started = asyncio.Event()
    child_cancelled = asyncio.Event()
    stop_event = asyncio.Event()

    class BlockingService(StubProcessingService):
        async def process_next(self, *, recovery_limit: int = 32) -> bool:
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                child_cancelled.set()
                raise
            return True

    worker_task = asyncio.create_task(
        run_worker(
            BlockingService(),
            once=False,
            stop_event=stop_event,
            poll_interval_seconds=1.0,
        )
    )
    await started.wait()

    worker_task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await worker_task
    assert child_cancelled.is_set()


async def test_run_command_uses_configured_poll_interval_and_closes_runtime() -> None:
    settings = Settings(_env_file=None, ingestion_worker_poll_interval_seconds=3.5)
    service = StubProcessingService(process_results=[False])
    lifecycle: list[str] = []
    stop_event = asyncio.Event()
    observed_intervals: list[float] = []

    async def stop_after_idle(_: asyncio.Event, interval_seconds: float) -> None:
        observed_intervals.append(interval_seconds)
        stop_event.set()

    exit_code = await run_command(
        _worker_arguments(),
        settings=settings,
        runtime_factory=_runtime_factory(service, lifecycle),
        stop_event=stop_event,
        install_signal_handlers=False,
        idle_wait=stop_after_idle,
    )

    assert exit_code == 0
    assert observed_intervals == [3.5]
    assert lifecycle == ["entered", "closed"]


async def test_document_rebuild_reports_failure_as_nonzero() -> None:
    document_id = uuid4()
    failure = RebuildFailure(
        document_id=document_id,
        code="EMBEDDING_FAILED",
        safe_message="The derived index could not be rebuilt.",
    )
    service = StubProcessingService(rebuild_result=RebuildResult(1, 0, 0, failures=(failure,)))
    arguments = WorkerArguments(
        once=False,
        rebuild_document_id=document_id,
        rebuild_knowledge_base_id=None,
        max_chunks=123,
        max_documents=1_000,
        max_chunks_per_document=10_000,
    )

    exit_code = await run_command(
        arguments,
        settings=Settings(_env_file=None),
        runtime_factory=_runtime_factory(service),
        install_signal_handlers=False,
    )

    assert exit_code == 1
    assert service.document_rebuild_calls == [(document_id, 123)]


async def test_knowledge_base_rebuild_reports_success() -> None:
    knowledge_base_id = uuid4()
    service = StubProcessingService(rebuild_result=RebuildResult(4, 3, 18))
    arguments = WorkerArguments(
        once=False,
        rebuild_document_id=None,
        rebuild_knowledge_base_id=knowledge_base_id,
        max_chunks=10_000,
        max_documents=44,
        max_chunks_per_document=55,
    )

    exit_code = await run_command(
        arguments,
        settings=Settings(_env_file=None),
        runtime_factory=_runtime_factory(service),
        install_signal_handlers=False,
    )

    assert exit_code == 0
    assert service.knowledge_base_rebuild_calls == [(knowledge_base_id, 44, 55)]


async def test_stop_event_cancels_rebuild_and_closes_runtime() -> None:
    document_id = uuid4()
    started = asyncio.Event()
    cancelled = asyncio.Event()
    stop_event = asyncio.Event()
    lifecycle: list[str] = []

    class BlockingRebuildService(StubProcessingService):
        async def rebuild_document(
            self,
            document_id: UUID,
            *,
            max_chunks: int,
        ) -> RebuildResult:
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise
            return RebuildResult(1, 1, 1)

    arguments = WorkerArguments(
        once=False,
        rebuild_document_id=document_id,
        rebuild_knowledge_base_id=None,
        max_chunks=100,
        max_documents=1_000,
        max_chunks_per_document=10_000,
    )
    command_task = asyncio.create_task(
        run_command(
            arguments,
            settings=Settings(_env_file=None),
            runtime_factory=_runtime_factory(BlockingRebuildService(), lifecycle),
            stop_event=stop_event,
            install_signal_handlers=False,
        )
    )
    await started.wait()

    stop_event.set()

    assert await command_task == 130
    assert cancelled.is_set()
    assert lifecycle == ["entered", "closed"]


async def test_poll_wait_returns_immediately_when_already_stopped() -> None:
    stop_event = asyncio.Event()
    stop_event.set()

    await ingestion_worker._wait_for_next_poll(stop_event, 60.0)


@pytest.mark.parametrize("received_signal", [signal.SIGINT, signal.SIGTERM])
async def test_supported_signal_handlers_request_stop_and_are_removed(
    monkeypatch: pytest.MonkeyPatch,
    received_signal: signal.Signals,
) -> None:
    stop_event = asyncio.Event()

    class FakeLoop:
        def __init__(self) -> None:
            self.handlers: dict[
                signal.Signals,
                tuple[Any, tuple[signal.Signals, ...]],
            ] = {}
            self.removed: list[signal.Signals] = []

        def add_signal_handler(
            self,
            installed_signal: signal.Signals,
            callback: Any,
            *args: signal.Signals,
        ) -> None:
            self.handlers[installed_signal] = (callback, args)

        def remove_signal_handler(self, installed_signal: signal.Signals) -> bool:
            self.removed.append(installed_signal)
            return True

    loop = FakeLoop()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    remove_handlers = ingestion_worker._install_signal_handlers(stop_event)
    callback, args = loop.handlers[received_signal]
    callback(*args)
    remove_handlers()

    assert stop_event.is_set()
    assert loop.removed == [signal.SIGINT, signal.SIGTERM]


async def test_unsupported_signal_handler_is_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stop_event = asyncio.Event()

    class FakeLoop:
        def __init__(self) -> None:
            self.handlers: dict[
                signal.Signals,
                tuple[Any, tuple[signal.Signals, ...]],
            ] = {}
            self.removed: list[signal.Signals] = []

        def add_signal_handler(
            self,
            received_signal: signal.Signals,
            callback: Any,
            *args: signal.Signals,
        ) -> None:
            if received_signal is signal.SIGINT:
                raise NotImplementedError
            self.handlers[received_signal] = (callback, args)

        def remove_signal_handler(self, received_signal: signal.Signals) -> bool:
            self.removed.append(received_signal)
            return True

    loop = FakeLoop()
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)

    remove_handlers = ingestion_worker._install_signal_handlers(stop_event)
    callback, args = loop.handlers[signal.SIGTERM]
    callback(*args)
    remove_handlers()

    assert stop_event.is_set()
    assert loop.removed == [signal.SIGTERM]


async def test_production_runtime_initializes_and_closes_owned_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeEmbedding:
        def __init__(self, **_: object) -> None:
            calls.append("embedding-created")

        async def close(self) -> None:
            calls.append("embedding-closed")

    class FakeVector:
        def __init__(self, **_: object) -> None:
            calls.append("vector-created")

        async def close(self) -> None:
            calls.append("vector-closed")

    class FakeService:
        def __init__(self, **_: object) -> None:
            calls.append("service-created")

        async def initialize(self) -> None:
            calls.append("service-initialized")

        async def close(self) -> None:
            calls.append("service-closed")

    async def fake_dispose_engine() -> None:
        calls.append("engine-disposed")

    monkeypatch.setattr(ingestion_worker, "OllamaEmbeddingModel", FakeEmbedding)
    monkeypatch.setattr(ingestion_worker, "ChromaVectorStore", FakeVector)
    monkeypatch.setattr(ingestion_worker, "IngestionProcessingService", FakeService)
    monkeypatch.setattr(ingestion_worker, "dispose_engine", fake_dispose_engine)
    monkeypatch.setattr(ingestion_worker, "_worker_id", lambda: "worker-id")

    async with production_runtime(Settings(_env_file=None)) as runtime:
        assert runtime.worker_id == "worker-id"

    assert calls == [
        "embedding-created",
        "vector-created",
        "service-created",
        "service-initialized",
        "service-closed",
        "engine-disposed",
    ]


async def test_production_runtime_closes_embedding_when_vector_construction_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeEmbedding:
        def __init__(self, **_: object) -> None:
            calls.append("embedding-created")

        async def close(self) -> None:
            calls.append("embedding-closed")

    def fail_vector(**_: object) -> None:
        raise VectorStoreInputError("synthetic invalid vector configuration")

    async def fake_dispose_engine() -> None:
        calls.append("engine-disposed")

    monkeypatch.setattr(ingestion_worker, "OllamaEmbeddingModel", FakeEmbedding)
    monkeypatch.setattr(ingestion_worker, "ChromaVectorStore", fail_vector)
    monkeypatch.setattr(ingestion_worker, "dispose_engine", fake_dispose_engine)

    with pytest.raises(VectorStoreInputError, match="synthetic"):
        async with production_runtime(Settings(_env_file=None)):
            pytest.fail("runtime must not start")

    assert calls == ["embedding-created", "embedding-closed", "engine-disposed"]


def test_main_returns_nonzero_for_expected_startup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_command(*_: object, **__: object) -> int:
        raise VectorStoreRequestError("synthetic dependency failure")

    monkeypatch.setattr(ingestion_worker, "run_command", fail_command)
    monkeypatch.setattr(ingestion_worker, "configure_logging", lambda _: None)

    assert ingestion_worker.main(["--once"]) == 1


def test_main_reraises_unexpected_programming_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_command(*_: object, **__: object) -> int:
        raise RuntimeError("synthetic programming defect")

    monkeypatch.setattr(ingestion_worker, "run_command", fail_command)
    monkeypatch.setattr(ingestion_worker, "configure_logging", lambda _: None)

    with pytest.raises(RuntimeError, match="programming defect"):
        ingestion_worker.main(["--once"])


def test_main_normalizes_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def interrupt_command(*_: object, **__: object) -> int:
        raise KeyboardInterrupt

    monkeypatch.setattr(ingestion_worker, "run_command", interrupt_command)
    monkeypatch.setattr(ingestion_worker, "configure_logging", lambda _: None)

    assert ingestion_worker.main(["--once"]) == 130
