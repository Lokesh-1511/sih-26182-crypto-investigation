# System Architecture: SIH 26182

**System:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine  
**Platform Identity:** Crypto Investigation Copilot (Law Enforcement Forensic Console)  
**Document Version:** 1.0.0

---

## 1. Multi-Tier Layered Architecture

The system is designed as a decoupled, modular monorepo partitioned cleanly across the three developer domains:

```
+-----------------------------------------------------------------------------------+
|               PRESENTATION LAYER (React + TypeScript + Plain CSS)                 |
|  - Case Dashboard   - Cytoscape Graph   - Explainable Card   - Counterfactual     |
|  - Fund Timeline    - Risk Badges       - Evidence Drilldown - PDF/Action Packet  |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (JSON)
+------------------------------------------v----------------------------------------+
|                      API & ORCHESTRATION LAYER (FastAPI)                          |
|  - /api/cases       - /api/tracing      - /api/graph         - /api/attribution   |
|  - /api/risk        - /api/evidence     - /api/reports       - /api/entities      |
+-------------------+----------------------+-------------------+--------------------+
                    |                      |                   |
+-------------------v----+   +-------------v------+   +--------v--------------------+
| BLOCKCHAIN INGESTION   |   | GRAPH & TRAVERSAL  |   | ATTRIBUTION & FORENSICS     |
| (Member 1 Domain)      |   | (Member 2 Domain)  |   | (Member 2 & 3 Domains)      |
|                        |   |                    |                                 |
| - Validation (BTC/ETH/ |   | - NetworkX Builder |   | - VASP Knowledge Base       |
|   TRX Checksums)       |   | - 3-5 Hop BFS      |   | - Multi-Factor Scorer       |
| - BlockchainProvider   |   | - Noise Pruning    |   | - Counterfactual Sensitivity|
|   (Fixtures & Live)    |   | - Path Analysis    |   | - Obfuscation Breakpoints   |
| - Transaction Normal-  |   |   (Shortest/Value) |   | - Operator vs Beneficiary   |
|   ization (UTXO/EVM)   |   |                    |   | - Rule-Assisted AML Typology|
+-------------------+----+   +-------------+------+   +--------+--------------------+
                    |                      |                   |
+-------------------v----------------------v-------------------v--------------------+
|                     DATA & PERSISTENCE LAYER (SQLAlchemy)                         |
|  - cases          - wallets            - transactions       - transfers           |
|  - entity_labels  - attributions       - risk_events        - snapshots & audit   |
|  - Storage: SQLite (Prototype) / PostgreSQL-Ready (Production)                    |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Pipeline & Data Flow

1. **Case Ingestion**:
   - Investigator submits a Case with an unknown `suspect_wallet` and `chain` (e.g. `ETH`, `BTC`, `TRX`).
   - Member 1's validation engine verifies cryptographic structure and checksum.
2. **Transaction Collection & Normalization**:
   - `BlockchainProvider` retrieves historical transactions (Mode 1: Offline fixtures; Mode 2: Live APIs).
   - UTXO inputs/outputs and Account transfers are normalized into uniform `NormalizedTransfer` records.
3. **Graph Construction & Traversal**:
   - Member 2's `GraphBuilder` converts transfers into a directed multigraph (`MultiDiGraph`).
   - Breadth-First Search traverses up to 5 hops, calculating cumulative flow volumes and hop distances while pruning dust noise.
4. **Entity Resolution & Clustering**:
   - Traversed addresses are checked against `EntityKnowledgeBase` containing known exchange deposit addresses, hot wallets, mixers, and bridges.
5. **Attribution & Sensitivity Analysis**:
   - The Attribution Engine calculates quantitative evidence factors:
     $$S = w_1 F_{\text{entity}} + w_2 F_{\text{sweep}} + w_3 F_{\text{proximity}} + w_4 F_{\text{flow}} + w_5 F_{\text{temporal}} - \text{Penalties}$$
   - Counterfactual engine recalculates scores under simulated evidence ablation.
   - Rigorous separation flags infrastructure as `VASP-Controlled` and beneficiary as `NOT ESTABLISHED`.
6. **Risk Analysis & Breakpoints**:
   - Obfuscation Breakpoint detection identifies sudden fan-out, rapid hops, fragmentation, or bridge jumps.
   - Typology engine flags structuring, layering, and mixer interactions.
7. **Reporting & Action Packets**:
   - Member 3's engine produces forensic PDF/HTML summaries and pre-populated Section 91 CrPC / MLAT lawful action packet drafts with SHA-256 evidence integrity hashes.

---

## 3. Technology Stack Justification

| Layer | Chosen Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+ / FastAPI | High asynchronous concurrency, native Pydantic v2 validation, automated OpenAPI documentation generation. |
| **ORM & Database** | SQLAlchemy 2.0 / SQLite & PostgreSQL | Frictionless local development and offline demo using SQLite; schema fully compatible with PostgreSQL. |
| **Graph Engine** | NetworkX | In-memory graph algorithms (shortest path, subgraph traversal, degree analysis) without requiring heavy Neo4j deployment for 15-day sprint. |
| **Frontend Framework**| React 18 / Vite / TypeScript | Fast compilation, strict type safety sharing backend API contracts. |
| **Styling** | Plain CSS / CSS Modules | Strict hackathon compliance: no Tailwind CSS. Ensures bespoke dark-mode LEA forensic console design. |
| **Graph Visualization**| Cytoscape.js | Industry-standard graph rendering supporting hierarchical layouts, edge badging, and sub-second interaction. |
| **Reporting** | ReportLab / HTML5 Print Engine | Deterministic, tamper-evident document generation with embedded SHA-256 hashes. |
| **Containerization** | Docker Compose | One-command orchestration for backend and frontend offline demonstration. |
