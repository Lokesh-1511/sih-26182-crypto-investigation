# Requirements Specification: SIH 26182

**Project Title:** Automated Attribution of Unknown Cryptocurrency Wallets to Nearest Virtual Asset Service Providers (VASPs) through Blockchain Intelligence APIs  
**Hackathon Target:** Smart India Hackathon 2026 | Prototype & DPoC  
**Team Allocation:** 3 Core Developers (M1: Blockchain/Ingestion, M2: Graph/Attribution, M3: Backend/Frontend/Report)  
**Document Version:** 1.0.0 (Baseline Frozen)

---

## 1. Executive Summary & Product Identity

The platform is designed as an **Explainable Crypto Investigation Copilot** for Law Enforcement Agencies (LEAs) and financial intelligence units. It addresses the critical bottleneck in cyber-crime and crypto fraud investigations: tracing illicit fund flows from an unknown suspect wallet through obfuscated intermediary hops to the deposit infrastructure of a Centralized Exchange / Virtual Asset Service Provider (VASP).

### Core Differentiating Axiom
The system strictly distinguishes:
1. **Observed Blockchain Fact** (Immutable on-chain transactions, block timestamps, inputs/outputs, fee)
2. **Inferred Infrastructure Attribution** (Candidate VASP clustering, confidence band, weight breakdown)
3. **Analytical Risk Finding** (Heuristic typologies, obfuscation breakpoints)
4. **Beneficiary Identity** (Strictly recorded as `NOT ESTABLISHED` on-chain)

---

## 2. Granular Requirements Matrix

| Req ID | Category | Priority | Requirement Description | Owner | Status | Acceptance Test |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-001** | Core Platform | **MUST** | **Case & Input Management**: Create, view, update, and persist cases with title, investigator metadata, priority, and suspect wallet address. | Member 3 | IN PROGRESS | Case persists in SQLite/PostgreSQL; assigned unique UUID; retrievable via API. |
| **REQ-002** | Ingestion | **MUST** | **Multi-Chain Address Validation**: Validate address format and cryptographic checksums for Bitcoin (P2PKH, P2SH, Bech32, Bech32m), Ethereum (EIP-55 checksummed hex), and Tron (Base58Check with 0x41 prefix). | Member 1 | IN PROGRESS | Validates valid test vectors and rejects malformed/checksum-invalid addresses with clear diagnostic errors. |
| **REQ-003** | Ingestion | **MUST** | **Controlled Offline Mode**: Ingest transaction traces from cached demo datasets without requiring active internet connectivity. | Member 1 | IN PROGRESS | Full 5-hop investigation executes end-to-end with network adapters disconnected. |
| **REQ-004** | Ingestion | **MUST** | **Blockchain Provider Adapter Contract**: Extensible `BlockchainProvider` interface supporting live API providers (e.g., Etherscan, Blockstream, TronGrid) alongside offline fixture adapters. | Member 1 | IN PROGRESS | Adapter interface implements `get_wallet_transactions`, `get_transaction`, `get_transfers`, `get_block`. |
| **REQ-005** | Normalization | **MUST** | **Common Transaction Schema**: Normalize heterogeneous UTXO and Account transactions into unified `NormalizedTransaction` and `NormalizedTransfer` schemas without losing raw transaction metadata. | Member 1 | IN PROGRESS | Multi-input/multi-output UTXO and token transfers map cleanly into standard transfer edges. |
| **REQ-006** | Graph Engine | **MUST** | **Directed Fund-Flow Graph Construction**: Build directed NetworkX graph representing wallet nodes and transfer edges with amounts, timestamps, and transaction IDs. | Member 2 | IN PROGRESS | Multigraph accurately stores node attributes (type, label) and edge attributes (tx_id, asset, amount, timestamp). |
| **REQ-007** | Graph Engine | **MUST** | **Multi-Hop Traversal (3–5 Hops)**: Breadth-first forward traversal from the suspect wallet up to configurable hop depth (3 to 5 hops). | Member 2 | IN PROGRESS | Accurately reconstructs known test paths across 4 hops without infinite loops on cyclic transactions. |
| **REQ-008** | Intelligence | **MUST** | **Entity Knowledge Base**: Curated local database of verified VASP deposit addresses, hot wallets, mixers, and bridges with explicit source attributions. | Member 2 | IN PROGRESS | JSON/SQL store containing verified entities; zero unverified or fake labels in production schemas. |
| **REQ-009** | Attribution | **MUST** | **VASP Candidate Attribution Engine**: Multi-factor quantitative scoring algorithm evaluating entity matches, sweep patterns, graph proximity, flow volume, and temporal consistency. | Member 2 | IN PROGRESS | Ranks candidate VASPs with calibrated confidence score (0-100%) and confidence band (HIGH, MEDIUM, LOW). |
| **REQ-010** | Differentiation | **MUST** | **Explainable VASP Attribution Card**: UI card displaying additive factor contributions (+28 deposit match, +22 sweep, +17 volume, etc.) directly linked to supporting transactions. | Member 3 / M2 | IN PROGRESS | User sees exact mathematical reasoning explaining *WHY* this VASP was attributed; click opens transaction evidence. |
| **REQ-011** | Legal / Ethics | **MUST** | **Operator vs Beneficiary Separation**: Explicit forensic distinction between VASP-controlled infrastructure and customer beneficiary identity. | Member 2 / M3 | IN PROGRESS | System and reports clearly assert beneficiary identity is `NOT ESTABLISHED` without off-chain KYC. |
| **REQ-012** | Forensics | **MUST** | **Transaction Evidence Drill-Down**: Every graph node, attribution factor, and risk event links directly to raw transaction identifiers and parameters. | Member 3 | IN PROGRESS | Clicking any evidence item renders complete transaction breakdown (tx_id, block, timestamp, fee, raw inputs). |
| **REQ-013** | Reporting | **MUST** | **Forensic Investigation Report**: Structured PDF/HTML report generation including case details, fund-flow topology, attribution card, and SHA-256 evidence integrity hash. | Member 3 | IN PROGRESS | Generates tamper-evident report file verifiable via SHA-256 digest. |
| **REQ-014** | Differentiation | **SHOULD** | **Counterfactual Attribution (Sensitivity Analysis)**: Dynamic re-scoring of VASP candidates upon selectively removing specific evidence factors. | Member 2 | IN PROGRESS | API returns baseline vs counterfactual scores demonstrating whether attribution relies on a single clue or multi-signal consensus. |
| **REQ-015** | Differentiation | **SHOULD** | **Obfuscation Breakpoint Detection**: Algorithmic detection of structural shifts (fan-out, rapid hops, fragmentation, bridge hopping) along the flow. | Member 2 | IN PROGRESS | Node highlighted on graph with warning badge and breakdown of anomalous indicators. |
| **REQ-016** | Risk Analysis | **SHOULD** | **Risk & AML Typology Engine**: Rule-assisted detection of money-laundering patterns (layering, burst transfers, mixer exposure, peeling chains). | Member 3 / M2 | IN PROGRESS | Generates typed risk events with severity levels (LOW, MEDIUM, HIGH, CRITICAL) and transaction references. |
| **REQ-017** | Visualization | **SHOULD** | **Chronological Fund-Flow Timeline**: Ordered temporal sequence of fund movements with asset, amount, and hop distance filtering. | Member 3 | IN PROGRESS | Timeline component correctly displays sequential movements with millisecond ordering. |
| **REQ-018** | Lawful Action | **SHOULD** | **Lawful Action Packet Drafting**: Automated generation of review-ready legal notice drafts (Section 91 CrPC / MLAT / preservation requests) for authorized officer review. | Member 3 | IN PROGRESS | Action packet draft populated with case ID, target VASP, suspect wallet, and statutory disclaimers. |
| **REQ-019** | Multi-Chain | **SHOULD** | **Multi-Chain Coverage**: Deep demonstration of at least two chains (Bitcoin, Ethereum) and Tron adapter foundation. | Member 1 | IN PROGRESS | Case A (BTC) and Case B (ETH) fully validated; Tron validation and normalization ready. |
| **REQ-020** | Multi-Chain | **STRETCH** | **Cross-Chain Bridge Tracing**: Controlled tracking of fund transfers crossing EVM to Non-EVM bridge contracts. | Member 1 / M2 | PLANNED | Controlled Case C maps lock-and-mint bridge hops between Ethereum and Tron/L2. |
| **REQ-021** | Machine Learning| **STRETCH** | **Baseline ML Anomaly Detection**: Unsupervised anomaly detection (Isolation Forest) on feature vectors of wallet transactions. | Member 3 | PLANNED | Model flags statistical outliers based on transfer frequency and value deviations. |
| **REQ-022** | Interoperability| **STRETCH** | **Mock National Sahyog Integration**: Export case intelligence in standard Indian Law Enforcement Agency (LEA) Sahyog schema. | Member 3 | PLANNED | Valid JSON payload generated conforming to Sahyog data interchange specs. |

---

## 3. Non-Functional Requirements

1. **Deterministic Reproducibility**: Repeated execution on the same transaction snapshot must yield identical graph structures, attribution scores, and report hashes.
2. **Execution Latency**: Graph construction and multi-factor scoring for a 5-hop trace must complete in under 2.5 seconds on demo fixtures.
3. **Security & Boundary Protection**:
   - Zero access to private keys or wallet tampering capabilities.
   - Zero automated execution of legal notices or freezing orders.
   - All credentials and provider keys managed via `.env`.
4. **UI Design Standard**: Clean, high-density, dark forensic aesthetic using Plain CSS / CSS Modules (strictly no Tailwind CSS).
