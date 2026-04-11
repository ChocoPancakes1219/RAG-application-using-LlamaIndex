# R/20 - 인수 기준

## AC-ARAG-01: ingest 요청 수락

| # | Given | When | Then |
|---|-------|------|------|
| 1 | backend가 user_id와 문서 메타데이터를 보낼 때 | ingest 요청을 보내면 | engine이 document_id와 초기 status를 반환한다 |
| 2 | 유효한 파일 형식일 때 | ingest 요청이 수락되면 | 비동기 인덱싱 작업이 큐에 등록된다 |

## AC-ARAG-02: user_id 격리 검색

| # | Given | When | Then |
|---|-------|------|------|
| 1 | 서로 다른 user_id 문서가 존재할 때 | 특정 user_id로 검색하면 | 다른 user_id의 chunk는 결과에 포함되지 않는다 |

## AC-ARAG-03: hybrid retrieval 응답

| # | Given | When | Then |
|---|-------|------|------|
| 1 | 같은 사용자 문서가 Qdrant/Elasticsearch에 존재할 때 | query 요청을 보내면 | top-k chunk와 citation metadata가 반환된다 |
| 2 | 관련 citation이 존재할 때 | query 요청을 보내면 | `response`는 citation 기반 자연어 답변을 우선 반환하고 synthesis 실패 시 retrieval fallback을 반환한다 |
| 3 | 관련 citation이 존재할 때 | query 요청을 보내면 | `primary_citation_*` 필드가 최종 답변의 대표 근거를 식별한다 |

## AC-ARAG-04: 상태 추적

| # | Given | When | Then |
|---|-------|------|------|
| 1 | 인덱싱이 아직 끝나지 않았을 때 | 상태 조회를 하면 | `queued` 또는 `processing`이 반환된다 |
| 2 | 인덱싱이 끝나면 | 상태 조회를 하면 | `ready`와 chunk_count가 반환된다 |
| 3 | 실패하면 | 상태 조회를 하면 | `failed`와 에러 메시지가 반환된다 |

## AC-ARAG-05: 내부 LLM 게이트웨이

| # | Given | When | Then |
|---|-------|------|------|
| 1 | backend가 기본 Ollama 경로를 사용할 때 | internal chat 요청을 보내면 | AIRAG가 로컬 Ollama에 전달하고 `answer`, `provider`, `model`을 반환한다 |
| 2 | 앱 사용자가 custom Ollama URL을 설정하지 않았을 때 | backend chat이 `auto` 또는 `ollama`를 선택하면 | 앱에 internal host를 노출하지 않고 AIRAG gateway가 기본 응답 경로가 된다 |
