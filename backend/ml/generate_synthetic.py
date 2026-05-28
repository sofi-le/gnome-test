"""
G-Nome Synthetic Training Data Generator
=========================================
Generates a 500-sample synthetic dataset for training Elastic Net disease
risk models. Uses biologically-informed minor allele frequencies and
hand-crafted log-odds effect sizes to produce realistic class balance.

Usage:
    python -m ml.generate_synthetic

Output:
    backend/ml/synthetic_training_data.csv
"""

import os
import numpy as np
import pandas as pd
from ml.snp_config import (
    ALL_SNPS,
    DISEASES,
    ANCESTRY_GWAS_WEIGHT,
    SNP_MINOR_ALLELE_FREQ,
    SNP_EFFECT_SIZES,
)

# Reproducibility
RANDOM_SEED = 42
N_SAMPLES = 500


def _genotype_from_maf(maf: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate genotype dosages (0, 1, 2) from a minor allele frequency
    under Hardy-Weinberg equilibrium.

    P(0) = (1 - maf)^2
    P(1) = 2 * maf * (1 - maf)
    P(2) = maf^2
    """
    p0 = (1 - maf) ** 2
    p1 = 2 * maf * (1 - maf)
    p2 = maf ** 2
    return rng.choice([0, 1, 2], size=n, p=[p0, p1, p2])


def _generate_ancestry_codes(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate ancestry codes (0-5) with a distribution skewed toward EUR (0),
    reflecting real-world biobank composition.
    """
    # Approximate Pan-UKBB ancestry distribution
    weights = np.array([0.50, 0.12, 0.10, 0.10, 0.08, 0.10])
    weights = weights / weights.sum()
    return rng.choice(range(6), size=n, p=weights)


def _compute_disease_labels(
    snp_data: pd.DataFrame,
    ancestry_codes: np.ndarray,
    disease: str,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate binary disease labels using a logistic model:
        logit(p) = intercept + Σ(effect_i * genotype_i) + ancestry_weight

    The intercept is tuned to produce ~20-30% positive class prevalence.
    """
    effect_sizes = SNP_EFFECT_SIZES[disease]

    # Start with a negative intercept to control prevalence
    intercept = -2.0

    logits = np.full(len(snp_data), intercept, dtype=np.float64)

    # Add SNP contributions
    for rsid, effect in effect_sizes.items():
        logits += effect * snp_data[rsid].values.astype(np.float64)

    # Add ancestry-based adjustment: non-EUR ancestry gets a slight
    # risk modifier to simulate population-level prevalence differences
    for i, code in enumerate(ancestry_codes):
        gwas_weight = ANCESTRY_GWAS_WEIGHT[int(code)]
        # Lower GWAS representation → slightly higher uncertainty in risk
        logits[i] += (1.0 - gwas_weight) * 0.3

    # Convert logits to probabilities
    probabilities = 1.0 / (1.0 + np.exp(-logits))

    # Sample binary labels from Bernoulli distribution
    labels = rng.binomial(1, probabilities)

    return labels


def generate_synthetic_dataset(
    n_samples: int = N_SAMPLES,
    seed: int = RANDOM_SEED,
    output_path: str | None = None,
) -> pd.DataFrame:
    """
    Generate the full synthetic training dataset.

    Returns:
        pd.DataFrame with columns: [all SNP rsIDs, ancestry_code,
                                     ancestry_weight, label_CAD,
                                     label_T2D, label_Alzheimer]
    """
    rng = np.random.default_rng(seed)

    # --- Generate SNP genotype features ---
    data: dict[str, np.ndarray] = {}
    for rsid in ALL_SNPS:
        maf = SNP_MINOR_ALLELE_FREQ[rsid]
        data[rsid] = _genotype_from_maf(maf, n_samples, rng)

    snp_df = pd.DataFrame(data)

    # --- Generate ancestry ---
    ancestry_codes = _generate_ancestry_codes(n_samples, rng)
    snp_df["ancestry_code"] = ancestry_codes
    snp_df["ancestry_weight"] = [
        ANCESTRY_GWAS_WEIGHT[int(c)] for c in ancestry_codes
    ]

    # --- Generate disease labels ---
    for disease in DISEASES:
        labels = _compute_disease_labels(snp_df, ancestry_codes, disease, rng)
        snp_df[f"label_{disease}"] = labels

    # --- Report summary ---
    print(f"Generated synthetic dataset: {n_samples} samples")
    print(f"Feature columns: {len(ALL_SNPS)} SNPs + ancestry_code + ancestry_weight")
    for disease in DISEASES:
        col = f"label_{disease}"
        pos_rate = snp_df[col].mean()
        print(f"  {disease}: {pos_rate:.1%} positive ({snp_df[col].sum()}/{n_samples})")
    print()

    # --- Save to CSV ---
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "synthetic_training_data.csv")

    snp_df.to_csv(output_path, index=False)
    print(f"Saved to: {output_path}")

    return snp_df


if __name__ == "__main__":
    df = generate_synthetic_dataset()
    print(f"\nDataset shape: {df.shape}")
    print(f"\nFirst 5 rows:")
    print(df.head())
