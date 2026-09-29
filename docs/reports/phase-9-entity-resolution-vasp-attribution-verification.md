# Phase 9 Verification Report — Entity Resolution + VASP Attribution

**Project:** SIH26182 — VASP Intel / Cryptocurrency Forensic Investigation System  
**Phase:** Phase 9 — Entity Resolution + VASP Attribution  
**Status:** COMPLETE & VERIFIED  
**Date:** September 29, 2026  

---

## 1. Objective

Phase 8 answered: *"How are blockchain addresses connected through multi-hop fund flow?"*  
Phase 9 answers:
1. *"What known entity, if any, is associated with each discovered address?"*
2. *"Is that entity categorized as a Virtual Asset Service Provider (VASP) or exchange?"*
3. *"What is the topological relationship (direction, path, hop distance) connecting the suspect wallet to that VASP?"*

The resulting execution pipeline is:
$$\text{Investigation Request} \longrightarrow \text{Multi-Hop Graph} \longrightarrow \text{Discovered Addresses} \longrightarrow \text{Entity Resolution} \longrightarrow \text{VASP Attribution} \longrightarrow \text{Investigation Response}$$

---

## 2. Architecture & Architectural Separation

Strict architectural boundaries are maintained across all layers:

```
Blockchain Provider (Bitquery V2 / Fixtures)
       ↓
Canonical Blockchain Data (NormalizedTransfer / NormalizedTransaction)
       ↓
Fund-Flow Graph Construction (GraphBuilder / MultiDiGraph)
       ↓
Multi-Hop Traversal (GraphTraversalEngine)
       ↓
Discovered Addresses (Deduplicated, Case-Normalized)
       ↓
Entity Resolution Layer (EntityResolver + AddressIntelligenceProvider)
       ↓
VASP Attribution Layer (VaspAttributionService)
       ↓
API & UI Investigation Results
```

### Architectural Safeguards:
- **No Entity Logic in Core Blockchain / Graph Modules:** `NormalizedTransfer`, `NormalizedTransaction`, `GraphBuilder`, `GraphTraversalEngine`, and `BitqueryProvider` remain pure blockchain and graph structures.
- **Pure Downstream Intelligence:** Entity resolution and VASP attribution consume the output of graph traversal and annotate nodes without mutating raw transaction or transfer facts.
- **Zero Live Network Calls in Tests:** A deterministic local registry provider handles test fixtures offline.

---

## 3. Entity Resolution Model

Implemented in `backend/app/intelligence/models.py`:

```python
class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"

class EntityType(str, Enum):
    VASP = "VASP"
    EXCHANGE = "EXCHANGE"
    CUSTODIAN = "CUSTODIAN"
    PAYMENT_PROVIDER = "PAYMENT_PROVIDER"
    MINER = "MINER"
    BRIDGE = "BRIDGE"
    PROTOCOL = "PROTOCOL"
    UNKNOWN = "UNKNOWN"

class EntityCandidate(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: EntityType
    vasp_status: bool
    source: str
    source_reference: str
    confidence: Optional[float] = None
    notes: Optional[str] = None

class EntityResolution(BaseModel):
    chain: str
    address: str
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    entity_type: Optional[EntityType] = None
    vasp_status: bool = False
    source: Optional[str] = None
    source_reference: Optional[str] = None
    resolution_status: ResolutionStatus = ResolutionStatus.NOT_FOUND
    resolved_at: datetime
    candidates: List[EntityCandidate] = []
```

### Resolution Status Principles:
- `RESOLVED`: Exactly one deterministic entity matched in the intelligence registry.
- `NOT_FOUND`: Address not recognized in intelligence database. **Not** treated as suspicious, criminal, or untrusted.
- `AMBIGUOUS`: Multiple candidate entities match the address; candidate details are retained without arbitrary tie-breaking.

---

## 4. VASP Attribution Model

Implemented in `backend/app/intelligence/models.py`:

```python
class VaspAttribution(BaseModel):
    address: str
    chain: str
    entity_id: str
    entity_name: str
    entity_type: EntityType = EntityType.VASP
    vasp_status: bool = True
    hop_distance: int
    direction: str  # 'outgoing' or 'incoming'
    path: List[str]  # Ordered list of addresses from root to VASP
    resolution_status: ResolutionStatus = ResolutionStatus.RESOLVED
    source: str
    source_reference: str
    relevant_transfer_ids: List[str] = []
    attributed_at: datetime
```

---

## 5. Provider Abstraction

Implemented in `backend/app/intelligence/providers/base.py`:

```python
class AddressIntelligenceProvider(ABC):
    @abstractmethod
    async def resolve_address(self, chain: str, address: str) -> EntityResolution:
        pass

    @abstractmethod
    async def resolve_addresses(self, chain: str, addresses: List[str]) -> List[EntityResolution]:
        pass
```

The application and investigation service remain decoupled from whether resolutions come from the local registry, Etherscan, Arkham, or future third-party APIs.

---

## 6. Local Deterministic Registry

Implemented in `backend/app/intelligence/providers/registry.py`:
- Loads pre-configured entity fixtures from `data/knowledge_base/` and `tests/fixtures/intelligence/entities.json`.
- Supports EVM case-insensitive matching (`address.lower()`) and checksum preservation.
- Flags multi-entity collisions as `ResolutionStatus.AMBIGUOUS`.
- Bounded lookup: Maximum batch size of 500 addresses to prevent resource exhaustion.

---

## 7. API Integration

Extended `POST /api/v1/investigations` with backward compatibility:
- `InvestigationResponse` schema adds:
  - `entity_resolutions: List[EntityResolution]`
  - `vasp_attributions: List[VaspAttribution]`
- `GraphNode` schema adds:
  - `entity_name: Optional[str]`
  - `entity_type: Optional[str]`
  - `is_vasp: bool`

Sample response snippet:
```json
{
  "investigation_id": "inv_486c91e0a2d5",
  "chain": "ethereum",
  "root_address": "0x28c6c06298d514db089934071355e5743bf21d60",
  "status": "completed",
  "summary": { "nodes": 7, "edges": 5, "transactions": 5, "transfers": 5, "hops": 1 },
  "trace": { "direction": "outgoing", "requested_max_hops": 1, "actual_max_hops": 1, "max_hops_reached": true },
  "graph": { "nodes": [...], "edges": [...] },
  "entity_resolutions": [
    {
      "chain": "ethereum",
      "address": "0x28c6c06298d514db089934071355e5743bf21d60",
      "resolution_status": "RESOLVED",
      "entity_id": "binance_hot_1",
      "entity_name": "Binance Hot Wallet",
      "entity_type": "VASP",
      "vasp_status": true,
      "source": "local_registry",
      "source_reference": "data/knowledge_base/entities_ethereum.json"
    }
  ],
  "vasp_attributions": [
    {
      "address": "0x28c6c06298d514db089934071355e5743bf21d60",
      "chain": "ethereum",
      "entity_id": "binance_hot_1",
      "entity_name": "Binance Hot Wallet",
      "entity_type": "VASP",
      "vasp_status": true,
      "hop_distance": 0,
      "direction": "outgoing",
      "path": ["0x28c6c06298d514db089934071355e5743bf21d60"],
      "resolution_status": "RESOLVED",
      "source": "local_registry",
      "source_reference": "data/knowledge_base/entities_ethereum.json"
    }
  ]
}
```

---

## 8. Frontend Integration

Updated `frontend/src/pages/WalletInvestigationPage.tsx` and `frontend/src/components/WalletFundFlowGraph.tsx`:
1. **Graph Visual Distinction:**
   - VASP nodes render with a cyan/teal forensic border (`#62929e` / `#006d77`), subtle background, and `◆ VASP` tag.
   - Graph Legend updated to: `■ SUSPECT`, `■ ADDRESS`, `◆ VASP-ASSOCIATED`, `□ BOUNDARY`.
2. **Forensic Node Inspector:**
   - **Classification:** Displays Entity Name, Entity Type, VASP Status badge, Resolution Status, Source, and Reference.
   - **Attribution Context:** When VASP-associated, displays Trace Direction (`OUTGOING` / `INCOMING`), Path Distance (`X Hops`), Path from Root (`Root → Transit → VASP`), and association disclaimer.
   - **Ambiguous Match Support:** Shows `Multiple candidates` and renders candidate entity breakdown list.

---

## 9. Test Cases & Coverage

### Backend Unit & Integration Tests (`tests/unit/test_entity_resolution.py`):
1. `test_known_vasp_address_resolves_correctly`: Verifies positive VASP resolution, fields, provenance.
2. `test_unknown_address_returns_not_found`: Verifies `NOT_FOUND` resolution without false positive flags.
3. `test_non_vasp_entity_returns_vasp_false`: Verifies Protocol / DEX entities resolve with `vasp_status=False`.
4. `test_ambiguous_entity_resolution`: Verifies collision detection returns `AMBIGUOUS` with candidate list.
5. `test_address_normalization_case_insensitivity`: EVM mixed-case lookups resolve identically.
6. `test_duplicate_addresses_resolved_only_once`: Deduplication before registry query.
7. `test_multiple_discovered_addresses_resolution`: Multi-address resolution in traversal batches.
8. `test_vasp_attribution_path_and_hop_preservation`: Verifies forward traversal path, hop distance, and transfer IDs.
9. `test_vasp_attribution_incoming_backward_tracing`: Verifies backward tracing attribution context.
10. `test_blockchain_models_remain_unmodified`: Assert `NormalizedTransfer` and `NormalizedTransaction` contain no entity fields.
11. `test_vasp_attribution_service_e2e_integration`: Full integration test against synthetic 4-hop fixture graph.

### Frontend Component Tests (`frontend/src/test/WalletInvestigationPage.test.tsx`):
1. Renders investigation form with direction and ready state.
2. Submits investigation request with direction.
3. Populates KPI cards and depth reached display.
4. Renders root suspect wallet in status bar and graph header.
5. Renders activity table with compact From → To routing.
6. Edge selection opens Fund Transfer Inspector.
7. Displays API errors cleanly in alert banner.
8. Handles empty investigation gracefully.
9. Preserves exact Decimal amount strings.
10. Copies full address/tx hash to clipboard.
11. Renders VASP node with classification and attribution context in Inspector.
12. Renders unresolved address with clean `Not identified` classification.

---

## 10. Test Results

- **Backend Pytest Suite:** `89 passed, 3 skipped, 0 failed in 2.25s`
- **Frontend Vitest Suite:** `12 passed, 0 failed in 0.693s`
- **Frontend Production Build:** `tsc && vite build` passed with 0 errors.

---

## 11. Attribution Semantics

- If $A \to B \to C \to D$ where $D$ is a known exchange address:
  - System reports: *"Known VASP-associated address $D$ was reached at hop 3 along forward fund flow."*
  - Provenance: Source and fixture/registry reference are attached to $D$.
  - Relationship: Graph connection / fund-flow proximity.

---

## 12. Explicit Statement on Ownership & Legal Proof

> [!IMPORTANT]
> **VASP Association $\neq$ Suspect Ownership.**  
> Identifying that an address on the fund-flow graph belongs to or is hosted by a VASP (e.g. Binance, Coinbase, Kraken) represents an **observational graph relationship** (i.e. funds moved to or from that exchange deposit/hot wallet). It does **NOT** prove that the suspect wallet owns or controls the exchange or the recipient account. Legal account attribution requires formal LEA subpoenas to the VASP.

---

## 13. Known Limitations

1. **Local Test Fixture Registry:** Phase 9 uses a deterministic local JSON registry. Live external entity resolution APIs (e.g., Etherscan labels, Arkham, Chainalysis) are intentionally abstracted and not called during automated testing.
2. **Deterministic Single/Multi Matches:** Address clustering and heuristic deposit wallet attribution are out of scope for Phase 9 and deferred to later phases.

---

## 14. Remaining Work for Phase 10

Phase 10 will implement:
- Evidence Panel & Case Dossier Assembly.
- Formal Subpoena / LEA Request Packet Generation.
- Exportable PDF / JSON forensic investigation reports.
