# I/10 - 구현 계획 및 상태

## 현재 상태

- 오픈소스 포크 기반 단일 `main.py`
- txt 업로드 + local Ollama + local storage query 수준
- multi-user, async indexing, Qdrant, Elasticsearch는 미반영

## 다음 구현 단계

- [x] docs/README.md + RDIV 구조 정비
- [x] 앱 공개 API와 internal API 경계 확정
- [x] 단일 `main.py`를 internal API + service/repository 구조로 1차 분리
- [x] `api -> domain/rag -> core` 기준의 2차 리팩터링
- [x] `adapters`, `workers` 뼈대 추가 및 service 연결
- [x] 문서 상태 모델 추가 (`queued`, `processing`, `ready`, `failed`)
- [x] user_id 기준 문서 디렉터리 / local index 분리 구조 추가
- [x] Celery + Redis bootstrap / eager fallback 추가
- [x] Qdrant adapter bootstrap 추가
- [x] Elasticsearch adapter bootstrap 추가
- [ ] hybrid retrieval + citations 구현 고도화
- [ ] 테스트/관찰성 추가
