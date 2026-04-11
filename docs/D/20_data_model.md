# D/20 - 데이터 모델

## 문서 메타데이터

| 필드 | 설명 |
|------|------|
| `document_id` | 문서 식별자 |
| `user_id` | 사용자 식별자 |
| `filename` | 원본 파일명 |
| `content_type` | MIME 타입 |
| `status` | `uploaded`, `queued`, `processing`, `ready`, `failed`, `deleted` |
| `chunk_count` | 생성된 chunk 수 |
| `storage_path` | 원본 저장 위치 |
| `error_message` | 실패 시 에러 요약 |

## chunk metadata

| 필드 | 설명 |
|------|------|
| `chunk_id` | 청크 식별자 |
| `document_id` | 원본 문서 식별자 |
| `user_id` | 사용자 식별자 |
| `chunk_index` | 문서 내 순서 |
| `page` | 페이지 번호 또는 위치 |
| `text` | chunk 본문 |
| `token_count` | 토큰 수 |

## internal LLM chat request/response

| 필드 | 설명 |
|------|------|
| `user_id` | backend가 전달하는 사용자 식별자 |
| `message` | 사용자 원문 질문 |
| `model` | backend가 선택한 Ollama 모델명(옵션) |
| `max_tokens` | 최대 출력 토큰 수 |
| `answer` | Ollama 최종 응답 |
