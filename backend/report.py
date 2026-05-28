"""LLM report generation via Nebius API (OpenAI-compatible)."""

import json
import os

from openai import AsyncOpenAI

_client = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    api_key = os.environ.get("NEBIUS_API_KEY", "")
    if not api_key:
        return None
    if _client is None:
        _client = AsyncOpenAI(
            api_key=api_key,
            base_url=os.environ.get("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1/"),
        )
    return _client


SYSTEM_PROMPT = """You are G-Nome, a genomic health report writer. You produce clear, accurate,
plain-language health guidance based on genetic analysis results.

Rules:
- Write for a general audience — avoid jargon, explain terms when first used
- Be factual and measured — never alarmist, never dismissive
- Always acknowledge limitations of SNP-array-based testing
- Never say "you will get X disease" — always frame as risk/likelihood
- End every section with a practical takeaway
- Keep each section to 2-3 short paragraphs

IMPORTANT: Always include this footer on every report:
"This is health guidance for informational purposes only, not medical advice.
Discuss any findings with your healthcare provider before making health decisions."
"""


def _build_user_prompt(modules: dict, ancestry: dict) -> str:
    """Build the user prompt from structured module results."""
    sections = []

    # Ancestry context
    if ancestry:
        ancestry_str = ", ".join(f"{k}: {v}%" for k, v in ancestry.items())
        sections.append(f"**Ancestry composition:** {ancestry_str}")
    else:
        sections.append("**Ancestry:** Not detected from file. Using general population data.")

    sections.append(f"\n**Analysis data (JSON):**\n```json\n{json.dumps(modules, indent=2, default=str)}\n```")

    sections.append("""
Write a personalized health passport report with these sections:
1. **Pharmacogenomics Summary** — which drugs to watch out for and why
2. **Disease Risk Overview** — what the risk scores mean, emphasizing the ancestry adjustment
3. **Carrier Status** — what was found (or not found) and what it means
4. **Nutrition & Traits** — actionable dietary and lifestyle insights
5. **Equity Note** — explain how ancestry affects genetic risk scoring and what G-Nome does differently

Format each section with a clear heading. Keep the total report under 800 words.
""")

    return "\n".join(sections)


async def generate_report(modules: dict, ancestry: dict) -> dict:
    """Call Nebius Llama 70B to generate plain-language report sections."""
    client = _get_client()

    if client is None:
        return {
            "full_text": _fallback_report(modules, ancestry),
            "llm_generated": False,
            "error": "NEBIUS_API_KEY not set — using fallback report",
        }

    model = os.environ.get("NEBIUS_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

    user_prompt = _build_user_prompt(modules, ancestry)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        report_text = response.choices[0].message.content
    except Exception as e:
        # Fallback — return structured summary without LLM
        report_text = _fallback_report(modules, ancestry)
        return {
            "full_text": report_text,
            "llm_generated": False,
            "error": str(e),
        }

    return {
        "full_text": report_text,
        "llm_generated": True,
    }


def _fallback_report(modules: dict, ancestry: dict) -> str:
    """Generate a basic report without LLM if the API call fails."""
    lines = ["# G-Nome Genomic Health Passport", ""]

    # PGx
    pgx = modules.get("pharmacogenomics", {})
    summary = pgx.get("summary", {})
    lines.append("## Pharmacogenomics")
    lines.append(f"- High-risk drug interactions: {summary.get('high_risk_drugs', 0)}")
    lines.append(f"- Moderate-risk interactions: {summary.get('moderate_risk_drugs', 0)}")
    lines.append(f"- Genes tested: {summary.get('genes_tested', 0)}")
    lines.append("")

    # Disease risk
    risk = modules.get("disease_risk", {})
    lines.append("## Disease Risk Scores")
    for cond in risk.get("conditions", []):
        label = cond.get("label", cond.get("condition", "Unknown"))
        if cond.get("status") == "computed":
            lines.append(f"- {label}: {cond['risk_label']} (percentile: {cond['percentile']})")
        else:
            lines.append(f"- {label}: {cond.get('message', 'Data not available')}")
    lines.append("")

    # Carrier
    carrier = modules.get("carrier_status", {})
    lines.append("## Carrier Status")
    lines.append(f"- Carriers detected: {carrier.get('carriers_found', 0)} of {carrier.get('conditions_tested', 0)} conditions tested")
    lines.append("")

    # Traits
    traits = modules.get("nutrition_traits", {})
    lines.append("## Nutrition & Traits")
    for t in traits.get("traits", []):
        if t.get("status") != "not_tested":
            lines.append(f"- {t['name']}: {t.get('label', 'Unknown')}")
    lines.append("")

    lines.append("---")
    lines.append("*This is health guidance for informational purposes only, not medical advice.*")

    return "\n".join(lines)
