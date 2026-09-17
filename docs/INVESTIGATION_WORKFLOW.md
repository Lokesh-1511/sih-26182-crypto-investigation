# Law Enforcement Investigation Workflow

**System:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine  
**Target User:** Law Enforcement Agency (LEA) Cybercrime Investigator / Financial Intelligence Analyst  
**Document Version:** 1.0.0

---

## 1. End-to-End Investigation Lifecycle

```
[ UNKNOWN SUSPECT WALLET ]
           |
           v
1. ADDRESS & CHAIN VALIDATION
   - Cryptographic format validation (BTC/ETH/TRX)
   - Checksum verification (EIP-55, Base58Check, Bech32)
           |
           v
2. TRANSACTION INGESTION & NORMALIZATION
   - Fetching transactions (Mode 1: Offline Fixtures / Mode 2: Live APIs)
   - Normalizing UTXO & Account transfers into standardized records
   - Retaining block height, timestamp, fees, and raw transaction hashes
           |
           v
3. DIRECTED FUND-FLOW GRAPH GENERATION
   - Constructing NetworkX multigraph
   - 3 to 5 hop forward breadth-first traversal
   - Pruning transaction dust and high-volume noise
           |
           v
4. ENTITY RESOLUTION & CLUSTERING
   - Matching addresses against VASP Knowledge Base
   - Distinguishing Deposit Wallets, Omnibus Hot Wallets, Mixers, Bridges
           |
           v
5. BEHAVIORAL & RISK ANALYSIS
   - Flagging Obfuscation Breakpoints (fan-out, rapid hops, fragmentation)
   - Rule-assisted AML typologies (layering, structuring, mixer interactions)
           |
           v
6. VASP ATTRIBUTION & EXPLAINABLE SCORING
   - Multi-factor quantitative scoring (entity match, sweeps, proximity, volume)
   - Counterfactual sensitivity analysis (evidence factor ablation)
   - Rigorous Operator vs Beneficiary distinction
           |
           v
7. EVIDENCE DRILL-DOWN & IMMUTABLE SNAPSHOT
   - Verifying every score factor against raw on-chain transaction IDs
   - Generating SHA-256 analysis snapshot hash
           |
           v
8. INVESTIGATION REPORT & LAWFUL ACTION PACKET
   - Exporting tamper-evident PDF/HTML forensic report
   - Generating draft Section 91 CrPC / MLAT preservation requests for officer review
```

---

## 2. Forensic Principles & Investigation Boundaries

### A. Four-Tier Truth Distinction
1. **Observed Blockchain Fact**: On-chain transfer `0xabc...` sent 5.0 ETH at timestamp `2026-03-10T14:22:01Z` with fee `0.002 ETH`. This is mathematically verifiable and indisputable.
2. **Inferred Attribution**: Wallet `0xdef...` exhibits repeated sweeps into Binance Hot Wallet 6, indicating a 91% confidence of being a Binance deposit address. This is a probabilistic investigative lead.
3. **Risk & Typology Finding**: Wallet `0x123...` engaged in 8 transfers within 3 minutes across 6 hops, indicating a potential layering pattern. This is an analytical hypothesis.
4. **Beneficiary Identity**: The legal identity of the natural person controlling the account remains **`NOT ESTABLISHED`**. On-chain data alone cannot prove human identity; off-chain KYC records subpoenaed via lawful process are mandatory.

### B. Prohibited System Behaviors
- The system **never** attempts private-key derivation or wallet exploitation.
- The system **never** automatically executes freezing orders or dispatches legal notices to exchanges without an authorized human officer's manual sign-off.
- The system **never** fabricates real-world entity attributions; all demo entities are explicitly tagged as `DEMO / CONTROLLED DATA`.
