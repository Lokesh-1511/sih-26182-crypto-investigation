# Known Limitations & Investigative Caveats: SIH 26182

**System:** AI-Assisted Multi-Chain Cryptocurrency Investigation & VASP Attribution Engine  
**Document Version:** 1.0.0

---

## 1. Technical & Algorithmic Limitations

1. **Probabilistic Nature of Attribution**:
   - On-chain attribution to a VASP is probabilistic and heuristic, based on deposit sweep patterns, clustering algorithms, and temporal correlation. It does not constitute mathematically indisputable cryptographic proof.
2. **Absence of Off-Chain KYC Data**:
   - The platform analyzes public ledger records. It cannot ascertain the true legal identity (KYC) of the account holder without official exchange subpoena disclosures.
3. **UTXO Peeling Chains & CoinJoin Obfuscation**:
   - In Bitcoin UTXO environments, advanced equal-output CoinJoin transactions (e.g., Wasabi, Whirlpool) disrupt standard multi-input clustering heuristics, introducing uncertainty penalties.
4. **Cross-Chain Bridge Opacity**:
   - While lock-and-mint transactions are flagged at the contract level, tracing fund flows across non-interoperable Layer-1 chains requires matching off-chain relayer/validator events. The prototype uses controlled bridge mappings.
5. **Decentralized Exchange (DEX) Liquidity Pools**:
   - Swapping assets through Uniswap or Curve pools consolidates funds into shared liquidity pools, requiring pool-reserve analysis to track output tokens.
