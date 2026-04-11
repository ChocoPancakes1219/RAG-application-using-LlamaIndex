# R/40 - 추적성 매트릭스

| 스토리 ID | 스토리 제목 | 핵심 설계 | API/작업 |
|----------|------------|----------|---------|
| US-ARAG-01 | 내부 문서 인덱싱 요청 | ingest pipeline, Celery worker | `POST /internal/rag/documents` |
| US-ARAG-02 | 사용자별 검색 | user_id filter, metadata model | `POST /internal/rag/query` |
| US-ARAG-03 | Hybrid retrieval | Qdrant + Elasticsearch + fusion | `POST /internal/rag/query` |
| US-ARAG-04 | 인덱싱 상태 조회 | document status model | `GET /internal/rag/documents/{document_id}` |
| US-ARAG-05 | 내부 LLM 게이트웨이 | internal chat bridge, backend default Ollama path | `POST /internal/llm/chat` |
