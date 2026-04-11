from __future__ import annotations

from pathlib import Path

from llama_index.core import SimpleDirectoryReader, StorageContext
from llama_index.core import VectorStoreIndex, load_index_from_storage

from app.core.config import AppConfig
from app.domain.rag.schemas import DocumentRecord


class LocalIndexAdapter:
    """Temporary adapter used until Qdrant/Elasticsearch are wired in."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def rebuild_user_index(
        self,
        user_id: str,
        records: dict[str, DocumentRecord],
    ) -> None:
        user_data_dir = self._config.user_data_dir(user_id)
        user_storage_dir = self._config.user_storage_dir(user_id)
        user_storage_dir.mkdir(parents=True, exist_ok=True)

        if not user_data_dir.exists():
            self.clear_user_index(user_id)
            return

        files = [
            path
            for path in user_data_dir.iterdir()
            if path.is_file() and path.name in records
        ]
        if not files:
            self.clear_user_index(user_id)
            return

        reader = SimpleDirectoryReader(
            input_files=[str(path) for path in files],
            file_metadata=lambda path: self._build_metadata(path, user_id, records),
        )
        documents = reader.load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=str(user_storage_dir))

    def query_user_index(self, user_id: str, query: str, top_k: int):
        user_storage_dir = self._config.user_storage_dir(user_id)
        if not user_storage_dir.exists():
            raise FileNotFoundError("인덱싱된 문서가 없습니다.")

        storage_context = StorageContext.from_defaults(
            persist_dir=str(user_storage_dir),
        )
        index = load_index_from_storage(storage_context)
        query_engine = index.as_query_engine(
            response_mode="compact",
            similarity_top_k=top_k,
        )
        return query_engine.query(query)

    def clear_user_index(self, user_id: str) -> None:
        user_storage_dir = self._config.user_storage_dir(user_id)
        if not user_storage_dir.exists():
            return
        for child in user_storage_dir.iterdir():
            if child.is_file():
                child.unlink()

    def _build_metadata(
        self,
        path: str,
        user_id: str,
        records: dict[str, DocumentRecord],
    ) -> dict[str, str]:
        filename = Path(path).name
        record = records.get(filename)
        return {
            "user_id": user_id,
            "document_id": record.document_id if record else "",
            "filename": record.filename if record else filename,
        }
