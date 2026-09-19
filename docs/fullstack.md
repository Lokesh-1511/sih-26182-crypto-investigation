# Full-Stack Platform Engineering Track: Phase-by-Phase Technical Specification

**Project:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine (SIH 26182)  
**Role:** Full-Stack Platform Engineer (FastAPI Backend, Database & Forensic UI Specialist) (Member 3)  
**Assigned Git Branch:** `feature/member3-fullstack-platform`  
**Document Version:** 2.0.0 (Phase-Gated Architecture)

---

## Architecture & Responsibilities Overview

As the **Full-Stack Platform Engineer (Member 3)**, you unify the system. You orchestrate the data ingestion pipeline from **Member 1 (Blockchain)** and the analytical intelligence engines from **Member 2 (ML & Graph)** into a robust, court-admissible, law-enforcement grade platform.

### Strict Engineering Principles
1. **Zero-Dependency Portable Persistence**: Database persistence uses SQLite with a standard-library mock fallback (`MockEngine`/`MockSession`), guaranteeing zero installation failures on any evaluation environment.
2. **Strict UI Style Constraint**: The entire frontend is styled strictly using **Plain CSS / CSS Modules**. **Tailwind CSS is strictly forbidden**.
3. **Evidentiary Integrity & Chain of Custody**: Every investigation export generates a cryptographic SHA-256 seal for court admissibility under Section 65B of the Indian Evidence Act.
4. **Lawful Action Packets**: Generates ready-to-sign statutory requisition notices under Section 91 CrPC / MLAT, strictly labeled as investigator drafts.
5. **No Timeline-Based Milestones**: Progressing through phases requires passing all defined test cases and verification gates.

---

## Phase 1: FastAPI Orchestrator, Zero-Dependency Persistence & Core Routers

### 1.1 Objective
Construct the FastAPI server architecture, configure permissive CORS, implement a resilient zero-dependency database layer (SQLAlchemy SQLite with standard-library mock fallback), and expose core case management and trace triggering endpoints.

### 1.2 Deliverables
- **Application Scaffolding:** `backend/app/main.py`
  - FastAPI app initialization, CORS middleware, lifespan events, health route (`GET /health`).
- **Persistence Engine:** `backend/app/models/database.py`, `backend/app/models/entities.py`
  - SQLAlchemy `SessionLocal` for SQLite (`data/investigation.db`).
  - Standard-library fallback classes: `MockEngine`, `MockSession`, `MockQuery`, `MockColumn` with support for `.filter()`, `.order_by()`, `.desc()`, and auto-seeding on first query.
  - Relational Models: `CaseModel`, `EvidenceSnapshotModel`, `AttributionLogModel`.
- **Core API Routers:**
  - `backend/app/api/cases.py`: `GET /api/cases`, `POST /api/cases`, `GET /api/cases/{case_id}`.
  - `backend/app/api/tracing.py`: `POST /api/tracing/{case_id}/start`.
- **Integration Test Suite:** `tests/integration/test_end_to_end_trace.py`

### 1.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/integration/test_end_to_end_trace.py -k "test_health_endpoint or test_vertical_slice_api_flow" -v
```

#### Test Case 1.1: System Health & Mode Indicator Check
- **Request:** `GET http://127.0.0.1:8000/health`
- **Expected Output:**
  - HTTP Status: `200 OK`
  - JSON Body: `{"status": "healthy", "mode": "MODE_1_FIXTURE", "database": "connected"}`
- **Pass Criteria:** Endpoint responds in $< 10\text{ms}$.

#### Test Case 1.2: Case Auto-Seeding & Listing
- **Request:** `GET http://127.0.0.1:8000/api/cases`
- **Expected Output:**
  - HTTP Status: `200 OK`
  - JSON Body contains at least 3 seeded cases:
    * `CASE-2026-001A` (Bitcoin Direct Flow)
    * `CASE-2026-002B` (Ethereum Layered Phish)
    * `CASE-2026-003C` (Tron Peel Chain & Bridge)
- **Pass Criteria:** All cases contain valid `case_id`, `chain`, `suspect_wallet`, and `status`.

#### Test Case 1.3: Trace Pipeline Execution
- **Request:** `POST http://127.0.0.1:8000/api/tracing/CASE-2026-002B/start`
- **Expected Output:**
  - HTTP Status: `200 OK`
  - JSON Body contains `status = "COMPLETED"`, `nodes_discovered >= 5`, `execution_time_ms < 200`.
- **Pass Criteria:** End-to-end trace executes without unhandled exceptions.

#### Phase 1 Exit Gate
> [!IMPORTANT]
> Phase 1 is complete ONLY when the server starts cleanly, auto-seeds demo cases, and completes end-to-end trace requests in $< 200\text{ms}$.

---

## Phase 2: Graph, Attribution & Risk REST Endpoints

### 2.1 Objective
Implement dedicated REST endpoints that transform the analytical outputs of Member 1 and Member 2 into structured payloads for graph rendering, explainable factor displays, and risk indicators.

### 2.2 Deliverables
- **Graph Serialization Router:** `backend/app/api/graph.py`
  - `GET /api/graph/{case_id}`: Serializes NetworkX `MultiDiGraph` into Cytoscape-compliant JSON elements (`nodes` with role styles and `edges` with transfer amounts).
- **Attribution Router:** `backend/app/api/attribution.py`
  - `GET /api/attribution/{case_id}`: Returns top VASP candidate, confidence band, factor breakdown, and counterfactual sensitivity matrix.
- **Risk & Breakpoint Router:** `backend/app/api/risk.py`
  - `GET /api/risk/{case_id}`: Returns overall AML risk score, detected typologies (TYP-01 to TYP-05), and Obfuscation Breakpoint coordinates.

### 2.3 Verification & Test Cases

#### Execution Command
```bash
curl -s http://127.0.0.1:8000/api/graph/CASE-2026-002B | jq .
curl -s http://127.0.0.1:8000/api/attribution/CASE-2026-002B | jq .
```

#### Test Case 2.1: Cytoscape Graph Schema Compliance
- **Input:** Case `CASE-2026-002B`
- **Expected Output:**
  - Elements dictionary containing `nodes: [...]` and `edges: [...]`.
  - Every node contains `data.id`, `data.label`, `data.node_type`, and `data.chain`.
  - Every edge contains `data.source`, `data.target`, `data.amount`, and `data.asset`.
- **Pass Criteria:** Payload format directly mountable in Cytoscape.js canvas without client-side mapping.

#### Test Case 2.2: Attribution Factor Breakdown Verification
- **Input:** Case `CASE-2026-002B`
- **Expected Output:**
  - `top_candidate.entity_name = "Kraken"`
  - `top_candidate.confidence_score >= 80.0`
  - `factors` list contains itemized contributions with non-negative point values summing to the total score.
- **Pass Criteria:** JSON response exposes the exact numerical basis for attribution.

#### Test Case 2.3: Obfuscation Breakpoint Extraction
- **Input:** Case `CASE-2026-002B`
- **Expected Output:**
  - `risk_summary.overall_risk_level` returned (`HIGH` or `CRITICAL`).
  - `breakpoints` array contains at least 1 identified breakpoint with node ID and reason.
- **Pass Criteria:** Breakpoint data includes `hop_index` and `trigger_rule`.

#### Phase 2 Exit Gate
> [!IMPORTANT]
> Phase 2 is complete ONLY when `/api/graph`, `/api/attribution`, and `/api/risk` return valid, schema-validated JSON payloads for all 3 demo cases.

---

## Phase 3: Evidentiary Snapshots, Forensic Reports & Lawful Action Packets

### 3.1 Objective
Implement cryptographic evidence snapshotting, tamper-evident audit hashing, court-admissible HTML/PDF dossier generation, and statutory legal notice draft generation (Section 91 CrPC and MLAT requests).

### 3.2 Deliverables
- **Evidence Storage:** `backend/app/evidence/evidence_store.py`, `backend/app/api/evidence.py`
  - In-memory/relational store calculating SHA-256 digests over case transaction trees.
  - `POST /api/evidence/{case_id}/snapshot`: Creates immutable snapshot with hash seal.
  - `GET /api/evidence/{case_id}/verify`: Verifies data integrity against stored SHA-256 hash.
- **Forensic Report Generator:** `backend/app/reports/pdf_generator.py`, `backend/app/api/reports.py`
  - `POST /api/reports/{case_id}/export`: Produces standalone HTML report with embedded SHA-256 seal.
- **Lawful Action Packet Generator:** `backend/app/reports/action_packet.py`
  - `POST /api/reports/{case_id}/action-packet`: Generates Section 91 CrPC requisition and preservation notices.

### 3.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/integration/test_end_to_end_trace.py -k "test_vertical_slice_api_flow" -v
```

#### Test Case 3.1: SHA-256 Evidence Integrity Seal
- **Execution:** Create snapshot $\to$ read SHA-256 hash $\to$ verify snapshot.
- **Expected Output:**
  - `status = "VALID"`
  - `hash_match = True`
- **Failure Simulation:** Mutate 1 character in case transaction data and re-verify.
- **Expected Output:**
  - `status = "TAMPERED"`
  - `hash_match = False`
  - Alert triggered: *"Integrity violation: data has been modified since snapshot creation."*
- **Pass Criteria:** Tamper detection algorithm detects single-bit payload alteration.

#### Test Case 3.2: Forensic HTML Report Generation
- **Execution:** Call `POST /api/reports/CASE-2026-002B/export`.
- **Expected Output:**
  - Generated file saved at `reports/generated/report_CASE-2026-002B.html`.
  - Report contains: Case ID, Suspect Wallet, Attributed VASP, Factor points table, and embedded SHA-256 digest.
  - Prominent banner: *"Beneficiary Identity: NOT ESTABLISHED"*.
- **Pass Criteria:** File exists on disk, opens in browser, and hash matches computed digest.

#### Test Case 3.3: Section 91 CrPC Action Packet Draft
- **Execution:** Call `POST /api/reports/CASE-2026-002B/action-packet`.
- **Expected Output:**
  - Requisition notice addressed to Legal Compliance Department of Kraken.
  - Cites Section 91 CrPC / Information Technology Act.
  - Lists specific terminal deposit address and transaction hashes.
  - Includes required guardrail: *"DRAFT FOR OFFICER REVIEW - NOT AN AUTOMATED LEGAL ISSUANCE"*.
- **Pass Criteria:** Legal notice draft contains complete case context and terminal addresses.

#### Phase 3 Exit Gate
> [!IMPORTANT]
> Phase 3 is complete ONLY when reports and action packets generate on demand in $< 100\text{ms}$ with verifiable SHA-256 integrity digests.

---

## Phase 4: Forensic Investigator Console HUD (React 18 + Plain CSS)

### 4.1 Objective
Construct the high-density frontend user interface using React 18, TypeScript, and **Plain CSS / CSS Modules**. Implement dark-mode design tokens, application navigation, active case HUD banner, and typed API communication.

### 4.2 Deliverables
- **Styling Architecture:** `frontend/src/styles/theme.css`
  - Dark-mode forensic design tokens (Canvas `#0d1117`, Cards `#161b22`, Borders `#21262d`, Terminal Blue `#58a6ff`, Danger `#f85149`, Warning `#d29922`, Success `#2ea043`).
  - Strict rule: **Zero Tailwind CSS classes or imports**.
- **Application Shell:** `frontend/src/App.tsx`, `frontend/src/main.tsx`
  - Top navigation bar with live status pill (`"OFFLINE MODE (FIXTURES)"`).
  - Active Case Banner showing case reference, suspect wallet, investigator name, and primary trace trigger button.
  - View Switcher Tabs: `[Graph & Attribution]`, `[Forensic Reports & Action Packet]`, `[Case Management]`.
- **Typed API Client:** `frontend/src/services/api.ts`
  - Typed Axios/Fetch service wrapping all backend endpoints with offline fallback resilience.

### 4.3 Verification & Test Cases

#### Execution Command
```bash
cd frontend
npm run build
```

#### Test Case 4.1: Production Asset Compilation
- **Execution:** Run `npm run build`.
- **Expected Output:** Vite builds TypeScript and CSS bundles without syntax errors or broken imports.
- **Pass Criteria:** Build exit code 0; bundle generated in `dist/`.

#### Test Case 4.2: Strict CSS Compliance Audit
- **Execution:** Search codebase for Tailwind directives (`@tailwind`, `tw-`, `className="flex flex-col..."`).
- **Pass Criteria:** Zero occurrences of Tailwind classes; all styling originates from `theme.css` or CSS modules.

#### Test Case 4.3: Active Case Switching
- **Execution:** In UI, switch active case from `CASE-2026-001A` to `CASE-2026-002B`.
- **Expected Output:** Banner updates suspect wallet address and target chain; triggers background API fetch for new case data.
- **Pass Criteria:** UI updates without page reload or state desynchronization.

#### Phase 4 Exit Gate
> [!IMPORTANT]
> Phase 4 is complete ONLY when `npm run build` succeeds cleanly and the UI renders without console errors.

---

## Phase 5: Interactive Cytoscape Fund-Flow Graph & Obfuscation Badging

### 5.1 Objective
Embed an interactive Cytoscape.js canvas rendering directed fund-flow graphs. Implement distinct entity node styling, transaction amount edge labels, and prominent visual badges at **Obfuscation Breakpoints**.

### 5.2 Deliverables
- **Interactive Graph Component:** `frontend/src/pages/InvestigationGraph.tsx`
  - Cytoscape container with zoom, pan, and viewport reset controls.
  - Directed graph layout (`breadthfirst` left-to-right hierarchical flow).
  - Node styling rules:
    * `SUSPECT`: Red glowing circle.
    * `INTERMEDIARY`: Neutral slate gray circle.
    * `VASP_DEPOSIT`: Golden amber circle.
    * `VASP_HOT`: Royal blue high-degree hub hexagon.
    * `MIXER`: Hazard magenta octagonal node.
    * `BRIDGE`: Cyan diamond node.
  - Obfuscation Breakpoint Badges: Render visual alert badge over nodes flagged as peel chains or rapid relays.
  - Node Selection Handler: Opens inspection drawer showing address details, balance, and transaction history.

### 5.3 Verification & Test Cases

#### Execution Command
```bash
# Verify frontend runs in dev mode
cd frontend && npm run dev
```

#### Test Case 5.1: Graph Canvas Initialization & Node Rendering
- **Input:** Case `CASE-2026-002B` graph payload (9 nodes, 8 edges).
- **Expected Output:**
  - Cytoscape canvas mounts in DOM.
  - Suspect wallet renders at Root (left) with red highlight.
  - Kraken Hot Wallet renders at Terminal (right) with blue hub styling.
- **Pass Criteria:** All 9 nodes and 8 edges visible and navigable.

#### Test Case 5.2: Obfuscation Breakpoint Badge Rendering
- **Input:** Case with detected rapid-relay breakpoint at Hop 2.
- **Expected Output:**
  - Hop 2 node displays alert badge (`⚠️ Breakpoint`).
  - Clicking the node displays flyout: *"Rapid Relay Obfuscation: 4 hops within 32 minutes"*.
- **Pass Criteria:** Breakpoint visually differentiates from standard intermediary hops.

#### Test Case 5.3: Graph Performance Under Stress
- **Input:** Graph payload with 50 nodes and 75 edges.
- **Expected Output:** Canvas renders with smooth 60fps pan/zoom interaction; layout calculation $< 300\text{ms}$.
- **Pass Criteria:** Zero browser thread blocking or unresponsive script warnings.

#### Phase 5 Exit Gate
> [!IMPORTANT]
> Phase 5 is complete ONLY when the graph renders all 3 demo cases smoothly with correct node coloring and visible Obfuscation Breakpoint badges.

---

## Phase 6: Explainable Attribution Card & Sensitivity Simulation UI

### 6.1 Objective
Construct the user-facing **Explainable Attribution Card**. Render quantitative factor contribution bars, the critical Operator vs. Beneficiary distinction banner, an interactive **Counterfactual Sensitivity** toggle, and one-click report and action packet modals.

### 6.2 Deliverables
- **Attribution Card Component:** `frontend/src/components/ExplainableCard.tsx`
  - Primary Attributed VASP header with Confidence Score Gauge (0–100%) and color band (High = Green, Medium = Amber, Low = Red).
  - **Operator vs. Beneficiary Distinction Banner**:
    * `Infrastructure Control: VASP-OPERATED INFRASTRUCTURE (Verified)`
    * `Beneficiary Identity: NOT ESTABLISHED (Requires Subpoena under Sec 91 CrPC)`
  - Quantitative Factor Progress Bars: Horizontal bars displaying points contribution (+30 pts Direct Sweep, +25 pts Hot Wallet, etc.).
  - **Interactive Counterfactual Sensitivity Toggle**: Switch simulating factor ablation; dynamically updates score and displays fragility warnings in real-time.
  - Quick Action Buttons: `[View Full Forensic Report]` and `[Generate Section 91 CrPC Notice]`.
- **Modals:**
  - `frontend/src/components/ReportModal.tsx`: Displays HTML forensic report with copyable SHA-256 seal.
  - `frontend/src/components/ActionPacketModal.tsx`: Displays Section 91 CrPC draft with 1-click clipboard copy.

### 6.3 Verification & Test Cases

#### Execution Command
```bash
# Verify UI interaction via browser or integration test
```

#### Test Case 6.1: Confidence Band & Color Gauge
- **Input:** Score $= 88.0\%$ $\to$ Gauge renders Green with label `"HIGH CONFIDENCE"`.
- **Input:** Score $= 62.0\%$ $\to$ Gauge renders Amber with label `"MEDIUM CONFIDENCE"`.
- **Input:** Score $= 35.0\%$ $\to$ Gauge renders Red with label `"LOW CONFIDENCE"`.
- **Pass Criteria:** Gauge visual state matches mathematical thresholds strictly.

#### Test Case 6.2: Interactive Counterfactual Sensitivity Toggle
- **Action:** User clicks toggle: *"Ablate Direct Sweep Factor (-30 pts)"*.
- **Expected UI Behavior:**
  - Confidence score drops dynamically from $88\%$ to $58\%$.
  - Gauge transitions from Green to Amber.
  - Warning appears: *"Attribution is fragile: dependent on terminal sweep proof"*.
- **Pass Criteria:** State update happens purely client-side or via sub-millisecond API call without reloading graph.

#### Test Case 6.3: Section 91 CrPC Action Packet Modal & Copy Action
- **Action:** User clicks `[Generate Section 91 CrPC Notice]`.
- **Expected UI Behavior:**
  - Modal opens displaying formatted statutory legal requisition.
  - Contains exact suspect address, terminal deposit address, and VASP entity name.
  - Clicking `[Copy Notice to Clipboard]` triggers navigator clipboard API and shows success toast.
- **Pass Criteria:** Clipboard text matches legal notice format exactly.

#### Phase 6 Exit Gate
> [!IMPORTANT]
> Phase 6 is complete ONLY when an investigator can select any case, run a multi-hop trace, view the fund-flow graph, inspect factor contributions, toggle sensitivity, export a tamper-proof forensic report, and copy a Section 91 CrPC notice in under 60 seconds without errors.
