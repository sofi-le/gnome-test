"""
G-Nome Risk Engine Integration Tests
======================================
Tests covering synthetic data generation, model training, feature extraction,
and FastAPI endpoint responses across all ancestry groups.

Usage:
    pytest tests/test_risk_engine.py -v
"""

import os
import sys
import time
import json
import pytest
import numpy as np
import pandas as pd

# Ensure backend is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.snp_config import ALL_SNPS, DISEASES, DISEASE_DISPLAY_NAMES, ANCESTRY_MAP
from ml.generate_synthetic import generate_synthetic_dataset
from ml.train_model import train_models, FEATURE_COLS
from inference.risk_engine import (
    extract_features,
    predict_risk,
    _encode_genotype,
    PredictionResponse,
)
from tests.mock_data import (
    MOCK_DATA_BY_ANCESTRY,
    EXPECTED_RESPONSE_KEYS,
    EXPECTED_RESULT_KEYS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def synthetic_data_path(tmp_path_factory):
    """Generate synthetic data to a temp directory."""
    tmp_dir = tmp_path_factory.mktemp("gnome_test")
    output_path = str(tmp_dir / "test_synthetic_data.csv")
    generate_synthetic_dataset(n_samples=200, seed=99, output_path=output_path)
    return output_path


@pytest.fixture(scope="module")
def trained_models(synthetic_data_path, tmp_path_factory):
    """Train models on the test synthetic data."""
    tmp_dir = tmp_path_factory.mktemp("gnome_models")
    model_path = str(tmp_dir / "test_models.joblib")
    results = train_models(data_path=synthetic_data_path, output_path=model_path)
    return results


# ---------------------------------------------------------------------------
# Phase 1: Synthetic Data Generation Tests
# ---------------------------------------------------------------------------

class TestSyntheticDataGeneration:
    """Tests for the synthetic training dataset."""

    def test_output_file_exists(self, synthetic_data_path):
        assert os.path.exists(synthetic_data_path)

    def test_correct_row_count(self, synthetic_data_path):
        df = pd.read_csv(synthetic_data_path)
        assert len(df) == 200

    def test_snp_columns_present(self, synthetic_data_path):
        df = pd.read_csv(synthetic_data_path)
        for rsid in ALL_SNPS:
            assert rsid in df.columns, f"Missing SNP column: {rsid}"

    def test_ancestry_columns_present(self, synthetic_data_path):
        df = pd.read_csv(synthetic_data_path)
        assert "ancestry_code" in df.columns
        assert "ancestry_weight" in df.columns

    def test_label_columns_present(self, synthetic_data_path):
        df = pd.read_csv(synthetic_data_path)
        for disease in DISEASES:
            col = f"label_{disease}"
            assert col in df.columns, f"Missing label column: {col}"

    def test_snp_values_valid(self, synthetic_data_path):
        df = pd.read_csv(synthetic_data_path)
        for rsid in ALL_SNPS:
            values = df[rsid].unique()
            assert set(values).issubset({0, 1, 2}), \
                f"Invalid genotype values in {rsid}: {values}"

    def test_ancestry_codes_valid(self, synthetic_data_path):
        df = pd.read_csv(synthetic_data_path)
        assert df["ancestry_code"].min() >= 0
        assert df["ancestry_code"].max() <= 5

    def test_labels_binary(self, synthetic_data_path):
        df = pd.read_csv(synthetic_data_path)
        for disease in DISEASES:
            col = f"label_{disease}"
            values = df[col].unique()
            assert set(values).issubset({0, 1}), \
                f"Non-binary values in {col}: {values}"

    def test_class_balance_reasonable(self, synthetic_data_path):
        """Positive class should be between 10% and 50%."""
        df = pd.read_csv(synthetic_data_path)
        for disease in DISEASES:
            col = f"label_{disease}"
            pos_rate = df[col].mean()
            assert 0.10 < pos_rate < 0.50, \
                f"Unreasonable class balance for {disease}: {pos_rate:.1%}"


# ---------------------------------------------------------------------------
# Phase 1: Model Training Tests
# ---------------------------------------------------------------------------

class TestModelTraining:
    """Tests for the trained ElasticNet models."""

    def test_all_diseases_trained(self, trained_models):
        for disease in DISEASES:
            assert disease in trained_models

    def test_model_has_required_keys(self, trained_models):
        required_keys = {"model", "best_params", "cv_score", "feature_names",
                         "non_zero_features", "coefficients"}
        for disease in DISEASES:
            assert required_keys.issubset(trained_models[disease].keys())

    def test_cv_score_positive(self, trained_models):
        for disease in DISEASES:
            assert trained_models[disease]["cv_score"] > 0.0

    def test_has_non_zero_features(self, trained_models):
        """Each model should select at least some features."""
        for disease in DISEASES:
            non_zero = trained_models[disease]["non_zero_features"]
            assert len(non_zero) > 0, \
                f"No features selected for {disease}"

    def test_feature_names_match(self, trained_models):
        for disease in DISEASES:
            assert trained_models[disease]["feature_names"] == FEATURE_COLS


# ---------------------------------------------------------------------------
# Phase 1: Genotype Encoding Tests
# ---------------------------------------------------------------------------

class TestGenotypeEncoding:
    """Tests for the genotype string → dosage encoding."""

    def test_homozygous_ref(self):
        assert _encode_genotype("AA") == 0
        assert _encode_genotype("CC") == 0
        assert _encode_genotype("GG") == 0
        assert _encode_genotype("TT") == 0

    def test_heterozygous(self):
        assert _encode_genotype("CT") == 1
        assert _encode_genotype("AG") == 1
        assert _encode_genotype("AC") == 1
        assert _encode_genotype("GT") == 1

    def test_missing_data(self):
        assert _encode_genotype("") == 0
        assert _encode_genotype("A") == 0
        assert _encode_genotype(None) == 0

    def test_case_insensitive(self):
        assert _encode_genotype("ct") == 1
        assert _encode_genotype("Ag") == 1
        assert _encode_genotype("aa") == 0


# ---------------------------------------------------------------------------
# Phase 1: Feature Extraction Tests
# ---------------------------------------------------------------------------

class TestFeatureExtraction:
    """Tests for extracting the model feature vector from SNP dicts."""

    def test_feature_vector_shape(self):
        snps = {rsid: "AA" for rsid in ALL_SNPS}
        features = extract_features(snps, ancestry_code=0)
        expected_len = len(ALL_SNPS) + 1  # SNPs + ancestry_weight
        assert features.shape == (1, expected_len)

    def test_missing_snps_default_to_zero(self):
        features = extract_features({}, ancestry_code=0)
        # All SNP features should be 0 (missing → reference)
        for i in range(len(ALL_SNPS)):
            assert features[0, i] == 0.0

    def test_ancestry_weight_appended(self):
        features = extract_features({}, ancestry_code=1)  # AFR
        # Last feature should be ancestry_weight for AFR (0.3)
        assert features[0, -1] == pytest.approx(0.3)

    def test_ancestry_weight_eur(self):
        features = extract_features({}, ancestry_code=0)  # EUR
        assert features[0, -1] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Phase 4: End-to-End Inference Tests
# ---------------------------------------------------------------------------

class TestInference:
    """End-to-end inference tests across all ancestry groups."""

    @pytest.fixture(autouse=True)
    def _load_models(self, trained_models, monkeypatch):
        """Monkey-patch the global models cache for testing."""
        import inference.risk_engine as engine
        engine._models = trained_models

    @pytest.mark.parametrize("ancestry_code", [0, 1, 2, 3, 4, 5])
    def test_predict_risk_returns_valid_response(self, ancestry_code):
        label, snp_dict = MOCK_DATA_BY_ANCESTRY[ancestry_code]
        response = predict_risk(snp_dict, ancestry_code)

        assert isinstance(response, PredictionResponse)
        assert response.ancestry_code == ancestry_code
        assert response.ancestry_label == ANCESTRY_MAP[ancestry_code]

    @pytest.mark.parametrize("ancestry_code", [0, 1, 2, 3, 4, 5])
    def test_risk_scores_in_valid_range(self, ancestry_code):
        _, snp_dict = MOCK_DATA_BY_ANCESTRY[ancestry_code]
        response = predict_risk(snp_dict, ancestry_code)

        for result in response.results:
            assert 0.0 <= result.risk_score <= 1.0, \
                f"Risk score out of range for {result.disease}: {result.risk_score}"

    @pytest.mark.parametrize("ancestry_code", [0, 1, 2, 3, 4, 5])
    def test_all_diseases_present_in_response(self, ancestry_code):
        _, snp_dict = MOCK_DATA_BY_ANCESTRY[ancestry_code]
        response = predict_risk(snp_dict, ancestry_code)

        disease_names = {r.disease for r in response.results}
        expected = {DISEASE_DISPLAY_NAMES[d] for d in DISEASES}
        assert disease_names == expected

    @pytest.mark.parametrize("ancestry_code", [0, 1, 2, 3, 4, 5])
    def test_top_driving_snps_are_valid_rsids(self, ancestry_code):
        _, snp_dict = MOCK_DATA_BY_ANCESTRY[ancestry_code]
        response = predict_risk(snp_dict, ancestry_code)

        for result in response.results:
            for snp in result.top_driving_snps:
                assert snp.startswith("rs"), \
                    f"Invalid rsID in top_driving_snps: {snp}"
                assert snp in ALL_SNPS, \
                    f"Unknown rsID in top_driving_snps: {snp}"

    def test_confidence_score_matches_ancestry(self):
        """EUR should have 1.0 confidence, AFR should have 0.3."""
        _, eur_snps = MOCK_DATA_BY_ANCESTRY[0]
        eur_response = predict_risk(eur_snps, 0)
        assert eur_response.confidence_score == pytest.approx(1.0)

        _, afr_snps = MOCK_DATA_BY_ANCESTRY[1]
        afr_response = predict_risk(afr_snps, 1)
        assert afr_response.confidence_score == pytest.approx(0.3)

    def test_inference_performance(self):
        """Single inference should complete in under 100ms."""
        _, snp_dict = MOCK_DATA_BY_ANCESTRY[0]
        start = time.perf_counter()
        predict_risk(snp_dict, 0)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 100, \
            f"Inference took {elapsed_ms:.1f}ms, exceeds 100ms budget"

    def test_response_serializable_to_json(self):
        """Response should be cleanly serializable to JSON."""
        _, snp_dict = MOCK_DATA_BY_ANCESTRY[0]
        response = predict_risk(snp_dict, 0)
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)

        # Verify all expected keys
        assert EXPECTED_RESPONSE_KEYS.issubset(parsed.keys())
        for result in parsed["results"]:
            assert EXPECTED_RESULT_KEYS.issubset(result.keys())


# ---------------------------------------------------------------------------
# Phase 4: FastAPI Endpoint Tests (via TestClient)
# ---------------------------------------------------------------------------

class TestFastAPIEndpoint:
    """Tests for the FastAPI HTTP endpoint."""

    @pytest.fixture(autouse=True)
    def _setup_client(self, trained_models, monkeypatch):
        """Set up TestClient with models loaded."""
        import inference.risk_engine as engine
        engine._models = trained_models

        from fastapi.testclient import TestClient
        self.client = TestClient(engine.app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_predict_risk_endpoint(self):
        _, snp_dict = MOCK_DATA_BY_ANCESTRY[0]
        payload = {"snps": snp_dict, "ancestry_code": 0}
        response = self.client.post("/predict-risk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3

    def test_invalid_ancestry_code(self):
        payload = {"snps": {}, "ancestry_code": 99}
        response = self.client.post("/predict-risk", json=payload)
        assert response.status_code == 422  # Validation error

    def test_model_info_endpoint(self):
        response = self.client.get("/model-info")
        assert response.status_code == 200
        data = response.json()
        assert "diseases" in data
        for disease in DISEASES:
            assert disease in data["diseases"]
