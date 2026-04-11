import io
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

from app.adapters.elasticsearch_adapter import ElasticsearchAdapter
from app.adapters.hybrid_index_adapter import HybridIndexAdapter
from app.adapters.local_index_adapter import LocalIndexAdapter
from app.adapters.qdrant_adapter import QdrantAdapter
from app.core.config import AppConfig
from app.domain.rag.repositories.document_repository import DocumentRepository
from app.domain.rag.services.document_service import DocumentService
from app.domain.rag.services.indexing_service import IndexingService
from app.domain.rag.services.query_service import QueryService
from app.workers.tasks import WorkerTaskDispatcher


@pytest.fixture
def rag_fixture(tmp_path: Path):
    config = AppConfig.from_root(tmp_path)
    config.ensure_directories()
    repository = DocumentRepository(config.metadata_path)
    index_adapter = HybridIndexAdapter(
        config,
        LocalIndexAdapter(config),
        QdrantAdapter(config),
        ElasticsearchAdapter(config),
    )
    indexing_service = IndexingService(config, repository, index_adapter)
    dispatcher = WorkerTaskDispatcher(config)
    document_service = DocumentService(
        config,
        repository,
        indexing_service,
        dispatcher,
    )
    query_service = QueryService(config, index_adapter)
    return {
        "config": config,
        "repository": repository,
        "index_adapter": index_adapter,
        "indexing_service": indexing_service,
        "dispatcher": dispatcher,
        "document_service": document_service,
        "query_service": query_service,
    }


def make_upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(file=io.BytesIO(content), filename=filename)
