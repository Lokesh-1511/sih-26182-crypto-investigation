# Team Workflow & Git Strategy (3-Member Allocation)

**Project:** Automated Attribution of Unknown Cryptocurrency Wallets to Nearest VASPs (SIH 26182)  
**Team Allocation:** 3 Developers  
**Document Version:** 1.0.0

---

## 1. Domain Ownership Breakdown

To maximize velocity during the 15-day sprint and eliminate merge conflicts, the codebase is partitioned into three independent domains:

### Member 1: Blockchain Data Engineering & Adapters
- **Domain Directory:** `backend/app/blockchain/`, `data/demo/transactions/`
- **Core Responsibilities:**
  1. Multi-chain address validation & checksums (`BitcoinValidator`, `EthereumValidator`, `TronValidator`).
  2. Ingestion pipeline and `BlockchainProvider` abstraction.
  3. `FixtureProvider` for Mode 1 offline demo cases and `LiveProvider` for Mode 2 APIs.
  4. Common transaction and transfer normalization (UTXO multi-inputs/outputs & EVM token events).
  5. Generating high-fidelity mock datasets for Case A (Direct), Case B (Layered), and Case C (Cross-chain).

### Member 2: Graph Intelligence & VASP Attribution Engine
- **Domain Directory:** `backend/app/graph/`, `backend/app/entities/`, `backend/app/attribution/`, `data/knowledge_base/`
- **Core Responsibilities:**
  1. Directed NetworkX multigraph builder from normalized transfers.
  2. Configurable 3 to 5 hop BFS traversal with cycle detection.
  3. Noise control filters (dust suppression, time window filtering, high-degree hub thresholds).
  4. VASP entity resolution against the local knowledge base.
  5. Multi-factor VASP attribution scoring engine with calibrated confidence bands.
  6. Signature Feature: **Explainable Attribution Factor Breakdown**.
  7. Signature Feature: **Counterfactual Attribution (Sensitivity Analysis)**.
  8. Signature Feature: **Obfuscation Breakpoint Detection**.

### Member 3: Platform Orchestration, Risk Engine, Frontend Console & Reports
- **Domain Directory:** `backend/app/api/`, `backend/app/models/`, `backend/app/risk/`, `backend/app/reports/`, `frontend/`
- **Core Responsibilities:**
  1. FastAPI application setup, database models (SQLAlchemy), and REST API routing.
  2. Rule-assisted AML typology detection and baseline statistical anomaly engine.
  3. Forensic PDF/HTML report generator with SHA-256 evidence package hashing.
  4. Review-ready Lawful Action Packet generator (Section 91 CrPC / MLAT preservation drafts).
  5. React 18 + Vite frontend console using Plain CSS / CSS Modules (no Tailwind).
  6. Cytoscape.js interactive graph integration, Explainable Attribution Card UI, and Timeline components.
  7. Docker Compose orchestration, seed scripts, and demo packaging.

---

## 2. Git Branching Strategy

```
  main (Stable release tags: v0.1.0, v1.0.0)
   ^
   |  [Squash merge after full integration pass]
 develop (Integration & staging)
   ^
   +--- feature/member1-blockchain-adapters
   +--- feature/member2-graph-attribution
   +--- feature/member3-platform-dashboard
```

### Rules of Engagement
1. **Branch Naming**:
   - `feature/m1-address-validation`
   - `feature/m2-attribution-engine`
   - `feature/m3-fastapi-routers`
2. **Commit Message Format**:
   - `feat: implement EIP-55 ethereum address checksum validation`
   - `fix: resolve cycle recursion in 5-hop BFS traversal`
   - `test: add unit tests for counterfactual sensitivity deltas`
   - `docs: update API specification for attribution endpoint`
3. **No Direct Commits to Main**: All code merges into `develop` via pull requests verified by unit tests (`pytest tests/`).
4. **Immutable Shared Schemas**: Any modification to `backend/app/schemas/` requires explicit consensus from all 3 members before merging.
