export interface ParseResult {
  session_id: string;
  source: string;
  snp_count: number;
  chromosomes: number;
  ancestry: Record<string, number>;
}

export interface DrugFlag {
  drug: string;
  severity: 'HIGH' | 'MODERATE' | 'LOW';
  action: string;
  reason: string;
}

export interface GeneResult {
  gene: string;
  metabolizer_status: string;
  status_label: string;
  drug_flags: DrugFlag[];
  disclaimer: string;
  status?: string;
  affected_drugs?: string[];
}

export interface AncestryAdjustment {
  primary_ancestry?: string;
  ancestry_percentage?: number;
  population_used?: string;
  confidence?: string;
  note?: string;
}

export interface RiskCondition {
  condition: string;
  label?: string;
  description?: string;
  status: string;
  raw_score?: number;
  percentile?: number;
  risk_tier?: string;
  risk_label?: string;
  snps_matched?: number;
  snps_total?: number;
  coverage_pct?: number;
  ancestry_adjustment?: AncestryAdjustment;
  message?: string;
  disclaimer?: string;
  is_ml_model?: boolean;
  driving_factors?: string[];
}

export interface CarrierResult {
  gene: string;
  condition: string;
  rsid: string;
  genotype: string;
  status: string;
  status_label: string;
  detail: string;
  notes: string;
  disclaimer: string;
}

export interface TraitResult {
  name: string;
  category: string;
  gene: string;
  rsid: string;
  genotype: string;
  status: string;
  label: string;
  detail: string;
}

export interface ReportResult {
  pharmacogenomics: {
    genes: GeneResult[];
    summary: { high_risk_drugs: number; moderate_risk_drugs: number; genes_tested: number };
  };
  disease_risk: {
    conditions: RiskCondition[];
    equity_note: string;
  };
  carrier_status: {
    results: CarrierResult[];
    carriers_found: number;
    conditions_tested: number;
    disclaimer: string;
  };
  nutrition_traits: {
    traits: TraitResult[];
    total_tested: number;
  };
  report_text: {
    full_text: string;
    llm_generated: boolean;
    error?: string;
  };
}
