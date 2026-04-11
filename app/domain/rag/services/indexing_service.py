from __future__ import annotations

from pathlib import Path

from app.adapters.hybrid_index_adapter import HybridIndexAdapter
from app.core.config import AppConfig
from app.domain.rag.repositories.document_repository import DocumentRepository
from app.domain.rag.schemas import DocumentRecord, DocumentStatus


class IndexingService:
    def __init__(
        self,
        config: AppConfig,
        repository: DocumentRepository,
        index_adapter: HybridIndexAdapter,
    ) -> None:
        self._config = config
        self._repository = repository
        self._index_adapter = index_adapter

    def rebuild_user_index(self, user_id: str) -> None:
        records = {
            Path(item.storage_path).name: item
            for item in self._repository.list_by_user(user_id)
            if item.status
            in {
                DocumentStatus.processing,
                DocumentStatus.ready,
                DocumentStatus.queued,
            }
        }
        self._index_adapter.rebuild_user_index(user_id, records)

    def estimate_chunk_count(self, text: str) -> int:
        normalized = max(1, len(text.strip()))
        chunk_size = max(1, self._config.chunk_size)
        return max(1, (normalized + chunk_size - 1) // chunk_size)
