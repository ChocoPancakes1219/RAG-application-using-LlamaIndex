from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.internal_rag import create_internal_rag_router
from app.domain.rag.bootstrap import build_rag_components

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")
CONFIG, DOCUMENT_SERVICE, QUERY_SERVICE, CHAT_SERVICE = build_rag_components(ROOT_DIR)

app = FastAPI(title="MiniSaaS AIRAG Internal Engine")
app.include_router(
    create_internal_rag_router(
        document_service=DOCUMENT_SERVICE,
        query_service=QUERY_SERVICE,
        chat_service=CHAT_SERVICE,
        default_user_id=CONFIG.default_user_id,
        config=CONFIG,
    )
)


@app.get("/")
async def main():
    html_path = ROOT_DIR / "chat_interface.html"
    if not html_path.exists():
        return HTMLResponse(content="<h1>AIRAG</h1><p>chat_interface.html missing.</p>")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
