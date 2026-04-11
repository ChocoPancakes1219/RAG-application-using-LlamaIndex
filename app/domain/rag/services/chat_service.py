from __future__ import annotations

import httpx
from fastapi import HTTPException

from app.core.config import AppConfig
from app.domain.rag.schemas import InternalChatRequest, InternalChatResponse

_AIRAG_CHAT_STYLE_INSTRUCTION = (
    "You are an internal AI assistant for a mobile chat UI. "
    "Always answer in Korean unless the user explicitly asks for another language. "
    "Keep the answer direct, helpful, and under 200 characters. "
    "Do not add greetings, disclaimers, or extra filler."
)


class ChatService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    async def chat(self, request: InternalChatRequest) -> InternalChatResponse:
        model_name = (request.model or "").strip() or self._config.ollama_chat_model

        async with httpx.AsyncClient(
            base_url=self._config.ollama_base_url.rstrip("/"),
            timeout=30,
        ) as client:
            data = await self._request_chat_completion(
                client=client,
                model_name=model_name,
                message=request.message,
                max_tokens=request.max_tokens,
            )

        return InternalChatResponse(
            user_id=request.user_id,
            message=request.message,
            answer=(data.get("response") or "").strip(),
            provider="ollama",
            model=model_name,
        )

    def _build_prompt(self, message: str) -> str:
        return f"{_AIRAG_CHAT_STYLE_INSTRUCTION}\n\nUser message:\n{message}"

    async def _request_chat_completion(
        self,
        *,
        client: httpx.AsyncClient,
        model_name: str,
        message: str,
        max_tokens: int,
    ) -> dict[str, str]:
        chat_payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": _AIRAG_CHAT_STYLE_INSTRUCTION},
                {"role": "user", "content": message},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        chat_response = await client.post("/api/chat", json=chat_payload)
        if chat_response.is_success:
            data = chat_response.json()
            content = (
                data.get("message", {}).get("content")
                if isinstance(data.get("message"), dict)
                else None
            )
            return {"response": (content or "").strip()}

        if chat_response.status_code != 404:
            self._raise_as_http_error(chat_response)

        generate_payload = {
            "model": model_name,
            "prompt": self._build_prompt(message),
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        generate_response = await client.post("/api/generate", json=generate_payload)
        if not generate_response.is_success:
            self._raise_as_http_error(generate_response)
        return generate_response.json()

    def _raise_as_http_error(self, response: httpx.Response) -> None:
        detail = "Ollama request failed."
        try:
            payload = response.json()
            detail = payload.get("error") or payload.get("detail") or detail
        except Exception:
            detail = response.text or detail
        raise HTTPException(status_code=response.status_code, detail=detail)
