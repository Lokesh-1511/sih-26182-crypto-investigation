# SIH 26182 – Automated Attribution of Unknown Cryptocurrency Wallets to Nearest VASPs

**Smart India Hackathon 2026 | Problem Statement 26182**  
**Core Identity:** Crypto Investigation Copilot — Evidence-Backed VASP Attribution  
**Team Structure:** 3 Core Developers (M1: Blockchain/Ingestion, M2: Graph/Attribution, M3: Platform/UI/Reports)

---

## 1. Problem
During cybercrime and financial fraud investigations involving cryptocurrency, law enforcement agencies face a critical obstacle: illicit funds are rapidly routed through obfuscated intermediary hops to centralized exchanges (VASPs) for fiat liquidation. Existing blockchain explorers simply dump hundreds of raw transactions, leaving investigators with an overwhelming manual tracing burden and no automated, evidence-backed attribution of the destination exchange infrastructure.

## 2. Solution
We built an **AI-Assisted Crypto Investigation Copilot** designed specifically for law enforcement and forensic analysts. Given an unknown suspect wallet, the system automatically validates the address, ingests and normalizes transaction flows, constructs a directed multi-hop graph (3–5 hops), resolves known entity clusters, flags obfuscation breakpoints, and attributes the fund flow to candidate Virtual Asset Service Providers (VASPs) with an **Explainable Attribution Score**.

## 3. Key Features
- **Multi-Chain Support**: Validates and normalizes Bitcoin (UTXO), Ethereum (Account/Tokens), and Tron transactions.
- **Multi-Hop Graph Intelligence**: Breadth-First Search traversal (3 to 5 hops) with automated dust suppression.
- **Evidence Drill-Down**: Every graph node and score factor links directly to verifiable on-chain transaction IDs.
- **Chronological Fund-Flow Timeline**: Ordered, filterable sequence of asset movements with millisecond precision.
- **Tamper-Evident Forensic Reports**: Automated PDF/HTML export containing case findings and SHA-256 evidence package hashes.

## 4. Winning Differentiators
1. **Explainable VASP Attribution Card ("WHY THIS VASP?")**: Shows exact factor contributions (+28 deposit match, +22 sweep pattern, +17 volume, etc.) rather than a black-box percentage.
2. **Operator vs Beneficiary Intelligence**: Strictly separates VASP-controlled infrastructure from customer identity, explicitly noting that beneficiary identity is **NOT ESTABLISHED** on-chain without lawful KYC disclosures.
3. **Counterfactual Attribution (Sensitivity Analysis)**: Demonstrates attribution robustness by recalculating confidence when major evidence factors are selectively removed.
4. **Fund-Flow Obfuscation Breakpoint Detection**: Automatically detects and highlights anomalous topological shifts (sudden fan-out, rapid hops, fragmentation, bridge interactions) on the graph.
5. **Lawful Action Packet Generator**: Automatically drafts review-ready legal requests (Section 91 CrPC / MLAT preservation notices) for authorized officer review.

## 5. Architecture
The system adopts a modular 3-tier architecture:
- **Presentation Layer**: React 18, TypeScript, Plain CSS / CSS Modules (Strictly No Tailwind), Cytoscape.js canvas.
- **API & Orchestration Layer**: FastAPI, Pydantic v2 schemas, SQLAlchemy ORM (SQLite / PostgreSQL).
- **Core Forensic Engines**: NetworkX Graph Engine, Multi-Factor Attribution Engine, Rule-Assisted AML Typology Classifier, BlockchainProvider Adapters.

## 6. Tech Stack
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy, NetworkX, ReportLab, pytest.
- **Frontend**: React 18, TypeScript, Vite, Cytoscape.js, Plain CSS / CSS Modules.
- **Data & Ingestion**: Pluggable `BlockchainProvider` (Offline Cached Fixtures & Live APIs).
- **DevOps**: Docker, Docker Compose, Makefile.

## 7. Repository Structure
```
sih-26182-crypto-investigation/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Makefile
├── docs/                      # 16 detailed specification documents
├── backend/                   # FastAPI backend, models, schemas, and engines
│   ├── app/
│   │   ├── api/               # REST API routers
│   │   ├── blockchain/        # Ingestion, validation, normalization, adapters
│   │   ├── graph/             # NetworkX builder, traversal, filters
│   │   ├── entities/          # Knowledge base and resolver
│   │   ├── attribution/       # Multi-factor scorer, counterfactual, explainability
│   │   ├── risk/              # Obfuscation breakpoints, AML typologies
│   │   ├── evidence/          # Evidence store and audit logging
│   │   └── reports/           # Forensic PDF and Action Packet generators
├── frontend/                  # React + TypeScript + Plain CSS forensic console
│   └── src/pages/             # Dashboard, Graph, Attribution, Risk, Timeline, Reports
├── data/
│   ├── demo/                  # Controlled offline cases (A, B, C) and ground truth
│   └── knowledge_base/        # VASP labels, deposit wallets, hot wallets, bridges, mixers
├── scripts/                   # Seeding, case creation, and validation utilities
└── tests/                     # Unit, integration, graph, and attribution test suites
```

## 8. Installation
```bash
# 1. Clone repository
git clone https://github.com/sih-2026/sih-26182-crypto-investigation.git
cd sih-26182-crypto-investigation

# 2. Configure environment
cp .env.example .env

# 3. Setup Python virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. Install backend dependencies
pip install -r backend/requirements.txt

# 5. Install frontend dependencies
cd frontend && npm install && cd ..
```

## 9. Environment Variables
Defined in `.env.example`:
- `DATA_SOURCE_MODE`: Set to `OFFLINE_FIXTURE` (default) for hackathon demo or `LIVE_API`.
- `DATABASE_URL`: `sqlite:///./crypto_investigation.db` (or PostgreSQL connection string).
- `SECRET_KEY`: Security signing key.
- `ETHERSCAN_API_KEY`, `BLOCKSTREAM_API_KEY`, `TRONGRID_API_KEY`: Optional live provider keys.

## 10. Database
Initializes SQLite automatically on first launch or run:
```bash
python scripts/reset_database.py
python scripts/seed_demo_data.py
```

## 11. Running Backend
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation available at: `http://localhost:8000/docs`

## 12. Running Frontend
```bash
cd frontend
npm run dev
```
Access the investigator console at: `http://localhost:5173`

## 13. Demo Mode (100% Offline)
The application defaults to `DATA_SOURCE_MODE=OFFLINE_FIXTURE`. It requires zero internet connectivity and runs seamlessly from pre-cached test cases:
- **Case A**: Direct suspect to known deposit wallet sweep (BTC).
- **Case B**: 4-hop layered fraud flow with obfuscation breakpoint (ETH).
- **Case C**: Cross-chain bridge transition (TRX/ETH).

## 14. API Overview
- `POST /api/cases`: Create case.
- `POST /api/cases/{id}/trace`: Initiate multi-hop graph trace.
- `GET /api/cases/{id}/graph`: Fetch Cytoscape graph payload.
- `GET /api/cases/{id}/attribution`: Fetch candidate VASP rankings and confidence.
- `GET /api/cases/{id}/attribution/explanation`: Fetch Explainable Attribution Card.
- `GET /api/cases/{id}/attribution/counterfactual`: Recompute scores under factor ablation.
- `GET /api/cases/{id}/risk`: Fetch detected obfuscation breakpoints and typologies.
- `POST /api/cases/{id}/report`: Export forensic investigation report.
- `POST /api/cases/{id}/action-packet`: Generate Section 91 CrPC legal draft.

## 15. Graph Intelligence
Powered by NetworkX `MultiDiGraph`. Supports 3–5 hop BFS forward traversal, cycle handling, micro-dust filtering ($< 0.0001\text{ BTC}$), and Dijkstra-based strongest-value path extraction.

## 16. VASP Attribution
Computes a transparent score $S = \sum w_i F_i - P_{\text{uncertainty}}$ factoring in verified deposit matches, consolidation sweeps into hot wallets, graph proximity, flow volume ratio, and temporal consistency.

## 17. Explainability
Rather than presenting an uninterpretable AI score, the system renders the **Explainable Attribution Card** displaying exact point additions (+28, +22, etc.) and direct links to transaction hashes.

## 18. Risk Analysis
Rule-assisted AML classification identifying:
- Rapid multi-hop layering.
- Fan-out structuring (smurfing).
- Mixer and bridge contract exposure.
- Peel chain asset consolidation.

## 19. Reports
Generates court-ready PDF/HTML reports with case summaries, visual graph renderings, transaction tables, and SHA-256 evidence package digests.

## 20. Validation
Automated benchmark test suite:
```bash
pytest tests/ -v
```
Evaluates Top-1 attribution accuracy, traversal speed, and obfuscation detection against ground truth.

## 21. Security
- Read-only intelligence pipeline (no wallet tampering, no private keys).
- No automated legal dispatch without human officer authorization.
- Strict input validation and SHA-256 evidence hashing.

## 22. Limitations
- Attribution is probabilistic and heuristic.
- Public blockchain data cannot verify natural person KYC without lawful exchange subpoena.
- UTXO CoinJoin mixes introduce analytical uncertainty penalties.

## 23. Team Structure
- **Member 1**: Blockchain adapters, multi-chain validation, transaction normalization, demo datasets.
- **Member 2**: Graph builder, traversal, VASP knowledge base, attribution engine, counterfactual analysis.
- **Member 3**: FastAPI backend, database models, risk engine, React console, forensic reports, demo integration.

## 24. Git Workflow
- `main`: Tagged production releases.
- `develop`: Staging and continuous integration.
- `feature/*`: Granular feature branches per developer.

## 25. 15-Day Roadmap
Structured sprint progressing from core schemas and validation (Days 1–3), graph & attribution engines (Days 4–7), explainability & breakpoints (Days 8–10), frontend integration & reports (Days 11–13), to final rehearsal and freeze (Days 14–15).

## 26. SIH Demo
Execute the full offline demo in one command:
```bash
docker compose up --build
```
Open `http://localhost:5173`, select Case B, click "Start Trace", view the Obfuscation Breakpoint, open the Explainable Attribution Card, simulate Counterfactual Sensitivity, and export the Lawful Action Packet in under 3 minutes.
