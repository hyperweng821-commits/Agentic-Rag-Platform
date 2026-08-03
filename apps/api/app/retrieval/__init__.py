"""Provider-independent retrieval contracts."""

from app.retrieval.domain import (
    RetrievalRequest,
    RetrievalRequestValidationError,
    parse_retrieval_request,
)
from app.retrieval.postgres import MAX_KEYWORD_CANDIDATES, PostgresRetrievalAccess
from app.retrieval.service import (
    KeywordCandidate,
    RetrievalAuthenticationError,
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
    ScopedKeywordResult,
    ScopedKeywordRetrievalService,
)

__all__ = [
    "MAX_KEYWORD_CANDIDATES",
    "KeywordCandidate",
    "PostgresRetrievalAccess",
    "RetrievalAuthenticationError",
    "RetrievalRequest",
    "RetrievalRequestValidationError",
    "RetrievalTargetNotFoundError",
    "RetrievalUnavailableError",
    "ScopedKeywordResult",
    "ScopedKeywordRetrievalService",
    "parse_retrieval_request",
]
