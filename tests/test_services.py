import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock
from unittest.mock import patch

from starlette.datastructures import UploadFile

from app.adapters.elasticsearch_adapter import ElasticsearchAdapter
from app.adapters.hybrid_index_adapter import HybridIndexAdapter
from app.adapters.local_index_adapter import LocalIndexAdapter
from app.adapters.qdrant_adapter import QdrantAdapter
from app.core.config import AppConfig
from app.domain.rag.repositories.document_repository import DocumentRepository
from app.domain.rag.schemas import QueryRequest
from app.domain.rag.services.document_service import DocumentService
from app.domain.rag.services.indexing_service import IndexingService
from app.domain.rag.services.query_service import QueryService
from app.workers.tasks import WorkerTaskDispatcher


class DocumentServiceTest(IsolatedAsyncioTestCase):
    async def test_ingest_files_creates_ready_document(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = AppConfig.from_root(root)
            config.ensure_directories()
            object.__setattr__(config, "celery_task_always_eager", True)
            repository = DocumentRepository(config.metadata_path)
            index_adapter = HybridIndexAdapter(
                config,
                LocalIndexAdapter(config),
                QdrantAdapter(config),
                ElasticsearchAdapter(config),
            )
            indexing_service = IndexingService(config, repository, index_adapter)
            dispatcher = WorkerTaskDispatcher(config)
            service = DocumentService(
                config,
                repository,
                indexing_service,
                dispatcher,
            )
            upload = UploadFile(
                file=io.BytesIO(b"hello world from airag"),
                filename="note.txt",
            )

            with patch.object(indexing_service, "rebuild_user_index", return_value=None):
                response = await service.ingest_files("user-1", [upload])

            self.assertEqual(response.rejected_files, [])
            self.assertEqual(len(response.items), 1)
            self.assertEqual(response.items[0].status.value, "ready")
            self.assertEqual(repository.list_by_user("user-1")[0].filename, "note.txt")

    async def test_ingest_files_stays_queued_when_celery_async(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = AppConfig.from_root(root)
            config.ensure_directories()
            object.__setattr__(config, "celery_task_always_eager", False)
            repository = DocumentRepository(config.metadata_path)
            index_adapter = HybridIndexAdapter(
                config,
                LocalIndexAdapter(config),
                QdrantAdapter(config),
                ElasticsearchAdapter(config),
            )
            indexing_service = IndexingService(config, repository, index_adapter)
            dispatcher = WorkerTaskDispatcher(config)
            service = DocumentService(
                config,
                repository,
                indexing_service,
                dispatcher,
            )
            upload = UploadFile(
                file=io.BytesIO(b"queued for worker"),
                filename="note.txt",
            )

            with patch.object(dispatcher, "_celery_app", MagicMock()), patch.object(
                dispatcher._celery_app, "send_task", return_value=None
            ):
                response = await service.ingest_files("user-1", [upload])

            self.assertEqual(response.items[0].status.value, "queued")
            self.assertEqual(repository.list_by_user("user-1")[0].status.value, "queued")

    async def test_process_ingest_job_marks_ready(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = AppConfig.from_root(root)
            config.ensure_directories()
            object.__setattr__(config, "celery_task_always_eager", True)
            repository = DocumentRepository(config.metadata_path)
            index_adapter = HybridIndexAdapter(
                config,
                LocalIndexAdapter(config),
                QdrantAdapter(config),
                ElasticsearchAdapter(config),
            )
            indexing_service = IndexingService(config, repository, index_adapter)
            dispatcher = WorkerTaskDispatcher(config)
            service = DocumentService(
                config,
                repository,
                indexing_service,
                dispatcher,
            )
            upload = UploadFile(
                file=io.BytesIO(b"hello world from worker"),
                filename="note.txt",
            )

            with patch.object(dispatcher, "dispatch_ingest", return_value=None):
                response = await service.ingest_files("user-1", [upload])

            self.assertEqual(response.items[0].status.value, "queued")
            with patch.object(indexing_service, "rebuild_user_index", return_value=None):
                service.process_ingest_job("user-1")

            self.assertEqual(repository.list_by_user("user-1")[0].status.value, "ready")

    async def test_ingest_files_rejects_unsupported_extension(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = AppConfig.from_root(root)
            config.ensure_directories()
            object.__setattr__(config, "celery_task_always_eager", True)
            repository = DocumentRepository(config.metadata_path)
            index_adapter = HybridIndexAdapter(
                config,
                LocalIndexAdapter(config),
                QdrantAdapter(config),
                ElasticsearchAdapter(config),
            )
            indexing_service = IndexingService(config, repository, index_adapter)
            dispatcher = WorkerTaskDispatcher(config)
            service = DocumentService(
                config,
                repository,
                indexing_service,
                dispatcher,
            )
            upload = UploadFile(
                file=io.BytesIO(b"binary"),
                filename="image.png",
            )

            response = await service.ingest_files("user-1", [upload])

            self.assertEqual(response.rejected_files, ["image.png"])
            self.assertEqual(response.items, [])


class QueryServiceTest(IsolatedAsyncioTestCase):
    async def test_hybrid_query_includes_keyword_citation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = AppConfig.from_root(root)
            config.ensure_directories()
            index_adapter = HybridIndexAdapter(
                config,
                LocalIndexAdapter(config),
                QdrantAdapter(config),
                ElasticsearchAdapter(config),
            )
            query_service = QueryService(config, index_adapter)
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

            self.assertTrue(response.citations)
            self.assertEqual(response.citations[0].filename, "note.txt")
