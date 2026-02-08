# RAG Application using LlamaIndex + Ollama

A local RAG (Retrieval-Augmented Generation) web application using LlamaIndex with **Ollama** for completely local, privacy-friendly operation. No API keys required!

## Features

- 🦙 **100% Local** - Uses Ollama (gemma2:9b + nomic-embed-text)
- 🔒 **Privacy-First** - Your data never leaves your machine
- 📄 **Document Ingestion** - Upload .txt files to build your knowledge base
- 🔍 **Semantic Search** - Query your documents with natural language
- 🌐 **Web Interface** - Simple chat UI for easy interaction

## Prerequisites

1. **Ollama** installed and running
   ```bash
   # Install Ollama: https://ollama.ai
   ollama serve
   ```

2. **Required models**
   ```bash
   ollama pull gemma2:9b
   ollama pull nomic-embed-text
   ```

3. **Python 3.10+**

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/RAG-application-using-LlamaIndex.git
cd RAG-application-using-LlamaIndex

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r Requirements.txt

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 in your browser.

## API Endpoints

### POST `/ingest`
Upload text files to build your knowledge base.

```bash
curl -X POST http://localhost:8000/ingest -F "files=@document.txt"
```

### GET `/query`
Query your knowledge base.

```bash
curl "http://localhost:8000/query?query=What is the main topic?"
```

### GET `/`
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
├── main.py              # FastAPI application
├── chat_interface.html  # Web UI
├── Requirements.txt     # Python dependencies
├── data/               # Sample data (gitignored)
├── storage/            # Vector index (gitignored)
└── sample/             # Example files for testing
```

## How It Works

1. **Ingest**: Upload .txt files → chunked (512 tokens) → embedded via Ollama → stored in vector index
2. **Query**: Question → embedded → semantic search → top 3 chunks retrieved → LLM generates answer

## Troubleshooting

**"Connection refused" error**
- Make sure Ollama is running: `ollama serve`

**Slow responses**
- First query loads the model into memory (takes ~10-30s)
- Subsequent queries are faster

**Out of memory**
- Try a smaller model: `ollama pull gemma2:2b`

## Original Project

Forked and modified to use Ollama instead of OpenAI API.
- Original: Uses OpenAI API (requires API key)
- This version: Uses Ollama (fully local, free)

## License

MIT
