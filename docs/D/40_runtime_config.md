# D/40 - 런타임 설정 규칙

## Redis namespace

- `min-minisaas-backend`
  - `REDIS_URL=redis://localhost:36378/0`
- `min-minisaas-airag`
  - `REDIS_URL=redis://localhost:36378/15`

## 의도

- backend cache/session/event key와 airag Celery broker/result key를 분리한다
- 개발 단계에서도 DB index 충돌을 피한다
- 추후 `51`, `52`를 airag test/experiment 용도로 확장할 수 있게 한다

## AIRAG 로컬 기준

```env
REDIS_URL=redis://localhost:36378/15
REDIS_PASSWORD=<set in local .env only>
```

## QA client

- live QA는 `qa/airag_qa_client`에서 독립적으로 실행한다
- 서비스 코드와 분리해 fixture / scenario / report를 관리한다
- QA 환경값은 `qa/airag_qa_client/.env.qa`로 분리한다
