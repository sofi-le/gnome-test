"""Skin lesion scanner — EfficientNet-B4 inference + MC1R genetic risk fusion.

MC1R risk multipliers driven by HIrisPlex-S JSON dataset.
"""

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

# HAM10000 class labels
CLASSES = ["MEL", "NV", "BCC", "AKIEC", "BKL", "DF", "VASC"]
CLASS_LABELS = {
    "MEL": "Melanoma",
    "NV": "Melanocytic Nevus (common mole)",
    "BCC": "Basal Cell Carcinoma",
    "AKIEC": "Actinic Keratosis / Intraepithelial Carcinoma",
    "BKL": "Benign Keratosis",
    "DF": "Dermatofibroma",
    "VASC": "Vascular Lesion",
}

# Lazy-loaded MC1R risk data from HIrisPlex
_mc1r_variants = None


def _load_mc1r():
    global _mc1r_variants
    if _mc1r_variants is not None:
        return
    path = DATA_DIR / "hirisplex" / "hirisplex_s_snps.json"
    if path.exists():
        data = json.loads(path.read_text())
        _mc1r_variants = data.get("mc1r_melanoma_risk", {}).get("high_risk_variants", [])
    else:
        _mc1r_variants = []


def _get_mc1r_multiplier(snps: pd.DataFrame) -> dict:
    """Check MC1R variants for melanoma genetic risk adjustment using HIrisPlex data."""
    _load_mc1r()
    lookup = dict(zip(snps["rsid"].str.lower(), snps["genotype"]))

    detected_variants = []
    max_multiplier = 1.0

    for variant in _mc1r_variants:
        rsid = variant["rsid"]
        genotype = lookup.get(rsid.lower(), "")
        if not genotype or genotype == "--":
            continue

        # Check if the effect allele is present in the genotype
        # Each variant in HIrisPlex has an effect allele implied by the variant name
        # The multiplier applies if any non-reference allele is present
        multiplier = variant.get("multiplier", 1.0)
        # MC1R variants are loss-of-function — any non-wildtype allele counts
        # For SNP arrays, heterozygous = one copy, homozygous = two copies
        ref_alleles = {"rs1805007": "C", "rs1805008": "C", "rs1805006": "G",
                       "rs1805009": "G", "rs2228479": "G"}
        ref = ref_alleles.get(rsid, "")
        gt_upper = genotype.upper()

        if ref and ref in gt_upper and gt_upper != ref * 2:
            # Heterozygous carrier
            detected_variants.append({
                "rsid": rsid, "variant": variant.get("variant", ""),
                "genotype": genotype, "multiplier": multiplier, "copies": 1,
            })
            max_multiplier = max(max_multiplier, multiplier)
        elif ref and ref not in gt_upper:
            # Homozygous variant — higher risk
            detected_variants.append({
                "rsid": rsid, "variant": variant.get("variant", ""),
                "genotype": genotype, "multiplier": multiplier * 1.3, "copies": 2,
            })
            max_multiplier = max(max_multiplier, multiplier * 1.3)

    return {
        "multiplier": round(max_multiplier, 2),
        "variants_detected": detected_variants,
        "mc1r_status": "variant_detected" if detected_variants else "wildtype",
    }


def _run_inference(img_bytes: bytes) -> dict:
    """Run EfficientNet-B4 inference on skin lesion image."""
    try:
        from PIL import Image
        import torch
        from torchvision import transforms
        from transformers import AutoModelForImageClassification

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        transform = transforms.Compose([
            transforms.Resize((380, 380)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        tensor = transform(img).unsqueeze(0)

        model = AutoModelForImageClassification.from_pretrained(
            "google/efficientnet-b4",
            num_labels=7,
            ignore_mismatched_sizes=True,
        )
        model.eval()

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs.logits, dim=1).squeeze().numpy()

        class_probs = {cls: round(float(prob), 4) for cls, prob in zip(CLASSES, probs)}
        return {"success": True, "probabilities": class_probs}

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "probabilities": _mock_probabilities(),
        }


def _mock_probabilities() -> dict:
    """Generate realistic-looking mock probabilities for demo."""
    return {"MEL": 0.08, "NV": 0.72, "BCC": 0.05, "AKIEC": 0.03, "BKL": 0.07, "DF": 0.03, "VASC": 0.02}


def _compute_fused_risk(p_melanoma: float, genetic_multiplier: float) -> dict:
    """Fuse CV melanoma probability with MC1R genetic risk."""
    fused = p_melanoma * genetic_multiplier
    fused_pct = min(round(fused * 100, 1), 100)

    if fused_pct >= 75:
        urgency, urgency_label, color = "urgent", "Urgent — seek review within 1 week", "#e74c3c"
    elif fused_pct >= 55:
        urgency, urgency_label, color = "high", "High — see dermatologist within 4 weeks", "#e67e22"
    elif fused_pct >= 30:
        urgency, urgency_label, color = "moderate", "Moderate — discuss with GP", "#f39c12"
    else:
        urgency, urgency_label, color = "low", "Low — routine monitoring", "#27ae60"

    return {"fused_risk_pct": fused_pct, "urgency": urgency, "urgency_label": urgency_label, "color": color}


def analyze_skin_lesion(img_bytes: bytes, snps: pd.DataFrame) -> dict:
    """Full skin lesion analysis: CV inference + genetic risk fusion."""
    inference = _run_inference(img_bytes)
    probs = inference["probabilities"]

    mc1r = _get_mc1r_multiplier(snps)
    p_melanoma = probs.get("MEL", 0)
    fused = _compute_fused_risk(p_melanoma, mc1r["multiplier"])

    classifications = []
    for cls in sorted(probs, key=probs.get, reverse=True):
        classifications.append({
            "class": cls,
            "label": CLASS_LABELS.get(cls, cls),
            "probability": probs[cls],
            "probability_pct": round(probs[cls] * 100, 1),
        })

    return {
        "classifications": classifications,
        "melanoma_probability": round(p_melanoma, 4),
        "mc1r_variant_detected": mc1r["mc1r_status"] == "variant_detected",
        "mc1r_details": mc1r["variants_detected"],
        "genetic_multiplier": mc1r["multiplier"],
        **fused,
        "model_available": inference["success"],
        "data_source": "HIrisPlex-S MC1R melanoma risk (Walsh et al. 2017)",
        "disclaimer": "Not a dermatological assessment. Consult a clinician for any skin concern.",
    }
