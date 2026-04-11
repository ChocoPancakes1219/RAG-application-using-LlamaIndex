# RAG Application using LlamaIndex + Ollama

A local RAG (Retrieval-Augmented Generation) application using LlamaIndex with **Ollama** for completely local, privacy-friendly operation. No API keys required!

## Features

- 🦙 **100% Local** - Uses Ollama (gemma2:9b + nomic-embed-text)
- 🔒 **Privacy-First** - Your data never leaves your machine
- 📄 **Document Ingestion** - Upload .txt files to build your knowledge base
- 🔍 **Semantic Search** - Query your documents with natural language
- 🌐 **Web Interface** - Simple chat UI for easy interaction
- 🚀 **systemd Service** - Easy start/stop/restart commands

## Prerequisites

1. **Ollama** installed and running
   ```bash
   # Install Ollama: https://ollama.ai
   # Should be running on 127.0.0.1:11434
   ```

2. **Required models**
   ```bash
   ollama pull gemma2:9b
   ollama pull nomic-embed-text
   ```

3. **Python 3.10+**

## Quick Start

### 1. Setup

```bash
# backend와 동일한 conda env 사용
conda run -n backend python -m pip install -r Requirements.txt
```

### 2. Run (Simple)

```bash
# Start server manually
conda run -n backend uvicorn main:app --host 127.0.0.1 --port 58777
```

Open http://127.0.0.1:58777 in your browser.

### 3. Install as System Service (Recommended)

For automatic startup and easy management:

```bash
# Install CLI tool
sudo cp rag-server-cli.sh /usr/local/bin/rag-server

# Install systemd service
sudo cp rag-server.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable auto-start on boot
rag-server enable

# Start the service
rag-server start

# Check status
rag-server status
```

**Note**: 현재 저장소 표준 실행 환경은 별도 `userenv`가 아니라 `conda run -n backend ...` 이다.

## Usage

### Commands (with systemd)

```bash
rag-server start    # Start the server
rag-server stop     # Stop the server
rag-server restart  # Restart the server
rag-server status   # Check status
rag-server logs     # View logs
rag-server enable   # Enable auto-start
rag-server disable  # Disable auto-start
```

### API Endpoints

#### POST `/ingest`
Upload text files to build your knowledge base.

```bash
curl -X POST http://127.0.0.1:58777/ingest \
  -F "files=@document.txt"
```

#### GET `/query`
Query your knowledge base.

```bash
curl "http://127.0.0.1:58777/query?query=What is the main topic?"
```

#### GET `/`
Web interface for chat-based interaction.

## Configuration

The app uses these Ollama models (configurable in `main.py`):

| Purpose | Model | Size |
|---------|-------|------|
| LLM | gemma2:9b | ~5GB |
| Embeddings | nomic-embed-text | ~274MB |

To change models, edit `main.py`:
```python
Settings.llm = Ollama(model="your-model-name")
Settings.embed_model = OllamaEmbedding(model_name="your-embed-model")
```

## Project Structure

```
.
├── main.py                  # FastAPI application
├── chat_interface.html      # Web UI
├── Requirements.txt         # Python dependencies
├── rag-server.service       # systemd service file
├── rag-server-cli.sh        # CLI wrapper script
├── data/                    # Uploaded documents (gitignored)
├── storage/                 # Vector index (gitignored)
└── docs/                    # RDIV documents
```

## Security

✅ **Ollama**: Runs on `127.0.0.1:11434` (localhost only)  
✅ **RAG Server**: Runs on `127.0.0.1:58777` (localhost only)  
✅ **No external exposure** by default  
✅ **All data stays local**

## How It Works

1. **Ingest**: Upload .txt files → chunked (512 tokens) → embedded via Ollama → stored in vector index
2. **Query**: Question → embedded → semantic search → top 3 chunks retrieved → LLM generates answer

## Troubleshooting

**"Connection refused" error**
- Make sure Ollama is running: `ollama list`
- Check Ollama is on 127.0.0.1:11434: `ss -tlnp | grep 11434`

**Slow responses**
- First query loads the model into memory (takes ~10-30s)
- Subsequent queries are faster

**Out of memory**
- Try a smaller model: `ollama pull gemma2:2b`

**Service won't start**
- Check logs: `rag-server logs`
- Verify paths in `rag-server.service` match your system
- Ensure `conda run -n backend python --version` works

## Development

This project uses:
- **FastAPI** for the web server
- **LlamaIndex** for RAG implementation
- **Ollama** for local LLM/embeddings
- **uvicorn** as ASGI server

## Runtime Convention

- backend와 동일하게 `conda`의 `backend` env를 기본 실행 환경으로 사용한다
- 예시:

```bash
conda run -n backend python -m pip install -r Requirements.txt
conda run -n backend uvicorn main:app --host 127.0.0.1 --port 58777
conda run -n backend python -m unittest discover -s tests -v
```

## QA Client

- live QA용 독립 폴더:
  - [`qa/airag_qa_client`](/Users/mikemin/Development/MyProjects/SaaS/min-minisaas-airag/qa/airag_qa_client)
- QA 전용 환경파일:
  - `qa/airag_qa_client/.env.qa`
  - 템플릿: `qa/airag_qa_client/.env.qa.example`
- 실행 예시:

```bash
cp qa/airag_qa_client/.env.qa.example qa/airag_qa_client/.env.qa
cd qa/airag_qa_client
bash run.sh
```

## Original Project

Forked and modified to use Ollama instead of OpenAI API.
- Original: Uses OpenAI API (requires API key)
- This version: Uses Ollama (fully local, free)

## License

MIT

## Contributing

Pull requests welcome! Please ensure:
- All changes work with Ollama (no external API dependencies)
- Code follows existing style
- Update README for new features
