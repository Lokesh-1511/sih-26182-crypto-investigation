# REST API Specification: SIH 26182

**Protocol:** HTTP/1.1 (JSON)  
**Base URL:** `http://localhost:8000/api`  
**Interactive Docs:** `http://localhost:8000/docs` (OpenAPI 3.1)  
**Document Version:** 1.0.0

---

## 1. Endpoints Overview

| Method | Endpoint | Description | Query / Body Params | Response Model |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | System health and provider status | None | `HealthStatus` |
| `POST` | `/cases` | Create a new investigation case | `CaseCreate` body | `CaseResponse` |
| `GET` | `/cases` | List all investigation cases | `status`, `limit`, `offset` | `List[CaseResponse]` |
| `GET` | `/cases/{id}` | Retrieve specific case details | None | `CaseResponse` |
| `POST` | `/cases/{id}/wallet`| Update suspect wallet & chain | `WalletInput` body | `CaseResponse` |
| `POST` | `/cases/{id}/trace` | Initiate multi-hop graph trace | `TraceConfig` body (hops, min_amt) | `TraceProgressStatus` |
| `GET` | `/cases/{id}/status`| Poll trace ingestion progress | None | `TraceProgressStatus` |
| `GET` | `/cases/{id}/transactions`| Retrieve normalized transactions | `limit`, `offset` | `List[NormalizedTransaction]` |
| `GET` | `/cases/{id}/graph` | Retrieve visual graph data | `min_amount`, `max_hops` | `GraphResponse` |
| `GET` | `/cases/{id}/timeline` | Retrieve chronological transfers | `asset` | `List[TimelineEvent]` |
| `GET` | `/cases/{id}/attribution` | Get ranked VASP candidates | None | `AttributionSummary` |
| `GET` | `/cases/{id}/attribution/explanation` | Get Explainable Attribution Card | `vasp_name` | `ExplainableAttributionCard` |
| `GET` | `/cases/{id}/attribution/counterfactual` | Re-score with factor ablation | `exclude_factors` query | `CounterfactualResult` |
| `GET` | `/cases/{id}/risk` | Retrieve AML typologies & breakpoints | None | `RiskSummary` |
| `GET` | `/cases/{id}/evidence` | Transaction drilldown details | `tx_id` query | `EvidenceItem` |
| `GET` | `/cases/{id}/snapshot` | Generate/verify SHA-256 snapshot | None | `AnalysisSnapshot` |
| `POST` | `/cases/{id}/report` | Generate forensic PDF/HTML report | None | `ReportResponse` |
| `POST` | `/cases/{id}/action-packet` | Generate Lawful Action Packet draft | None | `ActionPacketResponse` |
| `GET` | `/entities/search` | Search VASP knowledge base | `query`, `chain`, `type` | `List[EntityLabel]` |
