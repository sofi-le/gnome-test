"""Carrier status detection — ClinVar dataset-driven with hardcoded fallback."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

CARRIER_GENES = ["BRCA1", "BRCA2", "MLH1", "MSH2", "MSH6", "CFTR", "HBB", "GJB2", "HEXA", "PMS2"]

GENE_CONDITIONS = {
    "BRCA1": "Hereditary Breast/Ovarian Cancer",
    "BRCA2": "Hereditary Breast/Ovarian Cancer",
    "MLH1": "Lynch Syndrome (Colorectal Cancer)",
    "MSH2": "Lynch Syndrome",
    "MSH6": "Lynch Syndrome",
    "CFTR": "Cystic Fibrosis",
    "HBB": "Sickle Cell Disease / Beta-Thalassemia",
    "GJB2": "Hereditary Hearing Loss",
    "HEXA": "Tay-Sachs Disease",
    "PMS2": "Lynch Syndrome",
}

# Lazy-loaded ClinVar data
_clinvar_df = None


def _load_clinvar():
    global _clinvar_df
    if _clinvar_df is not None:
        return
    path = DATA_DIR / "clinvar" / "clinvar_carrier_genes.txt.gz"
    if path.exists():
        _clinvar_df = pd.read_csv(path, sep="\t", compression="gzip", low_memory=False)
        # Filter to rows with valid rsIDs
        _clinvar_df = _clinvar_df[_clinvar_df["RS# (dbSNP)"].notna() & (_clinvar_df["RS# (dbSNP)"] != -1)]
    else:
        _clinvar_df = pd.DataFrame()


def _check_gene_clinvar(snp_lookup: dict, gene: str) -> list[dict]:
    """Check a gene against ClinVar pathogenic variants."""
    _load_clinvar()
    if _clinvar_df is None or _clinvar_df.empty:
        return []

    gene_df = _clinvar_df[_clinvar_df["GeneSymbol"] == gene]
    found = []

    for _, row in gene_df.iterrows():
        try:
            rsid = f"rs{int(row['RS# (dbSNP)'])}"
        except (ValueError, TypeError):
            continue

        genotype = snp_lookup.get(rsid.lower())
        if not genotype or genotype == "--":
            continue

        # Check if alternate (pathogenic) allele is present
        alt_allele = str(row.get("AlternateAllele", "")) if pd.notna(row.get("AlternateAllele")) else ""
        ref_allele = str(row.get("ReferenceAllele", "")) if pd.notna(row.get("ReferenceAllele")) else ""

        if alt_allele and alt_allele in genotype.upper():
            copies = genotype.upper().count(alt_allele)
            found.append({
                "rsid": rsid,
                "genotype": genotype,
                "significance": str(row.get("ClinicalSignificance", "Pathogenic")),
                "condition": str(row.get("PhenotypeList", GENE_CONDITIONS.get(gene, ""))),
                "review_status": str(row.get("ReviewStatus", "")),
                "copies": copies,
                "status": "Carrier (One Copy)" if copies == 1 else "Two Copies Detected",
            })

    return found


# Hardcoded fallback panel for key SNPs (used when ClinVar doesn't match)
FALLBACK_PANEL = [
    {"rsid": "rs334", "gene": "HBB", "condition": "Sickle Cell Disease",
     "pathogenic_genotypes": ["AT", "TA"], "affected_genotypes": ["TT"]},
    {"rsid": "rs75961395", "gene": "CFTR", "condition": "Cystic Fibrosis",
     "pathogenic_genotypes": ["AG", "GA"], "affected_genotypes": ["AA"]},
    {"rsid": "rs76723693", "gene": "HEXA", "condition": "Tay-Sachs Disease",
     "pathogenic_genotypes": ["CT", "TC"], "affected_genotypes": ["TT"]},
]


def check_carrier_status(snps: pd.DataFrame) -> dict:
    """Check carrier status using ClinVar dataset + hardcoded fallback."""
    lookup = dict(zip(snps["rsid"].str.lower(), snps["genotype"]))

    results = []
    genes_with_clinvar_hits = set()

    # ClinVar-driven check for all carrier genes
    for gene in CARRIER_GENES:
        found = _check_gene_clinvar(lookup, gene)

        if found:
            genes_with_clinvar_hits.add(gene)
            # Group by gene — report the most significant finding
            best = max(found, key=lambda v: v["copies"])
            results.append({
                "gene": gene,
                "condition": GENE_CONDITIONS.get(gene, best["condition"]),
                "rsid": best["rsid"],
                "genotype": best["genotype"],
                "status": "carrier" if best["copies"] == 1 else "two_copies",
                "status_label": best["status"],
                "detail": f"Pathogenic variant detected at {best['rsid']}. Clinical significance: {best['significance']}.",
                "review_status": best["review_status"],
                "variants_found": len(found),
                "notes": f"ClinVar data — {len(found)} pathogenic variant(s) checked in {gene}.",
                "disclaimer": "We tested for known pathogenic variants in this gene. A negative result does not rule out carrier status.",
            })
        else:
            results.append({
                "gene": gene,
                "condition": GENE_CONDITIONS.get(gene, ""),
                "rsid": "multiple",
                "genotype": "N/A",
                "status": "not_detected",
                "status_label": "No Pathogenic Variants Detected",
                "detail": f"None of the tested pathogenic variants in {gene} were found in your data.",
                "variants_found": 0,
                "notes": f"Tested against ClinVar pathogenic variants for {gene}.",
                "disclaimer": "A negative result does not rule out carrier status. SNP arrays only test known variants.",
            })

    # Hardcoded fallback for key SNPs not covered above
    for panel in FALLBACK_PANEL:
        if panel["gene"] in genes_with_clinvar_hits:
            continue
        rsid = panel["rsid"]
        genotype = lookup.get(rsid.lower())
        if not genotype or genotype == "--":
            continue

        # Update existing gene result if we find something
        existing = next((r for r in results if r["gene"] == panel["gene"]), None)
        if genotype.upper() in [g.upper() for g in panel.get("affected_genotypes", [])]:
            if existing:
                existing.update({"rsid": rsid, "genotype": genotype, "status": "two_copies",
                                 "status_label": "Two Copies Detected",
                                 "detail": f"Homozygous pathogenic variant at {rsid}."})
        elif genotype.upper() in [g.upper() for g in panel["pathogenic_genotypes"]]:
            if existing:
                existing.update({"rsid": rsid, "genotype": genotype, "status": "carrier",
                                 "status_label": "Carrier (One Copy)",
                                 "detail": f"Heterozygous variant detected at {rsid}."})

    carriers_found = sum(1 for r in results if r["status"] in ("carrier", "two_copies"))

    return {
        "results": results,
        "carriers_found": carriers_found,
        "conditions_tested": len(CARRIER_GENES),
        "data_source": "ClinVar (NCBI)",
        "disclaimer": "Carrier screening tested known pathogenic variants. A negative result does not rule out carrier status for untested variants.",
    }
