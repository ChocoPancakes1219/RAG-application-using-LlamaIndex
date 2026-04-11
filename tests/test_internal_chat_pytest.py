import httpx
import pytest

from app.domain.rag.schemas import InternalChatRequest
from app.domain.rag.services.chat_service import ChatService


class _MockResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.is_success = status_code < 400
        self.text = ""

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class _MockAsyncClient:
    def __init__(self, capture: dict[str, object]) -> None:
        self._capture = capture

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, path: str, json: dict[str, object]):
        self._capture["path"] = path
        self._capture["json"] = json
        return _MockResponse({"message": {"content": "짧은 요약 답변"}})


@pytest.mark.asyncio
async def test_internal_chat_service_calls_local_ollama(rag_fixture, monkeypatch):
    config = rag_fixture["config"]
    capture: dict[str, object] = {}
    service = ChatService(config)

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *args, **kwargs: _MockAsyncClient(capture),
    )

    response = await service.chat(
        InternalChatRequest(
            user_id="user-1",
            message="행사 일정 한 줄 요약해줘",
            model="qwen2.5:7b",
            max_tokens=128,
        )
    )

    assert response.answer == "짧은 요약 답변"
    assert response.provider == "ollama"
    assert capture["path"] == "/api/chat"
    assert capture["json"]["model"] == "qwen2.5:7b"
