# D/90 - 결정 기록

## ADR-001: AIRAG는 internal engine으로 유지한다

- 앱은 직접 호출하지 않는다
- 공개 API는 `min-minisaas-backend`가 담당한다

## ADR-002: dense vector는 Qdrant, keyword search는 Elasticsearch로 분리한다

- dense semantic retrieval은 Qdrant
- BM25/keyword 보조 검색은 Elasticsearch
- hybrid fusion은 engine service에서 수행한다

## ADR-003: 인덱싱은 Celery + Redis 비동기 처리로 전환한다

- 업로드 요청의 응답 시간을 짧게 유지
- 장시간 문서 파싱/임베딩 작업을 worker로 분리

## ADR-004: backend 기본 Ollama 경로는 AIRAG internal gateway로 수렴한다

- 앱에는 내부 Ollama host를 직접 노출하지 않는다
- backend는 사용자 custom URL이 없을 때 AIRAG `/internal/llm/chat`을 기본 경로로 사용한다
- custom Ollama URL이 설정된 경우에만 backend가 사용자 지정 host로 직접 연결한다
