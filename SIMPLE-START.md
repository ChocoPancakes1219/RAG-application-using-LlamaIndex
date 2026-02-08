# 🚀 RAG 서버 - 간단 실행

## 가장 간단한 방법 (수동)

```bash
cd ~/Development/Workspace/AiAgent/RAG-application-using-LlamaIndex
source userenv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 58777
```

접속: http://127.0.0.1:58777

## systemd로 자동 시작

```bash
# 서비스 등록
sudo cp rag-server.service /etc/systemd/system/
sudo systemctl daemon-reload

# 시작
sudo systemctl start rag-server

# 부팅 시 자동 시작
sudo systemctl enable rag-server

# 상태 확인
sudo systemctl status rag-server

# 로그 보기
sudo journalctl -u rag-server -f

# 중지
sudo systemctl stop rag-server
```

## 보안

✅ Ollama: 127.0.0.1:11434  
✅ RAG: 127.0.0.1:58777  
✅ 외부 차단  
✅ 복잡한 설정 없음

## 다음 단계

→ MLOps 실험 로그를 RAG에 저장  
→ 자연어로 검색
