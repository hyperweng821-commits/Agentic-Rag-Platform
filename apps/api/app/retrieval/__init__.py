"""Provider-independent retrieval contracts."""

from app.retrieval.domain import (
    RetrievalRequest,
    RetrievalRequestValidationError,
    parse_retrieval_request,
)
from app.retrieval.postgres import (
    MAX_KEYWORD_CANDIDATES,
    PostgresFinalAuthoritativeLoader,
    PostgresRetrievalAccess,
)
from app.retrieval.service import (
    FINAL_VALIDATION_BATCH_SIZE,
    MAX_FINAL_CANDIDATES,
    FinalCandidateLimitError,
    FinalCandidateValidatorLoader,
    KeywordCandidate,
    RetrievalAuthenticationError,
    RetrievalTargetNotFoundError,
    RetrievalUnavailableError,
    ScopedKeywordResult,
    ScopedKeywordRetrievalService,
)

__all__ = [
    "FINAL_VALIDATION_BATCH_SIZE",
    "MAX_FINAL_CANDIDATES",
    "MAX_KEYWORD_CANDIDATES",
    "FinalCandidateLimitError",
    "FinalCandidateValidatorLoader",
    "KeywordCandidate",
    "PostgresFinalAuthoritativeLoader",
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
