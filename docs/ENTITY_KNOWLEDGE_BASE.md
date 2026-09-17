# Entity Knowledge Base Specification

**Module:** `backend/app/entities/`  
**Storage:** JSON Fixtures (`data/knowledge_base/`) + SQLite/Postgres Cache  
**Owner:** Member 2  
**Document Version:** 1.0.0

---

## 1. Entity Classification Taxonomy

Every labeled address in the system is categorized under one of the following verified taxonomy roles:

1. **VASP_HOT_WALLET**: High-volume omnibus wallet holding exchange liquidity and servicing customer withdrawals (e.g., Binance Hot Wallet 6, Kraken Pool 1).
2. **VASP_DEPOSIT**: Ephemeral or permanent custodial address assigned to an individual exchange user that forwards incoming balances via consolidation sweeps.
3. **MIXER**: Coin tumbler, privacy mixer, or cryptographic zero-knowledge pool (e.g., Tornado.Cash).
4. **BRIDGE**: Cross-chain lock-and-mint or liquidity bridge smart contract (e.g., Multichain, Hop Protocol).
5. **DEX_POOL**: Automated Market Maker (AMM) liquidity pool (e.g., Uniswap V3 Pool).

---

## 2. Knowledge Base Schema & Fixture Files

The knowledge base is stored under `data/knowledge_base/`:
- `vasp_labels.json`: Master directory of Virtual Asset Service Providers.
- `deposit_wallets.json`: Known and verified VASP deposit addresses with associated exchange mapping.
- `hot_wallets.json`: Publicly documented hot wallets.
- `bridges.json`: Known multi-chain bridge router contracts.
- `mixers.json`: Publicly documented privacy mixer addresses.

### Entity Label Object Schema
```json
{
  "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
  "chain": "ETH",
  "entity_name": "Binance",
  "entity_type": "HOT_WALLET",
  "confidence": 1.0,
  "label_source": "PUBLIC_INTELLIGENCE",
  "notes": "Binance Hot Wallet 14 (Verified Etherscan Tag)"
}
```

*Ethical Rule: No fictitious or unverified labels are ever introduced into production schemas. Synthetic fixtures used for controlled hackathon demonstration are explicitly marked with `label_source: "CONTROLLED_DEMO"`.*
