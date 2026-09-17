# Relational Database Schema: SIH 26182

**ORM:** SQLAlchemy 2.0  
**Storage Engine:** SQLite (Prototype / Demo) | PostgreSQL-Compatible (Production Ready)  
**Document Version:** 1.0.0

---

## 1. Tables & Entity Relationships

```
+---------------+       1:N       +------------------+
|     cases     +-----------------+     wallets      |
+-------+-------+                 +------------------+
        |
        | 1:N
        +-------------------------+   attributions   |
        |                         +------------------+
        | 1:N
        +-------------------------+   risk_events    |
        |                         +------------------+
        | 1:N
        +-------------------------+analysis_snapshots|
                                  +------------------+

+---------------+       1:N       +------------------+
|  transactions +-----------------+    transfers     |
+---------------+                 +------------------+

+---------------+                 +------------------+
| entity_labels |                 |    audit_log     |
+---------------+                 +------------------+
```

### Table Definitions

1. **`cases`**
   - `id` (VARCHAR PK): Unique case UUID.
   - `title` (VARCHAR NOT NULL): Descriptive case name.
   - `investigator` (VARCHAR NOT NULL): Officer name or badge ID.
   - `description` (TEXT): Case notes and objectives.
   - `status` (VARCHAR): `OPEN`, `IN_PROGRESS`, `CLOSED`.
   - `priority` (VARCHAR): `LOW`, `MEDIUM`, `HIGH`, `URGENT`.
   - `suspect_wallet` (VARCHAR): Input address under investigation.
   - `chain` (VARCHAR): Target blockchain (`ETH`, `BTC`, `TRX`).
   - `created_at` (DATETIME): UTC creation timestamp.

2. **`wallets`**
   - `id` (INTEGER PK AUTOINCREMENT): Internal ID.
   - `case_id` (VARCHAR FK -> `cases.id`): Associated case.
   - `chain` (VARCHAR NOT NULL): Blockchain identifier.
   - `address` (VARCHAR NOT NULL INDEX): Wallet address string.
   - `wallet_role` (VARCHAR): `SUSPECT`, `INTERMEDIARY`, `DEPOSIT`, `HOT_WALLET`, `MIXER`, `BRIDGE`.
   - `label` (VARCHAR): Resolved entity label if known.
   - `first_seen`, `last_seen` (DATETIME): Temporal bounds.

3. **`transactions`**
   - `tx_id` (VARCHAR PK INDEX): On-chain transaction hash.
   - `chain` (VARCHAR NOT NULL): Blockchain.
   - `block_number` (INTEGER): Ledger block height.
   - `timestamp` (DATETIME NOT NULL): Block timestamp.
   - `fee` (FLOAT): Transaction fee paid in native unit.
   - `status` (VARCHAR): `SUCCESS`, `FAILED`.
   - `raw_reference` (TEXT): Verbatim raw payload string.
   - `source` (VARCHAR): Data provenance (`CONTROLLED_FIXTURE`, `ETHERSCAN_API`, etc.).
   - `retrieved_at` (DATETIME): Ingestion timestamp.

4. **`transfers`**
   - `id` (INTEGER PK AUTOINCREMENT): Transfer event ID.
   - `tx_id` (VARCHAR FK -> `transactions.tx_id`): Parent transaction.
   - `from_address` (VARCHAR NOT NULL INDEX): Sender address.
   - `to_address` (VARCHAR NOT NULL INDEX): Recipient address.
   - `asset` (VARCHAR NOT NULL): Symbol (e.g. `ETH`, `BTC`, `USDT`).
   - `amount` (FLOAT NOT NULL): Transferred value.
   - `hop_distance` (INTEGER): Relative hop distance from suspect wallet.

5. **`entity_labels`**
   - `address` (VARCHAR PK INDEX): Identified address.
   - `chain` (VARCHAR NOT NULL): Blockchain.
   - `entity_name` (VARCHAR NOT NULL INDEX): Name (e.g. `Binance`, `Kraken`, `Tornado.Cash`).
   - `entity_type` (VARCHAR NOT NULL): `VASP`, `HOT_WALLET`, `DEPOSIT_WALLET`, `MIXER`, `BRIDGE`.
   - `confidence` (FLOAT): Verification certainty (0.0 to 1.0).
   - `label_source` (VARCHAR): `PUBLIC_INTELLIGENCE`, `CONTROLLED_DEMO`, `EXCHANGE_DISCLOSURE`.

6. **`attributions`**
   - `id` (INTEGER PK AUTOINCREMENT): Attribution record ID.
   - `case_id` (VARCHAR FK -> `cases.id` INDEX): Associated case.
   - `candidate_vasp` (VARCHAR NOT NULL): Attributed exchange name.
   - `confidence_score` (FLOAT NOT NULL): Numerical score (0.0 to 100.0).
   - `confidence_band` (VARCHAR NOT NULL): `HIGH`, `MEDIUM`, `LOW`.
   - `operator_attribution` (VARCHAR): Role (e.g. `VASP-Controlled Deposit Infrastructure`).
   - `beneficiary_identity` (VARCHAR): Default: `NOT ESTABLISHED`.
   - `evidence_breakdown_json` (TEXT NOT NULL): Serialized factor point contributions.
   - `model_version` (VARCHAR): Algorithm version (e.g. `v1.0.0`).

7. **`risk_events`**
   - `id` (VARCHAR PK): Unique finding UUID.
   - `case_id` (VARCHAR FK -> `cases.id` INDEX): Associated case.
   - `typology_code` (VARCHAR NOT NULL): Code (e.g. `TYP-01`, `BREAKPOINT-01`).
   - `typology_name` (VARCHAR NOT NULL): Human-readable name.
   - `severity` (VARCHAR NOT NULL): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
   - `node_address` (VARCHAR NOT NULL): Flagged address.
   - `explanation` (TEXT NOT NULL): Analytical justification.
   - `evidence_json` (TEXT NOT NULL): Linked transaction hashes.

8. **`analysis_snapshots`**
   - `id` (VARCHAR PK): Snapshot UUID.
   - `case_id` (VARCHAR FK -> `cases.id` INDEX): Associated case.
   - `snapshot_hash` (VARCHAR NOT NULL): SHA-256 integrity digest.
   - `payload_json` (TEXT NOT NULL): Complete immutable state serialization.
   - `created_at` (DATETIME): Snapshot timestamp.

9. **`audit_log`**
   - `id` (INTEGER PK AUTOINCREMENT): Log ID.
   - `actor` (VARCHAR NOT NULL): Officer username / badge.
   - `action` (VARCHAR NOT NULL): Performed action (`TRACE_START`, `REPORT_EXPORT`).
   - `object_id` (VARCHAR NOT NULL): Affected entity or case ID.
   - `timestamp` (DATETIME): UTC timestamp.
   - `event_hash` (VARCHAR NOT NULL): Tamper-evident checksum.
