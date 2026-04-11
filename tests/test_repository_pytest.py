from datetime import timezone

from app.domain.rag.schemas import DocumentRecord, DocumentStatus


def test_repository_upsert_and_list_by_user_pytest(rag_fixture) -> None:
    repository = rag_fixture["repository"]
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

    assert len(items) == 1
    assert items[0].document_id == "doc-1"
    assert items[0].created_at.tzinfo == timezone.utc


def test_repository_delete_removes_document_pytest(rag_fixture) -> None:
    repository = rag_fixture["repository"]
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

    assert repository.get("doc-1") is None
