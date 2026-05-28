"""PDF export via weasyprint — renders the report as a downloadable health passport."""

import io
import os
import sys
from datetime import datetime

# WeasyPrint needs GLib C libraries — ensure Homebrew lib path is visible on macOS
if sys.platform == "darwin":
    _brew_lib = "/opt/homebrew/lib"
    _env_key = "DYLD_FALLBACK_LIBRARY_PATH"
    _current = os.environ.get(_env_key, "")
    if _brew_lib not in _current:
        os.environ[_env_key] = f"{_brew_lib}:{_current}" if _current else _brew_lib

try:
    from weasyprint import HTML
    WEASYPRINT_OK = True
except (ImportError, OSError) as e:
    WEASYPRINT_OK = False
    print(f"[pdf] weasyprint unavailable: {e} — PDF export will return plain text")


def render_pdf(results: dict, ancestry: dict) -> bytes:
    """Render the full report as a styled PDF. Returns raw PDF bytes."""
    report_text = results.get("report_text", {}).get("full_text", "No report generated.")

    if not WEASYPRINT_OK:
        return _text_fallback(report_text)

    html = _build_html(results, ancestry, report_text)
    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes


def _build_html(results: dict, ancestry: dict, report_text: str) -> str:
    """Build styled HTML for the PDF passport."""
    date = datetime.now().strftime("%B %d, %Y")

    # Ancestry line
    if ancestry:
        ancestry_line = ", ".join(f"{k}: {v}%" for k, v in ancestry.items())
    else:
        ancestry_line = "Not detected"

    # PGx summary
    pgx = results.get("pharmacogenomics", {})
    pgx_summary = pgx.get("summary", {})
    high = pgx_summary.get("high_risk_drugs", 0)
    moderate = pgx_summary.get("moderate_risk_drugs", 0)

    # Drug flags HTML
    drug_rows = ""
    for gene in pgx.get("genes", []):
        for flag in gene.get("drug_flags", []):
            severity_color = {"HIGH": "#e74c3c", "MODERATE": "#f39c12", "LOW": "#27ae60"}.get(flag["severity"], "#888")
            drug_rows += f"""
            <tr>
                <td>{gene['gene']}</td>
                <td>{flag['drug']}</td>
                <td style="color: {severity_color}; font-weight: bold;">{flag['severity']}</td>
                <td>{flag['action']}</td>
            </tr>"""

    # Risk scores HTML
    risk_rows = ""
    for cond in results.get("disease_risk", {}).get("conditions", []):
        if cond.get("status") == "computed":
            tier_color = {"high": "#e74c3c", "moderate": "#f39c12", "average": "#27ae60", "low": "#3498db"}.get(cond["risk_tier"], "#888")
            risk_rows += f"""
            <tr>
                <td>{cond.get('label', cond['condition'])}</td>
                <td>{cond['percentile']}th percentile</td>
                <td style="color: {tier_color}; font-weight: bold;">{cond['risk_label']}</td>
                <td>{cond['ancestry_adjustment']['population_used']}</td>
            </tr>"""

    # Carrier results
    carrier_rows = ""
    for r in results.get("carrier_status", {}).get("results", []):
        status_color = {"carrier": "#f39c12", "two_copies": "#e74c3c", "not_detected": "#27ae60", "not_tested": "#888"}.get(r["status"], "#888")
        carrier_rows += f"""
        <tr>
            <td>{r['condition']}</td>
            <td>{r['gene']}</td>
            <td style="color: {status_color}; font-weight: bold;">{r['status_label']}</td>
        </tr>"""

    # Traits
    trait_rows = ""
    for t in results.get("nutrition_traits", {}).get("traits", []):
        if t.get("status") != "not_tested":
            trait_rows += f"""
            <tr>
                <td>{t['name']}</td>
                <td>{t['gene']}</td>
                <td>{t.get('label', 'Unknown')}</td>
            </tr>"""

    # Convert markdown report text to basic HTML paragraphs
    report_html = report_text.replace("\n\n", "</p><p>").replace("\n", "<br>")
    report_html = f"<p>{report_html}</p>"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ margin: 1.5cm; size: A4; }}
    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #2c3e50; line-height: 1.6; font-size: 11px; }}
    .header {{ text-align: center; border-bottom: 3px solid #8e44ad; padding-bottom: 16px; margin-bottom: 24px; }}
    .header h1 {{ font-size: 28px; color: #8e44ad; margin: 0; letter-spacing: 2px; }}
    .header .subtitle {{ color: #7f8c8d; font-size: 12px; margin-top: 4px; }}
    .meta {{ display: flex; justify-content: space-between; margin-bottom: 20px; font-size: 10px; color: #7f8c8d; }}
    h2 {{ color: #8e44ad; border-bottom: 1px solid #ddd; padding-bottom: 4px; font-size: 16px; margin-top: 24px; }}
    h3 {{ color: #2c3e50; font-size: 13px; margin-top: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 8px 0 16px 0; font-size: 10px; }}
    th {{ background: #f8f7f3; text-align: left; padding: 6px 8px; border-bottom: 2px solid #ddd; }}
    td {{ padding: 5px 8px; border-bottom: 1px solid #eee; }}
    .badge {{ display: inline-block; background: #f0ebf8; color: #8e44ad; padding: 2px 8px; border-radius: 4px; font-size: 9px; font-weight: bold; }}
    .disclaimer {{ background: #fef9e7; border-left: 4px solid #f39c12; padding: 8px 12px; margin: 16px 0; font-size: 9px; color: #7f6c3e; }}
    .report-text {{ font-size: 11px; line-height: 1.7; }}
    .footer {{ text-align: center; margin-top: 32px; padding-top: 12px; border-top: 1px solid #ddd; font-size: 9px; color: #bbb; }}
</style>
</head>
<body>
    <div class="header">
        <h1>G-Nome</h1>
        <div class="subtitle">Genomic Health Passport</div>
    </div>

    <div class="meta">
        <span>Generated: {date}</span>
        <span>Ancestry: {ancestry_line}</span>
    </div>

    <h2>Drug Safety (Pharmacogenomics)</h2>
    <p><span class="badge">{high} HIGH RISK</span> &nbsp; <span class="badge">{moderate} MODERATE RISK</span></p>
    <table>
        <tr><th>Gene</th><th>Drug</th><th>Risk</th><th>Action</th></tr>
        {drug_rows}
    </table>
    <div class="disclaimer">Discuss with your prescriber before making any medication changes.</div>

    <h2>Disease Risk Scores</h2>
    <table>
        <tr><th>Condition</th><th>Percentile</th><th>Risk Level</th><th>Ancestry Used</th></tr>
        {risk_rows}
    </table>
    <div class="disclaimer">This is not a diagnosis. Risk scores indicate likelihood, not certainty.</div>

    <h2>Carrier Status</h2>
    <table>
        <tr><th>Condition</th><th>Gene</th><th>Result</th></tr>
        {carrier_rows}
    </table>
    <div class="disclaimer">We did not detect the specific variants we tested for. This does not mean you are not a carrier.</div>

    <h2>Nutrition &amp; Traits</h2>
    <table>
        <tr><th>Trait</th><th>Gene</th><th>Result</th></tr>
        {trait_rows}
    </table>

    <h2>Full Report</h2>
    <div class="report-text">{report_html}</div>

    <div class="footer">
        G-Nome Genomic Health Passport &mdash; For informational purposes only, not medical advice.
    </div>
</body>
</html>"""


def _text_fallback(report_text: str) -> bytes:
    """Simple text-to-PDF fallback if weasyprint is unavailable."""
    content = f"G-Nome Genomic Health Passport\n{'=' * 40}\n\n{report_text}"
    return content.encode("utf-8")
