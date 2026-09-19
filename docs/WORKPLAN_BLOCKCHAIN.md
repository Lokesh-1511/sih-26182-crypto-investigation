# Workplan: Blockchain Engineering Track (Member 1)

**Project:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine (SIH 26182)  
**Role:** Blockchain Data Engineer & Protocol Specialist (Member 1)  
**Assigned Git Branch:** `feature/member1-blockchain`  
**Target Delivery Window:** 15-Day SIH Accelerated Sprint  
**Document Version:** 1.0.0

---

## 1. Domain Overview & Purpose

As the **Blockchain Data Engineer (Member 1)**, your primary objective is to build the foundation of the investigation pipeline: ensuring every cryptocurrency address fed into the system is cryptographically valid, fetching and collecting transaction histories across multiple blockchains (UTXO, Account, and Token layers), and normalizing heterogeneous on-chain events into a unified, lossless schema for the downstream Graph and Attribution engines.

### Key Philosophy
- **Zero Hallucinated Transactions**: Raw blockchain transaction proofs (hashes, block heights, fee amounts, and timestamps) must remain intact.
- **Offline Resilience**: The system must run flawlessly in **Mode 1 (Offline Cached Fixtures)** without an internet connection, while maintaining modular interfaces for **Mode 2 (Configured Live APIs)**.
- **Multi-Chain Robustness**: Deep handling of Bitcoin (BTC), Ethereum (ETH), and Tron (TRX) with extensible contracts for Solana (SOL), BNB Chain, and Polygon.

---

## 2. Codebase Ownership & Directory Boundary

You have strict ownership and write permissions over the following paths:

```
backend/app/blockchain/
├── validation/
│   └── validator.py             # Multi-chain cryptographic address & checksum validation
├── adapters/
│   ├── __init__.py
│   ├── base.py                  # Abstract BlockchainProvider interface
│   ├── fixture_adapter.py       # Offline demo fixture provider (Mode 1)
│   └── live_adapter.py          # Live explorer API connectors (Mode 2)
├── normalization/
│   └── normalizer.py            # UTXO & Account transfer normalizer
└── ingestion/
    └── collector.py             # Multi-hop transaction collection & deduplication

data/demo/
├── cases/                       # Demo case metadata (case_a_direct.json, case_b_layered.json, case_c_bridge.json)
└── transactions/                # Raw multi-hop transaction fixtures (case_a, case_b, case_c)

tests/unit/
└── test_validation.py           # Unit tests for address validation & checksums
```

*Shared Contracts (Read-Only without Team Consensus):*  
`backend/app/schemas/wallet.py`, `backend/app/schemas/transaction.py`

---

## 3. Detailed Work Breakdown & Deliverables

### Milestone 1: Multi-Chain Address & Checksum Validation Engine
**Target File:** `backend/app/blockchain/validation/validator.py`  
**Dependencies:** `backend/app/schemas/wallet.py`

#### Detailed Tasks:
1. **Ethereum Validation (ETH, BNB, Polygon)**:
   - Validate 42-character hexadecimal format starting with `0x`.
   - Implement **EIP-55 mixed-case checksum verification** using Keccak-256 hashing.
   - Return diagnostic feedback indicating whether the address is standard hex or verified EIP-55 checksummed.
2. **Bitcoin Validation (BTC)**:
   - **Legacy P2PKH**: Starts with `1`, length 26–35, Base58 alphabet (strictly rejecting `0`, `O`, `I`, `l`).
   - **Nested SegWit P2SH**: Starts with `3`, length 26–35, Base58 alphabet.
   - **Native SegWit (Bech32)**: Starts with `bc1q`, length 42–62, lowercase alphanumeric character set.
   - **Taproot (Bech32m)**: Starts with `bc1p`, length 62, Bech32m checksum polynomial verification.
3. **Tron Validation (TRX)**:
   - Validate Base58Check encoding: starts with uppercase `T`, exactly 34 characters long, payload starting with byte `0x41`.
4. **Solana Validation (SOL)**:
   - Validate Base58 string length between 32 and 44 characters with Ed25519 public key byte validation.
5. **Acceptance Test**:
   - `python -m pytest tests/unit/test_validation.py -v` must pass 100% of valid test vectors and reject malformed inputs without false positives.

---

### Milestone 2: Pluggable `BlockchainProvider` Adapter Architecture
**Target Files:** `backend/app/blockchain/adapters/base.py`, `fixture_adapter.py`, `live_adapter.py`  
**Dependencies:** `backend/app/schemas/transaction.py`

#### Detailed Tasks:
1. **Abstract Contract (`base.py`)**:
   - Define abstract methods:
     * `get_wallet_transactions(address: str, chain: Chain, limit: int = 50) -> List[NormalizedTransaction]`
     * `get_transaction(tx_id: str, chain: Chain) -> Optional[NormalizedTransaction]`
     * `get_transfers(address: str, chain: Chain) -> List[NormalizedTransfer]`
     * `get_block(block_number: int, chain: Chain) -> Optional[Dict[str, Any]]`
2. **Offline Fixture Provider (`fixture_adapter.py`)**:
   - Read and index JSON files from `data/demo/transactions/`.
   - Implement fast in-memory reverse-index mapping addresses (`from_address`, `to_address`, and token recipients) to transactions.
   - Cache results in memory to guarantee $< 50\text{ms}$ retrieval latency during judge presentations.
3. **Live API Provider Skeleton (`live_adapter.py`)**:
   - Integrate standard REST endpoints for external block explorers when keys are present in `.env`:
     * Etherscan API (`api.etherscan.io`) for Ethereum account transfers and ERC-20 logs.
     * Blockstream / Mempool.space API (`mempool.space/api`) for Bitcoin UTXO vin/vout tracking.
     * TronGrid API (`api.trongrid.io`) for Tron TRX and TRC-20 transfers.
   - Implement automatic rate-limiting and connection-timeout fallbacks to offline fixtures.

---

### Milestone 3: Common Transaction Normalization Engine
**Target File:** `backend/app/blockchain/normalization/normalizer.py`  
**Dependencies:** `backend/app/schemas/transaction.py`

#### Detailed Tasks:
1. **UTXO to Transfer Unification**:
   - Deconstruct Bitcoin multi-input, multi-output transactions.
   - Map primary input address to each distinct output address as a discrete `NormalizedTransfer`.
   - Accurately convert Satoshi values to BTC floating units ($1\text{ BTC} = 10^8\text{ Satoshis}$).
   - Preserve transaction fees, block heights, and confirmation timestamps.
2. **Account Model & Smart Contract Token Normalization**:
   - Parse native coin transfers (ETH, TRX, BNB).
   - Parse smart contract token events:
     * ERC-20 `Transfer(address from, address to, uint256 value)` log events.
     * TRC-20 transfer logs for USDT on Tron.
   - Extract `token_contract`, `token_symbol`, `token_decimals`, and compute human-readable `token_amount`.
3. **Raw Reference Preservation**:
   - Never destroy original API payloads; serialize verbatim responses into `raw_reference` for forensic audit trails.

---

### Milestone 4: Multi-Hop Ingestion Collector
**Target File:** `backend/app/blockchain/ingestion/collector.py`  
**Dependencies:** `backend/app/blockchain/adapters/base.py`

#### Detailed Tasks:
1. **Breadth-First Ingestion Pipeline**:
   - Given a suspect wallet and max hops (default: 4):
     * Level 0: Query all direct inbound and outbound transactions.
     * Level 1 to $N$: Extract unique downstream counterparty addresses; fetch and batch their transactions.
   - Implement strict deduplication using transaction hash sets to prevent reprocessing of cyclic flows.
2. **Batch Serialization**:
   - Return structured `TransactionIngestionBatch` records tagged with provenance metadata and retrieval timestamps.

---

### Milestone 5: High-Fidelity Controlled Demo Datasets
**Target Files:** `data/demo/cases/`, `data/demo/transactions/`

#### Detailed Tasks:
1. **Case A (Bitcoin Direct Sweep)**:
   - `data/demo/cases/case_a_direct.json` & `case_a_transactions.json`
   - Suspect wallet `1A1zP1eP...` directly deposits 1.45 BTC into Binance custodial deposit address `1NDyJt...`, followed by an automated consolidation sweep to Binance Hot Wallet 6.
2. **Case B (Ethereum 4-Hop Layered Flow with Obfuscation Breakpoint)**:
   - `data/demo/cases/case_b_layered.json` & `case_b_transactions.json`
   - Suspect wallet `0x71C83e20...` sends 12.5 ETH $\to$ Hop 1 $\to$ Hop 2 (Fan-out into 3 parallel addresses) $\to$ Hop 3 (Binance deposit wallet) $\to$ Hop 4 (Sweep to Binance Hot Wallet 14).
3. **Case C (Cross-Chain Bridge Transition)**:
   - `data/demo/cases/case_c_bridge.json` & `case_c_transactions.json`
   - Tron USDT flow (`TR7NHq...`) interacting with a cross-chain bridge gateway contract (`0x3ee18...`) releasing assets into OKX deposit infrastructure (`TYDzsY...`).

---

## 4. 15-Day Day-by-Day Execution Plan

| Day | Primary Focus | Daily Deliverable |
| :---: | :--- | :--- |
| **Day 1** | Scaffolding & Setup | Setup `feature/member1-blockchain` branch; establish adapter directory layout. |
| **Day 2** | Address Validation | Implement `MultiChainValidator` for BTC, ETH, and TRX; write positive/negative test vectors. |
| **Day 3** | Provider Interfaces | Implement abstract `BlockchainProvider` and offline `FixtureBlockchainProvider`. |
| **Day 4** | Normalization | Implement `TransactionNormalizer` for Account transfers (ETH) and UTXO inputs/outputs (BTC). |
| **Day 5** | Token Parsing | Add ERC-20 / TRC-20 event parsing and decimal conversion logic to `normalizer.py`. |
| **Day 6** | Multi-Hop Ingestion | Build `TransactionCollector` with cycle prevention and depth control. |
| **Day 7** | Case A Data Curation | Finalize Bitcoin direct sweep fixtures with exact satoshi balance math. |
| **Day 8** | Case B Data Curation | Finalize Ethereum 4-hop layered fixtures with Hop 2 fan-out breakpoint. |
| **Day 9** | Case C Data Curation | Finalize Tron cross-chain bridge fixtures with lock-and-mint mappings. |
| **Day 10** | Live Adapter Skeleton | Implement optional live Etherscan and TronGrid fetchers with API key injections. |
| **Day 11** | Gas & Fee Forensics | Verify fee and block height calculations across all test cases. |
| **Day 12** | Performance Tuning | Benchmark fixture indexing speed ($< 50\text{ms}$ loading for 100+ transactions). |
| **Day 13** | Integration Testing | Pair with Member 2 to verify graph builder consumes normalized transfers cleanly. |
| **Day 14** | Rehearsal & Verification | Validate all 3 demo cases run offline with WiFi turned off. |
| **Day 15** | Code Freeze & Backup | Final code cleanup, linting, and merge into `develop`. |

---

## 5. Verification Commands for Member 1

Run these commands locally to verify your deliverables:

```powershell
# 1. Run unit tests for address validation
python -m pytest tests/unit/test_validation.py -v

# 2. Run normalization and fixture loading test
python -c "from backend.app.blockchain.adapters.fixture_adapter import FixtureBlockchainProvider; p = FixtureBlockchainProvider(); print('Loaded transactions:', len(p._cache))"

# 3. Test multi-chain address validation via CLI
python -c "from backend.app.blockchain.validation.validator import MultiChainValidator; from backend.app.schemas.wallet import Chain; print(MultiChainValidator.validate('0x71C83e20e8F468a3E282241F8C936f4521487439', Chain.ETH))"
```
