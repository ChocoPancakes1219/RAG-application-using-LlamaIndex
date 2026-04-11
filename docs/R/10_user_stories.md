# R/10 - 사용자 스토리

## US-ARAG-01: 내부 문서 인덱싱 요청

As a backend gateway,  
I want to internal RAG engine에 문서 인덱싱을 요청하고 싶다,  
So that 사용자 문서를 비동기로 검색 가능한 상태로 만들 수 있다.

## US-ARAG-02: 사용자별 검색

As a backend gateway,  
I want to 특정 사용자 범위 안에서만 chunk를 검색하고 싶다,  
So that 다른 사용자의 문서가 섞이지 않도록 보장할 수 있다.

## US-ARAG-03: Hybrid retrieval

As a backend gateway,  
I want to dense vector와 BM25를 결합한 retrieval 결과를 받고 싶다,  
So that keyword miss와 semantic miss를 함께 줄일 수 있다.

## US-ARAG-04: 인덱싱 상태 조회

As a backend gateway,  
I want to 문서 인덱싱 상태를 조회하고 싶다,  
So that 앱에 queued/processing/ready/failed 상태를 반영할 수 있다.

## US-ARAG-05: 내부 LLM 게이트웨이

As a backend gateway,  
I want to 기본 Ollama 대화 요청을 internal AIRAG endpoint로 보내고 싶다,  
So that 앱에 내부 host를 노출하지 않고 backend 기본 모델 경로를 일원화할 수 있다.
