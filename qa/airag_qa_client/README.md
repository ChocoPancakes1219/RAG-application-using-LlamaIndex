# AIRAG QA Client

`airag_qa_client`는 `min-minisaas-airag`의 live 품질을 수동/반자동으로 점검하기 위한 작은 독립 QA 프로젝트다.

## 목적

- 업로드 -> 상태 전이 -> 질의 -> 삭제까지 end-to-end 확인
- retrieval 인식률을 시나리오 기반으로 반복 점검
- 서비스 코드와 분리된 QA 도구 유지

## 폴더 구조

```text
qa/airag_qa_client/
  README.md
  runner.py
  scenarios/
    smoke.json
    league_table_hard.json
    korean_incident_guide.json
  fixtures/
    smoke_note.txt
    league_table_2003.txt
    korean_incident_guide.txt
  reports/
    .gitkeep
```

## 전제 조건

- AIRAG FastAPI 서버 실행
- AIRAG Celery worker 실행
- Redis / Ollama / Qdrant / Elasticsearch 실행

QA client는 서비스 루트 `.env`를 읽지 않는다.
대신 `qa/airag_qa_client/.env.qa`를 별도로 사용한다.

필수 환경값:

- `qa/airag_qa_client/.env.qa` 안의 `AIRAG_INTERNAL_API_KEY`

선택 환경값:

- `AIRAG_BASE_URL=http://127.0.0.1:58777`

## 실행

```bash
cd /Users/mikemin/Development/MyProjects/SaaS/min-minisaas-airag
cp qa/airag_qa_client/.env.qa.example qa/airag_qa_client/.env.qa
```

가장 직관적인 실행:

```bash
cd /Users/mikemin/Development/MyProjects/SaaS/min-minisaas-airag/qa/airag_qa_client
bash run.sh
```

하드 시나리오 실행:

```bash
cd /Users/mikemin/Development/MyProjects/SaaS/min-minisaas-airag/qa/airag_qa_client
bash run.sh --scenario scenarios/league_table_hard.json
```

한국어 설명문 시나리오 실행:

```bash
cd /Users/mikemin/Development/MyProjects/SaaS/min-minisaas-airag/qa/airag_qa_client
bash run.sh --scenario scenarios/korean_incident_guide.json
```

직접 Python으로 실행:

```bash
cd /Users/mikemin/Development/MyProjects/SaaS/min-minisaas-airag/qa/airag_qa_client
../../.venv/bin/python runner.py
```

## 결과

- 실행 결과는 `qa/airag_qa_client/reports/` 아래 JSON으로 저장된다
- 요약에는 다음이 포함된다
  - upload status
  - ready polling 결과
  - query answer/citations
  - 단일 시나리오 또는 다중 case 결과
  - 정답지 비교 결과
  - keyword hit
  - answer phrase hit
  - forbidden phrase hit
  - expected filename hit
  - minimum citation count 판정
  - delete 결과

## 확장 방향

- fixture를 여러 개 추가해서 회귀 시나리오 확장
- expected keywords 외에 expected filenames / expected document ids 검증 추가
- 인식률 리포트 누적 및 비교 기능 추가
