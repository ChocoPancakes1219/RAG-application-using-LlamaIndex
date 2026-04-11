# R/00 - 프로젝트 개요

`min-minisaas-airag`는 `min-minisaas-backend`가 호출하는 internal AI RAG engine 이다.

- 역할: 문서 ingest, chunking, embedding, indexing, retrieval
- 비역할: 앱 공개 API, 사용자 인증, 앱 세션 관리
- 저장소: Qdrant(dense vector), Elasticsearch(BM25), Redis(Celery broker/backend)
