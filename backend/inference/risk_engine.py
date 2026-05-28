"""
G-Nome Risk Engine — FastAPI Inference Endpoint
=================================================
Accepts parsed user SNP dictionaries, extracts features, runs ElasticNet
.predict_proba(), and returns structured risk scores with driving SNPs.

Usage:
    uvicorn inference.risk_engine:app --host 0.0.0.0 --port 8000
"""

import os
import time
from typing import Dict, List, Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ml.snp_config import (
    ALL_SNPS,
    DISEASES,
    DISEASE_DISPLAY_NAMES,
    ANCESTRY_MAP,
    ANCESTRY_DISPLAY_NAMES,
    ANCESTRY_GWAS_WEIGHT,
)

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------

app = FastAPI(
    title="G-Nome Risk Engine",
    description="Elastic Net polygenic disease risk prediction with Pan-UKBB ancestry weighting",
    version="1.0.0",
)

# Load models at startup
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "ml", "models.joblib"
)
_models: Optional[dict] = None


def _get_models() -> dict:
    """Lazy-load serialized models."""
    global _models
    if _models is None:
        if not os.path.exists(_MODEL_PATH):
            raise RuntimeError(
                f"Model file not found at {_MODEL_PATH}. "
                "Run `python -m ml.generate_synthetic && python -m ml.train_model` first."
            )
        _models = joblib.load(_MODEL_PATH)
    return _models


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    """Input from the teammate's SNP parser."""
    snps: Dict[str, str] = Field(
        ...,
        description="Mapping of rsID → genotype string (e.g., 'CT', 'AA', 'GG')",
        json_schema_extra={"example": {"rs1333049": "CT", "rs429358": "CC"}},
    )
    ancestry_code: int = Field(
        ...,
        ge=0,
        le=5,
        description="Pan-UKBB ancestry group code (0=EUR, 1=AFR, 2=CSA, 3=EAS, 4=MID, 5=AMR)",
    )


class DiseaseRiskResult(BaseModel):
    """Risk prediction for a single disease."""
    disease: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    top_driving_snps: List[str]


class PredictionResponse(BaseModel):
    """Full prediction output."""
    results: List[DiseaseRiskResult]
    ancestry_code: int
    ancestry_label: str
    ancestry_display: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    inference_time_ms: float


# ---------------------------------------------------------------------------
# Genotype encoding
# ---------------------------------------------------------------------------

# Canonical mapping: count of non-reference (alternate) alleles
# In a simplified model: homozygous ref → 0, het → 1, homozygous alt → 2
# We use alphabetical sorting to normalize strand orientation

_HOMOZYGOUS_GENOTYPES = {"AA", "CC", "GG", "TT"}


def _encode_genotype(genotype: str) -> int:
    """
    Encode a two-character genotype string to dosage (0, 1, 2).

    Rules:
        - Homozygous (both alleles same): 0 (reference-like)
        - Heterozygous (different alleles): 1
        - Missing or unknown: defaults to 0 (conservative)

    Note: In a real pipeline, we'd need ref/alt allele definitions per SNP.
    For this hackathon model trained on synthetic dosage data, we use a
    simplified encoding where heterozygosity = 1 dose of risk allele.
    """
    if not genotype or len(genotype) < 2:
        return 0  # Missing data → reference

    genotype = genotype.upper().strip()

    if len(genotype) == 2:
        if genotype[0] == genotype[1]:
            # Homozygous — could be ref or alt, encode as 0 or 2
            # For synthetic data compatibility, we'll use a simple heuristic:
            # The "first" allele alphabetically is treated as reference
            return 0 if genotype in _HOMOZYGOUS_GENOTYPES else 0
        else:
            return 1  # Heterozygous
    return 0


def _encode_genotype_dosage(genotype: str, risk_allele: str = "") -> int:
    """
    Enhanced genotype encoding with risk allele awareness.
    Counts the number of risk alleles present (0, 1, or 2).

    Falls back to simple het/hom encoding if risk allele is unknown.
    """
    if not genotype or len(genotype) < 2:
        return 0

    genotype = genotype.upper().strip()

    if risk_allele:
        risk_allele = risk_allele.upper()
        count = sum(1 for allele in genotype if allele == risk_allele)
        return min(count, 2)

    # Fallback: simple encoding
    return _encode_genotype(genotype)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(
    snps: Dict[str, str],
    ancestry_code: int,
) -> np.ndarray:
    """
    Extract the feature vector from a user's SNP dictionary.

    Returns a 1D numpy array of length len(ALL_SNPS) + 1 (ancestry weight).
    Order matches the training feature order: [SNP dosages..., ancestry_weight].
    """
    features = []

    for rsid in ALL_SNPS:
        genotype = snps.get(rsid, "")
        dosage = _encode_genotype(genotype)
        features.append(dosage)

    # Append ancestry GWAS representation weight
    ancestry_weight = ANCESTRY_GWAS_WEIGHT.get(ancestry_code, 0.5)
    features.append(ancestry_weight)

    return np.array(features, dtype=np.float64).reshape(1, -1)


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

def predict_risk(
    snps: Dict[str, str],
    ancestry_code: int,
) -> PredictionResponse:
    """
    Run disease risk inference for a single user.

    Args:
        snps: rsID → genotype string mapping from parser
        ancestry_code: Pan-UKBB ancestry code (0-5)

    Returns:
        PredictionResponse with risk scores and driving SNPs
    """
    start_time = time.perf_counter()

    models = _get_models()
    X = extract_features(snps, ancestry_code)

    results: List[DiseaseRiskResult] = []

    for disease in DISEASES:
        model_data = models[disease]
        model = model_data["model"]

        # Predict probability of positive class (disease risk)
        proba = model.predict_proba(X)[0]

        # Class 1 probability = risk score
        risk_score = float(proba[1]) if len(proba) > 1 else float(proba[0])

        # Get non-zero coefficient features (driving SNPs only, not ancestry)
        top_driving_snps = [
            feat for feat in model_data["non_zero_features"]
            if feat.startswith("rs")  # Only include rsIDs, not ancestry_weight
        ]

        results.append(DiseaseRiskResult(
            disease=DISEASE_DISPLAY_NAMES[disease],
            risk_score=round(risk_score, 4),
            top_driving_snps=top_driving_snps,
        ))

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return PredictionResponse(
        results=results,
        ancestry_code=ancestry_code,
        ancestry_label=ANCESTRY_MAP.get(ancestry_code, "Unknown"),
        ancestry_display=ANCESTRY_DISPLAY_NAMES.get(ancestry_code, "Unknown"),
        confidence_score=round(ANCESTRY_GWAS_WEIGHT.get(ancestry_code, 0.5), 2),
        inference_time_ms=round(elapsed_ms, 2),
    )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "G-Nome Risk Engine"}


@app.post("/predict-risk", response_model=PredictionResponse)
def predict_risk_endpoint(request: PredictionRequest):
    """
    Predict disease risk from parsed SNP data.

    Accepts the JSON output from the teammate's 23andMe parser and returns
    risk probabilities with identified driving SNPs.
    """
    try:
        response = predict_risk(
            snps=request.snps,
            ancestry_code=request.ancestry_code,
        )
        return response
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


@app.get("/model-info")
def model_info():
    """Return model metadata and feature importance."""
    try:
        models = _get_models()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    info = {}
    for disease in DISEASES:
        model_data = models[disease]
        info[disease] = {
            "display_name": DISEASE_DISPLAY_NAMES[disease],
            "best_params": model_data["best_params"],
            "cv_roc_auc": round(model_data["cv_score"], 4),
            "non_zero_features": model_data["non_zero_features"],
            "coefficients": {
                k: round(v, 4) for k, v in model_data["coefficients"].items()
            },
        }

    return {
        "diseases": info,
        "total_features": len(ALL_SNPS) + 1,
        "snp_features": ALL_SNPS,
        "ancestry_groups": ANCESTRY_DISPLAY_NAMES,
    }
