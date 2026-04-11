# V/40 - 관찰성

## 핵심 지표

- ingest 요청 수
- 인덱싱 성공/실패 수
- 평균 chunk 수
- retrieval latency
- Qdrant 검색 latency
- Elasticsearch 검색 latency
- Celery queue 적체량

## 로그 포인트

- document_id, user_id, task_id
- status transition
- retrieval top_k, latency, source count
