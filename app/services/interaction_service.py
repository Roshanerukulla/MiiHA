"""
Drug Interaction Checker Service (Feature 4)

Uses Cohere generate to identify drug-drug interactions.
Also searches OpenFDA FAISS index for relevant drug data.
"""
from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path
from typing import Optional

import cohere
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_co: Optional[cohere.Client] = None
_model: Optional[SentenceTransformer] = None
_openfda_index = None
_openfda_metadata: Optional[list] = None


def _get_client() -> cohere.Client:
    global _co
    if _co is None:
        _co = cohere.Client(settings.cohere_api_key)
    return _co


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def _load_openfda():
    global _openfda_index, _openfda_metadata
    if _openfda_index is not None:
        return
    base = Path(__file__).resolve().parent.parent
    index_path = base / "db" / "openfda_all_drugs.index"
    meta_path = base / "data" / "metadata" / "openfda_all_drugs_metadata.json"
    if index_path.exists():
        _openfda_index = faiss.read_index(str(index_path))
    else:
        logger.warning("OpenFDA index not found at %s", index_path)
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            _openfda_metadata = json.load(f)
    else:
        _openfda_metadata = []


def _search_openfda_context(medications: list[str], top_k: int = 5) -> str:
    """Search OpenFDA FAISS index for drug info and return as context string."""
    _load_openfda()
    if _openfda_index is None or not _openfda_metadata:
        return ""
    model = _get_model()
    query = " ".join(medications)
    embedding = model.encode([query])[0].astype("float32")
    _, indices = _openfda_index.search(np.array([embedding]), top_k)
    snippets = []
    for i in indices[0]:
        if 0 <= i < len(_openfda_metadata):
            doc = _openfda_metadata[i]
            name = doc.get("drug_name", "")
            purpose = doc.get("purpose", "")
            warnings = doc.get("warnings", "")
            if name:
                snippets.append(f"Drug: {name}. Purpose: {purpose}. Warnings: {warnings}")
    return "\n".join(snippets)


def check_interactions(medications: list[str]) -> dict:
    """
    Check drug interactions for the given medication list.

    Returns dict with interactions, safe_combinations, warnings.
    """
    try:
        co = _get_client()
        fda_context = _search_openfda_context(medications)
        meds_str = ", ".join(medications)
        pairs = [f"{a} + {b}" for a, b in combinations(medications, 2)]
        pairs_str = "\n".join(f"- {p}" for p in pairs) if pairs else "- (only one medication provided)"

        context_section = (
            f"\nAdditional drug data from FDA database:\n{fda_context}\n"
            if fda_context
            else ""
        )

        prompt = f"""You are a clinical pharmacist. Analyse the following medications for interactions.

Medications: {meds_str}

Pairs to evaluate:
{pairs_str}
{context_section}
Return ONLY a JSON object in this exact format (no extra text):
{{
  "interactions": [
    {{
      "drug_a": "<drug name>",
      "drug_b": "<drug name>",
      "severity": "<minor|moderate|major|contraindicated>",
      "description": "<brief description of the interaction>"
    }}
  ],
  "safe_combinations": ["<pair description>"],
  "warnings": ["<general warning>"]
}}

Rules:
- Only include pairs with known or suspected interactions in "interactions".
- List pairs with no significant interaction in "safe_combinations".
- Add general warnings relevant to these medications in "warnings".
- Output ONLY the JSON object."""

        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=600,
            temperature=0.2,
        )
        raw = response.generations[0].text.strip()
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if not json_match:
            raise ValueError(f"No JSON found in Cohere response: {raw}")
        parsed = json.loads(json_match.group())

        return {
            "interactions": parsed.get("interactions", []),
            "safe_combinations": parsed.get("safe_combinations", []),
            "warnings": parsed.get("warnings", []),
        }

    except Exception as exc:
        logger.error("Interaction check failed: %s", exc)
        return {
            "interactions": [],
            "safe_combinations": [],
            "warnings": [
                "Unable to perform automated interaction check. "
                "Please consult your pharmacist or physician."
            ],
        }
