# AI/20 — 태스크 큐

## 진행 중 (In Progress)

| ID | 태스크 | 담당 | 메모 |
|----|--------|------|------|
| ARAG-01 | AIRAG RDIV 구조 정리 | AI/개발자 | backend gateway / airag engine 책임 분리 |
| ARAG-08 | internal LLM gateway 추가 | AI/개발자 | backend 기본 Ollama 트래픽을 AIRAG internal endpoint로 수렴 |

## 대기 중 (Pending)

| ID | 태스크 | 설명 |
|----|--------|------|
| ARAG-02 | ingest pipeline 리빌드 | txt/md/pdf 파싱, chunking, Celery task 분리 |
| ARAG-03 | Qdrant adapter 추가 | dense vector upsert/search/delete |
| ARAG-04 | Elasticsearch adapter 추가 | BM25 index/search/delete |
| ARAG-05 | hybrid retrieval 구현 | dense + BM25 score fusion + citations |
| ARAG-06 | user_id 격리 | 모든 인덱스/조회/삭제에 user scope 필터 적용 |
| ARAG-07 | backend internal API 정합성 | min-minisaas-backend와 request/response 계약 정렬 |

## 완료 (Completed)

| ID | 태스크 | 완료일 | 결과 |
|----|--------|--------|------|
