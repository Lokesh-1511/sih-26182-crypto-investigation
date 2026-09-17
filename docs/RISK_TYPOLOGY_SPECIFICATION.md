# Risk & AML Typology Specification

**Module:** `backend/app/risk/`  
**Owners:** Member 2 & Member 3  
**Document Version:** 1.0.0

---

## 1. Obfuscation Breakpoint Detection

An **Obfuscation Breakpoint** is an address node along the transaction graph where normal fund-flow patterns abruptly transition into high-complexity anonymization behavior.

### Algorithmic Trigger Conditions
A node $v \in V$ is flagged as an Obfuscation Breakpoint if any of the following conditions evaluate to true:
1. **Fan-Out Burst**: Node out-degree $\text{deg}^+(v) \ge 4$ executed within a time window $\Delta t \le 15\text{ minutes}$.
2. **Rapid Relay**: Median holding time $\tau \le 90\text{ seconds}$ across incoming and outgoing transfers.
3. **Value Fragmentation**: Incoming amount split into $\ge 3$ smaller transfers within $\pm 5\%$ value deviation (structuring / smurfing).
4. **Bridge / Mixer Boundary**: Node interacts directly with a verified cross-chain bridge gateway or privacy tumbler contract.

### UI & Investigative Presentation
- Highlighted on the Cytoscape.js canvas with an animated amber/red warning beacon.
- Displays an analytical breakdown: *"WHY FLAGGED? 1-to-4 fan-out observed within 240 seconds with 98% value fragmentation."*

---

## 2. Rule-Assisted AML Typology Catalog

| Code | Typology Name | Severity | Heuristic Criteria |
| :--- | :--- | :---: | :--- |
| **TYP-01** | Rapid Layering (Multi-Hop Relay) | **HIGH** | $\ge 3$ consecutive hops executed in under 10 minutes total elapsed time. |
| **TYP-02** | Fan-Out Structuring (Smurfing) | **HIGH** | Single input split into 4+ sub-threshold outputs within a 1-hour window. |
| **TYP-03** | Peel Chain Accumulation | **MEDIUM** | Repeated sequence where a large output creates one small transfer and one large change output. |
| **TYP-04** | Privacy Mixer Exposure | **CRITICAL**| Direct transfer to or from an OFAC-sanctioned mixer or privacy pool. |
| **TYP-05** | Cross-Chain Liquidity Hop | **MEDIUM** | Transfer interacting with a decentralized bridge smart contract. |
