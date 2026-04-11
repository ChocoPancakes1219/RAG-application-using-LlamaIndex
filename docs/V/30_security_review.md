# V/30 - 보안 리뷰 체크리스트

- [ ] backend 우회 없이 internal API만 사용하도록 경계가 유지됨
- [ ] `X-Internal-API-Key` 없이는 internal/legacy RAG 엔드포인트 접근 불가
- [ ] user_id scope 검증이 ingest/query/delete 전 경로에 적용됨
- [ ] adapter 설정값(Qdrant/Elasticsearch/Redis/API key) 하드코딩 없음
- [ ] worker/task 로그에 API key, 토큰, 원본 문서 본문 전체를 출력하지 않음
- [ ] 내부 host/port를 앱 공개 계약에 직접 노출하지 않음
- [ ] internal API는 backend 외 직접 노출되지 않음
- [ ] 모든 ingest/query/delete 요청에 user_id scope 검증 적용
- [ ] 파일 원본 경로, 토큰, internal host를 과도하게 로그 출력하지 않음
- [ ] Qdrant/Elasticsearch 접근 정보는 환경변수 또는 비밀 저장소로만 주입
- [ ] 문서 삭제 시 Qdrant/Elasticsearch/original storage 동기 삭제 경로 존재
