"""
Symptom Checker Service (Feature 3)

Uses Cohere generate to analyse reported symptoms and return structured JSON.
"""
from __future__ import annotations

import json
import re
from typing import Optional

import cohere

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

DISCLAIMER = (
    "This information is for educational purposes only and does not constitute "
    "medical advice. Always consult a qualified healthcare professional for "
    "diagnosis and treatment. In case of emergency, call your local emergency "
    "services immediately."
)

_co: Optional[cohere.Client] = None


def _get_client() -> cohere.Client:
    global _co
    if _co is None:
        _co = cohere.Client(settings.cohere_api_key)
    return _co


def check_symptoms(
    symptoms: list[str],
    duration_days: int,
    severity: str,
    age: int,
    gender: str,
) -> dict:
    """
    Call Cohere to analyse symptoms and return structured result.

    Returns dict with possible_conditions, urgency, next_steps, disclaimer.
    """
    try:
        co = _get_client()
        symptoms_str = ", ".join(symptoms)
        prompt = f"""You are a clinical decision-support assistant. A patient has the following symptoms.

Patient details:
- Age: {age}
- Gender: {gender}
- Symptoms: {symptoms_str}
- Duration: {duration_days} day(s)
- Severity: {severity}

Based on this information, provide a clinical analysis in the following JSON format ONLY (no extra text):
{{
  "possible_conditions": ["<condition 1>", "<condition 2>", "<condition 3>"],
  "urgency": "<self-care|see doctor|emergency>",
  "next_steps": ["<step 1>", "<step 2>", "<step 3>"]
}}

Rules:
- List exactly 3 possible conditions, from most to least likely.
- urgency must be exactly one of: self-care, see doctor, emergency.
- Provide 3 actionable next steps.
- Output ONLY the JSON object with no additional commentary."""

        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=400,
            temperature=0.3,
        )
        raw = response.generations[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if not json_match:
            raise ValueError(f"No JSON found in Cohere response: {raw}")
        parsed = json.loads(json_match.group())

        return {
            "possible_conditions": parsed.get("possible_conditions", [])[:3],
            "urgency": parsed.get("urgency", "see doctor"),
            "next_steps": parsed.get("next_steps", [])[:3],
            "disclaimer": DISCLAIMER,
        }

    except Exception as exc:
        logger.error("Symptom check failed: %s", exc)
        return {
            "possible_conditions": ["Unable to determine — please consult a doctor"],
            "urgency": "see doctor",
            "next_steps": [
                "Consult a healthcare professional",
                "Monitor your symptoms",
                "Seek emergency care if symptoms worsen significantly",
            ],
            "disclaimer": DISCLAIMER,
        }
