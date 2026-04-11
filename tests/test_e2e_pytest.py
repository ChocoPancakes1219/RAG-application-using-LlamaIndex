from __future__ import annotations

import os
import time
from uuid import uuid4

import httpx
import pytest


AIRAG_BASE_URL = os.getenv("AIRAG_BASE_URL", "http://127.0.0.1:58777")
AIRAG_INTERNAL_API_KEY = os.getenv("AIRAG_INTERNAL_API_KEY")
AIRAG_E2E_TIMEOUT_SECONDS = float(os.getenv("AIRAG_E2E_TIMEOUT_SECONDS", "30"))
RUN_AIRAG_E2E = os.getenv("RUN_AIRAG_E2E", "0") == "1"


def _headers() -> dict[str, str]:
    return {"X-Internal-API-Key": AIRAG_INTERNAL_API_KEY}


def _poll_ready(client: httpx.Client, user_id: str, document_id: str) -> dict:
    deadline = time.time() + AIRAG_E2E_TIMEOUT_SECONDS
    last_payload: dict | None = None
    while time.time() < deadline:
        response = client.get(
            f"/internal/rag/documents/{document_id}",
            params={"user_id": user_id},
            headers=_headers(),
        )
        response.raise_for_status()
        payload = response.json()
        last_payload = payload
        if payload["status"] == "ready":
            return payload
        if payload["status"] == "failed":
            pytest.fail(f"E2E ingest failed: {payload}")
        time.sleep(1.0)
    pytest.fail(f"E2E ingest did not reach ready before timeout: {last_payload}")


@pytest.mark.e2e
def test_e2e_ingest_query_and_delete_live_airag() -> None:
    if not RUN_AIRAG_E2E:
        pytest.skip("Set RUN_AIRAG_E2E=1 to run live AIRAG end-to-end pytest.")
    if not AIRAG_INTERNAL_API_KEY:
        pytest.skip("Set AIRAG_INTERNAL_API_KEY to run live AIRAG end-to-end pytest.")
    user_id = f"pytest-e2e-{uuid4().hex[:8]}"
    file_name = "pytest-e2e-note.txt"
    file_content = (
        "AIRAG e2e document for hybrid retrieval.\n"
        "This document mentions backend orchestration and qdrant elasticsearch citations.\n"
    ).encode("utf-8")

    with httpx.Client(base_url=AIRAG_BASE_URL, timeout=60.0) as client:
        ingest_response = client.post(
            "/internal/rag/documents",
            headers=_headers(),
            data={"user_id": user_id},
            files={"files": (file_name, file_content, "text/plain")},
        )
        ingest_response.raise_for_status()
        ingest_payload = ingest_response.json()
        assert ingest_payload["items"], ingest_payload
        document_id = ingest_payload["items"][0]["document_id"]

        ready_payload = _poll_ready(client, user_id, document_id)
        assert ready_payload["status"] == "ready"
        assert ready_payload["chunk_count"] >= 1

        query_response = client.post(
            "/internal/rag/query",
            headers=_headers(),
            json={
                "user_id": user_id,
                "query": "backend orchestration",
                "top_k": 3,
            },
        )
        query_response.raise_for_status()
        query_payload = query_response.json()
        assert query_payload["citations"], query_payload
        assert any(
            citation.get("filename") == file_name for citation in query_payload["citations"]
        ), query_payload

        delete_response = client.delete(
            f"/internal/rag/documents/{document_id}",
            params={"user_id": user_id},
            headers=_headers(),
        )
        assert delete_response.status_code == 204
