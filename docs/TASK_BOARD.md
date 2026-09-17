# Task Board & 15-Day Sprint Plan (SIH 26182)

**Sprint Model:** 15-Day Accelerated Prototype & Validation  
**Current Milestone:** Day 1–2 Architecture, Schemas, & Engine Interfaces  
**Document Version:** 1.0.0

---

## 1. 15-Day Sprint Schedule

| Day | Focus Area | Key Deliverables |
| :---: | :--- | :--- |
| **Day 1** | Architecture & Contracts | Monorepo scaffolding, Git workflow, Pydantic schemas, database models, Docker Compose. |
| **Day 2** | Ingestion & API Foundation | Address validation engine, FastAPI CRUD for cases, SQLite database initialization. |
| **Day 3** | Normalization & Fixtures | UTXO/EVM transaction normalizer, cached demo fixtures for Cases A, B, and C. |
| **Day 4** | Graph Construction | NetworkX directed multigraph builder, transfer edge mapping, initial visual layout. |
| **Day 5** | Traversal & Pruning | 3 to 5 hop BFS traversal, dust noise filtering, shortest-path calculation. |
| **Day 6** | Entity Resolution | VASP knowledge base, label lookup, hot vs deposit vs mixer classification. |
| **Day 7** | Attribution Engine | Weighted scoring formulation, confidence calibration, candidate VASP ranking. |
| **Day 8** | Explainability & Card UI | Explainable Attribution Card, factor breakdown (+points), transaction drilldown links. |
| **Day 9** | Breakpoints & Typologies | Obfuscation Breakpoint detector, rule-assisted AML typologies (fan-out, layering). |
| **Day 10** | Counterfactual Analysis | Evidence ablation simulator, score delta calculation, sensitivity visualization. |
| **Day 11** | Console Dashboard | React 18 UI integration, Cytoscape.js canvas, interactive filters, timeline view. |
| **Day 12** | Forensic Reports & Packet | Automated PDF/HTML report generation, Section 91 CrPC action packet drafting. |
| **Day 13** | Validation & Benchmarking | Ground-truth test execution, Top-1/Top-3 accuracy evaluation, latency profiling. |
| **Day 14** | Presentation & Dry Run | Slide deck alignment, 3-minute demo script rehearsal, judge Q&A preparation. |
| **Day 15** | Release Freeze & Packaging | Offline bundle verification, backup builds, final smoke tests. |

---

## 2. Granular Task Board

| Task ID | Task Description | Owner | Priority | Dependency | Status | Acceptance Criteria |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **M1-001** | Multi-chain address validator (BTC, ETH, TRX) | Member 1 | **P0** | None | **DONE** | Validates P2PKH/Bech32/EIP-55/Base58Check test vectors; rejects malformed inputs. |
| **M1-002** | `BlockchainProvider` interface & `FixtureAdapter` | Member 1 | **P0** | Schemas | **DONE** | Ingests transactions for Cases A, B, C completely offline without network calls. |
| **M1-003** | UTXO & Account transfer normalizer | Member 1 | **P0** | M1-001 | **DONE** | Extracts unified `NormalizedTransfer` records with amounts, assets, and timestamps. |
| **M1-004** | Live API adapter skeleton (Etherscan/TronGrid) | Member 1 | **P1** | M1-002 | **DONE** | Implements live polling interface with API key injection from `.env`. |
| **M2-001** | NetworkX directed fund-flow graph builder | Member 2 | **P0** | Schemas | **DONE** | Instantiates `MultiDiGraph` with wallet nodes and typed transfer edges. |
| **M2-002** | 3–5 hop BFS traversal with cycle detection | Member 2 | **P0** | M2-001 | **DONE** | Traverses 5 hops without infinite recursion on cyclical transfers. |
| **M2-003** | Graph noise pruning & dust filters | Member 2 | **P1** | M2-001 | **DONE** | Prunes micro-dust transfers (< 0.0001 BTC / 1 USDT) with transparent parameter flags. |
| **M2-004** | VASP knowledge base & entity resolver | Member 2 | **P0** | None | **DONE** | Matches known exchange deposit addresses, hot wallets, bridges, and mixers. |
| **M2-005** | Multi-factor VASP attribution scoring engine | Member 2 | **P0** | M2-002, M2-004| **DONE** | Computes quantitative scores ($w_1..w_5$), calibrated bands, and uncertainty. |
| **M2-006** | Explainable Attribution factor breakdown | Member 2 | **P0** | M2-005 | **DONE** | Produces additive score factors (+28, +22, etc.) linked to transaction IDs. |
| **M2-007** | Counterfactual sensitivity analysis module | Member 2 | **P1** | M2-005 | **DONE** | Re-computes VASP scores when specific evidence factors are removed. |
| **M2-008** | Obfuscation Breakpoint detection | Member 2 | **P1** | M2-001 | **DONE** | Algorithmatically flags fan-out hubs, rapid hopping, and bridge transitions. |
| **M3-001** | FastAPI backend & database initialization | Member 3 | **P0** | Schemas | **DONE** | Initializes SQLite/Postgres tables; provides `/api/health` and case CRUD. |
| **M3-002** | REST API routers (tracing, graph, attribution) | Member 3 | **P0** | M3-001 | **DONE** | Serves graph JSON, attribution ranking, evidence drilldown, and risk summaries. |
| **M3-003** | Rule-assisted AML typology engine | Member 3 | **P1** | M1-003, M2-001| **DONE** | Identifies rapid layering, structuring, and mixer interactions with severity tags. |
| **M3-004** | React 18 investigation console (Plain CSS) | Member 3 | **P1** | M3-002 | **DONE** | Dark-mode LEA console rendering cases, trace status, and timeline (No Tailwind). |
| **M3-005** | Cytoscape.js graph visualization component | Member 3 | **P1** | M2-001, M3-004| **DONE** | Renders interactive node/edge canvas with breakpoint badges and node inspection. |
| **M3-006** | Explainable Attribution Card UI component | Member 3 | **P0** | M2-006, M3-004| **DONE** | Displays score progress bars, factor breakdown, and Operator vs Beneficiary banner. |
| **M3-007** | Forensic Report & Lawful Action Packet generator | Member 3 | **P0** | M2-005, M3-001| **DONE** | Generates tamper-evident forensic reports and Section 91 CrPC draft notices. |
| **M3-008** | Automated validation & benchmark test suite | Member 3 | **P0** | All | **DONE** | Validates Top-1/Top-3 attribution accuracy across ground-truth fixtures. |
