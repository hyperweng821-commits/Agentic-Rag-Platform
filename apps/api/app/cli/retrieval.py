"""Authenticated developer inspection command for internal AF-3B retrieval."""

from __future__ import annotations

import argparse
import asyncio
import getpass
from collections.abc import Sequence
from datetime import timedelta
from uuid import UUID

from app.core.config import Settings, get_settings
from app.db.session import async_session_maker, dispose_engine
from app.ingestion.embeddings import OllamaEmbeddingModel
from app.retrieval import (
    ChromaDenseRetrievalAdapter,
    FinalCandidateValidatorLoader,
    HybridRetrievalResult,
    HybridRetrievalService,
    PostgresFinalAuthoritativeLoader,
    PostgresRetrievalAccess,
    RetrievalAuthenticationError,
    RetrievalRequestValidationError,
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
    ScopedKeywordRetrievalService,
)
from app.security.authentication import (
    AuthenticationError,
    AuthenticationService,
    SessionAuthenticationProof,
)
from app.security.passwords import PasswordWorkLimiter


class RetrievalInspectionError(Exception):
    """Safe command-line failure with no credential or Provider detail."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect bounded internal hybrid retrieval.")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Run authenticated AF-3B retrieval.")
    inspect.add_argument("--knowledge-base-id", required=True, type=UUID)
    inspect.add_argument("--requested-count", type=int, default=10)
    return parser


async def _authenticate_session(
    *,
    settings: Settings,
    session_token: str,
) -> SessionAuthenticationProof:
    limiter = PasswordWorkLimiter(settings.argon2_max_concurrency)
    try:
        async with async_session_maker() as session:
            service = AuthenticationService(
                session,
                session_ttl=timedelta(seconds=settings.session_ttl_seconds),
                password_work_limiter=limiter,
            )
            return await service.authenticate_session_with_proof(session_token)
    finally:
        limiter.shutdown()


async def _inspect(
    args: argparse.Namespace,
    *,
    session_token: str,
    query: str,
) -> HybridRetrievalResult:
    settings = get_settings()
    if settings.chroma_collection_uuid is None:
        raise RetrievalInspectionError("CHROMA_COLLECTION_UUID is required for retrieval.")
    proof = await _authenticate_session(settings=settings, session_token=session_token)
    embedding = OllamaEmbeddingModel(
        base_url=settings.ollama_base_url,
        model_id=settings.ollama_embed_model,
        dimension=settings.embedding_dimension,
        batch_size=settings.embedding_batch_size,
        timeout_seconds=settings.embedding_request_timeout_seconds,
    )
    dense = ChromaDenseRetrievalAdapter(
        host=settings.chroma_host,
        http_port=settings.chroma_http_port,
        ssl=settings.chroma_ssl,
        collection_uuid=settings.chroma_collection_uuid,
        timeout_seconds=settings.chroma_retrieval_timeout_seconds,
    )
    try:
        service = HybridRetrievalService(
            keyword_service=ScopedKeywordRetrievalService(
                PostgresRetrievalAccess(async_session_maker)
            ),
            embedding_model=embedding,
            dense_retrieval=dense,
            final_validator=FinalCandidateValidatorLoader(
                PostgresFinalAuthoritativeLoader(async_session_maker)
            ),
        )
        return await service.retrieve(
            proof=proof,
            knowledge_base_id=args.knowledge_base_id,
            payload={"query": query, "requested_count": args.requested_count},
        )
    finally:
        await embedding.close()
        await dense.close()


def _print_result(result: HybridRetrievalResult) -> None:
    print(f"records={len(result.records)}")
    for item in result.records:
        print(
            " ".join(
                (
                    f"fused_rank={item.fused_rank}",
                    f"keyword_rank={item.keyword_rank}",
                    f"dense_rank={item.dense_rank}",
                )
            )
        )


async def _run_and_dispose(
    args: argparse.Namespace,
    *,
    session_token: str,
    query: str,
) -> HybridRetrievalResult:
    try:
        return await _inspect(args, session_token=session_token, query=query)
    finally:
        await dispose_engine()


def main(argv: Sequence[str] | None = None) -> int:
    """Prompt for private inputs, run one authenticated retrieval, and print diagnostics."""
    args = _build_parser().parse_args(argv)
    session_token = getpass.getpass("Session token: ")
    query = getpass.getpass("Retrieval query: ")
    try:
        result = asyncio.run(_run_and_dispose(args, session_token=session_token, query=query))
    except (AuthenticationError, RetrievalAuthenticationError):
        print("Error: authentication failed.")
        return 2
    except RetrievalTargetNotFoundError:
        print("Error: retrieval target was not found.")
        return 2
    except RetrievalRequestValidationError:
        print("Error: retrieval request validation failed.")
        return 2
    except (RetrievalInspectionError, RetrievalUnavailableError):
        print("Error: retrieval is unavailable.")
        return 2
    _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
