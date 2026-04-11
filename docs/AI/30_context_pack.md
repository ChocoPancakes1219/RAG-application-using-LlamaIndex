# AI/30 — 컨텍스트 팩

## 프로젝트 한 줄 요약

`min-minisaas-airag`는 `min-minisaas-backend` 뒤에서 동작하는 internal RAG engine 이다.

## 현재 상태

- 기반: LlamaIndex + Ollama 오픈소스 포크
- 리빌드 대상: 단일 로컬 txt ingest/query 앱
- 목표: Celery + Redis + Qdrant + Elasticsearch 기반 multi-user RAG engine

## 핵심 경계

- 앱은 이 저장소를 직접 호출하지 않는다
- 공개 API는 `min-minisaas-backend`
- 이 저장소는 internal API와 worker 처리만 담당한다

## 우선 리빌드 대상

- `POST /ingest` 단일 파일 업로드 엔드포인트
- `GET /query` 단일 질의 엔드포인트
- 로컬 storage 기반 인덱스 처리
- txt 전용 파일 처리

## 다음 목표

- 파일 상태 모델 추가
- 비동기 인덱싱
- user_id 기반 분리
- Qdrant/Elasticsearch hybrid retrieval
