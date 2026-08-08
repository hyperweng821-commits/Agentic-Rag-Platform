"""Bounded internal retrieval request, Provider, and PostgreSQL boundaries."""

from app.retrieval.chroma import (
    CHROMA_COMPATIBILITY_ID,
    ChromaDenseRetrievalAdapter,
    DenseProviderError,
)
from app.retrieval.domain import (
    RetrievalRequest,
    RetrievalRequestValidationError,
    parse_retrieval_request,
)
from app.retrieval.hybrid import (
    DENSE_OVERFETCH_FACTOR,
    MAX_DENSE_CANDIDATES,
    MAX_PROVIDER_CANDIDATES,
    MAX_UNIQUE_CANDIDATES,
    RRF_K,
    HybridRetrievalResult,
    HybridRetrievalService,
    configured_provider_count,
    fuse_authoritative_records,
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
    "CHROMA_COMPATIBILITY_ID",
    "DENSE_OVERFETCH_FACTOR",
    "FINAL_VALIDATION_BATCH_SIZE",
    "MAX_DENSE_CANDIDATES",
    "MAX_FINAL_CANDIDATES",
    "MAX_KEYWORD_CANDIDATES",
    "MAX_PROVIDER_CANDIDATES",
    "MAX_UNIQUE_CANDIDATES",
    "RRF_K",
    "ChromaDenseRetrievalAdapter",
    "DenseProviderError",
    "FinalCandidateLimitError",
    "FinalCandidateValidatorLoader",
    "HybridRetrievalResult",
    "HybridRetrievalService",
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
    "configured_provider_count",
    "fuse_authoritative_records",
    "parse_retrieval_request",
]
