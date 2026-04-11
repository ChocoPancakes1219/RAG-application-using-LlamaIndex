from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException

from app.adapters.hybrid_index_adapter import HybridIndexAdapter
from app.core.config import AppConfig
from app.domain.rag.schemas import QueryCitation, QueryRequest, QueryResponse


class QueryService:
    def __init__(self, config: AppConfig, index_adapter: HybridIndexAdapter) -> None:
        self._config = config
        self._index_adapter = index_adapter

    def query(self, request: QueryRequest) -> QueryResponse:
        try:
            result = self._index_adapter.query_user_index(
                request.user_id,
                request.query,
                request.top_k,
            )
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="인덱싱된 문서가 없습니다.")
        citations = self._to_citations(result.source_nodes)
        return QueryResponse(
            user_id=request.user_id,
            query=request.query,
            response=str(result),
            citations=citations,
        )

    def _to_citations(self, source_nodes: Iterable) -> list[QueryCitation]:
        citations: list[QueryCitation] = []
        for source_node in source_nodes:
            metadata = getattr(source_node.node, "metadata", {}) or {}
            text = getattr(source_node.node, "text", "") or ""
            citations.append(
                QueryCitation(
                    document_id=metadata.get("document_id"),
                    filename=metadata.get("filename"),
                    score=getattr(source_node, "score", None),
                    snippet=text[:240],
                )
            )
        return citations
