"""Pharmacogenomics engine — CPIC + PharmGKB dataset-driven."""

import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

# Lazy-loaded datasets
_cpic_diplotypes = None
_cpic_recs = None
_pharmgkb = None


def _load_cpic():
    global _cpic_diplotypes, _cpic_recs
    if _cpic_diplotypes is not None:
        return
    dip_path = DATA_DIR / "cpic" / "diplotypes.json"
    rec_path = DATA_DIR / "cpic" / "recommendations.json"
    _cpic_diplotypes = json.loads(dip_path.read_text()) if dip_path.exists() else []
    _cpic_recs = json.loads(rec_path.read_text()) if rec_path.exists() else []


def _load_pharmgkb():
    global _pharmgkb
    if _pharmgkb is not None:
        return
    path = DATA_DIR / "pharmgkb" / "clinical" / "clinical_annotations.tsv"
    if path.exists():
        df = pd.read_csv(path, sep="\t", low_memory=False)
        _pharmgkb = df[df["Level of Evidence"].isin(["1A", "1B"])]
    else:
        _pharmgkb = pd.DataFrame()


# Star allele SNP lookup
STAR_ALLELES = {
    "CYP2C19": {
        "rs4244285": {"GG": "*1/*1", "AG": "*1/*2", "AA": "*2/*2"},
        "rs12248560": {"CC": "*1/*1", "CT": "*1/*17", "TT": "*17/*17"},
    },
    "CYP2C9": {
        "rs1799853": {"CC": "*1/*1", "CT": "*1/*2", "TT": "*2/*2"},
        "rs1057910": {"AA": "*1/*1", "AC": "*1/*3", "CC": "*3/*3"},
    },
    "CYP1A2": {
        "rs762551": {"AA": "*1F/*1F", "AC": "*1/*1F", "CC": "*1/*1"},
    },
    "SLCO1B1": {
        "rs4149056": {"TT": "*1a/*1a", "TC": "*1a/*5", "CC": "*5/*5"},
    },
    "DPYD": {
        "rs3918290": {"GG": "*1/*1", "GA": "*1/*2A", "AA": "*2A/*2A"},
        "rs55886062": {"AA": "*1/*1", "AG": "*1/*13", "GG": "*13/*13"},
    },
    "TPMT": {
        "rs1800462": {"GG": "*1/*1", "GA": "*1/*2", "AA": "*2/*2"},
        "rs1142345": {"AA": "*1/*1", "AG": "*1/*3C", "GG": "*3C/*3C"},
    },
}

PHENOTYPE_MAP = {
    "*1/*1": "Normal Metabolizer", "*1/*2": "Intermediate Metabolizer", "*2/*2": "Poor Metabolizer",
    "*1/*3": "Intermediate Metabolizer", "*3/*3": "Poor Metabolizer",
    "*1/*17": "Rapid Metabolizer", "*17/*17": "Ultra-rapid Metabolizer",
    "*1/*2A": "Intermediate Metabolizer", "*2A/*2A": "Poor Metabolizer",
    "*1/*13": "Intermediate Metabolizer",
    "*1/*3C": "Intermediate Metabolizer", "*3C/*3C": "Poor Metabolizer",
    "*1F/*1F": "Ultra-rapid Metabolizer", "*1/*1F": "Rapid Metabolizer",
    "*1a/*1a": "Normal Function", "*1a/*5": "Decreased Function", "*5/*5": "Poor Function",
}

DRUG_FLAGS_FALLBACK = {
    "CYP2C19": {
        "Poor Metabolizer": [
            {"drug": "Clopidogrel (Plavix)", "severity": "HIGH", "action": "Avoid — use prasugrel or ticagrelor", "reason": "Cannot convert clopidogrel to active form"},
            {"drug": "Escitalopram / Citalopram", "severity": "MODERATE", "action": "Consider dose reduction or switch to sertraline", "reason": "Reduced metabolism"},
            {"drug": "Omeprazole / Lansoprazole", "severity": "MODERATE", "action": "Consider dose reduction", "reason": "Slower metabolism"},
        ],
        "Intermediate Metabolizer": [
            {"drug": "Clopidogrel (Plavix)", "severity": "MODERATE", "action": "Monitor effectiveness — may need alternative", "reason": "Reduced activation"},
        ],
        "Rapid Metabolizer": [
            {"drug": "Omeprazole / Lansoprazole", "severity": "MODERATE", "action": "May need higher dose", "reason": "Faster clearance"},
        ],
        "Ultra-rapid Metabolizer": [
            {"drug": "Omeprazole / Lansoprazole", "severity": "MODERATE", "action": "May need higher dose", "reason": "Very fast clearance"},
        ],
    },
    "CYP2C9": {
        "Poor Metabolizer": [
            {"drug": "Warfarin (Coumadin)", "severity": "HIGH", "action": "Start at 50% lower dose — high bleeding risk", "reason": "Cannot clear warfarin normally"},
            {"drug": "Celecoxib", "severity": "MODERATE", "action": "Use lowest effective dose", "reason": "Slower metabolism"},
        ],
        "Intermediate Metabolizer": [
            {"drug": "Warfarin (Coumadin)", "severity": "MODERATE", "action": "Start at reduced dose — monitor INR closely", "reason": "Reduced clearance"},
        ],
    },
    "SLCO1B1": {
        "Poor Function": [
            {"drug": "Simvastatin", "severity": "HIGH", "action": "Avoid high-dose — use pravastatin or rosuvastatin", "reason": "5x increased myopathy risk"},
            {"drug": "Atorvastatin", "severity": "MODERATE", "action": "Use lowest effective dose", "reason": "Increased statin exposure"},
        ],
        "Decreased Function": [
            {"drug": "Simvastatin", "severity": "MODERATE", "action": "Limit to 20mg — consider alternative", "reason": "Increased myopathy risk"},
        ],
    },
    "DPYD": {
        "Poor Metabolizer": [
            {"drug": "5-Fluorouracil / Capecitabine", "severity": "HIGH", "action": "Avoid — life-threatening toxicity", "reason": "Cannot break down fluoropyrimidines"},
        ],
        "Intermediate Metabolizer": [
            {"drug": "5-Fluorouracil / Capecitabine", "severity": "HIGH", "action": "Reduce dose by 50% minimum", "reason": "Impaired clearance"},
        ],
    },
    "TPMT": {
        "Poor Metabolizer": [
            {"drug": "Azathioprine / 6-Mercaptopurine", "severity": "HIGH", "action": "Reduce to 10% or avoid", "reason": "Fatal myelosuppression risk"},
        ],
        "Intermediate Metabolizer": [
            {"drug": "Azathioprine / 6-Mercaptopurine", "severity": "MODERATE", "action": "Start at 50% dose and monitor", "reason": "Reduced metabolism"},
        ],
    },
}

CYP2D6_WARNING = {
    "gene": "CYP2D6", "status": "not_callable",
    "disclaimer": "CYP2D6 cannot be reliably determined from SNP array data. This gene affects codeine, tramadol, tamoxifen, and many antidepressants. Full CYP2D6 testing requires specialized sequencing.",
    "affected_drugs": ["Codeine / Tramadol (pain)", "Tamoxifen (breast cancer)", "Atomoxetine (ADHD)", "Nortriptyline / Amitriptyline (depression)"],
}


def _get_cpic_phenotype(gene: str, diplotype: str) -> str | None:
    _load_cpic()
    for entry in _cpic_diplotypes:
        if entry.get("genesymbol") == gene and entry.get("diplotype") == diplotype:
            return entry.get("description") or entry.get("phenotype")
    return None


def _get_cpic_drug_recs(gene: str, phenotype: str) -> list[dict]:
    _load_cpic()
    results = []
    for rec in _cpic_recs:
        if rec.get("genesymbol") != gene:
            continue
        phenotype_map = rec.get("phenotypes", {})
        if not isinstance(phenotype_map, dict):
            continue
        matched = any(phenotype.lower() in str(v).lower() for v in phenotype_map.values())
        if matched:
            drug_name = rec.get("drug", {}).get("name", "Unknown") if isinstance(rec.get("drug"), dict) else str(rec.get("drug", "Unknown"))
            implications = rec.get("implications", {})
            impl_text = implications.get(phenotype, next(iter(implications.values()), "")) if isinstance(implications, dict) else str(implications)
            results.append({"drug": drug_name, "implication": impl_text, "cpic_level": rec.get("cpiclevel", "")})
    return results


def _get_pharmgkb_flags(rsid: str) -> list[dict]:
    _load_pharmgkb()
    if _pharmgkb is None or _pharmgkb.empty:
        return []
    matches = _pharmgkb[_pharmgkb["Variant/Haplotypes"].str.contains(rsid, na=False)]
    if matches.empty:
        return []
    return matches[["Drug(s)", "Phenotype Category", "Level of Evidence"]].to_dict("records")


def run_pharmacogenomics(snps: pd.DataFrame) -> dict:
    lookup = dict(zip(snps["rsid"].str.lower(), snps["genotype"]))
    results = []

    for gene, snp_map in STAR_ALLELES.items():
        tested_snps = []
        diplotype = None

        for rsid, geno_map in snp_map.items():
            genotype = lookup.get(rsid.lower())
            detected = genotype is not None and genotype != "--"
            tested_snps.append({"rsid": rsid, "genotype": genotype or "not_found", "detected": detected})
            if detected and genotype.upper() in geno_map:
                diplotype = geno_map[genotype.upper()]

        if not diplotype:
            diplotype = "*1/*1"

        # Phenotype: try CPIC dataset, fall back to local map
        phenotype = _get_cpic_phenotype(gene, diplotype) or PHENOTYPE_MAP.get(diplotype, "Normal Metabolizer")

        # Drug flags: hardcoded fallback + CPIC recs
        drug_flags = list(DRUG_FLAGS_FALLBACK.get(gene, {}).get(phenotype, []))
        cpic_recs = _get_cpic_drug_recs(gene, phenotype)
        for rec in cpic_recs:
            if not any(rec["drug"].lower() in f["drug"].lower() for f in drug_flags):
                drug_flags.append({
                    "drug": rec["drug"], "severity": "MODERATE",
                    "action": (rec["implication"][:120] if rec["implication"] else "See CPIC guidelines"),
                    "reason": f"CPIC Level {rec['cpic_level']}" if rec["cpic_level"] else "",
                })

        # PharmGKB annotations
        pharmgkb_notes = []
        for si in tested_snps:
            if si["detected"]:
                pharmgkb_notes.extend(_get_pharmgkb_flags(si["rsid"]))

        results.append({
            "gene": gene, "diplotype": diplotype, "phenotype": phenotype,
            "metabolizer_status": phenotype.lower().replace(" ", "_"),
            "status_label": phenotype,
            "tested_snps": tested_snps, "drug_flags": drug_flags,
            "pharmgkb_annotations": pharmgkb_notes[:5],
            "data_sources": ["CPIC", "PharmGKB"] if pharmgkb_notes else ["CPIC"],
            "disclaimer": "Discuss with your prescriber before making any medication changes.",
        })

    results.append(CYP2D6_WARNING)

    high = sum(1 for r in results for f in r.get("drug_flags", []) if f.get("severity") == "HIGH")
    moderate = sum(1 for r in results for f in r.get("drug_flags", []) if f.get("severity") == "MODERATE")

    return {"genes": results, "summary": {"high_risk_drugs": high, "moderate_risk_drugs": moderate, "genes_tested": len(STAR_ALLELES)}}
