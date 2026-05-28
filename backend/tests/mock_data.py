"""
G-Nome Test Fixtures — Mock SNP Data
=====================================
Shared mock SNP dictionaries for testing the risk engine across
different ancestry groups. Genotypes are plausible but synthetic.
"""

from ml.snp_config import ALL_SNPS, ANCESTRY_MAP

# ---------------------------------------------------------------------------
# Mock SNP dictionaries simulating parsed 23andMe output
# ---------------------------------------------------------------------------

MOCK_SNP_DICT_EUR = {
    # CAD SNPs
    "rs1333049": "CC",
    "rs4977574": "AG",
    "rs10757278": "AG",
    "rs6725887": "CC",
    "rs9818870": "CT",
    # T2D SNPs
    "rs7903146": "CT",
    "rs1801282": "CC",
    "rs5219": "CT",
    "rs13266634": "CC",
    "rs10811661": "TT",
    # Alzheimer SNPs
    "rs429358": "CT",   # Heterozygous for APOE ε4
    "rs7412": "CC",
    "rs11136000": "CT",
    "rs3851179": "CT",
    "rs744373": "CC",
}

MOCK_SNP_DICT_AFR = {
    # CAD SNPs
    "rs1333049": "CG",
    "rs4977574": "GG",
    "rs10757278": "GG",
    "rs6725887": "CT",
    "rs9818870": "CC",
    # T2D SNPs
    "rs7903146": "TT",   # Homozygous risk allele
    "rs1801282": "CG",
    "rs5219": "TT",
    "rs13266634": "CT",
    "rs10811661": "CT",
    # Alzheimer SNPs
    "rs429358": "CC",    # No APOE ε4
    "rs7412": "CT",
    "rs11136000": "TT",
    "rs3851179": "CC",
    "rs744373": "CT",
}

MOCK_SNP_DICT_EAS = {
    # CAD SNPs
    "rs1333049": "CC",
    "rs4977574": "AA",
    "rs10757278": "AA",
    "rs6725887": "CC",
    "rs9818870": "CC",
    # T2D SNPs
    "rs7903146": "CC",
    "rs1801282": "CC",
    "rs5219": "CC",
    "rs13266634": "CC",
    "rs10811661": "CC",
    # Alzheimer SNPs
    "rs429358": "CC",
    "rs7412": "CC",
    "rs11136000": "CC",
    "rs3851179": "CC",
    "rs744373": "CC",
}

MOCK_SNP_DICT_CSA = {
    # CAD SNPs
    "rs1333049": "CG",
    "rs4977574": "AG",
    "rs10757278": "AG",
    "rs6725887": "CC",
    "rs9818870": "CT",
    # T2D SNPs
    "rs7903146": "CT",
    "rs1801282": "CC",
    "rs5219": "CT",
    "rs13266634": "CT",
    "rs10811661": "CT",
    # Alzheimer SNPs
    "rs429358": "CT",
    "rs7412": "CC",
    "rs11136000": "CT",
    "rs3851179": "CT",
    "rs744373": "CT",
}

MOCK_SNP_DICT_MID = {
    # CAD SNPs
    "rs1333049": "GG",
    "rs4977574": "AG",
    "rs10757278": "GG",
    "rs6725887": "CT",
    "rs9818870": "CC",
    # T2D SNPs
    "rs7903146": "CT",
    "rs1801282": "CC",
    "rs5219": "CC",
    "rs13266634": "CC",
    "rs10811661": "CT",
    # Alzheimer SNPs
    "rs429358": "CC",
    "rs7412": "CC",
    "rs11136000": "CT",
    "rs3851179": "CC",
    "rs744373": "CC",
}

MOCK_SNP_DICT_AMR = {
    # CAD SNPs
    "rs1333049": "CG",
    "rs4977574": "GG",
    "rs10757278": "AG",
    "rs6725887": "CC",
    "rs9818870": "CC",
    # T2D SNPs
    "rs7903146": "TT",
    "rs1801282": "CG",
    "rs5219": "CT",
    "rs13266634": "CT",
    "rs10811661": "CC",
    # Alzheimer SNPs
    "rs429358": "CC",
    "rs7412": "CT",
    "rs11136000": "CC",
    "rs3851179": "CT",
    "rs744373": "CT",
}

# Mapping of ancestry codes to their mock SNP dicts
MOCK_DATA_BY_ANCESTRY = {
    0: ("EUR", MOCK_SNP_DICT_EUR),
    1: ("AFR", MOCK_SNP_DICT_AFR),
    2: ("CSA", MOCK_SNP_DICT_CSA),
    3: ("EAS", MOCK_SNP_DICT_EAS),
    4: ("MID", MOCK_SNP_DICT_MID),
    5: ("AMR", MOCK_SNP_DICT_AMR),
}

# Expected response structure keys for validation
EXPECTED_RESPONSE_KEYS = {"results", "ancestry_code", "ancestry_label",
                           "ancestry_display", "confidence_score", "inference_time_ms"}
EXPECTED_RESULT_KEYS = {"disease", "risk_score", "top_driving_snps"}

# Mock PGx metabolizer flags for prompt testing
MOCK_PGX_FLAGS_EUR = {
    "CYP2D6": "Normal Metabolizer",
    "CYP2C19": "Normal Metabolizer",
    "CYP3A5": "Non-expresser",
}

MOCK_PGX_FLAGS_AFR = {
    "CYP2D6": "Ultrarapid Metabolizer",
    "CYP2C19": "Normal Metabolizer",
    "CYP3A5": "Expresser",
}

MOCK_PGX_FLAGS_EAS = {
    "CYP2D6": "Intermediate Metabolizer",
    "CYP2C19": "Poor Metabolizer",
    "CYP3A5": "Non-expresser",
}

MOCK_PGX_FLAGS_CSA = {
    "CYP2D6": "Intermediate Metabolizer",
    "CYP2C19": "Normal Metabolizer",
    "CYP3A5": "Non-expresser",
}
