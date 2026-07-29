"""Central owner/editor/viewer capability policy."""

from enum import StrEnum

from starlette import status

from app.api.errors import AppException
from app.db.models import KnowledgeBaseRole


class AuthorizationError(AppException):
    """The authenticated principal lacks the required capability."""

    code = "FORBIDDEN"
    message = "The requested operation is not permitted."
    status_code = status.HTTP_403_FORBIDDEN


class Capability(StrEnum):
    """Current authenticated knowledge-API operations."""

    KNOWLEDGE_BASE_CREATE = "knowledge_base_create"
    KNOWLEDGE_BASE_READ = "knowledge_base_read"
    DOCUMENT_READ = "document_read"
    DOCUMENT_UPLOAD = "document_upload"
    INGESTION_JOB_READ = "ingestion_job_read"
    INGESTION_JOB_RETRY = "ingestion_job_retry"


_AUTHENTICATED_CAPABILITIES = frozenset({Capability.KNOWLEDGE_BASE_CREATE})
_ROLE_CAPABILITIES: dict[KnowledgeBaseRole, frozenset[Capability]] = {
    KnowledgeBaseRole.OWNER: frozenset(
        {
            Capability.KNOWLEDGE_BASE_READ,
            Capability.DOCUMENT_READ,
            Capability.DOCUMENT_UPLOAD,
            Capability.INGESTION_JOB_READ,
            Capability.INGESTION_JOB_RETRY,
        }
    ),
    KnowledgeBaseRole.EDITOR: frozenset(
        {
            Capability.KNOWLEDGE_BASE_READ,
            Capability.DOCUMENT_READ,
            Capability.DOCUMENT_UPLOAD,
            Capability.INGESTION_JOB_READ,
            Capability.INGESTION_JOB_RETRY,
        }
    ),
    KnowledgeBaseRole.VIEWER: frozenset(
        {
            Capability.KNOWLEDGE_BASE_READ,
            Capability.DOCUMENT_READ,
            Capability.INGESTION_JOB_READ,
        }
    ),
}


def capabilities_for(role: KnowledgeBaseRole | str | None) -> frozenset[Capability]:
    """Return capabilities granted to an authenticated principal in one KB."""
    resolved_role = _resolve_role(role)
    role_capabilities = (
        frozenset() if resolved_role is None else _ROLE_CAPABILITIES.get(resolved_role, frozenset())
    )
    return _AUTHENTICATED_CAPABILITIES | role_capabilities


def require_capability(
    role: KnowledgeBaseRole | str | None,
    capability: Capability,
) -> None:
    """Raise a generic 403 when an authenticated principal lacks a capability."""
    if capability not in capabilities_for(role):
        raise AuthorizationError


def _resolve_role(role: KnowledgeBaseRole | str | None) -> KnowledgeBaseRole | None:
    if role is None:
        return None
    if isinstance(role, KnowledgeBaseRole):
        return role
    try:
        return KnowledgeBaseRole(role)
    except ValueError:
        return None
