from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.domain.rag.schemas import QueryRequest
from tests.conftest import make_upload


async def test_ingest_files_creates_ready_document_pytest(rag_fixture) -> None:
    config = rag_fixture["config"]
    indexing_service = rag_fixture["indexing_service"]
    document_service = rag_fixture["document_service"]
    repository = rag_fixture["repository"]
    object.__setattr__(config, "celery_task_always_eager", True)
    upload = make_upload("note.txt", b"hello world from pytest")

    with patch.object(indexing_service, "rebuild_user_index", return_value=None):
        response = await document_service.ingest_files("user-1", [upload])

    assert response.rejected_files == []
    assert len(response.items) == 1
    assert response.items[0].status.value == "ready"
    assert repository.list_by_user("user-1")[0].filename == "note.txt"


async def test_ingest_files_stays_queued_when_celery_async_pytest(rag_fixture) -> None:
    config = rag_fixture["config"]
    dispatcher = rag_fixture["dispatcher"]
    document_service = rag_fixture["document_service"]
    repository = rag_fixture["repository"]
    object.__setattr__(config, "celery_task_always_eager", False)
    upload = make_upload("note.txt", b"queued for worker from pytest")

    with patch.object(dispatcher, "_celery_app", MagicMock()), patch.object(
        dispatcher._celery_app, "send_task", return_value=None
    ):
        response = await document_service.ingest_files("user-1", [upload])

    assert response.items[0].status.value == "queued"
    assert repository.list_by_user("user-1")[0].status.value == "queued"


async def test_process_ingest_job_marks_ready_pytest(rag_fixture) -> None:
    config = rag_fixture["config"]
    dispatcher = rag_fixture["dispatcher"]
    document_service = rag_fixture["document_service"]
    indexing_service = rag_fixture["indexing_service"]
    repository = rag_fixture["repository"]
    object.__setattr__(config, "celery_task_always_eager", True)
    upload = make_upload("note.txt", b"hello world from worker pytest")

    with patch.object(dispatcher, "dispatch_ingest", return_value=None):
        response = await document_service.ingest_files("user-1", [upload])

    assert response.items[0].status.value == "queued"
    with patch.object(indexing_service, "rebuild_user_index", return_value=None):
        document_service.process_ingest_job("user-1")

    assert repository.list_by_user("user-1")[0].status.value == "ready"


async def test_ingest_files_rejects_unsupported_extension_pytest(rag_fixture) -> None:
    config = rag_fixture["config"]
    document_service = rag_fixture["document_service"]
    object.__setattr__(config, "celery_task_always_eager", True)
    upload = make_upload("image.png", b"binary")

    response = await document_service.ingest_files("user-1", [upload])

    assert response.rejected_files == ["image.png"]
    assert response.items == []


def test_hybrid_query_includes_keyword_citation_pytest(rag_fixture) -> None:
    index_adapter = rag_fixture["index_adapter"]
    query_service = rag_fixture["query_service"]
    keyword_nodes = [
        SimpleNamespace(
            node=SimpleNamespace(
                metadata={
                    "document_id": "doc-1",
                    "filename": "note.txt",
                    "source": "keyword",
                },
                text="backend orchestration lexical snippet",
            ),
            score=2.0,
        )
    ]

    with patch.object(
        index_adapter._qdrant_adapter,
        "query_chunks",
        side_effect=RuntimeError("dense backend unavailable"),
    ), patch.object(
        index_adapter._local_adapter,
        "query_user_index",
        side_effect=RuntimeError("dense backend unavailable"),
    ), patch.object(
        index_adapter._elasticsearch_adapter,
        "query_chunks",
        return_value=keyword_nodes,
    ):
        response = query_service.query(
            QueryRequest(
                user_id="user-1",
                query="backend orchestration",
                top_k=3,
            )
        )

    assert response.citations
    assert response.citations[0].filename == "note.txt"


def test_rebuild_user_index_calls_qdrant_and_elasticsearch_pytest(rag_fixture) -> None:
    index_adapter = rag_fixture["index_adapter"]
    record = SimpleNamespace(
        document_id="doc-1",
        user_id="user-1",
        filename="note.txt",
        content_type="text/plain",
        storage_path="",
        status="ready",
    )
    # Build an actual file so chunking has something to read.
    data_dir = rag_fixture["config"].user_data_dir("user-1")
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / "doc-1.txt"
    file_path.write_text("hello world " * 100, encoding="utf-8")
    record.storage_path = str(file_path)
    records = {"doc-1.txt": record}

    with patch.object(index_adapter._local_adapter, "rebuild_user_index", return_value=None), patch.object(
        index_adapter._qdrant_adapter, "upsert_chunks", return_value=None
    ) as qdrant_upsert, patch.object(
        index_adapter._elasticsearch_adapter, "index_chunks", return_value=None
    ) as elastic_index:
        index_adapter.rebuild_user_index("user-1", records)

    assert qdrant_upsert.called
    assert elastic_index.called
