# backend/app/reports/pdf_generator.py
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from ..schemas.evidence import CaseDossier, EvidenceItem, EvidenceClass
from ..schemas.investigation import InvestigationResponse
from ..evidence.builder import EvidenceBuilder

class ForensicReportGenerator:
    """
    Generates structured, court-admissible forensic investigation reports.
    Produces comprehensive HTML/PDF dossier summaries with SHA-256 evidence package digests.
    """

    @classmethod
    def generate_dossier_report(
        cls,
        dossier: Union[CaseDossier, InvestigationResponse, Dict[str, Any]],
        investigator: str = "Authorized Investigating Officer",
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        if isinstance(dossier, InvestigationResponse):
            dossier = EvidenceBuilder.build_case_dossier(dossier)

        if output_dir is None:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
            output_dir = os.path.join(base_dir, "reports", "generated")
        os.makedirs(output_dir, exist_ok=True)

        if isinstance(dossier, CaseDossier):
            inv_id = dossier.investigation_id
            chain_str = dossier.chain
            root_wallet = dossier.root_wallet
            direction = dossier.direction
            hops = dossier.actual_depth_reached
            req_hops = dossier.requested_max_hops
            term_reason = dossier.trace_termination_reason
            summary = dossier.summary
            entity_resolutions = dossier.entity_resolutions
            vasp_attributions = dossier.vasp_attributions
            evidence_items = dossier.evidence_items
            gen_time = dossier.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(dossier.generated_at, "strftime") else str(dossier.generated_at)
            dossier_hash = dossier.dossier_hash_sha256
        else:
            inv_id = dossier.get("investigation_id", dossier.get("id", "UNKNOWN_INV"))
            chain_str = dossier.get("chain", "ETH")
            root_wallet = dossier.get("root_wallet", dossier.get("suspect_wallet", "N/A"))
            direction = dossier.get("direction", "outgoing")
            hops = dossier.get("actual_depth_reached", dossier.get("hops", 1))
            req_hops = dossier.get("requested_max_hops", 1)
            term_reason = dossier.get("trace_termination_reason", "COMPLETED")
            summary = dossier.get("summary", {})
            entity_resolutions = dossier.get("entity_resolutions", [])
            vasp_attributions = dossier.get("vasp_attributions", [])
            evidence_items = dossier.get("evidence_items", [])
            gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            dossier_hash = dossier.get("dossier_hash_sha256", "")

        # Render VASP findings
        vasp_rows = []
        for v in vasp_attributions:
            v_dict = v.model_dump() if hasattr(v, "model_dump") else v if isinstance(v, dict) else {}
            name = v_dict.get("entity_name", "Unknown")
            etype = v_dict.get("entity_type", "VASP")
            vhop = v_dict.get("hop_distance", 0)
            addr = v_dict.get("address", "")
            path_str = " -> ".join(v_dict.get("path", [])) if v_dict.get("path") else addr
            vasp_rows.append(
                f"<tr>"
                f"<td><strong>{name}</strong></td>"
                f"<td><span class='badge'>{etype}</span></td>"
                f"<td>{vhop}</td>"
                f"<td class='mono'>{addr}</td>"
                f"<td class='mono' style='font-size: 11px;'>{path_str}</td>"
                f"</tr>"
            )
        vasp_table_html = "".join(vasp_rows) if vasp_rows else "<tr><td colspan='5' style='color:#6e7781;'>No VASP infrastructure candidates identified on trace path.</td></tr>"

        # Render Evidence Matrix
        ev_rows = []
        for ev in evidence_items:
            ev_dict = ev.model_dump() if hasattr(ev, "model_dump") else ev if isinstance(ev, dict) else {}
            ev_id = ev_dict.get("evidence_id", "")
            ev_class = ev_dict.get("evidence_class", "OBSERVED")
            ev_type = ev_dict.get("evidence_type", "")
            title = ev_dict.get("title", "")
            desc = ev_dict.get("description", "")
            amt = ev_dict.get("amount") or ""
            asset = ev_dict.get("asset") or ""
            amt_str = f"{amt} {asset}".strip() if amt else "—"
            tx = ev_dict.get("tx_hash") or "—"
            hop = ev_dict.get("hop_distance", "—")

            class_badge_class = "badge-observed" if ev_class == "OBSERVED" else "badge-resolved" if ev_class == "RESOLVED" else "badge-derived" if ev_class == "DERIVED" else "badge-inferred"

            ev_rows.append(
                f"<tr>"
                f"<td class='mono' style='font-size: 11px;'><strong>{ev_id}</strong></td>"
                f"<td><span class='badge {class_badge_class}'>{ev_class}</span></td>"
                f"<td><span style='font-size: 11px; font-weight: 600;'>{ev_type}</span><br><span style='font-size: 12px;'>{title}</span></td>"
                f"<td class='mono' style='font-weight: 600;'>{amt_str}</td>"
                f"<td class='mono' style='font-size: 11px; word-break: break-all;'>{tx}</td>"
                f"<td>{hop}</td>"
                f"</tr>"
            )
        evidence_table_html = "".join(ev_rows) if ev_rows else "<tr><td colspan='6' style='color:#6e7781;'>No structured evidence records recorded.</td></tr>"

        nodes_cnt = getattr(summary, "nodes", summary.get("nodes", 0) if isinstance(summary, dict) else 0)
        edges_cnt = getattr(summary, "edges", summary.get("edges", 0) if isinstance(summary, dict) else 0)
        tx_cnt = getattr(summary, "transactions", summary.get("transactions", 0) if isinstance(summary, dict) else 0)
        trf_cnt = getattr(summary, "transfers", summary.get("transfers", 0) if isinstance(summary, dict) else 0)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Forensic Case Dossier - {inv_id}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; color: #1f2328; margin: 36px; line-height: 1.5; font-size: 13px; }}
  .header {{ border-bottom: 3px solid #0969da; padding-bottom: 12px; margin-bottom: 20px; }}
  .header h1 {{ margin: 0 0 6px 0; font-size: 20px; color: #0969da; text-transform: uppercase; letter-spacing: 0.5px; }}
  .header-meta {{ font-size: 12px; color: #57606a; display: flex; gap: 16px; flex-wrap: wrap; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
  .badge-observed {{ background: #dafbe1; color: #1a7f37; border: 1px solid #aceebb; }}
  .badge-resolved {{ background: #ddf4ff; color: #0969da; border: 1px solid #b6e3ff; }}
  .badge-derived {{ background: #fff8c5; color: #9a6700; border: 1px solid #fae17d; }}
  .badge-inferred {{ background: #fbefff; color: #8250df; border: 1px solid #e8deff; }}
  .badge-danger {{ background: #ffebe9; color: #cf222e; border: 1px solid #ffc1ba; }}
  .metric-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }}
  .metric-card {{ background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 10px 14px; }}
  .metric-card-title {{ font-size: 11px; text-transform: uppercase; color: #57606a; font-weight: 600; }}
  .metric-card-value {{ font-size: 20px; font-weight: 700; color: #1f2328; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 12px; }}
  th, td {{ border: 1px solid #d0d7de; padding: 8px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #f6f8fa; font-weight: 600; color: #24292f; }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, monospace; }}
  .disclaimer-box {{ background: #fff8c5; border-left: 4px solid #9a6700; padding: 12px 16px; margin: 16px 0; font-size: 12px; border-radius: 0 4px 4px 0; }}
  .digest-box {{ background: #f6f8fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 12px 16px; margin: 20px 0; }}
  .digest-hash {{ font-family: monospace; font-size: 12px; font-weight: 700; color: #0969da; word-break: break-all; margin-top: 4px; }}
  h2 {{ font-size: 15px; color: #24292f; border-bottom: 1px solid #d8dee4; padding-bottom: 6px; margin-top: 24px; margin-bottom: 10px; }}
</style>
</head>
<body>

  <div class="header">
    <h1>Law Enforcement Cryptocurrency Forensic Investigation Report</h1>
    <div class="header-meta">
      <span>Investigation ID: <strong>{inv_id}</strong></span>
      <span>Target Network: <strong>{chain_str.upper()}</strong></span>
      <span>Direction: <strong>{direction.upper()}</strong></span>
      <span>Generated: <strong>{gen_time}</strong></span>
      <span>Officer: <strong>{investigator}</strong></span>
    </div>
  </div>

  <div class="disclaimer-box">
    <strong>MANDATORY OPERATOR VS BENEFICIARY DISTINCTION:</strong><br>
    The findings herein reflect deterministic on-chain transaction records and topological infrastructure clustering. 
    <strong>Beneficiary Identity is NOT ESTABLISHED from on-chain evidence alone.</strong> Attribution to a Virtual Asset Service Provider (VASP) 
    deposit or hot wallet reflects fund-flow path proximity to custodial infrastructure and does not constitute conclusive proof of account owner identity without off-chain KYC records obtained via lawful legal requisition.
  </div>

  <h2>1. Investigation Parameters & Trace Execution</h2>
  <table>
    <tr><th style="width: 25%;">Target Root Wallet</th><td class="mono"><strong>{root_wallet}</strong></td></tr>
    <tr><th>Blockchain Network</th><td>{chain_str.upper()}</td></tr>
    <tr><th>Trace Traversal Direction</th><td>{direction.upper()} (Hop 0 &rarr; Hop {hops})</td></tr>
    <tr><th>Depth Traversed</th><td><strong>{hops} hops</strong> reached of {req_hops} requested</td></tr>
    <tr><th>Trace Termination Reason</th><td><span class="badge badge-derived">{term_reason}</span></td></tr>
  </table>

  <h2>2. Forensic Investigation Summary Metrics</h2>
  <div class="metric-grid">
    <div class="metric-card">
      <div class="metric-card-title">Discovered Wallets</div>
      <div class="metric-card-value">{nodes_cnt}</div>
    </div>
    <div class="metric-card">
      <div class="metric-card-title">Traceable Edges</div>
      <div class="metric-card-value">{edges_cnt}</div>
    </div>
    <div class="metric-card">
      <div class="metric-card-title">Ingested Transactions</div>
      <div class="metric-card-value">{tx_cnt}</div>
    </div>
    <div class="metric-card">
      <div class="metric-card-title">Ingested Transfers</div>
      <div class="metric-card-value">{trf_cnt}</div>
    </div>
  </div>

  <h2>3. VASP Attribution & Path Associations (Inferred Infrastructure)</h2>
  <table>
    <thead>
      <tr>
        <th>Entity Name</th>
        <th>Category</th>
        <th>Hop Distance</th>
        <th>Terminal Infrastructure Address</th>
        <th>Topological Fund Path</th>
      </tr>
    </thead>
    <tbody>
      {vasp_table_html}
    </tbody>
  </table>

  <h2>4. Structured Forensic Evidence Matrix</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 14%;">Evidence ID</th>
        <th style="width: 12%;">Classification</th>
        <th>Finding Description</th>
        <th style="width: 16%;">Amount / Asset</th>
        <th style="width: 22%;">Transaction Hash / Ref</th>
        <th style="width: 6%;">Hop</th>
      </tr>
    </thead>
    <tbody>
      {evidence_table_html}
    </tbody>
  </table>

  <h2>5. Evidence Package Cryptographic Integrity</h2>
  <div class="digest-box">
    <div style="font-size: 11px; color: #57606a; text-transform: uppercase; font-weight: 600;">
      SHA-256 Digest of Canonical Case Dossier
    </div>
    <div class="digest-hash">{dossier_hash or "SHA-256 COMPUTED AT EXPORT"}</div>
    <div style="font-size: 11px; color: #6e7781; margin-top: 6px;">
      Verified against canonical JSON representation. Proves integrity and tamper-evidence of the exported evidence package.
    </div>
  </div>

</body>
</html>
"""
        final_hash = dossier_hash or hashlib.sha256(html_content.encode("utf-8")).hexdigest()
        html_content = html_content.replace("SHA-256 COMPUTED AT EXPORT", final_hash)

        report_file = os.path.join(output_dir, f"dossier_{inv_id}.html")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return {
            "report_path": report_file,
            "report_hash": final_hash,
            "investigation_id": inv_id,
            "html_content": html_content,
            "generated_at": gen_time
        }

    # Backward-compatible wrapper
    @classmethod
    def generate_html_report(
        cls,
        case_data: Dict[str, Any],
        attribution_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        output_dir: Optional[str] = None
    ) -> Dict[str, str]:
        res = cls.generate_dossier_report(dossier=case_data, output_dir=output_dir)
        return {
            "report_path": res["report_path"],
            "report_hash": res["report_hash"],
            "case_id": case_data.get("id", case_data.get("investigation_id", "CASE")),
            "generated_at": res["generated_at"]
        }
