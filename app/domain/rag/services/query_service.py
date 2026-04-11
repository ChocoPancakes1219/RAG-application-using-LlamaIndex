from __future__ import annotations

from collections.abc import Iterable
import re

import httpx
from fastapi import HTTPException

from app.adapters.hybrid_index_adapter import HybridIndexAdapter
from app.core.config import AppConfig
from app.domain.rag.schemas import QueryCitation, QueryRequest, QueryResponse

_QUERY_SYNTHESIS_SYSTEM_PROMPT = (
    "You are a retrieval answer synthesizer for an internal RAG engine. "
    "Answer using only the provided citations. "
    "Prefer the highest-scoring citation when it directly answers the question. "
    "Keep the answer concise and natural. "
    "If the answer is not supported by the citations, say that the answer could not be found."
)


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
        response = self._synthesize_response(
            query=request.query,
            citations=citations,
            fallback=str(result),
        )
        primary_citation = self._select_primary_citation(
            response=response,
            citations=citations,
        )
        return QueryResponse(
            user_id=request.user_id,
            query=request.query,
            response=response,
            citations=citations,
            primary_citation_document_id=(
                primary_citation.document_id if primary_citation else None
            ),
            primary_citation_filename=(
                primary_citation.filename if primary_citation else None
            ),
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

    def _synthesize_response(
        self,
        *,
        query: str,
        citations: list[QueryCitation],
        fallback: str,
    ) -> str:
        if not citations:
            return fallback

        context_lines = []
        for index, citation in enumerate(citations[:3], start=1):
            label = citation.filename or f"document-{index}"
            score = f"{citation.score:.3f}" if citation.score is not None else "n/a"
            context_lines.append(
                f"[{index}] filename={label} score={score}\n{citation.snippet}"
            )

        payload = {
            "model": self._config.ollama_chat_model,
            "messages": [
                {"role": "system", "content": _QUERY_SYNTHESIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Question:\n{query}\n\n"
                        f"Citations:\n{chr(10).join(context_lines)}\n\n"
                        "Return only the final answer."
                    ),
                },
            ],
            "stream": False,
            "options": {"num_predict": 256},
        }

        try:
            with httpx.Client(
                base_url=self._config.ollama_base_url.rstrip("/"),
                timeout=20,
            ) as client:
                response = client.post("/api/chat", json=payload)
                if not response.is_success:
                    return fallback
                data = response.json()
        except Exception:
            return fallback

        message = data.get("message")
        if isinstance(message, dict):
            content = (message.get("content") or "").strip()
            if content:
                return content
        return fallback

    def _select_primary_citation(
        self,
        *,
        response: str,
        citations: list[QueryCitation],
    ) -> QueryCitation | None:
        if not citations:
            return None

        response_tokens = self._tokenize(response)
        best_citation = citations[0]
        best_rank = self._citation_rank(best_citation, response_tokens)

        for citation in citations[1:]:
            rank = self._citation_rank(citation, response_tokens)
            if rank > best_rank:
                best_citation = citation
                best_rank = rank
        return best_citation

    def _citation_rank(
        self,
        citation: QueryCitation,
        response_tokens: set[str],
    ) -> tuple[float, float]:
        snippet_tokens = self._tokenize(citation.snippet)
        if response_tokens and snippet_tokens:
            overlap = len(response_tokens & snippet_tokens) / len(response_tokens)
        else:
            overlap = 0.0
        score = citation.score if citation.score is not None else float("-inf")
        return (overlap, score)

    def _tokenize(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[0-9A-Za-z가-힣]+", text.lower())
            if len(token) >= 2
        }
