"""
Test configuration and shared fixtures (Feature 14).

Provides:
- async test client backed by a real FastAPI app
- mocked MongoDB via mongomock-motor
- mocked Cohere client
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Event loop policy
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


# ---------------------------------------------------------------------------
# Mock Cohere client
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_cohere(monkeypatch):
    """Replace the Cohere client with a mock for all tests."""
    mock_generation = MagicMock()
    mock_generation.text = "This is a mocked medical answer."

    mock_response = MagicMock()
    mock_response.generations = [mock_generation]

    mock_rerank_result = MagicMock()
    mock_rerank_result.index = 0
    mock_rerank_response = MagicMock()
    mock_rerank_response.results = [mock_rerank_result]

    mock_client = MagicMock()
    mock_client.generate.return_value = mock_response
    mock_client.rerank.return_value = mock_rerank_response

    with patch("cohere.Client", return_value=mock_client):
        yield mock_client


# ---------------------------------------------------------------------------
# Mock MongoDB
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_mongodb(monkeypatch):
    """Replace MongoDB motor client with mongomock-motor."""
    try:
        import mongomock_motor

        mock_client = mongomock_motor.AsyncMongoMockClient()
        mock_db = mock_client["test_miha"]

        monkeypatch.setattr("app.db.mongodb.client", mock_client)
        monkeypatch.setattr("app.db.mongodb.db", mock_db)

        # Patch db references in services
        for module_path in [
            "app.services.auth_service",
            "app.services.chat_service",
            "app.services.feedback_service",
            "app.services.reminder_service",
            "app.services.export_service",
            "app.services.wearable_service",
            "app.services.query_service",
            "app.api.v1.admin",
            "app.core.dependencies",
        ]:
            try:
                monkeypatch.setattr(f"{module_path}.db", mock_db)
            except AttributeError:
                pass

        yield mock_db
    except ImportError:
        pytest.skip("mongomock-motor not installed")


# ---------------------------------------------------------------------------
# Mock FAISS + SentenceTransformer (heavy ML models)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_ml_models(monkeypatch):
    """Mock SentenceTransformer and FAISS to avoid loading heavy models in tests."""
    import numpy as np

    mock_model = MagicMock()
    mock_model.encode.return_value = np.zeros((1, 384), dtype="float32")

    mock_index = MagicMock()
    mock_index.search.return_value = (
        np.array([[0.9]], dtype="float32"),
        np.array([[0]], dtype="int64"),
    )

    with patch("sentence_transformers.SentenceTransformer", return_value=mock_model), \
         patch("faiss.read_index", return_value=mock_index):
        yield


# ---------------------------------------------------------------------------
# Mock scheduler
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_scheduler(monkeypatch):
    """Prevent the APScheduler from starting during tests."""
    monkeypatch.setattr(
        "app.scheduler.reminder_scheduler.start_scheduler", lambda: None
    )
    monkeypatch.setattr(
        "app.scheduler.reminder_scheduler.stop_scheduler", lambda: None
    )


# ---------------------------------------------------------------------------
# Async test client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client connected to the FastAPI test app."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Register a test user and return the registration response data."""
    payload = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "birthdate": "01/01/1990",
        "gender": "Male",
        "medications": [],
        "preferences": {
            "privacy_policy": "Yes",
            "data_sharing": "No",
            "memory_of_searches": "Yes",
            "explanation_of_answers": "Yes",
            "stored_health_data": "Yes",
        },
    }
    response = await client.post("/api/v1/onboarding", json=payload)
    assert response.status_code in (200, 201), response.text
    return payload


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, registered_user: dict) -> str:
    """Login and return a valid JWT bearer token."""
    response = await client.post(
        "/api/v1/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest_asyncio.fixture
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}
