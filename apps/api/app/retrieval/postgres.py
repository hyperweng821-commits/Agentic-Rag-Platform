"""Scoped PostgreSQL adapter for AF-3A initial access and keyword candidates."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import Select, bindparam, exists, func, literal, literal_column, select, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from app.db.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    KnowledgeBase,
    KnowledgeBaseMembership,
    KnowledgeBaseRole,
    User,
    UserSession,
)
from app.retrieval.service import (
    CandidateBatch,
    KeywordCandidate,
    RetrievalAuthenticationError,
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
    _canonical_candidate_batches,
    _InternalAuthoritativeRetrievalRecord,
    _TrustedAuthoritativeProvenance,
    _UntrustedDocumentContent,
)
from app.security.authentication import SessionAuthenticationProof

MAX_KEYWORD_CANDIDATES = 128

Clock = Callable[[], datetime]

_READ_ROLE_VALUES = (
    KnowledgeBaseRole.OWNER.value,
    KnowledgeBaseRole.EDITOR.value,
    KnowledgeBaseRole.VIEWER.value,
)
_VALID_CONTENT_SHA256_PATTERN = r"^[0-9a-f]{64}$"


def _utc_now() -> datetime:
    return datetime.now(UTC)


class PostgresRetrievalAccess:
    """Own two short sessions and never expose an unrestricted retrieval query."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        clock: Clock = _utc_now,
    ) -> None:
        self._session_factory = session_factory
        self._clock = clock

    async def verify_initial_access(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
    ) -> None:
        """Revalidate the proof, active user, exact target, membership, and reads."""
        now = self._now()
        try:
            async with self._session_factory() as session, session.begin():
                authentication_valid = await session.scalar(
                    _initial_authentication_statement(),
                    _proof_parameters(proof=proof, now=now),
                )
                if authentication_valid is None:
                    raise RetrievalAuthenticationError

                target_accessible = await session.scalar(
                    _initial_target_statement(),
                    {
                        "knowledge_base_id": knowledge_base_id,
                        "user_id": proof.principal.user_id,
                    },
                )
                if target_accessible is None:
                    raise RetrievalTargetNotFoundError
        except SQLAlchemyError:
            pass
        else:
            return

        raise RetrievalUnavailableError

    async def scoped_keyword_candidates(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        normalized_query: str,
    ) -> tuple[KeywordCandidate, ...]:
        """Return at most 128 candidates already scoped before score and rank."""
        now = self._now()
        parameters = _proof_parameters(proof=proof, now=now)
        parameters.update(
            {
                "knowledge_base_id": knowledge_base_id,
                "normalized_query": normalized_query,
            }
        )
        try:
            async with self._session_factory() as session, session.begin():
                rows = (await session.execute(_scoped_keyword_statement(), parameters)).all()
        except SQLAlchemyError:
            pass
        else:
            return tuple(
                KeywordCandidate(
                    chunk_id=row.chunk_id,
                    keyword_rank=row.keyword_rank,
                )
                for row in rows
            )

        raise RetrievalUnavailableError

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise RuntimeError("Retrieval clock must return a timezone-aware timestamp.")
        return now


class PostgresFinalAuthoritativeLoader:
    """Load final authoritative records in one fixed read-only snapshot."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        clock: Clock = _utc_now,
    ) -> None:
        self._session_factory = session_factory
        self._clock = clock

    async def load_authoritative_records(
        self,
        *,
        proof: SessionAuthenticationProof,
        knowledge_base_id: UUID,
        candidate_batches: tuple[CandidateBatch, ...],
    ) -> tuple[_InternalAuthoritativeRetrievalRecord, ...]:
        """Reauthorize first, then validate and load every batch atomically."""
        _assert_canonical_batches(candidate_batches)
        loaded_by_chunk: dict[UUID, _InternalAuthoritativeRetrievalRecord] = {}
        try:
            async with self._session_factory() as session, session.begin():
                await session.execute(
                    text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                )
                final_now = self._final_now()
                authorization = (
                    await session.execute(
                        _final_authorization_statement(),
                        _final_authorization_parameters(
                            proof=proof,
                            knowledge_base_id=knowledge_base_id,
                            final_now=final_now,
                        ),
                    )
                ).one()
                if authorization.transaction_isolation != "repeatable read":
                    raise RetrievalUnavailableError
                if authorization.transaction_read_only != "on":
                    raise RetrievalUnavailableError
                if not authorization.authentication_valid:
                    raise RetrievalAuthenticationError
                if not authorization.target_accessible:
                    raise RetrievalTargetNotFoundError

                statement = _final_candidate_statement()
                for batch in candidate_batches:
                    rows = (
                        await session.execute(
                            statement,
                            {
                                "knowledge_base_id": knowledge_base_id,
                                "candidate_ids": batch,
                            },
                        )
                    ).all()
                    for row in rows:
                        loaded_by_chunk[row.chunk_id] = _record_from_row(row)
        except (
            RetrievalAuthenticationError,
            RetrievalTargetNotFoundError,
            RetrievalUnavailableError,
        ):
            raise
        except SQLAlchemyError:
            raise RetrievalUnavailableError from None

        ordered_ids = tuple(candidate for batch in candidate_batches for candidate in batch)
        return tuple(
            loaded_by_chunk[candidate_id]
            for candidate_id in ordered_ids
            if candidate_id in loaded_by_chunk
        )

    def _final_now(self) -> datetime:
        final_now = self._clock()
        if final_now.tzinfo is None or final_now.utcoffset() != timedelta(0):
            raise RuntimeError("Final retrieval clock must return an aware UTC timestamp.")
        return final_now


def _assert_canonical_batches(candidate_batches: tuple[CandidateBatch, ...]) -> None:
    flattened = tuple(candidate for batch in candidate_batches for candidate in batch)
    if _canonical_candidate_batches(flattened) != candidate_batches:
        raise ValueError("Final candidate batches are not canonical.")


def _final_authorization_parameters(
    *,
    proof: SessionAuthenticationProof,
    knowledge_base_id: UUID,
    final_now: datetime,
) -> dict[str, object]:
    return {
        "session_id": proof.principal.session_id,
        "user_id": proof.principal.user_id,
        "session_token_sha256": proof.session_token_sha256,
        "knowledge_base_id": knowledge_base_id,
        "final_now": final_now,
    }


def _final_authorization_statement() -> Select[tuple[bool, bool, str, str]]:
    authentication_valid = exists(
        select(literal(1))
        .select_from(UserSession)
        .join(User, User.id == UserSession.user_id)
        .where(
            UserSession.id == bindparam("session_id"),
            UserSession.user_id == bindparam("user_id"),
            UserSession.token_sha256 == bindparam("session_token_sha256"),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > bindparam("final_now"),
            User.is_active.is_(True),
        )
    )
    target_accessible = exists(
        select(literal(1))
        .select_from(KnowledgeBase)
        .join(
            KnowledgeBaseMembership,
            KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
        )
        .where(
            KnowledgeBase.id == bindparam("knowledge_base_id"),
            KnowledgeBaseMembership.user_id == bindparam("user_id"),
            KnowledgeBaseMembership.role.in_(_READ_ROLE_VALUES),
        )
    )
    return select(
        authentication_valid.label("authentication_valid"),
        target_accessible.label("target_accessible"),
        func.current_setting(literal_column("'transaction_isolation'")).label(
            "transaction_isolation"
        ),
        func.current_setting(literal_column("'transaction_read_only'")).label(
            "transaction_read_only"
        ),
    )


def _final_candidate_statement() -> Select[tuple[object, ...]]:
    return (
        select(
            KnowledgeBase.id.label("knowledge_base_id"),
            Document.id.label("document_id"),
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.normalized_text.label("normalized_text"),
            DocumentChunk.content_sha256.label("content_sha256"),
            Document.original_filename.label("source_display_name"),
            DocumentChunk.page_start.label("page_start"),
            DocumentChunk.page_end.label("page_end"),
            DocumentChunk.start_offset.label("character_start"),
            DocumentChunk.end_offset.label("character_end"),
        )
        .select_from(DocumentChunk)
        .join(Document, Document.id == DocumentChunk.document_id)
        .join(KnowledgeBase, KnowledgeBase.id == Document.knowledge_base_id)
        .where(
            KnowledgeBase.id == bindparam("knowledge_base_id"),
            DocumentChunk.id.in_(
                bindparam(
                    "candidate_ids",
                    expanding=True,
                    type_=PostgreSQLUUID(as_uuid=True),
                )
            ),
            Document.status == DocumentStatus.COMPLETED.value,
            DocumentChunk.content_sha256.is_not(None),
            DocumentChunk.content_sha256.op("~")(_VALID_CONTENT_SHA256_PATTERN),
        )
    )


def _record_from_row(row: object) -> _InternalAuthoritativeRetrievalRecord:
    return _InternalAuthoritativeRetrievalRecord(
        trusted=_TrustedAuthoritativeProvenance(
            knowledge_base_id=row.knowledge_base_id,
            document_id=row.document_id,
            chunk_id=row.chunk_id,
            content_sha256=row.content_sha256,
            source_display_name=row.source_display_name,
            page_start=row.page_start,
            page_end=row.page_end,
            character_start=row.character_start,
            character_end=row.character_end,
        ),
        document_content=_UntrustedDocumentContent(text=row.normalized_text),
    )


def _proof_parameters(
    *,
    proof: SessionAuthenticationProof,
    now: datetime,
) -> dict[str, object]:
    return {
        "session_id": proof.principal.session_id,
        "user_id": proof.principal.user_id,
        "session_token_sha256": proof.session_token_sha256,
        "now": now,
    }


def _initial_authentication_statement() -> Select[tuple[bool]]:
    return (
        select(literal(True))
        .select_from(UserSession)
        .join(User, User.id == UserSession.user_id)
        .where(
            UserSession.id == bindparam("session_id"),
            UserSession.user_id == bindparam("user_id"),
            UserSession.token_sha256 == bindparam("session_token_sha256"),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > bindparam("now"),
            User.is_active.is_(True),
        )
    )


def _initial_target_statement() -> Select[tuple[bool]]:
    return (
        select(literal(True))
        .select_from(KnowledgeBase)
        .join(
            KnowledgeBaseMembership,
            KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id,
        )
        .where(
            KnowledgeBase.id == bindparam("knowledge_base_id"),
            KnowledgeBaseMembership.user_id == bindparam("user_id"),
            KnowledgeBaseMembership.role.in_(_READ_ROLE_VALUES),
        )
    )


def _scoped_keyword_statement() -> Select[tuple[UUID, int]]:
    simple_config: ColumnElement[str] = literal_column("'simple'::regconfig")
    query = func.plainto_tsquery(simple_config, bindparam("normalized_query"))
    vector = func.to_tsvector(simple_config, DocumentChunk.normalized_text)
    score = func.ts_rank_cd(vector, query, 0)

    eligible = (
        select(
            DocumentChunk.id.label("chunk_id"),
            score.label("keyword_score"),
        )
        .select_from(DocumentChunk)
        .join(Document, Document.id == DocumentChunk.document_id)
        .join(KnowledgeBase, KnowledgeBase.id == Document.knowledge_base_id)
        .join(
            KnowledgeBaseMembership,
            (KnowledgeBaseMembership.knowledge_base_id == KnowledgeBase.id)
            & (KnowledgeBaseMembership.user_id == bindparam("user_id")),
        )
        .join(User, User.id == KnowledgeBaseMembership.user_id)
        .join(
            UserSession,
            (UserSession.user_id == User.id) & (UserSession.id == bindparam("session_id")),
        )
        .where(
            KnowledgeBase.id == bindparam("knowledge_base_id"),
            KnowledgeBaseMembership.role.in_(_READ_ROLE_VALUES),
            User.id == bindparam("user_id"),
            User.is_active.is_(True),
            UserSession.token_sha256 == bindparam("session_token_sha256"),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > bindparam("now"),
            Document.status == DocumentStatus.COMPLETED.value,
            DocumentChunk.content_sha256.is_not(None),
            DocumentChunk.content_sha256.op("~")(_VALID_CONTENT_SHA256_PATTERN),
            vector.op("@@")(query),
        )
        .cte("eligible_keyword_candidates")
    )
    ranked = select(
        eligible.c.chunk_id,
        func.row_number()
        .over(
            order_by=(
                eligible.c.keyword_score.desc(),
                eligible.c.chunk_id.asc(),
            )
        )
        .label("keyword_rank"),
    ).cte("ranked_keyword_candidates")
    return (
        select(ranked.c.chunk_id, ranked.c.keyword_rank)
        .order_by(ranked.c.keyword_rank.asc())
        .limit(MAX_KEYWORD_CANDIDATES)
    )
