"""
Query endpoint tests (Feature 14).

Covers: mock query_rag, /query/full endpoint, input validation.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

MOCK_RAG_RESULT = {
    "query": "What is ibuprofen?",
    "answer": "Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID).",
    "sources": [{"source": "MedlinePlus", "title": "Ibuprofen"}],
    "detected_language": "en",
    "translated": False,
    "cached": False,
    "query_id": "507f1f77bcf86cd799439011",
}


async def test_full_query_success(client: AsyncClient, auth_headers: dict):
    """A valid query returns an answer from the mocked RAG pipeline."""
    with patch(
        "app.api.v1.query.query_rag",
        new=AsyncMock(return_value=MOCK_RAG_RESULT),
    ):
        response = await client.post(
            "/api/v1/query/full",
            json={"query": "What is ibuprofen?"},
            headers=auth_headers,
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "answer" in data
    assert data["answer"] == MOCK_RAG_RESULT["answer"]


async def test_full_query_unauthenticated(client: AsyncClient):
    """An unauthenticated request to /query/full is rejected."""
    response = await client.post(
        "/api/v1/query/full",
        json={"query": "What is ibuprofen?"},
    )
    assert response.status_code in (401, 403, 422)


async def test_full_query_blank_query(client: AsyncClient, auth_headers: dict):
    """A blank query string returns a 422 validation error."""
    with patch(
        "app.api.v1.query.query_rag",
        new=AsyncMock(return_value=MOCK_RAG_RESULT),
    ):
        response = await client.post(
            "/api/v1/query/full",
            json={"query": "   "},
            headers=auth_headers,
        )
    assert response.status_code == 422


async def test_full_query_too_long(client: AsyncClient, auth_headers: dict):
    """A query over 2000 characters returns a 422 validation error."""
    with patch(
        "app.api.v1.query.query_rag",
        new=AsyncMock(return_value=MOCK_RAG_RESULT),
    ):
        response = await client.post(
            "/api/v1/query/full",
            json={"query": "x" * 2001},
            headers=auth_headers,
        )
    assert response.status_code == 422


async def test_full_query_returns_query_id(client: AsyncClient, auth_headers: dict):
    """The query response includes a query_id field."""
    with patch(
        "app.api.v1.query.query_rag",
        new=AsyncMock(return_value=MOCK_RAG_RESULT),
    ):
        response = await client.post(
            "/api/v1/query/full",
            json={"query": "Tell me about aspirin"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert "query_id" in data
