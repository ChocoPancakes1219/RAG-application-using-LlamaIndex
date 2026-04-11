from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.adapters.elasticsearch_adapter import ElasticsearchAdapter
from app.adapters.local_index_adapter import LocalIndexAdapter
from app.adapters.qdrant_adapter import QdrantAdapter
from app.core.config import AppConfig
from app.domain.rag.schemas import ChunkRecord, DocumentRecord


@dataclass
class HybridHealthStatus:
    dense_backend: str
    dense_available: bool
    keyword_backend: str
    keyword_available: bool


@dataclass
class HybridQueryResult:
    response: str
    source_nodes: list

    def __str__(self) -> str:
        return self.response


class HybridIndexAdapter:
    """Hybrid retrieval facade for dense + lexical search orchestration."""

    def __init__(
        self,
        config: AppConfig,
        local_adapter: LocalIndexAdapter,
        qdrant_adapter: QdrantAdapter,
        elasticsearch_adapter: ElasticsearchAdapter,
    ) -> None:
        self._config = config
        self._local_adapter = local_adapter
        self._qdrant_adapter = qdrant_adapter
        self._elasticsearch_adapter = elasticsearch_adapter

    def rebuild_user_index(
        self,
        user_id: str,
        records: dict[str, DocumentRecord],
    ) -> None:
        self._local_adapter.rebuild_user_index(user_id, records)
        chunks = self._build_chunks(user_id, records)
        self._qdrant_adapter.upsert_chunks(user_id, chunks)
        self._elasticsearch_adapter.index_chunks(user_id, chunks)

    def clear_user_index(self, user_id: str) -> None:
        self._local_adapter.clear_user_index(user_id)
        self._qdrant_adapter.delete_user(user_id)
        self._elasticsearch_adapter.delete_user(user_id)

    def query_user_index(self, user_id: str, query: str, top_k: int) -> HybridQueryResult:
        dense_result = None
        dense_nodes = []
        try:
            dense_nodes = self._qdrant_adapter.query_chunks(user_id, query, top_k)
        except Exception:
            try:
                dense_result = self._local_adapter.query_user_index(user_id, query, top_k)
                dense_nodes = list(getattr(dense_result, "source_nodes", []) or [])
            except Exception:
                dense_result = None
        try:
            keyword_nodes = self._elasticsearch_adapter.query_chunks(user_id, query, top_k)
        except Exception:
            keyword_nodes = self._keyword_query(user_id, query, top_k)
        if dense_result is None and not dense_nodes and not keyword_nodes:
            raise FileNotFoundError("인덱싱된 문서가 없습니다.")
        merged_nodes = self._merge_source_nodes(dense_nodes, keyword_nodes, top_k)
        response = ""
        if dense_result is not None:
            response = str(dense_result).strip()
        response = response or self._build_keyword_summary(merged_nodes)
        if not response:
            response = "질문과 관련된 문서를 찾지 못했습니다."
        return HybridQueryResult(response=response, source_nodes=merged_nodes)

    def health_status(self) -> HybridHealthStatus:
        return HybridHealthStatus(
            dense_backend="qdrant",
            dense_available=self._safe_ping(self._qdrant_adapter),
            keyword_backend="elasticsearch",
            keyword_available=self._safe_ping(self._elasticsearch_adapter),
        )

    def _keyword_query(self, user_id: str, query: str, top_k: int) -> list:
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        candidates: list[tuple[float, str, DocumentRecord | None]] = []
        user_dir = self._config.user_data_dir(user_id)
        if not user_dir.exists():
            return []

        for path in sorted(user_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() not in {".txt", ".md"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            score = self._lexical_score(query_terms, text)
            if score <= 0:
                continue
            record = self._resolve_record(user_id, path)
            snippet = self._extract_snippet(text, query_terms)
            candidates.append((score, snippet, record))

        candidates.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, snippet, record in candidates[:top_k]:
            metadata = {
                "user_id": user_id,
                "document_id": record.document_id if record else None,
                "filename": record.filename if record else None,
                "source": "keyword",
            }
            results.append(
                SimpleNamespace(
                    node=SimpleNamespace(metadata=metadata, text=snippet),
                    score=score,
                )
            )
        return results

    def _build_chunks(
        self,
        user_id: str,
        records: dict[str, DocumentRecord],
    ) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []
        chunk_size = max(1, self._config.chunk_size)
        overlap = min(max(0, self._config.chunk_overlap), chunk_size - 1) if chunk_size > 1 else 0
        step = max(1, chunk_size - overlap)
        for filename, record in records.items():
            path = Path(record.storage_path)
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8").strip()
            except UnicodeDecodeError:
                continue
            if not text:
                continue
            for index, start in enumerate(range(0, len(text), step)):
                content = text[start : start + chunk_size].strip()
                if not content:
                    continue
                chunks.append(
                    ChunkRecord(
                        chunk_id=f"{record.document_id}:{index}:{uuid4().hex[:8]}",
                        document_id=record.document_id,
                        user_id=user_id,
                        filename=record.filename or filename,
                        content=content,
                        chunk_index=index,
                    )
                )
                if start + chunk_size >= len(text):
                    break
        return chunks

    def _resolve_record(self, user_id: str, path: Path) -> DocumentRecord | None:
        storage_path = str(path)
        metadata_path = self._config.metadata_path
        if not metadata_path.exists():
            return None

        from app.domain.rag.repositories.document_repository import DocumentRepository

        repository = DocumentRepository(metadata_path)
        for record in repository.list_by_user(user_id):
            if record.storage_path == storage_path:
                return record
        return None

    def _merge_source_nodes(self, dense_nodes: list, keyword_nodes: list, top_k: int) -> list:
        merged = []
        seen: set[tuple[str | None, str | None, str]] = set()
        for source_node in [*dense_nodes, *keyword_nodes]:
            metadata = getattr(source_node.node, "metadata", {}) or {}
            text = getattr(source_node.node, "text", "") or ""
            signature = (
                metadata.get("document_id"),
                metadata.get("filename"),
                text[:120],
            )
            if signature in seen:
                continue
            seen.add(signature)
            merged.append(source_node)
            if len(merged) >= top_k:
                break
        return merged

    def _build_keyword_summary(self, keyword_nodes: list) -> str:
        snippets = []
        for source_node in keyword_nodes[:3]:
            filename = (getattr(source_node.node, "metadata", {}) or {}).get("filename")
            text = getattr(source_node.node, "text", "") or ""
            label = filename or "문서"
            snippets.append(f"[{label}] {text}")
        return "\n".join(snippets)

    def _extract_snippet(self, text: str, query_terms: set[str]) -> str:
        lowered = text.lower()
        start = 0
        for term in query_terms:
            index = lowered.find(term)
            if index >= 0:
                start = max(0, index - 80)
                break
        snippet = text[start : start + 240].strip()
        return snippet or text[:240].strip()

    def _lexical_score(self, query_terms: set[str], text: str) -> float:
        lowered = text.lower()
        hits = 0
        for term in query_terms:
            hits += lowered.count(term)
        return float(hits)

    def _tokenize(self, text: str) -> set[str]:
        return {
            token.strip().lower()
            for token in text.split()
            if len(token.strip()) >= 2
        }

    def _safe_ping(self, adapter) -> bool:
        try:
            return bool(adapter.enabled and adapter.ping())
        except Exception:
            return False
