"""
Chat endpoint tests (Feature 14 — Feature 1).

Covers: send chat message, retrieve history, delete session.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

MOCK_RAG_RESULT = {
    "query": "What are the side effects of metformin?",
    "answer": "Metformin can cause nausea, diarrhea, and stomach upset.",
    "sources": [],
    "detected_language": "en",
    "translated": False,
    "cached": False,
    "query_id": "507f1f77bcf86cd799439022",
}


async def test_chat_send_message(client: AsyncClient, auth_headers: dict):
    """Sending a chat message returns a reply and session_id."""
    with patch(
        "app.api.v1.chat.query_rag",
        new=AsyncMock(return_value=MOCK_RAG_RESULT),
    ):
        response = await client.post(
            "/api/v1/chat",
            json={"message": "What are the side effects of metformin?", "session_id": "sess-001"},
            headers=auth_headers,
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "reply" in data
    assert data["session_id"] == "sess-001"
    assert data["reply"] == MOCK_RAG_RESULT["answer"]


async def test_chat_unauthenticated(client: AsyncClient):
    """Unauthenticated chat requests are rejected."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "Hello", "session_id": "sess-002"},
    )
    assert response.status_code in (401, 403, 422)


async def test_chat_blank_message(client: AsyncClient, auth_headers: dict):
    """A blank message returns 422."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": "  ", "session_id": "sess-003"},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_chat_history_empty_session(client: AsyncClient, auth_headers: dict):
    """Fetching history for a new session returns an empty turns list."""
    response = await client.get(
        "/api/v1/chat/history?session_id=new-session-xyz",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "new-session-xyz"
    assert isinstance(data["turns"], list)


async def test_chat_history_after_message(client: AsyncClient, auth_headers: dict):
    """After sending a message, history contains the turns."""
    session_id = "sess-history-test"
    with patch(
        "app.api.v1.chat.query_rag",
        new=AsyncMock(return_value=MOCK_RAG_RESULT),
    ):
        await client.post(
            "/api/v1/chat",
            json={"message": "What is metformin?", "session_id": session_id},
            headers=auth_headers,
        )
    response = await client.get(
        f"/api/v1/chat/history?session_id={session_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["turns"]) >= 2  # user turn + assistant turn


async def test_chat_delete_session(client: AsyncClient, auth_headers: dict):
    """Deleting an existing session returns 200."""
    session_id = "sess-to-delete"
    with patch(
        "app.api.v1.chat.query_rag",
        new=AsyncMock(return_value=MOCK_RAG_RESULT),
    ):
        await client.post(
            "/api/v1/chat",
            json={"message": "Hello", "session_id": session_id},
            headers=auth_headers,
        )
    response = await client.delete(
        f"/api/v1/chat/history/{session_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200


async def test_chat_delete_nonexistent_session(client: AsyncClient, auth_headers: dict):
    """Deleting a session that does not exist returns 404."""
    response = await client.delete(
        "/api/v1/chat/history/nonexistent-session-id",
        headers=auth_headers,
    )
    assert response.status_code == 404
