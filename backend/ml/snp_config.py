"""
G-Nome SNP Configuration
========================
Central registry of disease-associated SNPs, Pan-UKBB ancestry mappings,
and GWAS representation weights used across the ML pipeline.

SNP selections sourced from PGS Catalog and replicated GWAS literature.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# Disease → rsID mapping (5 SNPs per disease, high-confidence GWAS loci)
# ---------------------------------------------------------------------------

DISEASE_SNPS: Dict[str, List[str]] = {
    "CAD": [
        "rs1333049",   # 9p21.3 / CDKN2A-B — primary CAD risk marker
        "rs4977574",   # 9p21.3 / CDKN2A-B — independent 9p21 signal
        "rs10757278",  # 9p21.3 / CDKN2A-B — replicated CAD risk variant
        "rs6725887",   # 12q24 / WDR5 — CAD susceptibility locus
        "rs9818870",   # 3q22 / MRAS — myocardial infarction risk
    ],
    "T2D": [
        "rs7903146",   # TCF7L2 — strongest T2D genetic risk factor
        "rs1801282",   # PPARG — Pro12Ala, insulin sensitivity
        "rs5219",      # KCNJ11 — KATP channel / insulin secretion
        "rs13266634",  # SLC30A8 — zinc transporter / beta-cell function
        "rs10811661",  # CDKN2A/B — cell cycle / beta-cell mass
    ],
    "Alzheimer": [
        "rs429358",    # APOE — ε4 allele, primary AD risk factor
        "rs7412",      # APOE — ε2/ε3/ε4 isoform determination
        "rs11136000",  # CLU — amyloid-beta clearance
        "rs3851179",   # PICALM — synaptic vesicle endocytosis
        "rs744373",    # BIN1 — tau pathology / endocytosis
    ],
}

# Flat list of all unique SNP rsIDs used as model features
ALL_SNPS: List[str] = []
for _snps in DISEASE_SNPS.values():
    for _snp in _snps:
        if _snp not in ALL_SNPS:
            ALL_SNPS.append(_snp)

# Human-readable disease names for API responses
DISEASE_DISPLAY_NAMES: Dict[str, str] = {
    "CAD": "Coronary Artery Disease",
    "T2D": "Type 2 Diabetes",
    "Alzheimer": "Alzheimer's Disease",
}

DISEASES: List[str] = list(DISEASE_SNPS.keys())

# ---------------------------------------------------------------------------
# Pan-UKBB Ancestry Definitions
# ---------------------------------------------------------------------------

ANCESTRY_MAP: Dict[int, str] = {
    0: "EUR",  # European
    1: "AFR",  # African
    2: "CSA",  # Central/South Asian
    3: "EAS",  # East Asian
    4: "MID",  # Middle Eastern
    5: "AMR",  # Admixed American
}

ANCESTRY_DISPLAY_NAMES: Dict[int, str] = {
    0: "European",
    1: "African",
    2: "Central/South Asian",
    3: "East Asian",
    4: "Middle Eastern",
    5: "Admixed American",
}

# Approximate GWAS representation weights reflecting relative representation
# in training GWAS cohorts (EUR = 1.0 baseline). Used for:
#   1. Confidence score in EquityBadge
#   2. Feature input to the Elastic Net model
ANCESTRY_GWAS_WEIGHT: Dict[int, float] = {
    0: 1.00,  # EUR — baseline, overwhelmingly represented
    1: 0.30,  # AFR — significantly underrepresented
    2: 0.40,  # CSA — underrepresented
    3: 0.50,  # EAS — moderately represented
    4: 0.25,  # MID — most underrepresented
    5: 0.35,  # AMR — underrepresented
}

# ---------------------------------------------------------------------------
# Synthetic Data Generation Parameters
# ---------------------------------------------------------------------------

# Minor allele frequencies (approximate, for synthetic data generation)
# These are rough population-average MAFs from gnomAD/literature
SNP_MINOR_ALLELE_FREQ: Dict[str, float] = {
    # CAD SNPs
    "rs1333049":  0.47,
    "rs4977574":  0.46,
    "rs10757278": 0.48,
    "rs6725887":  0.15,
    "rs9818870":  0.15,
    # T2D SNPs
    "rs7903146":  0.30,
    "rs1801282":  0.12,
    "rs5219":     0.35,
    "rs13266634": 0.25,
    "rs10811661": 0.20,
    # Alzheimer SNPs
    "rs429358":   0.15,
    "rs7412":     0.08,
    "rs11136000": 0.40,
    "rs3851179":  0.35,
    "rs744373":   0.30,
}

# Effect sizes (log-odds) for synthetic label generation
# Positive = risk-increasing for the alternate allele
SNP_EFFECT_SIZES: Dict[str, Dict[str, float]] = {
    "CAD": {
        "rs1333049":  0.35,
        "rs4977574":  0.30,
        "rs10757278": 0.28,
        "rs6725887":  0.20,
        "rs9818870":  0.18,
    },
    "T2D": {
        "rs7903146":  0.45,
        "rs1801282":  0.25,
        "rs5219":     0.22,
        "rs13266634": 0.20,
        "rs10811661": 0.18,
    },
    "Alzheimer": {
        "rs429358":   0.85,  # APOE ε4 has a very large effect
        "rs7412":    -0.40,  # ε2 is protective
        "rs11136000": 0.15,
        "rs3851179":  0.12,
        "rs744373":   0.18,
    },
}
