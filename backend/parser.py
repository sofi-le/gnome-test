"""DNA file parser — supports 23andMe (.txt) and AncestryDNA (.csv) via snps library."""

import io
import tempfile
import os

import pandas as pd
from snps import SNPs


def parse_dna_file(raw_bytes: bytes, filename: str) -> dict:
    """Parse a raw DNA file into a standardized DataFrame.

    Returns dict with keys: snps (DataFrame), source (str), ancestry (dict).
    """
    # snps library needs a file path, so write to a temp file
    suffix = ".txt" if filename.endswith(".txt") else ".csv"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(raw_bytes)
        tmp_path = tmp.name

    try:
        s = SNPs(tmp_path)
    finally:
        os.unlink(tmp_path)

    if s.snps is None or s.snps.empty:
        raise ValueError("No SNPs found in file — check format")

    df = s.snps.reset_index()
    # Normalize column names
    col_map = {}
    for col in df.columns:
        low = col.lower()
        if low in ("rsid", "snp", "name"):
            col_map[col] = "rsid"
        elif low in ("chromosome", "chrom", "chr"):
            col_map[col] = "chrom"
        elif low in ("position", "pos"):
            col_map[col] = "pos"
        elif low in ("genotype", "alleles", "result"):
            col_map[col] = "genotype"

    df = df.rename(columns=col_map)

    required = {"rsid", "chrom", "genotype"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"Missing columns after parsing: {required - set(df.columns)}")

    # Drop rows with missing genotype
    df = df.dropna(subset=["genotype"])
    df = df[df["genotype"] != "--"]

    # Determine source
    source = s.source or ("23andMe" if filename.endswith(".txt") else "AncestryDNA")

    # Try to extract ancestry from 23andMe header comments
    ancestry = _extract_ancestry(raw_bytes)
    if not ancestry:
        ancestry = _infer_ancestry_from_snps(df)
        
    sex = _infer_sex(df)

    return {
        "snps": df,
        "source": source,
        "ancestry": ancestry,
        "sex": sex,
    }


def _extract_ancestry(raw_bytes: bytes) -> dict:
    """Best-effort extraction of ancestry composition from 23andMe file header."""
    ancestry = {}
    try:
        text = raw_bytes.decode("utf-8", errors="ignore")
        for line in text.split("\n")[:100]:
            if not line.startswith("#"):
                break
            low = line.lower()
            if "european" in low:
                ancestry["European"] = _parse_pct(line)
            elif "east asian" in low:
                ancestry["East Asian"] = _parse_pct(line)
            elif "african" in low:
                ancestry["African"] = _parse_pct(line)
            elif "south asian" in low:
                ancestry["South Asian"] = _parse_pct(line)
            elif "native american" in low or "indigenous" in low:
                ancestry["Native American"] = _parse_pct(line)
    except Exception:
        pass
    return ancestry


def _parse_pct(line: str) -> float:
    """Try to pull a percentage from a header line like '# European: 78.2%'."""
    import re
    match = re.search(r"([\d.]+)\s*%", line)
    if match:
        return float(match.group(1))
    return 0.0


def _infer_sex(snps: pd.DataFrame) -> str:
    """Infer sex by checking for Y chromosome SNPs."""
    y_snps = snps[snps["chrom"].astype(str).str.upper() == "Y"]
    valid_y = y_snps[y_snps["genotype"] != "--"]
    # Usually a male will have hundreds of valid Y SNPs. A few could be false positives.
    if len(valid_y) > 20:
        return "Male"
    return "Female"


def _infer_ancestry_from_snps(snps: pd.DataFrame) -> dict:
    """Fallback ancestry inference using Ancestry Informative Markers (AIMs)."""
    lookup = dict(zip(snps["rsid"].str.lower(), snps["genotype"]))
    scores = {"European": 0, "East Asian": 0, "African": 0, "South Asian": 0}
    
    # 1. European marker: rs1426654 (SLC24A5) A allele
    slc = lookup.get("rs1426654", "").upper()
    if slc:
        scores["European"] += slc.count("A") * 40
        scores["South Asian"] += slc.count("A") * 20
        scores["African"] += slc.count("G") * 20
        scores["East Asian"] += slc.count("G") * 20
        
    # 2. East Asian marker: rs3827760 (EDAR) G allele
    edar = lookup.get("rs3827760", "").upper()
    if edar:
        scores["East Asian"] += edar.count("G") * 50
        
    # 3. African marker: rs2814778 (DARC) C allele
    darc = lookup.get("rs2814778", "").upper()
    if darc:
        scores["African"] += darc.count("C") * 50
        
    total = sum(scores.values())
    if total == 0:
        return {}
    
    return {k: round((v / total) * 100, 1) for k, v in scores.items() if v > 0}
