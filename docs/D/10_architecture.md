# D/10 - 아키텍처 설계

## 역할

`min-minisaas-airag`는 internal RAG engine 이다.

```text
Flutter App
  -> min-minisaas-backend (public API, auth, session, orchestration)
    -> min-minisaas-airag (internal ingest/retrieve engine)
      -> Redis + Celery
      -> Qdrant
      -> Elasticsearch
      -> File Storage
```

## 책임 분리

- backend
  - JWT/auth
  - public `/api/v1/ai/rag/*`
  - user_id 주입
  - 최종 answer orchestration
- airag
  - file ingest
  - parsing/chunking
  - embedding
  - Qdrant upsert/search/delete
  - Elasticsearch index/search/delete
  - retrieval + citations
  - backend 전용 internal Ollama gateway

## 강제 원칙

### 모듈성

- HTTP 계약은 `app/api/`
- 도메인 정책은 `app/domain/rag/services/`
- metadata 저장은 `app/domain/rag/repositories/`
- 외부 시스템 연결은 `app/adapters/`
- 비동기 작업 진입점은 `app/workers/`
- internal LLM chat bridge는 retrieval과 분리된 service 경계로 유지한다

### 독립성

- 서비스 레이어는 특정 클라이언트 라이브러리에 직접 결합하지 않고 adapter를 경유한다
- backend가 없어도 internal engine 단독 실행/테스트가 가능해야 한다
- local index는 임시 구현일 뿐이며 service 계약은 Qdrant/Elasticsearch로 교체 가능해야 한다

### 이벤트 드리븐

- ingest/delete/reindex는 worker dispatcher를 경유하도록 유지한다
- eager fallback은 로컬 개발 편의일 뿐, 구조 기준은 Celery queue다

### 보안성

- internal API는 backend 전용이다
- user_id scope filter는 retrieval과 deletion에서 필수다
- API key, host, storage path는 환경변수/비밀 저장소로만 관리한다
- backend 기본 Ollama 경로는 internal gateway를 통해 전달하되, 앱에는 내부 host를 노출하지 않는다

## 리빌드 목표

- 기존 `main.py` 단일 파일 구조를 서비스/worker/adapter 구조로 분리
- txt-only + local storage 구조를 multi-format + multi-user 구조로 확장
- local persistent index를 Qdrant/Elasticsearch 기반으로 교체

## 현재 코드 구조 (2차 리빌드 기준)

```text
app/
  adapters/
    local_index_adapter.py   # 임시 local index adapter
    qdrant_adapter.py        # dense vector adapter bootstrap
    elasticsearch_adapter.py # BM25 adapter bootstrap
    hybrid_index_adapter.py  # dense + lexical orchestration facade
  api/
    internal_rag.py          # internal HTTP 계약
  core/
    config.py                # 공통 설정
  domain/rag/
    schemas.py               # request/response/status 모델
    bootstrap.py             # component wiring
    repositories/
      document_repository.py # metadata 저장
    services/
      document_service.py    # ingest/list/get/delete
      indexing_service.py    # 사용자별 local index 재빌드
      query_service.py       # retrieval/query
  workers/
    celery_app.py            # Celery/Redis bootstrap
    tasks.py                 # Celery dispatcher + eager fallback
  server.py                  # FastAPI app 조립
```
