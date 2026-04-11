# D/30 - internal API 계약

> 이 API는 외부 공개용이 아니다. `min-minisaas-backend`만 호출한다.
> 모든 엔드포인트는 `X-Internal-API-Key` 헤더가 필요하다.

## POST `/internal/rag/documents`

- 목적: 문서 ingest 요청
- 헤더: `X-Internal-API-Key: <AIRAG_INTERNAL_API_KEY>`
- 요청: `user_id`, 파일 메타데이터, 저장 위치 또는 multipart 업로드 정보
- 응답: `document_id`, `status`

## GET `/internal/rag/documents/{document_id}`

- 목적: 인덱싱 상태 조회
- 헤더: `X-Internal-API-Key: <AIRAG_INTERNAL_API_KEY>`
- 응답: `document_id`, `status`, `chunk_count`, `error_message`

## DELETE `/internal/rag/documents/{document_id}`

- 목적: 문서 및 인덱스 삭제
- 헤더: `X-Internal-API-Key: <AIRAG_INTERNAL_API_KEY>`
- 동작: 원본 파일, Qdrant chunk, Elasticsearch 문서를 함께 제거

## POST `/internal/rag/query`

- 목적: 특정 user_id 스코프에서 hybrid retrieval 수행
- 헤더: `X-Internal-API-Key: <AIRAG_INTERNAL_API_KEY>`
- 요청: `user_id`, `query`, `top_k`
- 응답: `chunks`, `citations`, `retrieval_meta`
