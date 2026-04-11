# I/20 - 변경 이력

## [0.2.17] 2026-04-09 - query 대표 citation 식별 추가

> Stack Tag: `AI-RAG-STACK-2026-04-09-01`
> 이 태그가 같은 backend/app/airag 커밋을 함께 사용해야 정상 동작한다.

### Changed
- `app/domain/rag/services/query_service.py`
  - citation 기반 답변 합성 후, 응답 텍스트와 snippet overlap을 사용해 대표 근거를 선택하도록 변경
- `app/domain/rag/schemas.py`
  - `QueryResponse`에 `primary_citation_document_id`, `primary_citation_filename` 추가
- `docs/D/30_api_contract.md`, `docs/R/20_acceptance_criteria.md`, `docs/V/20_test_cases.md`
  - 대표 citation 식별 계약을 반영

### Verification
- `.venv/bin/python -m pytest tests/test_services_pytest.py -q`

## [0.1.0] 2026-04-06 - RDIV 문서 구조 도입

### Added
- `docs/README.md`
- `docs/R`, `docs/D`, `docs/I`, `docs/V`, `docs/AI` 구조 추가

### Changed
- AIRAG 저장소 역할을 `internal RAG engine`으로 명확히 정의
- `min-minisaas-backend`와의 책임 분리를 문서화

## [0.2.0] 2026-04-06 - AIRAG internal API / service 구조 1차 분리

### Added
- `app/config.py`, `app/schemas.py`, `app/repositories.py`, `app/services.py`, `app/server.py`
- `tests/test_repositories.py`, `tests/test_services.py`

### Changed
- 단일 `main.py` 엔트리포인트를 `app.server` 기반 구조로 교체
- legacy `/ingest`, `/query` 외에 internal `/internal/rag/documents*`, `/internal/rag/query` 엔드포인트 추가
- user_id별 문서 디렉터리/로컬 storage 분리와 document status metadata 저장 추가

### Verification
- `PYTHONPYCACHEPREFIX=/tmp/airag-pyc python3 - <<'PY' ... py_compile ... PY` 통과
- `python3 -m unittest discover -s tests -v` 실행 시 로컬 Python 환경에 `pydantic`, `starlette` 미설치로 실패

## [0.2.1] 2026-04-06 - AIRAG 2차 레이어 리팩터링

### Changed
- `app/config.py`, `app/repositories.py`, `app/schemas.py`, `app/services.py`를 제거하고 backend 스타일에 맞춰 재배치
- `app/api/internal_rag.py`: internal routes 분리
- `app/core/config.py`: 공통 설정 분리
- `app/domain/rag/bootstrap.py`: component wiring 추가
- `app/domain/rag/repositories/document_repository.py`: metadata 저장소 이동
- `app/domain/rag/services/document_service.py`, `indexing_service.py`, `query_service.py`: 역할별 서비스 분리

### Verification
- `PYTHONPYCACHEPREFIX=/tmp/airag-pyc python3 - <<'PY' ... py_compile ... PY` 통과

## [0.2.2] 2026-04-06 - adapters / workers 뼈대 추가

### Added
- `app/adapters/local_index_adapter.py`
- `app/adapters/qdrant_adapter.py`
- `app/adapters/elasticsearch_adapter.py`
- `app/workers/tasks.py`

### Changed
- `indexing_service.py`, `query_service.py`가 직접 LlamaIndex storage를 다루지 않고 adapter를 경유하도록 변경
- `document_service.py`가 직접 sync 재빌드 호출 대신 worker dispatcher를 경유하도록 변경
- `bootstrap.py`에서 adapter/worker wiring 추가

### Verification
- `PYTHONPYCACHEPREFIX=/tmp/airag-pyc python3 - <<'PY' ... py_compile ... PY` 통과

## [0.2.3] 2026-04-06 - Celery / Qdrant / Elasticsearch bootstrap 추가

### Changed
- `app/core/config.py`: Redis, Celery, Qdrant, Elasticsearch 환경변수 설정 추가
- `app/workers/celery_app.py`: Celery app 생성 경로 추가
- `app/workers/tasks.py`: Celery 사용 가능 시 Redis broker를 읽고, 미설치/로컬 개발 시 eager fallback을 유지하도록 변경
- `app/adapters/qdrant_adapter.py`, `app/adapters/elasticsearch_adapter.py`: 실제 client 생성 및 `ping()` 가능한 bootstrap 코드 추가
- `Requirements.txt`: `celery`, `redis`, `qdrant-client`, `elasticsearch` 의존성 추가

### Verification
- `PYTHONPYCACHEPREFIX=/tmp/airag-pyc python3 - <<'PY' ... py_compile ... PY` 통과

## [0.2.4] 2026-04-06 - runtime convention을 backend conda env 기준으로 정렬

### Changed
- `README.md`, `SIMPLE-START.md`, `docs/README.md`
  - local runtime/install/test 예시를 `conda run -n backend ...` 기준으로 정렬

## [0.2.5] 2026-04-06 - VS Code 실행 환경 정렬

### Changed
- `.vscode/settings.json`
  - `${workspaceFolder}/.venv/bin/python` interpreter, unittest discovery, macOS terminal env 설정 추가
- `.vscode/launch.json`
  - FastAPI(`uvicorn main:app`) 실행과 unittest 실행 구성을 추가

## [0.2.6] 2026-04-06 - Python 3.12 .venv 재구성과 실행 검증

### Changed
- 기존 Python 3.9 `.venv`를 제거하고 backend 기준 Python 3.12로 재생성
- `Requirements.txt` 의존성을 새 `.venv`에 설치

### Verification
- `.venv/bin/python --version` -> `Python 3.12.13`
- `.venv/bin/python -m unittest discover -s tests -v` -> `4 passed`
- adapter live ping
  - qdrant: connection refused
  - elasticsearch: ping false

## [0.2.7] 2026-04-06 - 아키텍처 원칙 명시 강화

### Changed
- `docs/README.md`
  - 모듈성, 독립성, 이벤트 드리븐, 보안성 원칙을 명시적으로 추가
- `docs/D/10_architecture.md`
  - 레이어별 강제 원칙과 security boundary를 보강
- `docs/V/30_security_review.md`
  - backend 우회 금지, user scope, 비밀값/내부 host 보호 체크리스트를 강화

## [0.2.8] 2026-04-06 - 민감 설정 .env 분리

### Added
- `.env.example`
  - Redis, Qdrant, Elasticsearch 설정 템플릿 추가

### Changed
- `app/server.py`
  - 서버 시작 시 `.env`를 자동 로드하도록 `python-dotenv` 연결

### Security
- 실제 비밀값은 `.env`로만 관리하고, `.gitignore`로 커밋 제외 유지

## [0.2.9] 2026-04-06 - VS Code env 주입 및 hybrid adapter 연결

### Changed
- `.vscode/settings.json`
  - `python.envFile`, `python.terminal.useEnvFile`를 추가해 terminal에서도 `.env`가 주입되도록 수정
- `app/adapters/hybrid_index_adapter.py`
  - dense(local LlamaIndex) + lexical(local keyword fallback) 조합과 Qdrant/Elasticsearch health 체크를 담당하는 facade 추가
- `app/domain/rag/bootstrap.py`
  - `LocalIndexAdapter`, `QdrantAdapter`, `ElasticsearchAdapter`를 직접 service에 넘기지 않고 `HybridIndexAdapter`로 조립하도록 변경
- `app/domain/rag/services/indexing_service.py`, `app/domain/rag/services/query_service.py`
  - service가 hybrid adapter 계약만 바라보도록 변경

### Verification
- `.env` 기준 adapter ping 및 unittest 재실행 예정

## [0.2.10] 2026-04-06 - live ping 검증 및 hybrid query 테스트 안정화

### Changed
- `tests/test_services.py`
  - hybrid query 테스트가 외부 LLM/Ollama/OpenAI 상태에 의존하지 않도록 fallback 중심으로 안정화
- `docs/V/20_test_cases.md`
  - `.env` 기준 live ping 결과와 최신 unittest 결과를 반영

### Verification
- `.venv/bin/python -m unittest discover -s tests -v` -> `5 passed`
- `.env` 기준 live ping
  - `qdrant`: `ping() -> True`
  - `elasticsearch`: `ping() -> True`

## [0.2.11] 2026-04-06 - internal API key 경계와 gitignore 보강

### Changed
- `.gitignore`
  - secret/certificate/test cache 패턴을 추가해 민감 파일과 로컬 산출물이 git에 섞이지 않도록 강화
- `.env.example`
  - `AIRAG_INTERNAL_API_KEY` 템플릿 추가
- `app/core/config.py`
  - internal API key 설정과 constant-time 비교 추가
- `app/api/internal_rag.py`
  - 모든 internal/legacy RAG 엔드포인트에 `X-Internal-API-Key` 검증 추가
- `docs/D/30_api_contract.md`, `docs/V/30_security_review.md`
  - backend 호출 헤더 계약과 보안 경계를 문서화

## [0.2.12] 2026-04-07 - VS Code Python Debugger 전환

### Changed
- `.vscode/launch.json`
  - deprecated `type: "python"` 구성을 `type: "debugpy"`로 변경해 새 Python Debugger 확장 기준에 맞춤

## [0.2.13] 2026-04-07 - Celery 실동작 전환

### Changed
- `app/workers/celery_app.py`, `app/workers/tasks.py`
  - Celery app을 모듈 레벨로 고정하고 `airag.rebuild_user_index`, `airag.delete_user_index` task를 실제 등록
- `app/domain/rag/services/document_service.py`
  - 업로드 시 즉시 `ready`로 바꾸지 않고, 비동기 모드에서는 `queued`로 유지한 뒤 worker가 `processing -> ready/failed`를 갱신하도록 변경
- `.env`, `.env.example`
  - 기본 실행 모드를 `CELERY_TASK_ALWAYS_EAGER=false`로 변경
- `.vscode/launch.json`
  - `AIRAG Celery Worker` 디버그 구성을 추가
- `tests/test_services.py`
  - eager / async lifecycle 테스트를 분리하고 worker 완료 처리 테스트를 추가

### Verification
- `.venv/bin/python -m unittest discover -s tests -v` -> `7 passed`
- `celery_app.tasks` 확인
  - `airag.rebuild_user_index`
  - `airag.delete_user_index`

## [0.2.14] 2026-04-07 - pytest 스위트 추가

### Changed
- `Requirements.txt`
  - `pytest`, `pytest-asyncio` 추가
- `pytest.ini`
  - `asyncio_mode=auto`, `testpaths=tests` 설정 추가
- `tests/conftest.py`
  - 공통 RAG fixture와 upload helper 추가
- `tests/test_repository_pytest.py`, `tests/test_services_pytest.py`
  - repository/service/query 핵심 흐름의 pytest 버전 테스트 추가
- `.vscode/launch.json`
  - `AIRAG Pytest` 실행 구성을 추가

## [0.2.15] 2026-04-07 - Qdrant/Elasticsearch 실저장 흐름 1차 연결

### Changed
- `app/domain/rag/schemas.py`
  - chunk 단위 저장을 위한 `ChunkRecord` 모델 추가
- `app/adapters/qdrant_adapter.py`
  - chunk embedding upsert, user/document 범위 delete, dense query 구현 추가
- `app/adapters/elasticsearch_adapter.py`
  - BM25 index/search/delete 구현 추가
- `app/adapters/hybrid_index_adapter.py`
  - rebuild 시 local fallback과 함께 Qdrant/Elasticsearch에 chunk를 적재하고, query 시 원격 hybrid retrieval을 우선 사용하도록 변경
- `tests/test_services.py`, `tests/test_services_pytest.py`
  - remote query 경고를 피하도록 mock 범위를 명확히 하고, rebuild가 Qdrant/Elasticsearch adapter를 호출하는 pytest 검증 추가

### Verification
- `.venv/bin/python -m unittest discover -s tests -v` -> `7 passed`
- `.venv/bin/python -m pytest -q` -> `15 passed`

## [0.2.16] 2026-04-07 - 로컬 Redis broker 포트 정렬

### Changed
- `.env`
  - `REDIS_URL`을 `redis://localhost:36378/0`로 수정해 실제 로컬 Redis 포트와 일치시킴

## [0.2.17] 2026-04-07 - Redis 인증 정렬

### Changed
- `app/core/config.py`
  - backend와 같은 방식으로 `REDIS_PASSWORD`, `redis_url_with_auth` 지원 추가
- `app/workers/celery_app.py`
  - Celery broker/backend가 인증 포함 Redis URL을 사용하도록 변경
- `.env.example`, `.env`
  - 로컬 Redis 인증 정보 반영

## [0.2.18] 2026-04-07 - Redis DB namespace 분리

### Changed
- `.env`, `.env.example`, `.env.development`
  - AIRAG Redis DB를 `15`로 고정해 backend 기본 DB `0`과 분리

### Notes
- namespace rule
  - backend: `redis://localhost:36378/0`
  - airag: `redis://localhost:36378/15`

## [0.2.19] 2026-04-07 - live e2e pytest 추가

### Changed
- `pytest.ini`
  - `e2e` marker를 추가해 live integration 테스트를 일반 pytest와 분리
- `tests/test_e2e_pytest.py`
  - running AIRAG server를 상대로 ingest/query/delete를 검증하는 live e2e pytest 추가
- `.vscode/launch.json`
  - `AIRAG Pytest E2E` 실행 구성 추가
- `docs/V/20_test_cases.md`
  - live e2e 실행 방법과 기대 결과 반영

## [0.2.20] 2026-04-07 - 독립 QA client 프로젝트 추가

### Changed
- `qa/airag_qa_client/`
  - `runner.py`, `scenarios/`, `fixtures/`, `reports/`, `README.md` 추가
- `.gitignore`
  - QA report JSON 산출물 제외
- `README.md`, `docs/D/40_runtime_config.md`, `docs/V/20_test_cases.md`
  - QA client 위치와 실행 방법 반영

## [0.2.21] 2026-04-07 - internal API key 기본값 제거

### Changed
- `tests/test_e2e_pytest.py`
  - `AIRAG_INTERNAL_API_KEY` 기본값 제거, env 미설정 시 skip
- `qa/airag_qa_client/runner.py`
  - internal API key env가 없으면 즉시 실패하도록 변경
- `qa/airag_qa_client/README.md`
  - API key export를 필수 단계로 명시

## [0.2.22] 2026-04-07 - QA client 실행 편의 개선

### Changed
- `qa/airag_qa_client/runner.py`
  - 루트 `.env`를 자동으로 로드하고 기본 scenario를 smoke로 설정
- `qa/airag_qa_client/run_smoke.sh`
  - 한 줄 smoke 실행 스크립트 추가
- `.vscode/launch.json`
  - `AIRAG QA Smoke` 실행 구성 추가
- `qa/airag_qa_client/README.md`, `README.md`
  - 더 짧은 실행 방법 반영

## [0.2.23] 2026-04-07 - QA env 분리

### Changed
- `qa/airag_qa_client/.env.qa.example`
  - QA 전용 환경 템플릿 추가
- `qa/airag_qa_client/runner.py`
  - 루트 `.env` 대신 `qa/airag_qa_client/.env.qa`만 읽도록 변경
- `.gitignore`
  - `qa/airag_qa_client/.env.qa` 제외 추가
- `qa/airag_qa_client/README.md`, `README.md`, `docs/D/40_runtime_config.md`
  - QA env 분리 규칙과 실행 절차 반영

## [0.2.24] 2026-04-07 - QA 폴더 진입 실행 지원

### Changed
- `qa/airag_qa_client/run.sh`
  - QA 폴더 안에서 바로 실행할 수 있는 wrapper 추가
- `qa/airag_qa_client/README.md`, `README.md`
  - `cd qa/airag_qa_client && bash run.sh` 기준으로 실행 방법 단순화

## [0.2.25] 2026-04-07 - QA 정답지 비교 강화

### Changed
- `qa/airag_qa_client/scenarios/smoke.json`
  - `expected_answer_contains`, `expected_filenames`, `min_citations` 정답지 필드 추가
- `qa/airag_qa_client/runner.py`
  - keyword hit뿐 아니라 answer phrase, citation filename, minimum citation count를 함께 평가하도록 확장
- `qa/airag_qa_client/README.md`, `docs/V/20_test_cases.md`
  - QA 결과 해석과 정답지 비교 항목 반영

## [0.2.26] 2026-04-07 - 한국어 QA 시나리오와 블로그 초안 추가

### Changed
- `qa/airag_qa_client/fixtures/korean_incident_guide.txt`, `qa/airag_qa_client/scenarios/korean_incident_guide.json`
  - 한국어 설명문 기반 질의응답 QA 시나리오 추가
- `qa/airag_qa_client/fixtures/league_table_2003.txt`, `qa/airag_qa_client/scenarios/league_table_hard.json`
  - 표형 데이터 hard QA 시나리오와 다중 case 평가 추가
- `qa/airag_qa_client/runner.py`
  - 다중 case 시나리오, 금지 phrase 검증, QA 상대경로 시나리오 실행을 지원하도록 확장
- `qa/airag_qa_client/README.md`
  - 한국어/하드 시나리오 실행 방법 추가
- `docs/AI/90_blog_post_local_rag.md`
  - 로컬 RAG 실험 결과를 정리한 블로그용 마크다운 초안 추가

### Verification
- `.venv/bin/python -m pytest -q` -> `17 passed, 1 skipped`
- `bash qa/airag_qa_client/run.sh --scenario scenarios/korean_incident_guide.json` -> `passed: true`
- `bash qa/airag_qa_client/run.sh --scenario scenarios/league_table_hard.json`
  - 5 case 중 1 case 통과로 표형 데이터 한계 확인

## [0.2.27] 2026-04-08 - internal Ollama gateway 추가

### Added
- `app/domain/rag/services/chat_service.py`
  - backend 기본 Ollama 대화 요청을 로컬 Ollama `/api/generate`로 전달하는 internal service 추가
- `tests/test_internal_chat_pytest.py`
  - internal chat service의 Ollama 호출 경로 검증 추가

### Changed
- `app/core/config.py`
  - `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBED_MODEL` 설정 추가
- `app/domain/rag/bootstrap.py`
  - chat service wiring과 Ollama 설정값 공통화
- `app/domain/rag/schemas.py`
  - `InternalChatRequest`, `InternalChatResponse` 추가
- `app/api/internal_rag.py`, `app/server.py`
  - `POST /internal/llm/chat` endpoint 추가

### Notes
- final answer orchestration 기본 책임은 여전히 backend에 둔다
- 이 endpoint는 backend 기본 Ollama 트래픽을 숨은 internal path로 수렴시키기 위한 bridge이다

## [0.2.28] 2026-04-09 - query response synthesis 추가

### Changed
- `app/domain/rag/services/query_service.py`
  - hybrid retrieval 결과의 `citations`를 기반으로 Ollama `/api/chat` 합성 단계를 추가
  - synthesis 실패 시 기존 retrieval fallback 문자열을 유지하도록 보강
- `tests/test_services_pytest.py`
  - query synthesis 성공/실패 fallback 테스트 추가

### Notes
- retrieval/citation 구조는 유지하고 `response` 품질만 개선한다
- 답변 합성 실패 시에도 검색 결과를 잃지 않도록 fallback을 유지한다
