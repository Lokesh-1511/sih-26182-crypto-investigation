# backend/app/reports/action_packet.py
import hashlib
from datetime import datetime, timezone
from typing import Optional, Union, List
from ..schemas.snapshot import LawfulActionPacket
from ..schemas.attribution import VASPAttributionCandidate
from ..schemas.investigation import InvestigationResponse
from ..schemas.evidence import CaseDossier
from ..intelligence.models import VaspAttribution

class ActionPacketGenerator:
    """
    Drafts review-ready Lawful Action Packets (Section 91 CrPC / MLAT / FIU requests)
    for authorized law enforcement officers.
    NEVER automatically executes or sends requests.
    """

    @classmethod
    def generate_from_investigation(
        cls,
        investigation: Union[InvestigationResponse, CaseDossier],
        investigator: str = "Authorized Investigating Officer",
        target_vasp_id: Optional[str] = None
    ) -> LawfulActionPacket:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        inv_id = investigation.investigation_id
        suspect_wallet = investigation.root_address if hasattr(investigation, "root_address") else getattr(investigation, "root_wallet", "N/A")
        chain_val = investigation.chain.value if hasattr(investigation.chain, "value") else str(investigation.chain)

        vasp_list: List[VaspAttribution] = getattr(investigation, "vasp_attributions", []) or []
        target_vasp = None
        if target_vasp_id and vasp_list:
            for v in vasp_list:
                if v.entity_id == target_vasp_id:
                    target_vasp = v
                    break
        if not target_vasp and vasp_list:
            target_vasp = vasp_list[0]

        vasp_name = target_vasp.entity_name if target_vasp else "Designated Custodian / VASP"
        deposit_addr = target_vasp.address if target_vasp else "Identified Endpoint"
        hop_distance = target_vasp.hop_distance if target_vasp else 1
        conf_str = f"Hop Proximity: {hop_distance} hops"

        relevant_txs = []
        if hasattr(investigation, "graph") and investigation.graph and investigation.graph.edges:
            relevant_txs = [e.tx_hash for e in investigation.graph.edges if e.tx_hash][:5]
        elif hasattr(investigation, "evidence_items") and investigation.evidence_items:
            for ev in investigation.evidence_items:
                ev_tx = getattr(ev, "tx_hash", None) if hasattr(ev, "tx_hash") else ev.get("tx_hash") if isinstance(ev, dict) else None
                if ev_tx and ev_tx not in relevant_txs:
                    relevant_txs.append(ev_tx)
                if len(relevant_txs) >= 5:
                    break

        tx_list_str = ", ".join(relevant_txs) if relevant_txs else "Underlying Investigation Transfers"

        preservation_draft = f"""
OFFICIAL PRESERVATION NOTICE UNDER SECTION 91 CrPC / STATUTORY PRESERVATION (DRAFT FOR OFFICER REVIEW)
------------------------------------------------------------------------------------------------------
To: Legal Compliance Department, {vasp_name}
From: Cyber Crime Investigation Unit
Date of Notice: {now_str}
Investigation Reference: {inv_id}
Investigating Officer: {investigator}

SUBJECT: URGENT PRESERVATION OF TRANSACTION LOGS & KYC RECORDS

1. This agency is investigating cryptocurrency fund flows concerning suspect activity.
2. Forensic blockchain intelligence indicates that funds originating from Target Suspect Wallet:
   {suspect_wallet} ({chain_val.upper()})
   were traced to custodial deposit infrastructure associated with {vasp_name}:
   Deposit / Infrastructure Address: {deposit_addr}
   Topological Trace Distance: {hop_distance} hops
   Attribution Confidence: {conf_str}

3. YOU ARE HEREBY REQUESTED TO IMMEDIATELY PRESERVE FOR 90 DAYS:
   a. All user account registration details, KYC identity documents, email addresses, phone numbers, and login IP connection logs.
   b. All on-chain deposit, internal off-chain ledger transfers, and withdrawal logs linked to the above address.
   c. Linked fiat banking rails, withdrawal accounts, and payment beneficiary records.

NOTICE: This document is an automated intelligence draft generated for human review.
Official issuance requires authorization and official signature by the Investigating Officer.
"""

        disclosure_draft = f"""
FORMAL DISCLOSURE REQUISITION (SECTION 91 CrPC / STATUTORY NOTICE DRAFT)
------------------------------------------------------------------------
To: Designated Compliance / Grievance Officer, {vasp_name}
Case / Investigation File: {inv_id}

Requisition for certified evidentiary records concerning transaction hashes:
{tx_list_str}

Please supply certified copies of the identity records and transaction rails for the account
associated with deposit infrastructure: {deposit_addr} within 72 hours of official service.
"""

        disclaimer = (
            "STATUTORY LEGAL NOTICE & DISCLAIMER:\n"
            "This Lawful Action Packet is an automated intelligence draft prepared solely to assist "
            "authorized investigating officers. It does NOT constitute an automated legal order. "
            "Beneficiary identity is NOT established from on-chain clustering alone. "
            "Any submission to exchanges must be formally reviewed and signed by an authorized officer."
        )

        packet_body = preservation_draft + disclosure_draft + disclaimer
        integrity_hash = hashlib.sha256(packet_body.encode("utf-8")).hexdigest()

        return LawfulActionPacket(
            packet_id=f"act_{inv_id}_{int(datetime.now(timezone.utc).timestamp())}",
            case_id=inv_id,
            suspect_wallet=suspect_wallet,
            chain=chain_val,
            attributed_vasp=vasp_name,
            attribution_confidence=conf_str,
            operator_role="VASP-Controlled Infrastructure",
            beneficiary_identity="NOT ESTABLISHED (Awaiting Off-Chain KYC Records)",
            integrity_hash_sha256=integrity_hash,
            preservation_notice_draft=preservation_draft.strip(),
            disclosure_request_draft=disclosure_draft.strip(),
            statutory_disclaimer=disclaimer
        )

    @classmethod
    def generate_packet(
        cls,
        case_id: str,
        investigator: str,
        suspect_wallet: str,
        chain: str,
        candidate: VASPAttributionCandidate
    ) -> LawfulActionPacket:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        preservation_draft = f"""
OFFICIAL PRESERVATION NOTICE UNDER SECTION 91 CrPC / IT ACT (DRAFT FOR OFFICER REVIEW)
---------------------------------------------------------------------------------------
To: Legal Compliance Department, {candidate.entity_name}
From: Cyber Crime Police Station / Financial Investigation Unit
Date of Notice: {now_str}
Case Reference: {case_id}
Investigating Officer: {investigator}

SUBJECT: URGENT PRESERVATION OF TRANSACTION LOGS & KYC RECORDS

1. This agency is investigating financial fraud involving illicit cryptocurrency flows.
2. Blockchain intelligence indicates that funds originating from Suspect Wallet:
   {suspect_wallet} ({chain})
   were transferred to custodial deposit infrastructure associated with {candidate.entity_name}:
   Deposit Wallet: {candidate.terminal_deposit_address or "N/A"}
   Shortest Topological Path: {candidate.shortest_path_hops} hops
   Attribution Confidence: {candidate.confidence_score}% ({candidate.confidence_band})

3. YOU ARE HEREBY REQUESTED TO IMMEDIATELY PRESERVE:
   a. All account registration details, KYC documents, phone numbers, and IP connection logs.
   b. All deposit, withdrawal, and internal ledger logs linked to the above deposit infrastructure.
   c. Fiat bank accounts associated with liquidation withdrawals.

NOTICE: This document is an investigator draft generated by the Crypto Investigation Copilot.
Official issuance requires authorization and physical/digital signature by the Investigating Officer.
"""

        disclosure_draft = f"""
FORMAL DISCLOSURE REQUISITION (SECTION 91 CrPC / STATUTORY NOTICE DRAFT)
------------------------------------------------------------------------
To: Designated Grievance / Nodal Officer, {candidate.entity_name}
Case File: {case_id}

Requisition for production of documents and evidentiary records concerning transactions:
{', '.join(candidate.supporting_tx_ids[:5])}

Please supply certified copies of the identity records and banking rails for the account
holding custody of deposit address: {candidate.terminal_deposit_address or "Identified Infrastructure"}
within 72 hours of official receipt.
"""

        disclaimer = (
            "STATUTORY LEGAL NOTICE & DISCLAIMER:\n"
            "This Lawful Action Packet is an automated intelligence draft prepared solely to assist "
            "authorized investigating officers. It does NOT constitute an automated legal order. "
            "Beneficiary identity is NOT established from on-chain clustering alone. "
            "Any submission to exchanges must be formally reviewed and signed by an authorized officer."
        )

        packet_body = preservation_draft + disclosure_draft + disclaimer
        integrity_hash = hashlib.sha256(packet_body.encode("utf-8")).hexdigest()

        return LawfulActionPacket(
            packet_id=f"act_{case_id}_{int(datetime.now(timezone.utc).timestamp())}",
            case_id=case_id,
            suspect_wallet=suspect_wallet,
            chain=chain,
            attributed_vasp=candidate.entity_name,
            attribution_confidence=f"{candidate.confidence_score}% ({candidate.confidence_band})",
            operator_role="VASP-Controlled Deposit Infrastructure",
            beneficiary_identity="NOT ESTABLISHED (Awaiting Off-Chain KYC)",
            integrity_hash_sha256=integrity_hash,
            preservation_notice_draft=preservation_draft.strip(),
            disclosure_request_draft=disclosure_draft.strip(),
            statutory_disclaimer=disclaimer
        )
