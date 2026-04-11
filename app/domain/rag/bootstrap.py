from pathlib import Path

from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

from app.adapters.elasticsearch_adapter import ElasticsearchAdapter
from app.adapters.hybrid_index_adapter import HybridIndexAdapter
from app.adapters.local_index_adapter import LocalIndexAdapter
from app.adapters.qdrant_adapter import QdrantAdapter
from app.core.config import AppConfig
from app.domain.rag.repositories.document_repository import DocumentRepository
from app.domain.rag.services.chat_service import ChatService
from app.domain.rag.services.document_service import DocumentService
from app.domain.rag.services.indexing_service import IndexingService
from app.domain.rag.services.query_service import QueryService
from app.workers.tasks import WorkerTaskDispatcher


def build_rag_components(
    root_dir: Path,
) -> tuple[AppConfig, DocumentService, QueryService, ChatService]:
    config = AppConfig.from_root(root_dir)
    config.ensure_directories()
    _configure_llama_settings(config)
    repository = DocumentRepository(config.metadata_path)
    local_adapter = LocalIndexAdapter(config)
    dense_adapter = QdrantAdapter(config)
    keyword_adapter = ElasticsearchAdapter(config)
    index_adapter = HybridIndexAdapter(
        config,
        local_adapter,
        dense_adapter,
        keyword_adapter,
    )
    task_dispatcher = WorkerTaskDispatcher(config)
    indexing_service = IndexingService(config, repository, index_adapter)
    chat_service = ChatService(config)
    document_service = DocumentService(
        config,
        repository,
        indexing_service,
        task_dispatcher,
    )
    query_service = QueryService(config, index_adapter)
    return config, document_service, query_service, chat_service


def _configure_llama_settings(config: AppConfig) -> None:
    Settings.llm = Ollama(
        model=config.ollama_chat_model,
        base_url=config.ollama_base_url,
    )
    Settings.embed_model = OllamaEmbedding(
        model_name=config.ollama_embed_model,
        base_url=config.ollama_base_url,
    )
    Settings.chunk_size = config.chunk_size
    Settings.chunk_overlap = config.chunk_overlap
