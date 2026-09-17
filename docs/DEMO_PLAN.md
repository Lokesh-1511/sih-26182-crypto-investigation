# 3-Minute Hackathon Demo Script & Judge Playbook

**Hackathon Target:** Smart India Hackathon 2026 (Problem Statement 26182)  
**Pitch Identity:** "Crypto Investigation Copilot — Evidence-Backed VASP Attribution"  
**Total Allocated Time:** 3 Minutes  
**Document Version:** 1.0.0

---

## 1. Step-by-Step 3-Minute Demo Timeline

```
[00:00 - 00:30] THE PROBLEM & INITIATION
- Pitch: "Generic blockchain explorers dump transactions. Investigators drown in data. We built an AI Copilot that answers: WHICH VASP, and WHY?"
- Action: Open Investigation Console (Dark mode, Plain CSS). Select Case B (4-hop Ethereum fraud).
- Show: Cryptographic address validation confirms valid EIP-55 address `0x71C...439`.

[00:30 - 01:10] TRACE & GRAPH INTELLIGENCE
- Action: Click "Start Multi-Hop Trace".
- Visual: Trace progress reaches 100% in <1 second (running offline on cached fixtures).
- Show: Interactive Cytoscape.js directed multigraph renders 4 hops.
- Highlight: Amber warning beacon appears at Hop 2 — **Obfuscation Breakpoint Detected!**
- Explain: "The copilot detected an anomalous 1-to-4 fan-out within 4 minutes, signaling an intentional layering attempt."

[01:10 - 01:55] SIGNATURE FEATURE: EXPLAINABLE VASP ATTRIBUTION CARD
- Action: Click on destination cluster. The **Explainable Attribution Card** slides open.
- Highlight:
  * Top Candidate: **Binance (Confidence: 86% - HIGH)**
  * The "WHY?" factor points breakdown:
    - Known deposit-wallet match: `+28 pts`
    - Repeated sweep pattern: `+22 pts`
    - Behavioral volume similarity: `+17 pts`
    - Graph proximity (4 hops): `+11 pts`
    - Temporal consistency: `+8 pts`
- Forensic Principle: Call out the **Operator vs Beneficiary Notice**:
  "Infrastructure attribution is HIGH, but the natural beneficiary identity is strictly NOT ESTABLISHED without off-chain KYC."

[01:55 - 02:30] COUNTERFACTUAL ANALYSIS & EVIDENCE DRILL-DOWN
- Action: Toggle **Counterfactual Sensitivity Simulation**.
- Show: "What if the deposit match was spoofed? We disable it — Binance score drops to 58%, demonstrating the attribution is backed by multiple independent signals, not just one label."
- Action: Click on transaction `0x3a9b...`. Evidence drawer reveals exact block height, timestamp, transfer amount (12.5 ETH), and fee.

[02:30 - 03:00] FORENSIC REPORT & LAWFUL ACTION PACKET
- Action: Click "Generate Investigation Package".
- Show:
  1. Tamper-evident PDF/HTML report with SHA-256 integrity hash.
  2. Pre-populated **Section 91 CrPC / MLAT Preservation Notice** draft ready for the investigating officer's digital signature.
- Closing Pitch: "From an unknown wallet to an evidence-backed VASP lead, with an explainable path, risk context, and investigator-ready legal packet in one unified workflow."
```

---

## 2. Judge Q&A Defense Strategy

| Judge Question | Winning Response |
| :--- | :--- |
| **"How is this different from Etherscan or Blockchair?"** | Explorers display raw transactions without context. Our copilot performs multi-hop path synthesis, automated VASP clustering, quantitative evidence scoring (*"WHY THIS VASP?"*), and produces court-ready action packets. |
| **"Can you claim you know who owns the wallet?"** | Never. We strictly distinguish *VASP-controlled infrastructure* from *customer identity*. We explicitly flag beneficiary identity as `NOT ESTABLISHED` on-chain, preventing wrongful attribution. |
| **"What happens when criminals use mixers or cross-chain bridges?"** | Our Obfuscation Breakpoint detector algorithmically flags mixer and bridge contract interactions, applies uncertainty penalties to downstream confidence, and isolates the breakpoint on the fund-flow graph. |
| **"Why not just use a deep learning black box?"** | In criminal justice, unexplainable black-box outputs are inadmissible in court. Our hybrid evidence model provides mathematically auditable factor weights where every point links directly to a verifiable transaction hash. |
| **"Will this demo fail if the venue internet goes down?"** | No. Our dual-mode architecture includes a self-contained offline fixture provider with complete ground-truth cases that runs 100% locally in Docker. |
