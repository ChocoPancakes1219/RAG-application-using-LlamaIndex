from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.config import AppConfig
from app.domain.rag.repositories.document_repository import DocumentRepository
from app.domain.rag.schemas import (
    DocumentBatchIngestResponse,
    DocumentListResponse,
    DocumentRecord,
    DocumentStatus,
    utc_now,
)
from app.domain.rag.services.indexing_service import IndexingService
from app.workers.tasks import WorkerTaskDispatcher


class DocumentService:
    _allowed_extensions = {".txt", ".md"}

    def __init__(
        self,
        config: AppConfig,
        repository: DocumentRepository,
        indexing_service: IndexingService,
        task_dispatcher: WorkerTaskDispatcher,
    ) -> None:
        self._config = config
        self._repository = repository
        self._indexing_service = indexing_service
        self._task_dispatcher = task_dispatcher

    def list_documents(self, user_id: str) -> DocumentListResponse:
        return DocumentListResponse(items=self._repository.list_by_user(user_id))

    def get_document(self, user_id: str, document_id: str) -> DocumentRecord:
        return self._require_document(user_id, document_id)

    async def ingest_files(
        self,
        user_id: str,
        files: list[UploadFile],
    ) -> DocumentBatchIngestResponse:
        if not files:
            raise HTTPException(status_code=400, detail="업로드할 파일이 없습니다.")

        accepted: list[DocumentRecord] = []
        rejected: list[str] = []
        user_data_dir = self._config.user_data_dir(user_id)
        user_data_dir.mkdir(parents=True, exist_ok=True)

        for upload in files:
            filename = (upload.filename or "").strip()
            extension = Path(filename).suffix.lower()
            if not filename or extension not in self._allowed_extensions:
                rejected.append(filename or "<empty>")
                continue

            document_id = f"doc-{uuid4().hex}"
            storage_name = f"{document_id}{extension}"
            storage_path = user_data_dir / storage_name
            record = DocumentRecord(
                document_id=document_id,
                user_id=user_id,
                filename=filename,
                content_type=upload.content_type or "text/plain",
                storage_path=str(storage_path),
                status=DocumentStatus.queued,
            )
            self._repository.upsert(record)

            try:
                contents = await upload.read()
                contents.decode("utf-8")
                storage_path.write_bytes(contents)
                self._task_dispatcher.dispatch_ingest(
                    self.process_ingest_job,
                    user_id,
                )
                accepted.append(self._repository.get(document_id) or record)
            except UnicodeDecodeError:
                storage_path.unlink(missing_ok=True)
                record = record.model_copy(
                    update={
                        "status": DocumentStatus.failed,
                        "error_message": "UTF-8 텍스트 파일만 현재 지원합니다.",
                        "updated_at": utc_now(),
                    }
                )
                self._repository.upsert(record)
                accepted.append(record)
            except Exception as error:  # pragma: no cover - llama/model dependent
                storage_path.unlink(missing_ok=True)
                record = record.model_copy(
                    update={
                        "status": DocumentStatus.failed,
                        "error_message": str(error),
                        "updated_at": utc_now(),
                    }
                )
                self._repository.upsert(record)
                accepted.append(record)

        return DocumentBatchIngestResponse(items=accepted, rejected_files=rejected)

    def delete_document(self, user_id: str, document_id: str) -> None:
        record = self._require_document(user_id, document_id)
        Path(record.storage_path).unlink(missing_ok=True)
        self._repository.delete(document_id)
        self._task_dispatcher.dispatch_delete(
            self.process_delete_job,
            user_id,
        )

    def process_ingest_job(self, user_id: str) -> None:
        pending_records = [
            item
            for item in self._repository.list_by_user(user_id)
            if item.status in {DocumentStatus.queued, DocumentStatus.processing}
        ]
        if not pending_records:
            self._indexing_service.rebuild_user_index(user_id)
            return

        processing_records: list[DocumentRecord] = []
        for record in pending_records:
            updated = record.model_copy(
                update={
                    "status": DocumentStatus.processing,
                    "error_message": None,
                    "updated_at": utc_now(),
                }
            )
            self._repository.upsert(updated)
            processing_records.append(updated)

        try:
            self._indexing_service.rebuild_user_index(user_id)
            for record in processing_records:
                text = Path(record.storage_path).read_text(encoding="utf-8")
                self._repository.upsert(
                    record.model_copy(
                        update={
                            "status": DocumentStatus.ready,
                            "chunk_count": self._indexing_service.estimate_chunk_count(text),
                            "error_message": None,
                            "updated_at": utc_now(),
                        }
                    )
                )
        except Exception as error:  # pragma: no cover - worker/model dependent
            for record in processing_records:
                self._repository.upsert(
                    record.model_copy(
                        update={
                            "status": DocumentStatus.failed,
                            "error_message": str(error),
                            "updated_at": utc_now(),
                        }
                    )
                )
            raise

    def process_delete_job(self, user_id: str) -> None:
        self._indexing_service.rebuild_user_index(user_id)

    def _require_document(self, user_id: str, document_id: str) -> DocumentRecord:
        record = self._repository.get(document_id)
        if record is None or record.user_id != user_id:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        return record
