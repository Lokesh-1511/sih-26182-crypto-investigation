# Workplan: Full-Stack Platform Engineering Track (Member 3)

**Project:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine (SIH 26182)  
**Role:** Full-Stack Platform Engineer (FastAPI Backend, Database & Forensic UI Specialist)  
**Assigned Git Branch:** `feature/member3-fullstack-platform`  
**Target Delivery Window:** 15-Day SIH Accelerated Sprint  
**Document Version:** 1.0.0

---

## 1. Domain Overview & Purpose

As the **Full-Stack Platform Engineer (Member 3)**, you are the unifying force of the team. You integrate the raw blockchain ingestion layer built by **Member 1 (Blockchain)** and the intelligent graph traversal and attribution scoring engines built by **Member 2 (ML & Graph)** into a production-grade, court-admissible, law-enforcement grade investigative platform.

### Core Mission
Your responsibilities span both sides of the application boundary:
1. **Backend Orchestration & Evidentiary Integrity**:
   - Build high-performance FastAPI REST endpoints coordinating validation, multi-hop collection, graph building, entity resolution, and attribution scoring.
   - Implement relational persistence with SQLite and an zero-dependency standard-library fallback (`MockSession`/`MockQuery`) ensuring zero installation hurdles on any judge's laptop.
   - Implement the **Forensic Reporting Engine** producing court-ready HTML/PDF dossiers sealed with SHA-256 evidence package digests.
   - Generate **Lawful Action Packets** drafting statutory notices under Section 91 of the Code of Criminal Procedure (CrPC) and Mutual Legal Assistance Treaties (MLAT).
2. **Forensic Investigator Console (React 18 + TypeScript + Plain CSS)**:
   - Construct a high-density, dark-mode investigative console adhering strictly to **Plain CSS / CSS Modules** (Strictly zero Tailwind CSS).
   - Embed an interactive **Cytoscape.js** canvas rendering directed multi-hop fund-flow graphs with custom entity icons, clustering, and Obfuscation Breakpoint badges.
   - Create the **Explainable Attribution Card** featuring quantitative factor contribution bars, an interactive **Counterfactual Sensitivity** ablation simulator, and prominent **Operator vs. Beneficiary** legal distinction banners.

---

## 2. Codebase Ownership & Directory Boundary

You have primary write ownership and architectural authority over the following paths:

```
backend/app/
├── main.py                      # FastAPI application entrypoint, CORS & lifespan events
├── api/                         # REST API Router Suite
│   ├── __init__.py
│   ├── cases.py                 # Case creation, listing & detail endpoints
│   ├── tracing.py               # Multi-hop BFS pipeline execution triggers
│   ├── graph.py                 # Cytoscape-formatted graph serialization
│   ├── attribution.py           # VASP attribution results & counterfactual simulation
│   ├── risk.py                  # AML typologies & obfuscation breakpoint endpoints
│   ├── evidence.py              # Evidentiary snapshots & SHA-256 chain of custody
│   └── reports.py               # HTML/PDF report & Lawful Action Packet generation
├── models/                      # Relational persistence layer
│   ├── __init__.py
│   ├── database.py              # SQLite engine & standard-library Mock fallback
│   └── entities.py              # CaseModel, EvidenceSnapshotModel, AttributionRecordModel
└── reports/                     # Forensic documentation generators
    ├── __init__.py
    ├── pdf_generator.py         # Court-admissible HTML/PDF report generator with SHA-256 seal
    └── action_packet.py         # Section 91 CrPC & MLAT legal notice draft generator

frontend/
├── index.html                   # HTML5 application shell & title
├── package.json                 # React 18, Cytoscape.js, Lucide icons dependencies
├── vite.config.ts               # Vite build configuration & backend proxy
└── src/
    ├── main.tsx                 # React DOM mount point
    ├── App.tsx                  # Main forensic investigator HUD & tabbed layout
    ├── services/
    │   └── api.ts               # Typed Axios/Fetch backend communication client
    ├── components/
    │   ├── ExplainableCard.tsx  # "Why This VASP?" factor breakdown & counterfactual toggle
    │   ├── InvestigationGraph.tsx # Cytoscape.js interactive fund-flow graph canvas
    │   ├── RiskGauge.tsx        # AML typology & risk level visual gauge
    │   ├── ActionPacketModal.tsx# Lawful Action Packet preview & clipboard copy modal
    │   └── ReportModal.tsx      # Forensic report viewer with SHA-256 seal verification
    └── styles/
        ├── theme.css            # Global CSS variables, palette & typography (NO Tailwind)
        └── *.css                # Modular Plain CSS stylesheets
```

*Shared Contracts with Team Members:*
- `backend/app/schemas/` (Co-owned with Member 1 & 2 for typed API data transfer).

---

## 3. Detailed Work Breakdown & Deliverables

### Milestone 1: FastAPI Orchestrator, Database Persistence & Router Suite
**Target Files:** `backend/app/main.py`, `backend/app/models/database.py`, `backend/app/api/*.py`  
**Dependencies:** `backend/app/schemas/`, Member 1 & 2 modules

#### Detailed Tasks:
1. **FastAPI Application Scaffolding (`main.py`)**:
   - Initialize FastAPI application with title `"Crypto Investigation Copilot & VASP Attribution Engine"`.
   - Configure permissive CORS middleware for frontend origin (`http://localhost:5173`, `http://127.0.0.1:5173`).
   - Register all 7 core routers under `/api`:
     * `/api/cases` $\to$ Case management
     * `/api/tracing` $\to$ Trace orchestration
     * `/api/graph` $\to$ Graph visualization data
     * `/api/attribution` $\to$ Explainable attribution
     * `/api/risk` $\to$ Risk & breakpoint detection
     * `/api/evidence` $\to$ Evidentiary snapshots & SHA-256 audit
     * `/api/reports` $\to$ Report & Action Packet exports
   - Expose system health endpoint (`GET /health`) reporting Mode 1 vs Mode 2 status and database readiness.
2. **Zero-Dependency Database Persistence (`database.py`)**:
   - Provide standard SQLAlchemy `SessionLocal` connected to SQLite (`data/investigation.db`).
   - Implement **resilient standard-library fallback** (`MockEngine`, `MockSession`, `MockQuery`, `MockColumn`):
     * If `sqlalchemy` is not installed or SQLite fails, fallback transparently to an in-memory dictionary-backed mock database.
     * Support `.query()`, `.filter()`, `.all()`, `.first()`, `.order_by()`, and `.desc()` operations.
     * Auto-seed default cases from `data/demo/cases/*.json` on first query if the database is empty.
3. **Core Case Management Router (`api/cases.py`)**:
   - `GET /api/cases`: Return list of active cases with metadata, chain, suspect wallet, and status.
   - `POST /api/cases`: Create a new investigation case with auto-generated UUID case reference.
   - `GET /api/cases/{case_id}`: Retrieve detailed case dossier including suspect address validation status.
4. **Trace Execution Pipeline Router (`api/tracing.py`)**:
   - `POST /api/tracing/{case_id}/start`:
     * Validate suspect address using Member 1's `AddressValidator`.
     * Fetch normalized multi-hop transactions using Member 1's `BlockchainCollector`.
     * Construct directed graph using Member 2's `GraphBuilder`.
     * Execute entity resolution using Member 2's `EntityResolver`.
     * Calculate multi-factor attribution using Member 2's `AttributionScorer`.
     * Store evidentiary snapshot in database.
     * Return trace summary with execution time $< 150\text{ms}$ in Mode 1.

---

### Milestone 2: Automated Forensic Reporting Engine & Lawful Action Packet Generator
**Target Files:** `backend/app/reports/pdf_generator.py`, `backend/app/reports/action_packet.py`, `backend/app/api/reports.py`  
**Dependencies:** `backend/app/schemas/snapshot.py`, `backend/app/schemas/attribution.py`

#### Detailed Tasks:
1. **Forensic Investigation Report Generator (`pdf_generator.py`)**:
   - Generate standalone, court-admissible HTML/PDF investigation reports with professional legal layout.
   - Include prominent **Evidentiary Principles Disclaimer**:
     > *"CRITICAL INVESTIGATIVE PRINCIPLE: The findings herein reflect observed blockchain transaction facts and heuristic infrastructure clustering. Beneficiary Identity is NOT ESTABLISHED. VASP infrastructure attribution does NOT constitute conclusive proof of end-user identity without off-chain KYC records obtained via lawful legal requisition."*
   - Structure report sections:
     1. Case Summary (Reference, Investigator, Suspect Wallet, Target Chain, Date/Time UTC).
     2. VASP Attribution Findings ("WHY THIS VASP?", Top Candidate, Confidence Band, Factor Points Table).
     3. Topological Evidence Summary (Shortest Path, Strongest-Value Corridor, Terminal Deposit Address).
     4. Obfuscation & AML Risk Findings (Breakpoint locations, typologies detected).
     5. Tamper-Proof Cryptographic Seal: Calculate SHA-256 digest of the entire report contents and embed directly in the footer.
   - Save generated reports to `reports/generated/report_{case_id}.html`.
2. **Lawful Action Packet Generator (`action_packet.py`)**:
   - Generate ready-to-sign statutory requisition notices for investigating officers:
     * **Section 91 CrPC Requisition Draft** (Indian Jurisdictional Mandate): Formal notice to VASP Grievance/Nodal Officer requesting KYC documents, registration IPs, device IDs, and bank settlement details for the terminal deposit wallet.
     * **Emergency Preservation Notice**: Urgent demand to freeze or preserve transaction audit logs for 90 days.
     * **MLAT / Letter Rogatory Summary**: International assistance requisition draft for foreign-domiciled VASPs (e.g. Binance Seychelles/Malta).
   - Ensure the packet contains exact on-chain transaction hashes, terminal deposit wallet addresses, timestamps, and confidence scores.
   - **Crucial Guardrail**: Clearly mark notices as *"DRAFT FOR INVESTIGATING OFFICER REVIEW - NOT AN AUTOMATED LEGAL ISSUANCE"*.

---

### Milestone 3: Interactive Forensic Frontend Console (Plain CSS / CSS Modules)
**Target Files:** `frontend/src/App.tsx`, `frontend/src/styles/theme.css`, `frontend/src/services/api.ts`  
**Strict Design Constraint:** **NO Tailwind CSS**. Pure Plain CSS / CSS Modules only.

#### Detailed Tasks:
1. **Forensic Dark-Theme Design System (`theme.css`)**:
   - Define law-enforcement grade dark-mode palette:
     * Background: `#0d1117` (Canvas), `#161b22` (Card surface), `#21262d` (Borders).
     * Accents: `#58a6ff` (Terminal blue), `#2ea043` (Verified green), `#d29922` (Warning amber), `#f85149` (Critical alert crimson), `#bc8cff` (Mixer hazard purple).
     * Typography: Monospace for addresses and hashes (`Fira Code`, `SF Mono`, `Courier New`); Clean sans-serif for UI labels (`Segoe UI`, `Inter`, system-ui).
   - Define reusable utility classes: `.card`, `.badge`, `.badge-danger`, `.badge-warning`, `.badge-success`, `.btn-primary`, `.btn-secondary`, `.mono`.
2. **Application Layout & Navigation (`App.tsx`)**:
   - **Header / Navigation Bar**:
     * System Title: `"SIH 26182 | CRYPTO INVESTIGATION COPILOT"`.
     * Live Environment Pill: `"OFFLINE MODE (FIXTURES)"` / `"LIVE MODE (APIs)"`.
     * View Switcher Tabs: `[Graph & Attribution]`, `[Forensic Reports & Action Packet]`, `[Case Management]`.
   - **Active Case Banner**:
     * Display Active Case ID, Case Name, Target Blockchain, Suspect Wallet, and Investigator Name.
     * Primary Call-to-Action: `"Start Multi-Hop Trace"` button with real-time loading spinner.
   - **Case Switcher Modal / Sidebar**:
     * Quick-select presets: Case A (BTC Direct Flow), Case B (ETH Layered Phish), Case C (TRX Bridge & Peel Chain).
3. **Typed API Service Client (`services/api.ts`)**:
   - Implement typed functions for every REST endpoint using `fetch` or `axios`.
   - Implement resilient error handling displaying actionable toast banners if backend is unreachable.

---

### Milestone 4: Interactive Cytoscape Graph Visualization & Obfuscation Badging
**Target File:** `frontend/src/pages/InvestigationGraph.tsx`  
**Dependencies:** `cytoscape`, `frontend/src/services/api.ts`

#### Detailed Tasks:
1. **Cytoscape Graph Canvas Integration**:
   - Initialize Cytoscape container with dark canvas styling and fluid responsiveness.
   - Configure directed graph layout (`breadthfirst` with hierarchical directional flow left-to-right, or `cose` force-directed).
2. **Node Styling by Entity Role**:
   - `SUSPECT`: Red glowing circle, bold border, label showing truncated address.
   - `INTERMEDIARY`: Slate gray circle representing transit / layering hops.
   - `VASP_DEPOSIT`: Golden amber circle representing exchange deposit wallet.
   - `VASP_HOT`: Royal blue large hexagon representing high-degree exchange hot wallet pool.
   - `MIXER`: Hazard magenta octagonal node representing OFAC-sanctioned mixer contract.
   - `BRIDGE`: Cyan diamond node representing cross-chain liquidity bridge.
3. **Edge Styling & Value Flow**:
   - Directed arrows with thickness proportional to transfer volume.
   - Edge labels showing asset amount (e.g. `"4.25 ETH"`, `"15,000 USDT"`).
   - Highlighting shortest path and strongest-value corridor on user selection.
4. **Obfuscation Breakpoint Badging**:
   - If an edge or node triggers an AML Obfuscation Breakpoint (e.g. Peel Chain or Rapid Fan-out), render an animated alert icon badge directly above the node.
   - Clicking the breakpoint node opens a diagnostic flyout: *"Breakpoint Detected: Rapid 4-hop relay within 32 minutes across unclustered intermediaries"*.
5. **Graph Interaction & Controls**:
   - Zoom in/out, fit to viewport, reset view controls.
   - Node click handler: Populates address inspection sidebar showing balance, total txs, resolved entity name, and first/last seen timestamps.

---

### Milestone 5: Explainable Attribution Card & Counterfactual Sensitivity UI
**Target File:** `frontend/src/components/ExplainableCard.tsx`  
**Dependencies:** `backend/app/schemas/attribution.py`

#### Detailed Tasks:
1. **Top Attribution Candidate Card**:
   - Display Primary Attributed VASP (e.g. `Binance`, `Kraken`, `Coinbase`).
   - Confidence Score Gauge (0–100%) with color-coded band:
     * $\ge 80\%$: High Confidence (Green).
     * $50–79\%$: Medium Confidence (Amber).
     * $< 50\%$: Low Confidence (Red).
2. **Operator vs. Beneficiary Legal Distinction Banner**:
   - Prominently render dual-state status boxes:
     * Box 1: `Infrastructure Control: VASP-OPERATED INFRASTRUCTURE (Verified)`
     * Box 2: `Beneficiary Identity: NOT ESTABLISHED (Requires Subpoena under Sec 91 CrPC)`
   - Add warning tooltip explaining why on-chain clustering cannot legally establish real-world user identity.
3. **Quantitative Factor Contribution Breakdown ("WHY THIS VASP?")**:
   - Render horizontal stacked or individual progress bars for each attribution factor:
     * `Direct Deposit Sweep`: $+30\text{ pts}$
     * `Hot Wallet Interaction`: $+25\text{ pts}$
     * `Topological Closeness`: $+15\text{ pts}$
     * `Temporal Velocity`: $+10\text{ pts}$
     * `Volume Concentration`: $+10\text{ pts}$
   - Each factor includes an analytical explanation tooltip explaining the heuristic basis.
4. **Interactive Counterfactual Sensitivity Toggle**:
   - Provide interactive checkboxes / toggle switches:
     * *"What if the Direct Sweep factor is excluded?"*
     * *"What if transaction volume is ablated?"*
   - Dynamically re-evaluate score in the frontend:
     * Show animated transition: Score drops from $88\%$ (High) to $42\%$ (Low).
     * Highlight: *"Attribution is fragile without the Terminal Sweep evidence factor."*
5. **One-Click Action Triggers**:
   - Primary Button: `[View Full Forensic Report]` $\to$ Opens `ReportModal` with SHA-256 seal.
   - Secondary Button: `[Generate Section 91 CrPC Notice]` $\to$ Opens `ActionPacketModal` with copy-to-clipboard functionality.

---

## 4. Day-by-Day 15-Day Sprint Schedule

```
Sprint Timeline:
[Day 1-3] Backend Scaffolding & Database ──> [Day 4-6] API Router Suite & Pipeline
──> [Day 7-9] React Console & Cytoscape ──> [Day 10-12] Explainability & Counterfactuals
──> [Day 13-14] Forensic Reports & Action Packets ──> [Day 15] Full Integration & Pitch
```

| Days | Focus Area | Deliverables & Milestones | Verification Gate |
|---|---|---|---|
| **Day 1–3** | Backend Scaffolding & DB Engine | FastAPI `main.py`, CORS setup, `database.py` with MockEngine fallback, `api/cases.py` router. | `GET /api/cases` returns demo cases without errors. |
| **Day 4–6** | Full Router Suite & Integration | Implement `api/tracing.py`, `api/graph.py`, `api/attribution.py`, `api/risk.py`. Connect Member 1 ingestion & Member 2 graph engines. | End-to-end trace completes via API in $< 200\text{ms}$. |
| **Day 7–9** | React Frontend & Cytoscape Canvas | Vite setup, Plain CSS `theme.css`, Navbar, Case switcher, Cytoscape graph canvas with custom node styles. | Fund-flow graph renders smoothly with zoom & pan. |
| **Day 10–12** | Explainable UI & Counterfactuals | Build `ExplainableCard.tsx`, factor contribution bars, Beneficiary Identity warning banner, interactive sensitivity toggle. | Toggling sensitivity visibly updates score and confidence band. |
| **Day 13–14** | Reporting & Lawful Action Packets | Build `pdf_generator.py` with SHA-256 seal, `action_packet.py` (Sec 91 CrPC notice), Report Modal & Action Packet Modal. | HTML report generated with valid SHA-256 hash. |
| **Day 15** | Polish, Offline Demo & Final Rehearsal | Full end-to-end integration test across Case A, B, and C. Verify zero internet dependency in Mode 1. Dry run pitch. | Complete demo executes offline from scratch in $< 30$ seconds. |

---

## 5. Key SIH Pitch Features & Differentiation Highlights

During the 15-minute judge evaluation, your platform components directly demonstrate our 5 primary competitive differentiators:

1. **The 4-Tier Forensic Distinction (Legal Rigor)**:
   - Your UI makes the strict distinction crystal clear:
     * Tier 1: **Observed On-Chain Fact** (Tx hashes, block times, raw amounts).
     * Tier 2: **Inferred Attribution** (Heuristic VASP cluster candidate).
     * Tier 3: **Analytical Risk Score** (Typologies, fan-out velocity).
     * Tier 4: **Beneficiary Identity** (`NOT ESTABLISHED` - visually stamped in red).
   - Prevents judges from disqualifying the project for "claiming AI knows the suspect's real name".

2. **Interactive Counterfactual Sensitivity Toggle**:
   - Judges can toggle individual evidence factors on and off in real-time.
   - Demonstrates that our scoring is mathematically grounded and transparent, not a black-box neural net hallucination.

3. **Obfuscation Breakpoint Badging on Cytoscape Graph**:
   - Visual badges pinned directly to graph hops where criminals attempted peel chains or mixer hops.
   - Instantly guides the investigator's eye to the key laundering choke point.

4. **Section 91 CrPC / MLAT Lawful Action Packet Generator**:
   - Bridges the gap from blockchain analysis to real-world police action.
   - Generates immediate, copy-pasteable legal notices formatted for Indian law enforcement and international liaisons.

5. **Tamper-Proof SHA-256 Evidence Seal**:
   - Every exported report and evidence snapshot includes a cryptographic hash digest.
   - Proves chain of custody for court admissibility under Section 65B of the Indian Evidence Act.

---

## 6. Cross-Member Integration Contracts

### Contract with Member 1 (Blockchain Data Engineer):
- **Input Received:** `NormalizedTransaction` and `NormalizedTransfer` models from `backend/app/blockchain/normalization/normalizer.py`.
- **Validation Interface:** `AddressValidator.validate(address, chain)` called before initiating any trace.
- **Fixture Guarantees:** Ensure `data/demo/cases/*.json` contain valid, validated addresses for Case A (BTC), Case B (ETH), and Case C (TRX).

### Contract with Member 2 (ML & Graph Engineer):
- **Graph Serialization:** Member 2's `GraphBuilder.to_cytoscape_elements()` must output nodes and edges in format consumable by `InvestigationGraph.tsx`.
- **Attribution Payload:** Member 2's `AttributionScorer.evaluate()` returns `VASPAttributionResult` schema containing `top_candidate`, `factors`, and `counterfactuals`.
- **Risk Typologies:** Member 2's `TypologyDetector.detect()` feeds the risk badges in the UI.

---

## 7. Verification & Testing Commands

Execute these commands to verify your platform components at each stage:

```bash
# 1. Start backend development server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Verify all API endpoints respond
curl -s http://127.0.0.1:8000/api/cases | jq .
curl -s http://127.0.0.1:8000/api/graph/CASE-2026-002B | jq .
curl -s http://127.0.0.1:8000/api/attribution/CASE-2026-002B | jq .

# 3. Test report generation and SHA-256 digest
curl -X POST http://127.0.0.1:8000/api/reports/CASE-2026-002B/export | jq .

# 4. Run frontend development server
cd frontend
npm run dev

# 5. Build production frontend bundle
npm run build

# 6. Run full platform test suite
python -m pytest tests/ -v
```

---

*Document Author: Lead Software Architect & Full-Stack Systems Lead*  
*Approved for: Member 3 (Full-Stack Platform Engineer)*  
*Smart India Hackathon 2026 – Problem Statement 26182*
