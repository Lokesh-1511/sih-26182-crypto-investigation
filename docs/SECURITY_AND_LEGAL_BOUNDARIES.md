# Security & Legal Boundaries: SIH 26182

**System:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine  
**Classification:** Law Enforcement Intelligence-Support System  
**Document Version:** 1.0.0

---

## 1. System Operational Boundaries

The platform operates under strict legal and cryptographic boundaries to adhere to evidence admissibility standards (e.g., Indian Evidence Act / Bharatiya Sakshya Adhiniyam, Section 65B):

1. **Read-Only Intelligence Gathering**:
   - The system strictly consumes public distributed ledger data and authorized intelligence feeds.
   - The system contains zero capabilities to extract private keys, manipulate cryptographic signatures, access mnemonic seeds, or tamper with target wallets.
2. **No Autonomous Legal Execution**:
   - The platform generates **drafts** of legal instruments (such as Section 91 CrPC notices, MLAT preservation requests, or FIU disclosure demands).
   - The software **never** transmits automated orders to exchanges, nor does it freeze assets autonomously. All actions require discretionary review and official digital signature by an authorized law enforcement officer.
3. **Evidence Integrity & Auditability**:
   - Every analytical snapshot computed by the engine generates a SHA-256 cryptographic digest.
   - An immutable audit trail records investigator access, trace executions, report generation timestamps, and filter alterations.

---

## 2. Information Security Protocols

- **Secret Zero Principle**: No production API keys, private keys, or passwords are committed to version control. Configuration is ingested strictly via environment variables (`.env`).
- **Input Sanitization**: All incoming address queries are cryptographically validated to eliminate injection vectors and malformed payload processing.
- **Controlled Demo Integrity**: Demo datasets and synthetic fixtures are segregated from real intelligence and clearly badged in both the UI and forensic reports as `DEMO / CONTROLLED DATA`.
