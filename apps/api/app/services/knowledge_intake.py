"""AF-1 knowledge-intake use cases and transaction ownership."""

from dataclasses import dataclass
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import (
    ConflictError,
    InvalidUploadError,
    NotFoundError,
    ServiceUnavailableError,
    UnsupportedMediaTypeError,
    UploadTooLargeError,
)
from app.db.models import (
    Document,
    DocumentStatus,
    IngestionJob,
    IngestionJobStatus,
    KnowledgeBase,
)
from app.db.repositories import (
    DocumentRepository,
    IngestionJobRepository,
    KnowledgeBaseRepository,
)
from app.ingestion.storage import (
    AsyncReadable,
    EmptyFileError,
    FileStorage,
    FileTooLargeError,
    StorageError,
    StoredFile,
)
from app.security import Capability, Principal, require_capability

_ALLOWED_UPLOADS: dict[str, tuple[str, ...]] = {
    "application/pdf": (".pdf",),
    "text/markdown": (".md", ".markdown"),
    "text/plain": (".txt",),
}


@dataclass(frozen=True, slots=True)
class UploadResult:
    """Document and job returned by a new or duplicate upload."""

    document: Document
    job: IngestionJob
    duplicate: bool


class KnowledgeIntakeService:
    """Coordinate AF-1 persistence and local file storage."""

    def __init__(
        self,
        session: AsyncSession,
        storage: FileStorage,
        *,
        max_upload_size_bytes: int,
    ) -> None:
        self._session = session
        self._storage = storage
        self._max_upload_size_bytes = max_upload_size_bytes
        self._knowledge_bases = KnowledgeBaseRepository(session)
        self._documents = DocumentRepository(session)
        self._jobs = IngestionJobRepository(session)

    async def create_knowledge_base(
        self,
        principal: Principal,
        *,
        name: str,
        description: str | None,
    ) -> KnowledgeBase:
        require_capability(None, Capability.KNOWLEDGE_BASE_CREATE)
        knowledge_base = KnowledgeBase(name=name, description=description)
        async with self._session.begin():
            await self._knowledge_bases.add_with_owner(
                knowledge_base,
                owner_user_id=principal.user_id,
            )
        return knowledge_base

    async def list_knowledge_bases(
        self,
        principal: Principal,
        *,
        limit: int,
        offset: int,
    ) -> list[KnowledgeBase]:
        async with self._session.begin():
            visible = await self._knowledge_bases.list_for_user(
                user_id=principal.user_id,
                limit=limit,
                offset=offset,
            )
        for _, role in visible:
            require_capability(role, Capability.KNOWLEDGE_BASE_READ)
        return [knowledge_base for knowledge_base, _ in visible]

    async def get_knowledge_base(
        self,
        principal: Principal,
        knowledge_base_id: UUID,
    ) -> KnowledgeBase:
        async with self._session.begin():
            visible = await self._knowledge_bases.get_for_user(
                knowledge_base_id,
                user_id=principal.user_id,
            )
        if visible is None:
            raise NotFoundError("Knowledge base was not found.")
        knowledge_base, role = visible
        require_capability(role, Capability.KNOWLEDGE_BASE_READ)
        return knowledge_base

    async def list_documents(
        self,
        principal: Principal,
        knowledge_base_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Document]:
        async with self._session.begin():
            visible_knowledge_base = await self._knowledge_bases.get_for_user(
                knowledge_base_id,
                user_id=principal.user_id,
            )
            if visible_knowledge_base is None:
                raise NotFoundError("Knowledge base was not found.")
            _, role = visible_knowledge_base
            require_capability(role, Capability.DOCUMENT_READ)
            visible_documents = await self._documents.list_for_knowledge_base_for_user(
                knowledge_base_id,
                user_id=principal.user_id,
                limit=limit,
                offset=offset,
            )
        for _, document_role in visible_documents:
            require_capability(document_role, Capability.DOCUMENT_READ)
        return [document for document, _ in visible_documents]

    async def get_document(self, principal: Principal, document_id: UUID) -> Document:
        async with self._session.begin():
            visible = await self._documents.get_for_user(
                document_id,
                user_id=principal.user_id,
            )
        if visible is None:
            raise NotFoundError("Document was not found.")
        document, role = visible
        require_capability(role, Capability.DOCUMENT_READ)
        return document

    async def get_ingestion_job(
        self,
        principal: Principal,
        job_id: UUID,
    ) -> IngestionJob:
        async with self._session.begin():
            visible = await self._jobs.get_for_user(
                job_id,
                user_id=principal.user_id,
            )
        if visible is None:
            raise NotFoundError("Ingestion job was not found.")
        job, role = visible
        require_capability(role, Capability.INGESTION_JOB_READ)
        return job

    async def upload_document(
        self,
        principal: Principal,
        knowledge_base_id: UUID,
        *,
        filename: str,
        media_type: str,
        source: AsyncReadable,
    ) -> UploadResult:
        extension = self._validate_upload_metadata(filename, media_type)
        async with self._session.begin():
            upload_target = await self._knowledge_bases.get_upload_target_for_user(
                knowledge_base_id,
                user_id=principal.user_id,
            )
            if upload_target is None:
                raise NotFoundError("Knowledge base was not found.")
            _, role = upload_target
            require_capability(role, Capability.DOCUMENT_UPLOAD)

        document_id = uuid4()
        storage_key = f"{knowledge_base_id}/{document_id}{extension}"
        stored = await self._store_upload(source, storage_key)
        cleanup_owned = True
        try:
            self._validate_content(media_type, stored)
            result = await self._persist_upload(
                principal,
                knowledge_base_id,
                document_id=document_id,
                filename=filename,
                media_type=media_type,
                stored=stored,
            )
            cleanup_owned = False
            return result
        finally:
            if cleanup_owned:
                await self._storage.delete(storage_key)

    async def retry_ingestion_job(
        self,
        principal: Principal,
        job_id: UUID,
    ) -> IngestionJob:
        async with self._session.begin():
            retry_target = await self._jobs.get_retry_target_for_user(
                job_id,
                user_id=principal.user_id,
                for_update=True,
            )
            if retry_target is None:
                raise NotFoundError("Ingestion job was not found.")
            job, role = retry_target
            require_capability(role, Capability.INGESTION_JOB_RETRY)
            if job.status == IngestionJobStatus.PENDING.value:
                return job
            if job.status != IngestionJobStatus.FAILED.value:
                raise ConflictError("Only failed ingestion jobs can be retried.")

            job.status = IngestionJobStatus.PENDING.value
            job.progress_percent = 0
            job.claimed_by = None
            job.claimed_at = None
            job.lease_expires_at = None
            job.next_retry_at = None
            job.error_code = None
            job.safe_error_message = None
            job.started_at = None
            job.finished_at = None
            job.document.status = DocumentStatus.PENDING.value
            await self._session.flush()
            await self._session.refresh(job)
            return job

    async def _store_upload(self, source: AsyncReadable, storage_key: str) -> StoredFile:
        try:
            return await self._storage.store(
                source,
                storage_key=storage_key,
                max_bytes=self._max_upload_size_bytes,
            )
        except EmptyFileError as exc:
            raise InvalidUploadError("The uploaded file is empty.") from exc
        except FileTooLargeError as exc:
            raise UploadTooLargeError() from exc
        except StorageError as exc:
            raise ServiceUnavailableError("File storage is temporarily unavailable.") from exc
        except OSError as exc:
            raise ServiceUnavailableError("File storage is temporarily unavailable.") from exc

    async def _persist_upload(
        self,
        principal: Principal,
        knowledge_base_id: UUID,
        *,
        document_id: UUID,
        filename: str,
        media_type: str,
        stored: StoredFile,
    ) -> UploadResult:
        try:
            async with self._session.begin():
                upload_target = await self._knowledge_bases.get_upload_target_for_user(
                    knowledge_base_id,
                    user_id=principal.user_id,
                )
                if upload_target is None:
                    raise NotFoundError("Knowledge base was not found.")
                _, role = upload_target
                require_capability(role, Capability.DOCUMENT_UPLOAD)

                duplicate = await self._documents.get_by_digest_for_user(
                    knowledge_base_id=knowledge_base_id,
                    sha256=stored.sha256,
                    user_id=principal.user_id,
                )
                if duplicate is not None:
                    existing, duplicate_role = duplicate
                    require_capability(duplicate_role, Capability.DOCUMENT_UPLOAD)
                    if existing.ingestion_job is None:
                        raise ConflictError("Existing document has no ingestion job.")
                    await self._storage.delete(stored.storage_key)
                    return UploadResult(existing, existing.ingestion_job, duplicate=True)

                document = Document(
                    id=document_id,
                    knowledge_base_id=knowledge_base_id,
                    original_filename=filename,
                    media_type=media_type,
                    size_bytes=stored.size_bytes,
                    sha256=stored.sha256,
                    storage_key=stored.storage_key,
                    status=DocumentStatus.PENDING.value,
                )
                job = IngestionJob(
                    document=document,
                    status=IngestionJobStatus.PENDING.value,
                    attempt_count=0,
                )
                await self._documents.add_authorized_upload(document)
                await self._jobs.add_for_authorized_upload(job)
                return UploadResult(document, job, duplicate=False)
        except IntegrityError:
            await self._storage.delete(stored.storage_key)
            return await self._resolve_concurrent_duplicate(
                principal=principal,
                knowledge_base_id=knowledge_base_id,
                sha256=stored.sha256,
            )
        except SQLAlchemyError as exc:
            raise ServiceUnavailableError("Database is temporarily unavailable.") from exc

    async def _resolve_concurrent_duplicate(
        self,
        *,
        principal: Principal,
        knowledge_base_id: UUID,
        sha256: str,
    ) -> UploadResult:
        async with self._session.begin():
            upload_target = await self._knowledge_bases.get_upload_target_for_user(
                knowledge_base_id,
                user_id=principal.user_id,
            )
            if upload_target is None:
                raise NotFoundError("Knowledge base was not found.")
            _, role = upload_target
            require_capability(role, Capability.DOCUMENT_UPLOAD)
            duplicate = await self._documents.get_by_digest_for_user(
                knowledge_base_id=knowledge_base_id,
                sha256=sha256,
                user_id=principal.user_id,
            )
            if duplicate is None:
                existing = None
            else:
                existing, duplicate_role = duplicate
                require_capability(duplicate_role, Capability.DOCUMENT_UPLOAD)
        if existing is None or existing.ingestion_job is None:
            raise ConflictError("The document could not be stored due to a concurrent conflict.")
        return UploadResult(existing, existing.ingestion_job, duplicate=True)

    @staticmethod
    def _validate_upload_metadata(filename: str, media_type: str) -> str:
        if (
            not filename
            or filename in {".", ".."}
            or "\x00" in filename
            or PurePath(filename).name != filename
            or "/" in filename
            or "\\" in filename
        ):
            raise InvalidUploadError("The uploaded filename is unsafe.")
        if len(filename) > 255:
            raise InvalidUploadError("The uploaded filename is too long.")

        extension = PurePath(filename).suffix.lower()
        allowed_extensions = _ALLOWED_UPLOADS.get(media_type)
        if allowed_extensions is None or extension not in allowed_extensions:
            raise UnsupportedMediaTypeError()
        return extension

    @staticmethod
    def _validate_content(media_type: str, stored: StoredFile) -> None:
        if media_type == "application/pdf" and not stored.prefix.startswith(b"%PDF-"):
            raise InvalidUploadError("The uploaded PDF signature is invalid.")
        if media_type in {"text/markdown", "text/plain"} and b"\x00" in stored.prefix:
            raise InvalidUploadError("The uploaded text file contains binary data.")
