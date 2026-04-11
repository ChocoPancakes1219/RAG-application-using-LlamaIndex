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

## ADR-005: 환경설정은 코드 기본값보다 env와 템플릿으로 관리한다

- `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBED_MODEL` 같은 runtime 설정은 코드에 하드코딩된 기본값으로 숨기지 않는다
- 실제 실행값은 `.env`, `.env.development`, `.env.production` 같은 실행 환경 파일이나 배포 환경변수에서 관리한다
- `.env.example`에는 실제값이나 운영값처럼 보이는 내용을 넣지 않고, placeholder만 둔다
- Git에 추적되는 파일에는 secret뿐 아니라 운영 실값처럼 오해될 수 있는 설정값도 넣지 않는 쪽을 기본 원칙으로 한다
- 설정 변경 시에는 "이 값이 Git에 올라가도 되는가"를 먼저 점검하고, 편의보다 배포 안전성을 우선한다
