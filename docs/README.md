# MiniSaaS AIRAG 문서

> **문서는 internal RAG engine 유지보수를 위한 실행 기준이다.**
>
> 이 저장소는 앱이 직접 호출하는 공개 API가 아니라, `min-minisaas-backend`가 호출하는 내부 AI RAG 엔진이다.
> 모든 변경은 문서와 동기화되어야 한다.

---

## Start Here

**AI 또는 신규 개발자라면 반드시 이 파일을 먼저 읽어라.**

작업 시작 전 항상 다음 Runbook을 따른다:

- [AI/31_rdiv_execution_runbook.md](AI/31_rdiv_execution_runbook.md) — 작업 실행 단계별 가이드

---

## 문서 구조

| 폴더 | 목적 |
|------|------|
| `R/` | Requirements — 요구사항, 유저 스토리, 인수 기준, 비기능 요구사항 |
| `D/` | Design — 아키텍처, 데이터 모델, API 계약, 아키텍처 결정 기록 |
| `I/` | Implementation — 구현 계획, 변경 이력, 운영 메모 |
| `V/` | Verification — 테스트 계획, 테스트 케이스, 보안 검토, 관찰성 |
| `AI/` | AI Context — 프로젝트 브리프, 코딩 규칙, 작업 큐, 컨텍스트 팩 |

---

## Default Instruction for AI

1. **작업 시작 전** `AI/31_rdiv_execution_runbook.md`를 읽고 단계별로 따른다.
2. **코드 작성 전** `D/10_architecture.md`에서 internal engine 책임과 boundary를 확인한다.
3. **internal API 변경 시** `D/30_api_contract.md`를 먼저 갱신하고 코드를 수정한다.
4. **Qdrant / Elasticsearch / Celery / Redis 변경 시** `V/30_security_review.md`와 `V/40_observability.md`를 함께 확인한다.
5. **완료 전** R/D/I/V 문서를 동시 갱신한다.

## Runtime Convention

- 로컬 실행 환경은 backend와 동일한 `conda`의 `backend` env를 기본으로 사용한다
- 예시:
  - `conda run -n backend python -m pip install -r Requirements.txt`
  - `conda run -n backend uvicorn main:app --host 127.0.0.1 --port 58777`
  - `conda run -n backend python -m unittest discover -s tests -v`

## Prompt Example

새 대화에서 AI에게 작업을 시킬 때 아래 문장을 기준으로 사용한다:

```text
README.md를 먼저 읽고, README에 적힌 Start Here/Default Instruction대로 /docs/AI/31_rdiv_execution_runbook.md 기준으로 문서+코드+검증까지 완료해.
```

---

## Definition of Done (DoD)

- [ ] **R/D/I/V 동시 갱신**: 변경사항에 해당하는 문서를 모두 갱신했다
- [ ] **internal API 계약 기록**: 엔드포인트 추가/변경/삭제 시 `D/30_api_contract.md` 갱신
- [ ] **검색 인덱스 영향 기록**: Qdrant/Elasticsearch 인덱스 구조 변경 시 `D/20_data_model.md`와 `D/90_decisions.md` 갱신
- [ ] **테스트 결과 없이 완료 처리 금지**: ingest/retrieve/worker 관련 테스트를 작성하고 통과시켰다
- [ ] **보안 검토 통과**: `V/30_security_review.md` 체크리스트를 확인했다
- [ ] **관찰성 확인**: `V/40_observability.md`에 상태/지표/에러 포인트를 반영했다
- [ ] **변경 이력 기록**: `I/20_change_log.md`에 날짜와 함께 변경 내용을 기록했다

---

## Architecture Rules (AI 필독)

| 레이어 | 위치 | 담당 역할 | 금지 사항 |
|--------|------|-----------|-----------|
| **Routes** | `main.py` 또는 향후 `app/api/` | 내부 HTTP 계약, 요청 검증, service 호출 | chunking/retrieval 비즈니스 로직 직접 작성 금지 |
| **Services** | `app/services/` | ingest, chunking, indexing, retrieval orchestration | FastAPI Request/Response 직접 참조 금지 |
| **Workers** | `app/workers/` | Celery task, 재시도, 장시간 인덱싱 작업 | HTTP 계약/인증 로직 포함 금지 |
| **Adapters** | `app/adapters/` | Qdrant, Elasticsearch, storage, embedding provider 연결 | 도메인 정책 직접 결정 금지 |
| **Models/Schemas** | `app/models/`, `app/schemas/` | 상태 모델, internal request/response 구조 | 외부 공개 API 계약과 혼동 금지 |

## 모듈성 / 독립성 / 이벤트 드리븐 / 보안성

이 네 항목은 이 저장소에서 반드시 지켜야 하는 핵심 원칙이다.

### 모듈성

- `api`, `domain`, `adapters`, `workers`, `core`, `repositories`는 역할별로 분리한다
- ingest, retrieval, indexing, metadata 저장, external client 연결을 한 파일에 섞지 않는다
- Qdrant / Elasticsearch / storage / embedding 연동은 반드시 adapter 레이어로 분리한다

### 독립성

- `min-minisaas-airag`는 internal engine으로 독립 실행/테스트 가능해야 한다
- 앱과 backend 없이도 ingest/query/worker를 단독 검증할 수 있어야 한다
- backend 전용 공개 API 계약과 혼동하지 않도록 internal contract만 유지한다
- 특정 저장소(Qdrant/Elasticsearch/local index) 구현에 service 레이어가 직접 고정되지 않도록 adapter를 경유한다

### 이벤트 드리븐

- 장시간 ingest / reindex / delete 작업은 동기 HTTP 처리에 고정하지 않고 worker queue를 통해 처리 가능해야 한다
- 현재 eager fallback이 있더라도 구조는 Celery task 전환을 기준으로 유지한다
- status 전이는 `queued -> processing -> ready/failed`처럼 명시적 lifecycle을 따라야 한다

### 보안성

- 이 저장소는 외부 공개용이 아니다. 모든 호출은 `min-minisaas-backend`를 경유해야 한다
- `user_id` scope는 모든 ingest/query/delete 경로에서 강제되어야 한다
- Qdrant / Elasticsearch / Redis 접속 정보와 API key는 코드 하드코딩 금지, 환경변수로만 주입한다
- 문서 원본 경로, 내부 host, API key, 토큰을 로그에 평문으로 남기지 않는다
- internal API를 앱에 직접 노출하거나, backend를 우회해 storage engine에 직접 붙는 경로를 만들지 않는다

### 핵심 원칙

- 이 저장소는 **internal RAG engine** 이다. 앱이나 외부 클라이언트는 직접 접근하지 않는다.
- 모든 요청은 `min-minisaas-backend`를 경유한다.
- 검색/인덱싱 데이터는 반드시 `user_id` 스코프로 분리한다.
- dense vector는 Qdrant, keyword/BM25 검색은 Elasticsearch를 기본으로 사용한다.
- 장시간 ingest 작업은 Celery + Redis 큐로 처리한다.
- final answer 생성 책임은 기본적으로 backend orchestration에 두고, 이 저장소는 retrieval/context 제공을 우선 책임으로 본다.

---

## 빠른 링크

| 문서 | 용도 |
|------|------|
| [R/00_overview.md](R/00_overview.md) | 프로젝트 개요 |
| [R/10_user_stories.md](R/10_user_stories.md) | 유저 스토리 |
| [D/10_architecture.md](D/10_architecture.md) | 아키텍처 구조 |
| [D/30_api_contract.md](D/30_api_contract.md) | internal API 계약 |
| [D/90_decisions.md](D/90_decisions.md) | 아키텍처 결정 기록 |
| [I/10_implementation_plan.md](I/10_implementation_plan.md) | 구현 현황 |
| [V/10_test_plan.md](V/10_test_plan.md) | 테스트 계획 |
| [V/30_security_review.md](V/30_security_review.md) | 보안 체크리스트 |
| [V/40_observability.md](V/40_observability.md) | 지표/로깅/상태 추적 |
| [AI/31_rdiv_execution_runbook.md](AI/31_rdiv_execution_runbook.md) | AI 작업 Runbook |
