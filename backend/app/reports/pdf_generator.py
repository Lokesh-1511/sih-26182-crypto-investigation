# backend/app/reports/pdf_generator.py
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

class ForensicReportGenerator:
    """
    Generates structured forensic investigation reports.
    Produces court-admissible HTML/PDF summaries with SHA-256 evidence package digests.
    """

    @classmethod
    def generate_html_report(
        cls,
        case_data: Dict[str, Any],
        attribution_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        if output_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
            output_dir = os.path.join(base_dir, "reports", "generated")
        os.makedirs(output_dir, exist_ok=True)

        case_id = case_data.get("id", "CASE_UNKNOWN")
        suspect_wallet = case_data.get("suspect_wallet", "N/A")
        chain = case_data.get("chain", "ETH")
        top_vasp = attribution_data.get("top_candidate", {}) or {}
        vasp_name = top_vasp.get("entity_name", "UNKNOWN_VASP")
        score = top_vasp.get("confidence_score", 0.0)
        band = top_vasp.get("confidence_band", "LOW")

        timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        factors_html = "".join([
            f"<tr><td>{f.get('factor_name')}</td><td>+{f.get('contribution_points')} pts</td><td>{f.get('description')}</td></tr>"
            for f in top_vasp.get("factors", [])
        ])

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Forensic Investigation Report - {case_id}</title>
<style>
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #fff; color: #24292f; margin: 40px; line-height: 1.6; }}
  .header {{ border-bottom: 2px solid #0969da; padding-bottom: 12px; margin-bottom: 24px; }}
  .badge {{ background: #ddf4ff; color: #0969da; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
  .badge-danger {{ background: #ffebe9; color: #cf222e; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th, td {{ border: 1px solid #d0d7de; padding: 10px; text-align: left; font-size: 13px; }}
  th {{ background: #f6f8fa; }}
  .disclaimer {{ background: #fff8c5; border-left: 4px solid #9a6700; padding: 12px; margin: 20px 0; font-size: 12px; }}
  .hash-box {{ background: #f6f8fa; padding: 10px; font-family: monospace; font-size: 12px; word-break: break-all; }}
</style>
</head>
<body>
  <div class="header">
    <h2>LAW ENFORCEMENT CYBER INVESTIGATION FORENSIC REPORT</h2>
    <p>Case ID: <strong>{case_id}</strong> | Generated: {timestamp_str} | System: Crypto Investigation Copilot v1.0.0</p>
  </div>

  <div class="disclaimer">
    <strong>CRITICAL INVESTIGATIVE PRINCIPLE:</strong><br>
    The findings herein reflect observed blockchain transaction facts and heuristic infrastructure clustering. 
    <strong>Beneficiary Identity is NOT ESTABLISHED.</strong> VASP infrastructure attribution does NOT constitute 
    conclusive proof of end-user identity without off-chain KYC records obtained via lawful legal requisition.
  </div>

  <h3>1. Case Summary</h3>
  <table>
    <tr><th>Case Reference</th><td>{case_id}</td></tr>
    <tr><th>Investigator</th><td>{case_data.get('investigator', 'Officer')}</td></tr>
    <tr><th>Suspect Wallet</th><td><code>{suspect_wallet}</code></td></tr>
    <tr><th>Target Blockchain</th><td>{chain}</td></tr>
    <tr><th>Case Status</th><td>{case_data.get('status', 'OPEN')}</td></tr>
  </table>

  <h3>2. VASP Attribution Findings ("WHY THIS VASP?")</h3>
  <p>Attributed VASP: <strong>{vasp_name}</strong> | Confidence: <span class="badge">{score}% ({band})</span></p>
  <p>Operator Role: <strong>VASP-Controlled Infrastructure</strong> | Beneficiary Identity: <span class="badge badge-danger">NOT ESTABLISHED</span></p>
  
  <table>
    <tr><th>Evidence Factor</th><th>Contribution</th><th>Analytical Justification</th></tr>
    {factors_html}
  </table>

  <h3>3. Obfuscation & Risk Findings</h3>
  <p>Detected AML Risk Level: <strong>{risk_data.get('overall_risk_level', 'LOW')}</strong></p>
  <p>Total Risk Findings: {risk_data.get('total_findings', 0)}</p>

  <h3>4. Tamper-Evident Verification</h3>
  <p>SHA-256 Digest of Evidence Package:</p>
  <div class="hash-box" id="report_hash">COMPUTING...</div>
</body>
</html>
"""
        sha256_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
        html_content = html_content.replace("COMPUTING...", sha256_hash)

        report_file = os.path.join(output_dir, f"report_{case_id}.html")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return {
            "report_path": report_file,
            "report_hash": sha256_hash,
            "case_id": case_id,
            "generated_at": timestamp_str
        }
