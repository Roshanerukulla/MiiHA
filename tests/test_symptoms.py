"""
Symptom Checker endpoint tests (Feature 14 — Feature 3).

Uses mocked Cohere to test the /symptoms/check endpoint.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

MOCK_SYMPTOM_RESULT = {
    "possible_conditions": ["Common Cold", "Influenza", "Allergic Rhinitis"],
    "urgency": "self-care",
    "next_steps": [
        "Rest and drink plenty of fluids",
        "Take over-the-counter decongestants if needed",
        "See a doctor if symptoms worsen after 7 days",
    ],
    "disclaimer": (
        "This information is for educational purposes only and does not constitute "
        "medical advice."
    ),
}

VALID_SYMPTOM_PAYLOAD = {
    "symptoms": ["runny nose", "sore throat", "mild fever"],
    "duration_days": 3,
    "severity": "mild",
    "age": 30,
    "gender": "Male",
}


async def test_symptom_check_success(client: AsyncClient, auth_headers: dict):
    """A valid symptom check request returns structured diagnosis hints."""
    with patch(
        "app.api.v1.symptoms.check_symptoms",
        return_value=MOCK_SYMPTOM_RESULT,
    ):
        response = await client.post(
            "/api/v1/symptoms/check",
            json=VALID_SYMPTOM_PAYLOAD,
            headers=auth_headers,
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "possible_conditions" in data
    assert "urgency" in data
    assert "next_steps" in data
    assert "disclaimer" in data
    assert len(data["possible_conditions"]) == 3
    assert data["urgency"] in ("self-care", "see doctor", "emergency")


async def test_symptom_check_unauthenticated(client: AsyncClient):
    """Unauthenticated symptom check is rejected."""
    response = await client.post(
        "/api/v1/symptoms/check",
        json=VALID_SYMPTOM_PAYLOAD,
    )
    assert response.status_code in (401, 403, 422)


async def test_symptom_check_empty_symptoms(client: AsyncClient, auth_headers: dict):
    """An empty symptoms list returns 422."""
    payload = {**VALID_SYMPTOM_PAYLOAD, "symptoms": []}
    response = await client.post(
        "/api/v1/symptoms/check",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_symptom_check_invalid_severity(client: AsyncClient, auth_headers: dict):
    """An invalid severity value returns 422."""
    payload = {**VALID_SYMPTOM_PAYLOAD, "severity": "extreme"}
    response = await client.post(
        "/api/v1/symptoms/check",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_symptom_check_invalid_age(client: AsyncClient, auth_headers: dict):
    """A negative age returns 422."""
    payload = {**VALID_SYMPTOM_PAYLOAD, "age": -5}
    response = await client.post(
        "/api/v1/symptoms/check",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_symptom_check_severe_urgency(client: AsyncClient, auth_headers: dict):
    """Severe symptoms can return 'emergency' urgency."""
    severe_result = {**MOCK_SYMPTOM_RESULT, "urgency": "emergency"}
    payload = {
        **VALID_SYMPTOM_PAYLOAD,
        "symptoms": ["chest pain", "shortness of breath"],
        "severity": "severe",
    }
    with patch(
        "app.api.v1.symptoms.check_symptoms",
        return_value=severe_result,
    ):
        response = await client.post(
            "/api/v1/symptoms/check",
            json=payload,
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["urgency"] == "emergency"
