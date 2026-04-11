from __future__ import annotations

from types import SimpleNamespace

from app.core.config import AppConfig
from app.domain.rag.schemas import ChunkRecord

try:  # pragma: no cover - optional dependency in local env
    from elasticsearch import Elasticsearch
except ImportError:  # pragma: no cover - optional dependency in local env
    Elasticsearch = None


class ElasticsearchAdapter:
    """BM25 adapter backed by Elasticsearch."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = None

    @property
    def enabled(self) -> bool:
        return Elasticsearch is not None

    def get_client(self):
        if Elasticsearch is None:
            raise RuntimeError("elasticsearch dependency is not installed.")
        if self._client is None:
            kwargs = {}
            if self._config.elasticsearch_api_key:
                kwargs["api_key"] = self._config.elasticsearch_api_key
            self._client = Elasticsearch(
                self._config.elasticsearch_url,
                **kwargs,
            )
        return self._client

    def ping(self) -> bool:
        client = self.get_client()
        return bool(client.ping())

    def index_chunks(self, user_id: str, chunks: list[ChunkRecord]) -> None:
        client = self.get_client()
        self._ensure_index()
        self.delete_user(user_id)
        operations = []
        for chunk in chunks:
            operations.extend(
                [
                    {"index": {"_index": self._config.elasticsearch_index_name, "_id": chunk.chunk_id}},
                    {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "user_id": chunk.user_id,
                        "filename": chunk.filename,
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                    },
                ]
            )
        if operations:
            client.bulk(operations=operations, refresh=True)

    def query_chunks(self, user_id: str, query: str, top_k: int) -> list:
        client = self.get_client()
        self._ensure_index()
        response = client.search(
            index=self._config.elasticsearch_index_name,
            size=top_k,
            query={
                "bool": {
                    "filter": [{"term": {"user_id": user_id}}],
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["content^2", "filename"],
                            }
                        }
                    ],
                }
            },
        )
        hits = response.get("hits", {}).get("hits", [])
        return [
            SimpleNamespace(
                node=SimpleNamespace(
                    metadata={
                        "chunk_id": hit.get("_source", {}).get("chunk_id"),
                        "document_id": hit.get("_source", {}).get("document_id"),
                        "user_id": hit.get("_source", {}).get("user_id"),
                        "filename": hit.get("_source", {}).get("filename"),
                        "source": "elasticsearch",
                    },
                    text=hit.get("_source", {}).get("content", ""),
                ),
                score=hit.get("_score"),
            )
            for hit in hits
        ]

    def delete_user(self, user_id: str) -> None:
        client = self.get_client()
        if not client.indices.exists(index=self._config.elasticsearch_index_name):
            return
        client.delete_by_query(
            index=self._config.elasticsearch_index_name,
            query={"term": {"user_id": user_id}},
            refresh=True,
        )

    def delete_document(self, user_id: str, document_id: str) -> None:
        client = self.get_client()
        if not client.indices.exists(index=self._config.elasticsearch_index_name):
            return
        client.delete_by_query(
            index=self._config.elasticsearch_index_name,
            query={
                "bool": {
                    "filter": [
                        {"term": {"user_id": user_id}},
                        {"term": {"document_id": document_id}},
                    ]
                }
            },
            refresh=True,
        )

    def _ensure_index(self) -> None:
        client = self.get_client()
        index_name = self._config.elasticsearch_index_name
        if client.indices.exists(index=index_name):
            return
        client.indices.create(
            index=index_name,
            mappings={
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "filename": {"type": "keyword"},
                    "content": {"type": "text"},
                    "chunk_index": {"type": "integer"},
                }
            },
        )
