# Machine Learning & Graph Intelligence Track: Phase-by-Phase Technical Specification

**Project:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine (SIH 26182)  
**Role:** Senior Blockchain Intelligence Engineer, Graph & ML Specialist (Member 2)  
**Assigned Git Branch:** `feature/member2-graph-attribution`  
**Document Version:** 2.0.0 (Phase-Gated Architecture)

---

## Architecture & Responsibilities Overview

As the **Graph Intelligence, Machine Learning & Attribution Engineer (Member 2)**, you build the analytical and cognitive engine of the platform. Your system answers the core investigative question:

> **"Given an unknown suspect cryptocurrency address, what VASP/exchange infrastructure is it most closely associated with, WHY is it attributed, WHAT evidence supports the conclusion, and WHERE are the uncertainties?"**

### Strict Forensic Principles
1. **Explainable AI Over Black Boxes**: Attribution confidence scores are computed via an audited, deterministic multi-factor model with explicit points contribution breakdown (+30 pts direct sweep, +25 pts hot wallet, etc.).
2. **Counterfactual Sensitivity**: Every attribution candidate must expose counterfactual ablation results, demonstrating how confidence shifts if individual evidence factors are removed.
3. **Operator vs. Beneficiary Distinction**:
   - **Infrastructure Attribution**: VASP-controlled deposit address or hot wallet pool.
   - **Beneficiary Identity**: Always stamped as **`NOT ESTABLISHED`** (requires off-chain KYC disclosure).
4. **No Timeline-Based Milestones**: Advancement to the next phase occurs strictly when all defined test cases pass.

---

## Phase 1: Directed Fund-Flow Multigraph Engine & Noise Filtering

### 1.1 Objective
Transform raw normalized transfer lists into an in-memory directed multigraph (`networkx.MultiDiGraph`), execute 3 to 5 hop breadth-first traversals with cycle termination, filter irrelevant micro-dust, and compute shortest and strongest-value forensic paths.

### 1.2 Deliverables
- **Core Modules:** `backend/app/graph/`
  - `builder.py`: Constructs `networkx.MultiDiGraph` with typed nodes (`SUSPECT`, `INTERMEDIARY`, `VASP_DEPOSIT`, `VASP_HOT`, `MIXER`, `BRIDGE`) and weighted edges.
  - `traversal.py`: Breadth-first forward tracing up to configurable depth (3 to 5 hops) with visited set cycle prevention.
  - `filters.py`: Configurable dust suppression filter (pruning transfers below $0.0001\text{ BTC}$ or $1.0\text{ USDT}$ unless dust constitutes $\ge 50\%$ outbound volume).
  - `path_analysis.py`: Shortest topological hop path and Dijkstra strongest-value path (edge weight $w = \frac{1}{\text{amount}}$).
- **Unit Test Suite:** `tests/unit/test_graph.py`

### 1.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_graph.py -v
```

#### Test Case 1.1: Graph Construction & Node Typing
- **Input:** 5 normalized transfers: Root $A \to B \to C \to D \to E$.
- **Expected Output:**
  - Graph contains 5 nodes, 4 edges.
  - Node $A$ typed as `SUSPECT`.
  - Nodes $B, C, D$ typed as `INTERMEDIARY`.
  - Node $E$ typed according to resolution.
- **Pass Criteria:** `MultiDiGraph.number_of_nodes() == 5`, `MultiDiGraph.number_of_edges() == 4`.

#### Test Case 1.2: Circular Loop Traversal Termination
- **Input:** Transfer chain with loop: $A \to B \to C \to B \to D$.
- **Expected Output:**
  - Traversal completes without recursion overflow.
  - Loop back-edge detected and tagged: `cycle_detected = True`.
  - Node $D$ successfully reached and recorded in hop layer 4.
- **Pass Criteria:** Traversal completes in $< 20\text{ms}$.

#### Test Case 1.3: Dust Suppression Filter
- **Input:** Node $A$ sends:
  - Tx 1: $10.0\text{ ETH}$ to Node $B$ (Substantive transfer).
  - Tx 2: $0.000001\text{ ETH}$ to Node $C$ (Airdrop/dust).
  - Tx 3: $0.000002\text{ ETH}$ to Node $D$ (Airdrop/dust).
- **Expected Output:**
  - Filtered graph preserves Node $B$.
  - Micro-dust nodes $C$ and $D$ pruned from primary visualization.
- **Pass Criteria:** Nodes $C$ and $D$ excluded; substantive flow preserved without value loss on Node $B$.

#### Test Case 1.4: Strongest-Value Dijkstra Path Finding
- **Input:** Root $A$ splits funds:
  - Path 1: $A \to X \to \text{VASP}$ (Transfer amount: $0.1\text{ ETH}$).
  - Path 2: $A \to Y \to \text{VASP}$ (Transfer amount: $9.9\text{ ETH}$).
- **Expected Output:** Shortest path identifies both as 2 hops; Strongest-Value path explicitly selects Path 2 ($A \to Y \to \text{VASP}$) as the primary laundering corridor.
- **Pass Criteria:** Dijkstra inverse-weight path algorithm selects Path 2.

#### Phase 1 Exit Gate
> [!IMPORTANT]
> Phase 1 is complete ONLY when `test_graph.py` passes all graph construction, traversal, dust pruning, and pathfinding tests with zero failures.

---

## Phase 2: Curated VASP Knowledge Base & Entity Resolution

### 2.1 Objective
Build an offline, high-speed entity resolution engine supported by verified knowledge base fixtures. Classify addresses into custodial deposit addresses, omnibus hot wallet pools, cross-chain bridges, and sanctioned mixers.

### 2.2 Deliverables
- **Intelligence Fixtures:** `data/knowledge_base/`
  - `vasp_labels.json`: Master directory of major exchanges (Binance, Kraken, Coinbase, WazirX, OKX).
  - `deposit_wallets.json`: Verified custodial deposit sweep addresses.
  - `hot_wallets.json`: High-degree exchange omnibus hot wallets.
  - `bridges.json`: Cross-chain bridge contracts (Hop, Multichain, Stargate).
  - `mixers.json`: OFAC-sanctioned privacy mixers (Tornado Cash).
- **Core Modules:** `backend/app/entities/`
  - `knowledge_base.py`: In-memory lookup index with case-insensitive address hashing.
  - `resolver.py`: Class `EntityResolver` providing `resolve(address: str, chain: Chain) -> ResolvedEntity`.

### 2.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_entities.py -v
```

#### Test Case 2.1: Verified Hot Wallet Lookup
- **Input:** Address `0x28C6c06298d514Db089934071355E5743bf21d60` (Binance 14 Hot Wallet).
- **Expected Output:**
  - `entity_name = "Binance"`
  - `entity_type = "VASP_HOT"`
  - `confidence = 1.0`
  - `is_verified = True`
- **Pass Criteria:** Exact match in $< 2\text{ms}$.

#### Test Case 2.2: Case-Insensitive Checksum Normalization
- **Input:** Mixed-case `0x28c6c06298D514dB089934071355e5743bf21D60`.
- **Expected Output:** Successfully matches `Binance` hot wallet regardless of letter case variation.
- **Pass Criteria:** Hashing/lookup converts addresses to lowercase before index query.

#### Test Case 2.3: Unlabelled Transit Address Fallback
- **Input:** Unknown intermediate wallet `0x71c83e20e8f468a3e282241f8c936f4521487439`.
- **Expected Output:**
  - `entity_name = "Unlabeled Address"`
  - `entity_type = "INTERMEDIARY"`
  - `confidence = 0.0`
- **Pass Criteria:** Returns safe default entity without raising key errors.

#### Phase 2 Exit Gate
> [!IMPORTANT]
> Phase 2 is complete ONLY when the resolver correctly categorizes 100% of addresses in the curated test knowledge base with zero false positives.

---

## Phase 3: Multi-Factor Quantitative Attribution Scoring Engine

### 3.1 Objective
Implement the multi-factor VASP attribution algorithm. Score candidate VASPs on a transparent $+100$ point scale based on topological proximity, direct deposit sweeps, omnibus pooling interaction, temporal velocity, and volume concentration.

### 3.2 Deliverables
- **Core Modules:** `backend/app/attribution/`
  - `scorer.py`: Class `AttributionScorer` implementing the deterministic scoring formula:
    $$\text{Score} = w_{\text{deposit}} + w_{\text{hot}} + w_{\text{proximity}} + w_{\text{velocity}} + w_{\text{volume}} \le 100$$
    * Factor 1: Direct Deposit Sweep ($+30\text{ pts}$)
    * Factor 2: Hot Wallet Sweep ($+25\text{ pts}$)
    * Factor 3: Topological Proximity ($15 \times \frac{1}{\text{hops}}\text{ pts}$)
    * Factor 4: Temporal Velocity ($+10\text{ pts}$ if relay $< 2\text{ hours}$)
    * Factor 5: Volume Concentration ($+10\text{ pts}$ if $\ge 75\%$ fund volume reached VASP)
  - `explainability.py`: Builds itemized point contribution justifications and forensic evidence links.
- **Unit Test Suite:** `tests/unit/test_attribution.py`

### 3.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_attribution.py -v
```

#### Test Case 3.1: High Confidence Direct Deposit Attribution
- **Input:** Suspect transfers $10\text{ ETH}$ directly to a known Kraken deposit address, which sweeps funds to Kraken Hot Wallet within 45 minutes.
- **Expected Output:**
  - `top_candidate = "Kraken"`
  - `confidence_score >= 85.0`
  - `confidence_band = "HIGH"`
  - Contributing factors: Direct Deposit (+30), Hot Sweep (+25), Proximity (+15), Velocity (+10), Volume (+10).
- **Pass Criteria:** Score $\ge 85$ and classified as `HIGH`.

#### Test Case 3.2: Low Confidence Diffused Multi-Hop Flow
- **Input:** Suspect transfers split across 5 intermediary hops with $10\%$ volume reaching Binance deposit wallet after 14 days.
- **Expected Output:**
  - `top_candidate = "Binance"`
  - `confidence_score < 50.0`
  - `confidence_band = "LOW"`
  - Warning attached: *"Attribution weak: high hop distance and low volume concentration"*.
- **Pass Criteria:** Score $< 50$ and classified as `LOW`.

#### Test Case 3.3: Strict Beneficiary Guardrail Verification
- **Input:** Any attribution evaluation output.
- **Verification:** Inspect `candidate.beneficiary_identity`.
- **Pass Criteria:** Field MUST be strictly set to `"NOT ESTABLISHED"` and flagged with disclaimer: *"Requires KYC subpoena under Sec 91 CrPC"*.

#### Phase 3 Exit Gate
> [!IMPORTANT]
> Phase 3 is complete ONLY when `test_attribution.py` passes and the scoring formula produces 100% deterministic, mathematically verifiable point totals.

---

## Phase 4: Counterfactual Sensitivity Analysis Engine

### 4.1 Objective
Implement an algorithmic sensitivity simulation that executes systematic factor ablation ("What-if" analysis). Re-score candidate VASPs when individual evidence factors are excluded to compute the **Fragility Index** and identify single-point-of-failure evidence.

### 4.2 Deliverables
- **Core Module:** `backend/app/attribution/counterfactual.py`
  - Class `CounterfactualAnalyzer`:
    - `simulate_factor_ablation(candidate: VASPAttributionCandidate, ablate_factors: List[str]) -> CounterfactualResult`
    - `compute_fragility_index(candidate: VASPAttributionCandidate) -> float`
    - `generate_sensitivity_matrix(candidate: VASPAttributionCandidate) -> List[Dict[str, Any]]`

### 4.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_attribution.py -k "counterfactual" -v
```

#### Test Case 4.1: Single Factor Ablation (Direct Sweep Removal)
- **Input:** High-confidence Kraken candidate (Base Score: $88\%$). Ablate factor: `DIRECT_DEPOSIT_SWEEP` (Weight: 30 pts).
- **Expected Output:**
  - `ablated_score = 58.0`
  - `delta = -30.0`
  - `new_confidence_band = "MEDIUM"`
  - `fragility_assessment = "MODERATE"`
- **Pass Criteria:** Delta exactly matches factor point weight; confidence band shifts dynamically.

#### Test Case 4.2: Volume Concentration Ablation
- **Input:** High-confidence Binance candidate (Base Score: $85\%$). Ablate factor: `VOLUME_CONCENTRATION` (Weight: 10 pts).
- **Expected Output:**
  - `ablated_score = 75.0`
  - `delta = -10.0`
  - `new_confidence_band = "MEDIUM"`
- **Pass Criteria:** Score updates without affecting remaining topological factor weights.

#### Phase 4 Exit Gate
> [!IMPORTANT]
> Phase 4 is complete ONLY when the sensitivity matrix accurately recalculates score deltas for all 5 evidence factors and correctly alerts when an attribution is fragile.

---

## Phase 5: Obfuscation Breakpoint Detector & AML Typologies

### 5.1 Objective
Detect intentional fund-obfuscation techniques on the directed graph, flag critical **Obfuscation Breakpoints** (the exact hop where fund tracing becomes difficult), and classify patterns into standard AML typologies (TYP-01 to TYP-05).

### 5.2 Deliverables
- **Core Modules:** `backend/app/risk/`
  - `breakpoint.py`: Detects:
    * **Peel Chains**: Continuous 90/10 value splitting across single-use addresses.
    * **Rapid Relays**: Transfer hops occurring within $< 15\text{ minutes}$.
    * **High Fan-Out / Fan-In**: Value splitting across $> 5$ addresses and reconverging.
  - `typologies.py`: Rule-assisted classifier:
    * `TYP-01`: Direct Custodial Deposit
    * `TYP-02`: Layered Multi-Hop Transit
    * `TYP-03`: Peel Chain Structuring
    * `TYP-04`: Privacy Mixer Obfuscation (Tornado Cash)
    * `TYP-05`: Cross-Chain Bridge Hopping
  - `anomaly.py`: Statistical deviation and Isolation Forest velocity scoring.
- **Validation Script:** `scripts/validate_demo_case.py`

### 5.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_risk.py -v
```

#### Test Case 5.1: Peel Chain Structuring Detection (TYP-03)
- **Input:** Transaction sequence where address $A$ sends $9.5\text{ ETH}$ to change address $A'$ and $0.5\text{ ETH}$ to address $B$, repeated 3 times.
- **Expected Output:**
  - Flagged Typology: `TYP-03_PEEL_CHAIN`
  - Breakpoint identified: Address $A'$ flagged with `breakpoint_type = "PEEL_CHAIN_STEP"`
  - Risk points added: $+25$
- **Pass Criteria:** Algorithm flags peel chain with $> 80\%$ confidence.

#### Test Case 5.2: Privacy Mixer Interaction Detection (TYP-04)
- **Input:** Funds routed directly into Tornado Cash 10 ETH pool contract.
- **Expected Output:**
  - Flagged Typology: `TYP-04_MIXER_OBFUSCATION`
  - Critical Breakpoint: Node tagged with `breakpoint_type = "MIXER_INGRESS"`
  - Tracing alert: *"On-chain trail severed at mixer contract. Requires off-chain relayer subpoenas."*
- **Pass Criteria:** AML risk level escalated to `CRITICAL`.

#### Test Case 5.3: End-to-End Demo Case Benchmark Validation
- **Execution:** `python scripts/validate_demo_case.py`
- **Pass Criteria:**
  - Case A: Detects `TYP-01_DIRECT_DEPOSIT` (Binance Top-1).
  - Case B: Detects `TYP-02_LAYERED_TRANSIT` with Breakpoint at Hop 2 (Kraken Top-1).
  - Case C: Detects `TYP-03_PEEL_CHAIN` and `TYP-05_BRIDGE` (Binance Top-1).
  - All 3 benchmark cases achieve $100\%$ Top-1 accuracy.

#### Phase 5 Exit Gate
> [!IMPORTANT]
> Phase 5 is complete ONLY when `scripts/validate_demo_case.py` passes 100% across Case A, Case B, and Case C with all expected breakpoints and typologies identified.
