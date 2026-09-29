# Dashboard Investigation Integration

## Frontend
- **Framework**: React 18
- **Bundler & Tooling**: Vite 5 + TypeScript 5
- **Graph Engine**: Cytoscape.js 3.28
- **Route / View**: `Wallet Investigation` (`activeNav = 'INVESTIGATION'`) integrated into primary sidebar navigation.

## API
- **Endpoint**: `POST /api/v1/investigations` (and `POST /api/investigations`)
- **Transport**: HTTP JSON via centralized API client `investigateWallet()`

## Request
```json
{
  "chain": "ethereum",
  "address": "0x28C6c06298d514Db089934071355E5743bf21d60",
  "max_hops": 1,
  "max_transactions": 50
}
```

## Response
```json
{
  "investigation_id": "inv_...",
  "chain": "ethereum",
  "root_address": "0x28c6c06298d514db089934071355e5743bf21d60",
  "status": "completed",
  "summary": {
    "nodes": 7,
    "edges": 5,
    "transactions": 5,
    "transfers": 5,
    "hops": 1
  },
  "graph": {
    "nodes": [ ... ],
    "edges": [ ... ]
  }
}
```

## Components Created
1. `src/pages/WalletInvestigationPage.tsx`: Dedicated investigator workspace with form inputs, realistic multi-step loading indicators, error banners, KPI summary cards, fund-flow graph container, interactive node/edge inspector drawer, and activity table with clipboard copy utilities.
2. `src/components/WalletFundFlowGraph.tsx`: Cytoscape directed fund-flow visualizer supporting MultiDiGraphs, visual designation for root `SUSPECT` nodes, exact Decimal string amounts on edge labels, interactive node/edge tap selection, hierarchical and force-directed layouts, and viewport zoom/fit controls.
3. `src/test/WalletInvestigationPage.test.tsx`: 10 comprehensive unit/integration tests using Vitest and React Testing Library.
4. `src/test/setup.ts`: Test setup polyfilling JSDOM 2D Canvas context, ResizeObserver, and Clipboard APIs.

## API Client
- Implemented `investigateWallet(request: InvestigationCreateRequest): Promise<InvestigationResponse>` in `src/services/api.ts`.
- Strictly typed to `InvestigationResponse`, `InvestigationSummary`, `InvestigationNode`, and `InvestigationEdge`.
- Maps HTTP status codes (400, 422, 429, 502, 503, 504) and JSON detail payloads into clean, human-readable error messages.

## Graph Visualization
- **MultiDiGraph Support**: Individual transfers between the same addresses are preserved as separate bezier-curved edges.
- **Directionality**: Directed edges (`source -> target`) with arrowheads pointing strictly in the direction of fund movement.
- **Root Suspect Styling**: Prominently marked with `[SUSPECT]` label and distinct visual border/background.
- **Precision**: Exact string representation of transfer amounts is preserved on all edge labels and details.

## Error Handling
- **400 / 422**: Human-readable messages for invalid wallet addresses or out-of-bounds parameters.
- **429**: Specific upstream rate-limit notice.
- **502 / 503 / 504**: Clear upstream provider communication, unavailability, or timeout notices.
- **Network Error**: Graceful connection failure notification when backend is offline.

## Testing
- **Suite**: Vitest + React Testing Library + JSDOM.
- **Result**: 10 passed out of 10 tests in 0.54s.
- **Verifications**:
  1. Form rendering with inputs and submit action.
  2. Request submission with proper payload.
  3. KPI summary cards population.
  4. Root suspect wallet rendering.
  5. Graph nodes and edges rendering.
  6. Transfer inspection drawer on edge selection.
  7. Clear error message display on rejection.
  8. Empty investigation handling with 0 transfers.
  9. Preservation of exact Decimal strings (no float conversions).
  10. Copy-to-clipboard preservation of full untruncated values.

## Real Wallet Verification
Verified with real Ethereum wallet `0x28C6c06298d514Db089934071355E5743bf21d60`:
- **HTTP status**: 200 OK
- **Status**: `completed`
- **Nodes**: 7
- **Edges**: 5
- **Transactions**: 5
- **Transfers**: 5
- **Hops**: 1

## Security
Confirm:
- Browser **never** calls Bitquery directly; all intelligence flows via `POST /api/v1/investigations`.
- API credentials and tokens remain strictly on the backend.
- No internal provider details, GraphQL payloads, or stack traces leak to the client.

## Issues
- None. The frontend and backend communicate cleanly through the validated API contract.
