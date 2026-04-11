# V/20 - 테스트 케이스

## TC-ARAG-01: ingest 요청 수락

- 대상: `POST /internal/rag/documents`
- 기대: `document_id`, `status` 반환

## TC-ARAG-02: user_id 격리 검색

- 대상: `POST /internal/rag/query`
- 기대: 다른 user_id chunk 미포함

## TC-ARAG-03: 상태 조회

- 대상: `GET /internal/rag/documents/{document_id}`
- 기대: `queued/processing/ready/failed` 상태 반환

## TC-ARAG-04: live e2e ingest/query/delete

- 대상: running AIRAG server + Celery worker + Ollama + Qdrant + Elasticsearch + Redis
- 실행:
  - `pytest -m e2e -q tests/test_e2e_pytest.py`
- 기대:
  - upload 후 `queued/processing/ready`
  - query citations 반환
  - delete `204`

## TC-ARAG-05: QA client smoke run

- 대상: `qa/airag_qa_client/runner.py`
- 실행:
  - `.venv/bin/python qa/airag_qa_client/runner.py --scenario qa/airag_qa_client/scenarios/smoke.json`
- 기대:
  - report JSON 생성
  - expected keyword / answer / filename / citation count 정답지 비교

## 2026-04-06 실행 결과

- `PYTHONPYCACHEPREFIX=/tmp/airag-pyc .venv/bin/python -m py_compile ...`: 통과
- `.venv/bin/python -m unittest discover -s tests -v`: 통과 (`5 passed`)
- `pytest -q`: 통과 (`15 passed`)
- live e2e pytest: 수동 실행용 추가
- QA client: 수동 실행용 추가
- document ingest lifecycle
  - eager 모드: 업로드 직후 `ready`
  - Celery 비동기 모드: 업로드 직후 `queued`, worker 처리 후 `ready`
- `.env` 기반 live ping
  - `QDRANT_URL=http://localhost:36333`
  - `ELASTICSEARCH_URL=http://localhost:39200`
  - `qdrant`: `ping() -> True`
  - `elasticsearch`: `ping() -> True`
- `conda run -n backend python -m unittest discover -s tests -v`: 예정
- `python3 -m unittest discover -s tests -v`: 실패
  - 원인: 현재 로컬 Python 환경에 `pydantic`, `starlette` 패키지 미설치
- `.venv/bin/python` import smoke check: `pydantic`, `fastapi`, `starlette`, `celery`, `redis`, `qdrant_client`, `elasticsearch` 모두 통과
