# Workplan: Machine Learning, Graph & Attribution Track (Member 2)

**Project:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine (SIH 26182)  
**Role:** Senior Blockchain Intelligence Engineer, Graph & ML Specialist (Member 2)  
**Assigned Git Branch:** `feature/member2-graph-attribution`  
**Target Delivery Window:** 15-Day SIH Accelerated Sprint  
**Document Version:** 1.0.0

---

## 1. Domain Overview & Purpose

As the **Graph Intelligence, Machine Learning & Attribution Engineer (Member 2)**, you own the intellectual core of the platform: answering the central investigative question:

> **"Given an unknown suspect wallet, what VASP/exchange infrastructure is it most closely associated with, WHY do we believe that, WHAT evidence supports the conclusion, and WHERE are the uncertainties?"**

You transform normalized transfer streams into directed multigraphs, resolve addresses against curated knowledge bases, compute explainable attribution confidence scores, detect structural obfuscation breakpoints, simulate counterfactual evidence ablations, and maintain the critical forensic distinction between **VASP-controlled infrastructure** and **end-user beneficiary identity**.

---

## 2. Codebase Ownership & Directory Boundary

You have strict ownership and write permissions over the following modules:

```
backend/app/
├── graph/
│   ├── builder.py               # NetworkX MultiDiGraph construction
│   ├── traversal.py             # 3 to 5 hop BFS traversal with cycle detection
│   ├── filters.py               # Dust suppression & noise control filters
│   └── path_analysis.py         # Shortest & strongest-value Dijkstra path algorithms
├── entities/
│   ├── knowledge_base.py        # Knowledge base query engine & search
│   └── resolver.py              # Entity categorization (Hot, Deposit, Mixer, Bridge)
├── attribution/
│   ├── scorer.py                # Multi-factor quantitative scoring formula
│   ├── counterfactual.py        # Sensitivity analysis & evidence factor ablation
│   └── explainability.py        # Points contribution breakdown & evidence linking
└── risk/
    ├── breakpoint.py            # Obfuscation Breakpoint detector (fan-out, rapid hops)
    ├── typologies.py            # Rule-assisted AML typology classifier (TYP-01 to 05)
    └── anomaly.py               # Baseline statistical & Isolation Forest anomaly scoring

data/knowledge_base/             # Curated entity intelligence fixtures
├── vasp_labels.json             # Master exchange directory
├── deposit_wallets.json         # Known custodial deposit sweep addresses
├── hot_wallets.json             # Verified omnibus pooling hot wallets
├── bridges.json                 # Cross-chain bridge router contracts
└── mixers.json                  # OFAC-sanctioned mixers & privacy pools

tests/unit/
├── test_graph.py                # Unit tests for graph construction & traversal
└── test_attribution.py          # Unit tests for scoring & counterfactual sensitivity
```

---

## 3. Detailed Work Breakdown & Deliverables

### Milestone 1: Directed Fund-Flow Graph Engine
**Target Files:** `backend/app/graph/builder.py`, `traversal.py`, `filters.py`, `path_analysis.py`  
**Dependencies:** `backend/app/schemas/graph.py`, `backend/app/schemas/transaction.py`

#### Detailed Tasks:
1. **NetworkX Directed Multigraph Builder (`builder.py`)**:
   - Construct a `networkx.MultiDiGraph` where vertices represent cryptocurrency addresses and directed edges represent value transfers.
   - Node metadata: `address`, `chain`, `node_type` (`SUSPECT`, `INTERMEDIARY`, `VASP_DEPOSIT`, `VASP_HOT`, `MIXER`, `BRIDGE`), `entity_name`, `confidence`.
   - Edge metadata: `tx_id`, `asset`, `amount`, `timestamp`, `hop_distance`, `edge_type` (`TRANSFER`, `SWEEP`, `BRIDGE_ROUTE`).
2. **Breadth-First Traversal Engine (`traversal.py`)**:
   - Traverse forward from the suspect root address across configurable hop depth (3 to 5 hops).
   - Implement visited sets to gracefully terminate cyclical transfers (e.g. A $\to$ B $\to$ C $\to$ A).
   - Extract hop layers and list of reachable paths.
3. **Transparent Noise Control & Dust Suppression (`filters.py`)**:
   - Prune micro-dust transactions below threshold ($< 0.0001\text{ BTC}$ or $< 1.0\text{ USDT}$) unless dust represents $\ge 50\%$ of outbound volume.
   - High-degree hub aggregation: Collapse high-frequency hot wallet hubs into single cluster nodes to prevent UI canvas explosion.
4. **Forensic Path Analysis (`path_analysis.py`)**:
   - **Shortest Path**: Minimum-hop route linking suspect wallet to any identified exchange node.
   - **Strongest-Value Path**: Dijkstra shortest path with inverse amount edge weights ($w = \frac{1}{\text{amount}}$) highlighting the primary fund-laundering corridor.

---

### Milestone 2: VASP Entity Resolution & Knowledge Base
**Target Files:** `backend/app/entities/knowledge_base.py`, `resolver.py`, `data/knowledge_base/`

#### Detailed Tasks:
1. **Local Knowledge Base Engine (`knowledge_base.py`)**:
   - Index verified exchange clusters: Binance, Kraken, Coinbase, WazirX, OKX.
   - Ensure case-insensitive address lookup (`0x...` lowercase normalized).
   - Provide sub-string search API for entities and address prefixes.
2. **Entity Classification Hierarchy (`resolver.py`)**:
   - Classify addresses into:
     * `VASP_DEPOSIT`: Custodial address that sweeps funds forward.
     * `VASP_HOT`: Omnibus pooling hot wallet.
     * `MIXER`: Privacy pool / tumbler (Tornado.Cash).
     * `BRIDGE`: Multi-chain gateway contract (Hop, Multichain).
     * `INTERMEDIARY`: Unlabeled transit / layering address.
   - **Ethical Rule**: Never invent fictitious labels; mark all synthetic demo fixtures with `label_source: "CONTROLLED_DEMO"`.

---

### Milestone 3: Core Explainable VASP Attribution Engine
**Target File:** `backend/app/attribution/scorer.py`  
**Dependencies:** `backend/app/schemas/attribution.py`

#### Detailed Tasks:
1. **Mathematical Scoring Formulation**:
   $$S = \min\left(100, \max\left(0, \sum_{i=1}^{5} w_i F_i - P_{\text{penalties}}\right)\right)$$
2. **Configurable Evidence Factor Weights ($F_i$)**:
   - **$F_{\text{entity}}$ (Known Deposit Match)**: $+30\text{ pts}$ if destination matches verified VASP deposit infrastructure.
   - **$F_{\text{sweep}}$ (Consolidation Sweep)**: $+25\text{ pts}$ if address automatically sweeps into VASP omnibus hot wallet.
   - **$F_{\text{proximity}}$ (Graph Proximity)**: $+20\text{ pts}$ scaled inversely with hop distance ($\text{pts} = 20 - (\text{hops} \times 3)$).
   - **$F_{\text{flow}}$ (Flow Volume Strength)**: $+15\text{ pts}$ scaled by proportion of suspect funds terminating at this exchange.
   - **$F_{\text{temporal}}$ (Temporal Consistency)**: $+10\text{ pts}$ for sequential forward timestamps without retrospective anomalies.
3. **Uncertainty Penalties ($P_{\text{penalties}}$)**:
   - Mixer interaction: $-30\text{ pts}$.
   - Cross-chain bridge hop: $-15\text{ pts}$.
   - Complex fan-out layering ($\ge 8\text{ branches}$): $-10\text{ pts}$.
4. **Calibrated Confidence Bands**:
   - $\text{HIGH}: S \ge 75\%$ | $\text{MEDIUM}: 50\% \le S < 75\%$ | $\text{LOW}: S < 50\%$.

---

### Milestone 4: Four Signature Differentiation Features

#### 1. Signature Feature #1: Explainable Attribution Card
**Target File:** `backend/app/attribution/scorer.py`
- Rather than returning an opaque percentage, return an array of `EvidenceFactor` objects.
- Each factor contains: `factor_name`, `contribution_points`, `factor_type` (`POSITIVE`/`PENALTY`), human-readable `description`, and `supporting_tx_ids`.
- Every point is traceable directly to an immutable on-chain transaction hash.

#### 2. Signature Feature #2: Operator vs Beneficiary Intelligence
**Target File:** `backend/app/schemas/attribution.py`, `backend/app/attribution/scorer.py`
- Rigorously separate:
  * **Operator Attribution**: `VASP-Controlled Infrastructure` (High Confidence).
  * **Beneficiary Identity**: Strictly recorded as **`NOT ESTABLISHED`**.
- Embed statutory disclaimer: *"Available evidence establishes association with VASP-controlled infrastructure but does NOT establish the identity of the end beneficiary without off-chain KYC disclosures."*

#### 3. Signature Feature #3: Counterfactual Attribution (Sensitivity Analysis)
**Target File:** `backend/app/attribution/counterfactual.py`
- Implement `CounterfactualEngine.simulate_ablation(candidate)`:
  * Simulate score recalculation when specific factors are removed (e.g. deposit match removed $\to$ score drops from $88\%$ to $58\%$).
  * Compute `score_delta` and classify conclusion robustness:
    - $\Delta S \le 15\text{ pts}$: `ROBUST`
    - $15\text{ pts} < \Delta S \le 28\text{ pts}$: `MODERATE_DEPENDENCY`
    - $\Delta S > 28\text{ pts}$: `HIGH_DEPENDENCY`

#### 4. Signature Feature #4: Obfuscation Breakpoint Detection
**Target File:** `backend/app/risk/breakpoint.py`
- Algorithmically identify nodes where transaction behavior changes abruptly:
  * Sudden 1-to-$N$ Fan-out ($\text{out-degree} \ge 3$ within short time window).
  * Direct interaction with privacy mixers or decentralized bridges.
- Return structured `ObfuscationBreakpoint` records with analytical justification and supporting transaction hashes.

---

### Milestone 5: AML Typologies & Baseline Machine Learning
**Target Files:** `backend/app/risk/typologies.py`, `backend/app/risk/anomaly.py`

#### Detailed Tasks:
1. **Rule-Assisted Typology Classifier (`typologies.py`)**:
   - `TYP-01`: Rapid Layering (Multi-hop relay $\ge 3$ hops).
   - `TYP-02`: Fan-Out Structuring (Smurfing into multiple parallel wallets).
   - `TYP-03`: Peel Chain Accumulation.
   - `TYP-04`: Privacy Mixer Exposure (Critical severity).
   - `TYP-05`: Cross-Chain Liquidity Hop (Medium severity).
2. **Baseline ML Anomaly Detection (`anomaly.py`)**:
   - Implement an unsupervised `IsolationForest` or statistical z-score outlier model on extracted transfer feature vectors (transfer frequency, value entropy, and holding time).

---

## 4. 15-Day Day-by-Day Execution Plan

| Day | Primary Focus | Daily Deliverable |
| :---: | :--- | :--- |
| **Day 1** | Scaffolding | Setup `feature/member2-graph-attribution`; establish graph and attribution module structures. |
| **Day 2** | Knowledge Base | Populate `data/knowledge_base/` JSON files with verified VASP hot wallets and deposit addresses. |
| **Day 3** | Graph Construction | Implement `GraphBuilder` converting normalized transfers into NetworkX `MultiDiGraph`. |
| **Day 4** | Graph Traversal | Implement `GraphTraversalEngine` with BFS, hop limiters (3 to 5 hops), and cycle protection. |
| **Day 5** | Noise Filters | Build `GraphNoiseFilter` with configurable dust threshold suppression. |
| **Day 6** | Path Analysis | Implement shortest path and Dijkstra strongest-value path algorithms. |
| **Day 7** | Attribution Scoring | Implement multi-factor scoring formula ($w_1..w_5$) in `scorer.py`. |
| **Day 8** | Explainable Card | Implement additive factor point breakdown and link each factor to supporting transaction IDs. |
| **Day 9** | Operator / Beneficiary| Enforce strict separation of infrastructure attribution and customer identity. |
| **Day 10** | Counterfactual Analysis| Implement `CounterfactualEngine` sensitivity simulation and robustness classification. |
| **Day 11** | Breakpoint Detection | Implement `ObfuscationBreakpointDetector` flagging fan-out hubs and rapid hopping. |
| **Day 12** | AML Typology Rules | Implement `RiskTypologyEngine` detecting TYP-01 to TYP-05 patterns. |
| **Day 13** | Benchmark Validation | Execute `scripts/validate_demo_case.py` ensuring 100% Top-1 accuracy across Cases A, B, C. |
| **Day 14** | Edge Case Tuning | Fine-tune weight penalties for mixer/bridge interactions and cyclic flows. |
| **Day 15** | Code Freeze & Merge | Final unit tests pass (`pytest tests/unit/test_attribution.py`); merge into `develop`. |

---

## 5. Verification Commands for Member 2

Run these commands locally to verify your deliverables:

```powershell
# 1. Run unit tests for Graph Engine
python -m pytest tests/unit/test_graph.py -v

# 2. Run unit tests for Attribution & Counterfactual Sensitivity
python -m pytest tests/unit/test_attribution.py -v

# 3. Run ground-truth benchmark validation script
python scripts/validate_demo_case.py

# 4. Verify vertical slice execution
python scripts/create_demo_case.py
```
