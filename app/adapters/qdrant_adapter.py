from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid5, NAMESPACE_URL

from llama_index.core import Settings

from app.core.config import AppConfig
from app.domain.rag.schemas import ChunkRecord

try:  # pragma: no cover - optional dependency in local env
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qm
except ImportError:  # pragma: no cover - optional dependency in local env
    QdrantClient = None
    qm = None


class QdrantAdapter:
    """Dense vector adapter backed by Qdrant."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = None

    @property
    def enabled(self) -> bool:
        return QdrantClient is not None

    def get_client(self):
        if QdrantClient is None:
            raise RuntimeError("qdrant-client dependency is not installed.")
        if self._client is None:
            self._client = QdrantClient(
                url=self._config.qdrant_url,
                api_key=self._config.qdrant_api_key,
            )
        return self._client

    def ping(self) -> bool:
        client = self.get_client()
        client.get_collections()
        return True

    def upsert_chunks(self, user_id: str, chunks: list[ChunkRecord]) -> None:
        if not chunks:
            self.delete_user(user_id)
            return
        client = self.get_client()
        embeddings = Settings.embed_model.get_text_embedding_batch(
            [chunk.content for chunk in chunks]
        )
        self._ensure_collection(len(embeddings[0]))
        self.delete_user(user_id)
        points = [
            qm.PointStruct(
                id=str(uuid5(NAMESPACE_URL, chunk.chunk_id)),
                vector=embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "user_id": chunk.user_id,
                    "filename": chunk.filename,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                },
            )
            for chunk, embedding in zip(chunks, embeddings, strict=False)
        ]
        client.upsert(
            collection_name=self._config.qdrant_collection_name,
            points=points,
            wait=True,
        )

    def query_chunks(self, user_id: str, query: str, top_k: int) -> list:
        client = self.get_client()
        response = client.query_points(
            collection_name=self._config.qdrant_collection_name,
            query=Settings.embed_model.get_text_embedding(query),
            query_filter=self._user_filter(user_id),
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )
        points = getattr(response, "points", []) or []
        return [
            SimpleNamespace(
                node=SimpleNamespace(
                    metadata={
                        "chunk_id": point.payload.get("chunk_id"),
                        "document_id": point.payload.get("document_id"),
                        "user_id": point.payload.get("user_id"),
                        "filename": point.payload.get("filename"),
                        "source": "qdrant",
                    },
                    text=point.payload.get("content", ""),
                ),
                score=getattr(point, "score", None),
            )
            for point in points
        ]

    def delete_user(self, user_id: str) -> None:
        client = self.get_client()
        if not client.collection_exists(self._config.qdrant_collection_name):
            return
        client.delete(
            collection_name=self._config.qdrant_collection_name,
            points_selector=qm.FilterSelector(filter=self._user_filter(user_id)),
            wait=True,
        )

    def delete_document(self, user_id: str, document_id: str) -> None:
        client = self.get_client()
        if not client.collection_exists(self._config.qdrant_collection_name):
            return
        client.delete(
            collection_name=self._config.qdrant_collection_name,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[
                        qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id)),
                        qm.FieldCondition(
                            key="document_id",
                            match=qm.MatchValue(value=document_id),
                        ),
                    ]
                )
            ),
            wait=True,
        )

    def _ensure_collection(self, vector_size: int) -> None:
        client = self.get_client()
        collection_name = self._config.qdrant_collection_name
        if client.collection_exists(collection_name):
            return
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
        )

    def _user_filter(self, user_id: str):
        return qm.Filter(
            must=[
                qm.FieldCondition(key="user_id", match=qm.MatchValue(value=user_id)),
            ]
        )
