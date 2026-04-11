# AI/31 — RDIV 실행 런북

> AI 작업 시작 시 이 런북을 기준으로 문서 + 코드 + 검증까지 완료한다.

---

## 0. 작업 시작 전 필독

1. `docs/README.md`
2. `docs/AI/20_tasks_queue.md`
3. `docs/AI/30_context_pack.md`

---

## 1. R — 요구사항 확인

작업 전 반드시 확인:

```text
docs/R/00_overview.md
docs/R/10_user_stories.md
docs/R/20_acceptance_criteria.md
docs/R/40_traceability.md
```

---

## 2. D — 설계 확인 및 갱신

### 아키텍처 확인

- internal engine인지, backend gateway가 아닌지 먼저 확인
- `user_id` 격리, Qdrant/Elasticsearch 역할 분리, Celery 작업 경계를 문서 기준으로 유지

### 변경 시 필수 갱신

```text
docs/D/10_architecture.md
docs/D/20_data_model.md
docs/D/30_api_contract.md
docs/D/90_decisions.md
```

---

## 3. I — 구현

### 새 기능 추가 체크리스트

```text
[ ] internal API인지 worker인지 경계 판단
[ ] user_id scope 필터 적용
[ ] document lifecycle status 반영
[ ] Qdrant / Elasticsearch 동기 인덱싱 전략 반영
[ ] Celery retry / failure path 검토
[ ] docs/I/20_change_log.md 갱신
```

---

## 4. V — 검증

```text
[ ] ingest API 테스트
[ ] retrieval API 테스트
[ ] worker task 테스트
[ ] user_id 격리 테스트
[ ] Qdrant / Elasticsearch sync 검증
[ ] 민감정보 로그 출력 없음 확인
```

---

## 5. 문서 동시 갱신

```text
[ ] R/40_traceability.md
[ ] D/30_api_contract.md
[ ] D/20_data_model.md
[ ] D/90_decisions.md
[ ] I/10_implementation_plan.md
[ ] I/20_change_log.md
[ ] V/20_test_cases.md
[ ] AI/20_tasks_queue.md
```
