from datetime import timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.domain.rag.repositories.document_repository import DocumentRepository
from app.domain.rag.schemas import DocumentRecord, DocumentStatus


class DocumentRepositoryTest(TestCase):
    def test_upsert_and_list_by_user(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = DocumentRepository(Path(temp_dir) / "documents.json")
            record = DocumentRecord(
                document_id="doc-1",
                user_id="user-1",
                filename="note.txt",
                content_type="text/plain",
                storage_path="/tmp/note.txt",
                status=DocumentStatus.ready,
                chunk_count=3,
            )

            repository.upsert(record)
            items = repository.list_by_user("user-1")

            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].document_id, "doc-1")
            self.assertEqual(items[0].created_at.tzinfo, timezone.utc)

    def test_delete_removes_document(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = DocumentRepository(Path(temp_dir) / "documents.json")
            record = DocumentRecord(
                document_id="doc-1",
                user_id="user-1",
                filename="note.txt",
                content_type="text/plain",
                storage_path="/tmp/note.txt",
                status=DocumentStatus.ready,
            )

            repository.upsert(record)
            repository.delete("doc-1")

            self.assertIsNone(repository.get("doc-1"))
