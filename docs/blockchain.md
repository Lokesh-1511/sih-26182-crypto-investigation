# Blockchain Engineering Track: Phase-by-Phase Technical Specification

**Project:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine (SIH 26182)  
**Role:** Blockchain Data Engineer & Protocol Specialist (Member 1)  
**Assigned Git Branch:** `feature/member1-blockchain`  
**Document Version:** 2.0.0 (Phase-Gated Architecture)

---

## Architecture & Responsibilities Overview

As the **Blockchain Data Engineer (Member 1)**, you are responsible for the ingestion, cryptographic validation, and data normalization foundation of the platform. You ensure that every cryptocurrency address fed into the system is mathematically valid, fetch on-chain transaction histories across heterogeneous protocols (UTXO and Account-based), and normalize raw transfers into a lossless schema for downstream graph traversal and attribution scoring.

### Strict Engineering Rules
1. **Zero Hallucinated Proofs**: Raw transaction identifiers, block numbers, amounts, and timestamps must reflect authentic on-chain states or verified test fixtures.
2. **Dual-Mode Operation**:
   - **Mode 1 (Offline Cached Fixtures)**: Zero internet connection required; responses must return in $< 50\text{ms}$ using indexed local JSON.
   - **Mode 2 (Live API Connectors)**: Graceful degradation, connection timeout safeguards, and rate-limiting fallbacks.
3. **No Timeline-Based Milestones**: Advancement from one phase to the next is strictly gated by running and passing the defined automated test cases.

---

## Phase 1: Cryptographic Address & Checksum Validation Engine

### 1.1 Objective
Construct a multi-chain address validation library that cryptographically verifies public keys, character encodings, network prefixes, and checksums for Bitcoin (BTC), Ethereum (ETH), Tron (TRX), and Solana (SOL), rejecting malformed or malicious inputs before entering the pipeline.

### 1.2 Deliverables
- **Core Module:** `backend/app/blockchain/validation/validator.py`
  - Class `AddressValidator`:
    - `validate(address: str, chain: Chain) -> AddressValidationResult`
    - `_validate_ethereum(address: str) -> AddressValidationResult` (EIP-55 Keccak-256 mixed-case checksum)
    - `_validate_bitcoin(address: str) -> AddressValidationResult` (P2PKH, P2SH Base58Check, Bech32 `bc1q`, Bech32m `bc1p`)
    - `_validate_tron(address: str) -> AddressValidationResult` (Base58Check prefix `T`, length 34, 0x41 byte)
    - `_validate_solana(address: str) -> AddressValidationResult` (Base58 public key, length 32–44 chars)
- **Unit Test Suite:** `tests/unit/test_validation.py`

### 1.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_validation.py -v
```

#### Test Case 1.1: Ethereum EIP-55 Mixed-Case Checksum Verification
- **Input:** `0x71C83e20e8F468a3E282241F8C936f4521487439` (Valid EIP-55 checksum)
- **Expected Output:** `is_valid = True`, `is_checksummed = True`, `normalized_address = "0x71c83e20e8f468a3e282241f8c936f4521487439"`
- **Pass Criteria:** Keccak-256 capitalisation check matches EIP-55 specification exactly.

#### Test Case 1.2: Ethereum Invalid Checksum Mutation
- **Input:** `0x71c83E20e8F468a3E282241F8C936f4521487439` (Altered single character case)
- **Expected Output:** `is_valid = True`, `is_checksummed = False`, `warning = "Checksum mismatch: address is valid hex but fails EIP-55"`
- **Pass Criteria:** Does not reject valid hex addresses, but warns investigator of capitalization discrepancy.

#### Test Case 1.3: Bitcoin Multi-Format Encodings
- **Inputs:**
  1. Legacy P2PKH: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`
  2. Nested SegWit P2SH: `3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy`
  3. Native SegWit Bech32: `bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq`
  4. Taproot Bech32m: `bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0`
- **Expected Output:** `is_valid = True` for all 4 inputs with correct format subtype labeled.
- **Pass Criteria:** All valid formats accepted; invalid characters (`0`, `O`, `I`, `l`) strictly rejected.

#### Test Case 1.4: Tron Base58Check Validation
- **Input:** `TLyqzVGLV1srkB7dToTAwdg29NtTS14D4V`
- **Expected Output:** `is_valid = True`, `chain = "TRX"`, `format = "BASE58_CHECK"`
- **Failure Input:** `TLyqzVGLV1srkB7dToTAwdg29NtTS14D40` (Contains illegal '0')
- **Expected Failure:** `is_valid = False`, `error = "Invalid Base58 character in Tron address"`

#### Phase 1 Exit Gate
> [!IMPORTANT]
> Phase 1 is complete ONLY when `test_validation.py` passes 100% of valid test vectors and 100% of malformed vectors with zero unhandled exceptions.

---

## Phase 2: Lossless Multi-Chain Transaction Normalization

### 2.1 Objective
Design and implement a data normalization engine that ingests heterogenous transaction structures (Bitcoin UTXO multi-input/output transactions, Ethereum smart contract internal transfers and ERC-20 Transfer logs, Tron TRC-20 transfers) and transforms them into a unified, lossless schema.

### 2.2 Deliverables
- **Data Models:** `backend/app/schemas/transaction.py`
  - `NormalizedTransaction`: Transaction hash, block number, timestamp, network fee, raw input/output arrays.
  - `NormalizedTransfer`: Unique transfer ID, parent tx hash, from address, to address, asset symbol, amount (float/decimal), USD value, hop index.
- **Core Module:** `backend/app/blockchain/normalization/normalizer.py`
  - Class `TransactionNormalizer`:
    - `normalize_utxo(raw_tx: Dict[str, Any]) -> NormalizedTransaction`
    - `normalize_ethereum_account(raw_tx: Dict[str, Any], receipt: Optional[Dict[str, Any]]) -> NormalizedTransaction`
    - `normalize_token_transfers(raw_tx: Dict[str, Any]) -> List[NormalizedTransfer]`
    - `parse_erc20_transfer_log(log_entry: Dict[str, Any]) -> Optional[NormalizedTransfer]`
- **Unit Test Suite:** `tests/unit/test_normalization.py`

### 2.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_normalization.py -v
```

#### Test Case 2.1: Bitcoin Multi-Input Multi-Output UTXO Decomposition
- **Input:** Raw UTXO JSON with 2 inputs totaling $3.5\text{ BTC}$ and 2 outputs ($3.0\text{ BTC}$ to target, $0.4998\text{ BTC}$ change, $0.0002\text{ BTC}$ fee).
- **Expected Output:**
  - `NormalizedTransaction.tx_id` matches input hash.
  - Generates 2 `NormalizedTransfer` objects with sender resolved from input addresses.
  - Output change identified and marked.
- **Pass Criteria:** Value preservation check: $\sum \text{Inputs} = \sum \text{Outputs} + \text{Fee}$.

#### Test Case 2.2: ERC-20 Token Transfer Log Parsing
- **Input:** Ethereum receipt with log topic `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` (Transfer event), contract `0xdAC17F958D2ee523a2206206994597C13D831ec7` (USDT), 6 decimals, amount hex `0x00000000000000000000000000000000000000000000000000000002540be400` ($10,000\text{ USDT}$).
- **Expected Output:**
  - `asset = "USDT"`
  - `amount = 10000.0`
  - `from_address` and `to_address` correctly extracted from 32-byte padded topics.
- **Pass Criteria:** Decimal conversion accurately reflects contract definition ($10^{6}$ for USDT).

#### Test Case 2.3: Zero-Value / Spam Dust Flagging
- **Input:** Raw token transaction transferring $0.00000001\text{ SPAM}$ token.
- **Expected Output:** `NormalizedTransfer.is_dust = True` with dust flag metadata preserved.

#### Phase 2 Exit Gate
> [!IMPORTANT]
> Phase 2 is complete ONLY when UTXO and Account-based raw transactions convert into `NormalizedTransaction` objects without losing precision or discarding token transfer events.

---

## Phase 3: Pluggable Data Adapters (Mode 1 Fixtures & Mode 2 Live APIs)

### 3.1 Objective
Implement the decoupled `BlockchainProvider` abstraction allowing the application to switch seamlessly between Mode 1 (Offline Cached Fixtures) and Mode 2 (Configured External APIs) with automatic fallback and in-memory indexing.

### 3.2 Deliverables
- **Abstract Interface:** `backend/app/blockchain/adapters/base.py`
  - Class `BlockchainProvider(ABC)`:
    - `get_wallet_transactions(address: str, chain: Chain, limit: int) -> List[NormalizedTransaction]`
    - `get_transaction(tx_id: str, chain: Chain) -> Optional[NormalizedTransaction]`
    - `get_transfers(address: str, chain: Chain) -> List[NormalizedTransfer]`
- **Mode 1 Fixture Provider:** `backend/app/blockchain/adapters/fixture_adapter.py`
  - In-memory reverse index mapping addresses to transaction events.
  - Sub-millisecond retrieval latency for presentation demos.
- **Mode 2 Live Provider:** `backend/app/blockchain/adapters/live_adapter.py`
  - REST client for Etherscan, Mempool.space, and TronGrid with API key detection from `.env`.
  - Circuit breaker: Auto-fallback to Mode 1 fixtures if live network call fails or times out ($> 3000\text{ms}$).

### 3.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_adapters.py -v
```

#### Test Case 3.1: Offline Fixture Reverse-Indexing
- **Input:** Query address `0x71C83e20e8F468a3E282241F8C936f4521487439` (Case B Suspect) in `FixtureBlockchainProvider`.
- **Expected Output:** Returns exact matching transactions within $< 15\text{ms}$.
- **Pass Criteria:** Total transactions returned $\ge 1$, without initiating network requests.

#### Test Case 3.2: Non-Existent Address Query in Mode 1
- **Input:** Query random unrecorded address `0x000000000000000000000000000000000000dead` in `FixtureBlockchainProvider`.
- **Expected Output:** Returns empty list `[]` cleanly without throwing index errors or crashing.

#### Test Case 3.3: Live Adapter Circuit Breaker & Fallback
- **Input:** Trigger `LiveBlockchainProvider` with invalid host / disconnected network.
- **Expected Output:** System logs warning, engages circuit breaker, and falls back to fixture data.
- **Pass Criteria:** API call returns valid response data without uncaught `ConnectionError`.

#### Phase 3 Exit Gate
> [!IMPORTANT]
> Phase 3 is complete ONLY when the fixture provider can serve all demo cases in under $20\text{ms}$ per query with zero internet access.

---

## Phase 4: Multi-Hop Transaction Collection & Ingestion Engine

### 4.1 Objective
Construct an automated multi-hop transaction collector that starts from a suspect root address, fetches transactions, traces outbound value across multiple hops (depth 3 to 5), resolves internal cycles, and builds an aggregated transfer list for the Graph Engine.

### 4.2 Deliverables
- **Core Module:** `backend/app/blockchain/ingestion/collector.py`
  - Class `BlockchainCollector`:
    - `collect_multi_hop(root_address: str, chain: Chain, max_hops: int = 5) -> IngestionPackage`
    - `_collect_hop_layer(current_addresses: Set[str], hop_depth: int) -> List[NormalizedTransfer]`
    - `_deduplicate_and_prune(transfers: List[NormalizedTransfer]) -> List[NormalizedTransfer]`
- **Integration Test:** `tests/unit/test_collector.py`

### 4.3 Verification & Test Cases

#### Execution Command
```bash
python -m pytest tests/unit/test_collector.py -v
```

#### Test Case 4.1: Linear 3-Hop Collection
- **Input:** Root address $A$, transfers $A \to B \to C \to D$, `max_hops = 3`.
- **Expected Output:**
  - Total transfers: 3.
  - Hop distances: $A \to B$ (Hop 1), $B \to C$ (Hop 2), $C \to D$ (Hop 3).
  - Terminal addresses identified: $\{D\}$.
- **Pass Criteria:** Traversal stops precisely at `max_hops = 3`.

#### Test Case 4.2: Cyclical Transfer Handling
- **Input:** Root address $A$, transfers $A \to B \to C \to A$ (Circular loop).
- **Expected Output:**
  - Traversal terminates gracefully without entering an infinite loop.
  - Circular edge flagged in metadata: `is_cyclical = True`.
- **Pass Criteria:** Execution completes in $< 100\text{ms}$.

#### Test Case 4.3: High-Fanout Deduplication
- **Input:** Node $A$ fans out to 20 intermediary addresses, which reconverge into single node $B$.
- **Expected Output:** Intermediary nodes deduplicated; transfer array preserves all 20 inbound edges into $B$.

#### Phase 4 Exit Gate
> [!IMPORTANT]
> Phase 4 is complete ONLY when `collect_multi_hop()` successfully traverses all paths up to 5 hops across test fixtures without memory leaks or cycle deadlocks.

---

## Phase 5: Demo Case Fixtures & Ground-Truth Dataset Packaging

### 5.1 Objective
Package three complete, realistic investigation datasets spanning Bitcoin, Ethereum, and Tron. Each case must have validated cryptographic proofs, multi-hop transaction trees, known VASP terminal targets, and ground truth labels for hackathon demonstration.

### 5.2 Deliverables
- **Case Metadata:** `data/demo/cases/`
  - `case_a_direct.json`: Bitcoin direct-flow extortion case.
  - `case_b_layered.json`: Ethereum layered phishing case (3-hop relay to Kraken deposit).
  - `case_c_bridge.json`: Tron TRC-20 laundering case (peel chain and cross-chain bridge to Binance).
- **Transaction Fixtures:** `data/demo/transactions/`
  - `case_a_transactions.json`
  - `case_b_transactions.json`
  - `case_c_transactions.json`
- **Validation Script:** `scripts/validate_demo_case.py`

### 5.3 Verification & Test Cases

#### Execution Command
```bash
python scripts/validate_demo_case.py
```

#### Test Case 5.1: Case A (BTC Direct Flow) Integrity
- **Verification:**
  - Suspect address: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`
  - Target VASP: `Binance`
  - Topological distance: 1 hop.
- **Pass Criteria:** Script outputs `Case A Ground Truth Check: PASSED (100% Top-1 Match)`.

#### Test Case 5.2: Case B (ETH Layered Phish) Integrity
- **Verification:**
  - Suspect address: `0x71C83e20e8F468a3E282241F8C936f4521487439`
  - Target VASP: `Kraken`
  - Topological distance: 3 hops.
  - Intermediate nodes: 2 unlabelled layering hops.
- **Pass Criteria:** Script outputs `Case B Ground Truth Check: PASSED (100% Top-1 Match)`.

#### Test Case 5.3: Case C (TRX Peel Chain & Bridge) Integrity
- **Verification:**
  - Suspect address: `TLyqzVGLV1srkB7dToTAwdg29NtTS14D4V`
  - Target VASP: `Binance` (via bridge route)
  - Obfuscation typology: Peel chain with 90/10 value splits.
- **Pass Criteria:** Script outputs `Case C Ground Truth Check: PASSED (100% Top-1 Match)`.

#### Phase 5 Exit Gate
> [!IMPORTANT]
> Phase 5 is complete ONLY when `python scripts/validate_demo_case.py` executes across all 3 cases with zero failures, confirming the data pipeline is ready for downstream ML and Fullstack consumption.
