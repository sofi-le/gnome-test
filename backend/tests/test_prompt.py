"""
G-Nome Prompt Validation Tests
================================
Validates the PGx system prompt structure and tests that mock LLM
responses conform to the expected JSON output schema.

Usage:
    pytest tests/test_prompt.py -v
"""

import os
import sys
import json
import pytest

# Ensure backend is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.snp_config import DISEASES, DISEASE_DISPLAY_NAMES, ANCESTRY_DISPLAY_NAMES
from tests.mock_data import (
    MOCK_PGX_FLAGS_EUR,
    MOCK_PGX_FLAGS_AFR,
    MOCK_PGX_FLAGS_EAS,
    MOCK_PGX_FLAGS_CSA,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "prompts", "pgx_system_prompt.md"
)

# Expected JSON output schema fields
REQUIRED_OUTPUT_FIELDS = {
    "disease", "risk_level", "risk_score", "ancestry_context",
    "dietary_interventions", "lifestyle_modifications",
    "pharmacogenomic_notes", "disclaimer",
}

REQUIRED_DIETARY_FIELDS = {
    "recommendation", "cultural_context", "staple_foods",
    "herbs_and_supplements", "foods_to_limit",
}

VALID_RISK_LEVELS = {"LOW", "MODERATE", "HIGH"}


# ---------------------------------------------------------------------------
# Mock LLM Responses (simulating what Llama 3.3 70B should produce)
# ---------------------------------------------------------------------------

def _build_mock_llm_response(
    disease: str,
    risk_score: float,
    ancestry_label: str,
    ancestry_display: str,
    confidence_score: float,
) -> dict:
    """Build a mock LLM response matching the expected output schema."""
    # Determine risk level
    if risk_score < 0.30:
        risk_level = "LOW"
    elif risk_score < 0.60:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    # Confidence warning prefix
    confidence_prefix = "⚠️ Lower confidence: " if confidence_score < 0.5 else ""

    return {
        "disease": disease,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "ancestry_context": (
            f"{confidence_prefix}The {ancestry_display} population has "
            f"{'limited' if confidence_score < 0.5 else 'well-established'} "
            f"representation in the GWAS datasets used to derive this risk score."
        ),
        "dietary_interventions": [
            {
                "recommendation": "Increase intake of anti-inflammatory foods",
                "cultural_context": f"Drawn from traditional {ancestry_display} dietary practices",
                "staple_foods": ["leafy greens", "whole grains", "legumes"],
                "herbs_and_supplements": ["turmeric (evidence-based)", "ginger"],
                "foods_to_limit": ["processed meats", "refined sugars"],
            },
            {
                "recommendation": "Incorporate omega-3 rich foods",
                "cultural_context": f"Adapted for {ancestry_display} food availability",
                "staple_foods": ["fatty fish", "walnuts", "flax seeds"],
                "herbs_and_supplements": ["fish oil (evidence-based)", "vitamin D"],
                "foods_to_limit": ["trans fats", "excessive sodium"],
            },
        ],
        "lifestyle_modifications": [
            "Engage in 150 minutes of moderate aerobic activity per week",
            "Practice stress-reduction techniques (meditation, deep breathing)",
            "Maintain consistent sleep schedule of 7-9 hours per night",
        ],
        "pharmacogenomic_notes": (
            "Based on available metabolizer status, standard drug dosing "
            "guidelines apply. Consult CPIC/ClinPGx for specific gene-drug pairs."
        ),
        "disclaimer": (
            "This information is for educational purposes only and does not "
            "constitute medical advice. Consult a healthcare provider before "
            "making changes to diet, lifestyle, or medication."
        ),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPromptFileExists:
    """Verify the system prompt file exists and is well-formed."""

    def test_prompt_file_exists(self):
        assert os.path.exists(PROMPT_PATH), \
            f"System prompt not found at: {PROMPT_PATH}"

    def test_prompt_file_not_empty(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()
        assert len(content) > 500, "Prompt file seems too short"

    def test_prompt_contains_required_sections(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()

        required_sections = [
            "Input Payload Schema",
            "Output JSON Schema",
            "Risk Level Classification",
            "Ancestry-Specific Dietary Rules",
            "CPIC",
            "Quality Rules",
        ]
        for section in required_sections:
            assert section in content, \
                f"Missing required section in prompt: '{section}'"

    def test_prompt_contains_all_ancestry_labels(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()

        for label in ["EUR", "AFR", "CSA", "EAS", "MID", "AMR"]:
            assert label in content, \
                f"Missing ancestry label in prompt: {label}"

    def test_prompt_prohibits_generic_diet(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()

        assert "PROHIBITED" in content.upper() or "prohibited" in content.lower(), \
            "Prompt should explicitly prohibit generic Western dietary advice"


class TestPromptCulturalFoods:
    """Verify the prompt includes culturally specific food references."""

    def test_east_asian_foods(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()
        for food in ["kimchi", "miso", "natto", "bitter melon"]:
            assert food in content.lower(), f"Missing EAS food: {food}"

    def test_south_asian_foods(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()
        for food in ["turmeric", "fenugreek", "dal", "bitter gourd"]:
            assert food in content.lower(), f"Missing CSA food: {food}"

    def test_african_foods(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()
        for food in ["moringa", "plantain", "millet"]:
            assert food in content.lower(), f"Missing AFR food: {food}"

    def test_latin_american_foods(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()
        for food in ["nopales", "chia", "black beans"]:
            assert food in content.lower(), f"Missing AMR food: {food}"

    def test_middle_eastern_foods(self):
        with open(PROMPT_PATH, "r") as f:
            content = f.read()
        for food in ["sumac", "za'atar", "pomegranate", "freekeh"]:
            assert food in content.lower(), f"Missing MID food: {food}"


class TestMockResponseValidation:
    """Validate mock LLM responses match the expected JSON schema."""

    @pytest.mark.parametrize("disease", DISEASES)
    def test_response_has_required_fields(self, disease):
        response = _build_mock_llm_response(
            disease=DISEASE_DISPLAY_NAMES[disease],
            risk_score=0.45,
            ancestry_label="EUR",
            ancestry_display="European",
            confidence_score=1.0,
        )
        assert REQUIRED_OUTPUT_FIELDS.issubset(response.keys())

    @pytest.mark.parametrize("disease", DISEASES)
    def test_dietary_interventions_have_required_fields(self, disease):
        response = _build_mock_llm_response(
            disease=DISEASE_DISPLAY_NAMES[disease],
            risk_score=0.45,
            ancestry_label="EUR",
            ancestry_display="European",
            confidence_score=1.0,
        )
        for intervention in response["dietary_interventions"]:
            assert REQUIRED_DIETARY_FIELDS.issubset(intervention.keys())

    @pytest.mark.parametrize("disease", DISEASES)
    def test_minimum_dietary_interventions(self, disease):
        response = _build_mock_llm_response(
            disease=DISEASE_DISPLAY_NAMES[disease],
            risk_score=0.45,
            ancestry_label="EUR",
            ancestry_display="European",
            confidence_score=1.0,
        )
        assert len(response["dietary_interventions"]) >= 2

    @pytest.mark.parametrize("disease", DISEASES)
    def test_minimum_lifestyle_modifications(self, disease):
        response = _build_mock_llm_response(
            disease=DISEASE_DISPLAY_NAMES[disease],
            risk_score=0.45,
            ancestry_label="EUR",
            ancestry_display="European",
            confidence_score=1.0,
        )
        assert len(response["lifestyle_modifications"]) >= 3

    def test_risk_level_classification_low(self):
        response = _build_mock_llm_response(
            disease="Test", risk_score=0.15,
            ancestry_label="EUR", ancestry_display="European",
            confidence_score=1.0,
        )
        assert response["risk_level"] == "LOW"

    def test_risk_level_classification_moderate(self):
        response = _build_mock_llm_response(
            disease="Test", risk_score=0.45,
            ancestry_label="EUR", ancestry_display="European",
            confidence_score=1.0,
        )
        assert response["risk_level"] == "MODERATE"

    def test_risk_level_classification_high(self):
        response = _build_mock_llm_response(
            disease="Test", risk_score=0.75,
            ancestry_label="EUR", ancestry_display="European",
            confidence_score=1.0,
        )
        assert response["risk_level"] == "HIGH"

    def test_low_confidence_warning_present(self):
        response = _build_mock_llm_response(
            disease="Test", risk_score=0.5,
            ancestry_label="AFR", ancestry_display="African",
            confidence_score=0.3,
        )
        assert "⚠️" in response["ancestry_context"]

    def test_high_confidence_no_warning(self):
        response = _build_mock_llm_response(
            disease="Test", risk_score=0.5,
            ancestry_label="EUR", ancestry_display="European",
            confidence_score=1.0,
        )
        assert "⚠️" not in response["ancestry_context"]

    def test_disclaimer_always_present(self):
        response = _build_mock_llm_response(
            disease="Test", risk_score=0.5,
            ancestry_label="EUR", ancestry_display="European",
            confidence_score=1.0,
        )
        assert "educational purposes" in response["disclaimer"].lower()
        assert "medical advice" in response["disclaimer"].lower()

    def test_response_json_serializable(self):
        """Full response array must be valid JSON."""
        responses = []
        for disease in DISEASES:
            responses.append(_build_mock_llm_response(
                disease=DISEASE_DISPLAY_NAMES[disease],
                risk_score=0.45,
                ancestry_label="EUR",
                ancestry_display="European",
                confidence_score=1.0,
            ))

        json_str = json.dumps(responses)
        parsed = json.loads(json_str)
        assert len(parsed) == len(DISEASES)

    @pytest.mark.parametrize("ancestry_code,confidence", [
        (0, 1.0), (1, 0.3), (2, 0.4), (3, 0.5), (4, 0.25), (5, 0.35),
    ])
    def test_input_payload_construction(self, ancestry_code, confidence):
        """Verify input payload structure for all ancestry groups."""
        payload = {
            "user_id": "test_user",
            "ancestry_code": ancestry_code,
            "ancestry_label": ["EUR", "AFR", "CSA", "EAS", "MID", "AMR"][ancestry_code],
            "ancestry_display": ANCESTRY_DISPLAY_NAMES[ancestry_code],
            "confidence_score": confidence,
            "risk_results": [
                {
                    "disease": DISEASE_DISPLAY_NAMES[d],
                    "risk_score": 0.45,
                    "top_driving_snps": ["rs1333049"],
                }
                for d in DISEASES
            ],
            "pgx_metabolizer_flags": {
                "CYP2D6": "Normal Metabolizer",
                "CYP2C19": "Normal Metabolizer",
                "CYP3A5": "Non-expresser",
            },
        }

        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        assert parsed["ancestry_code"] == ancestry_code
        assert len(parsed["risk_results"]) == 3
