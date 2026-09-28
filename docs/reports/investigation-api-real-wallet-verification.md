# Investigation API Real Wallet Verification

## Wallet
Ethereum:
`0x28C6c06298d514Db089934071355E5743bf21d60`

## API
`POST /api/v1/investigations`

## Parameters
- `max_hops`: 1
- `max_transactions`: 5

## Provider
`BitqueryProvider`

## Dataset
`realtime`

## Offline Test Result
- Number passed: 58
- Number skipped: 2 (opt-in live Bitquery tests)
- Number failed: 0

## Live Test Result
- HTTP status: 200
- Investigation status: completed
- Nodes: 7
- Edges: 5
- Transactions: 5
- Transfers: 5
- Hops: 1

## Verification
- Real Bitquery provider reached via `ProviderFactory.get_provider()`
- Real blockchain data normalized into canonical `NormalizedTransfer` and `NormalizedTransaction`
- `InvestigationService` orchestrated collection, graph creation, and traversal
- Fund-flow graph constructed via `GraphBuilder`
- Breadth-First Search traversal executed via `GraphTraversalEngine`
- API response serialized correctly into `InvestigationResponse`
- Decimal amounts preserved as exact string serialization
- Root wallet (`0x28c6c06298d514db089934071355e5743bf21d60`) identified as `SUSPECT`
- No provider internals, GraphQL queries, API keys, or raw headers exposed

## Bitquery Safety
Confirm:
- Normal pytest execution made **zero live calls** (all offline fixtures and mocks passed).
- Live test was explicitly opt-in (`RUN_LIVE_BITQUERY=1` and `DATA_SOURCE_MODE=LIVE_BITQUERY`).
- No unnecessary requests were made (bounded strictly to `max_hops=1, max_transactions=5`).

## Files Changed
- `tests/integration/test_investigation_live.py` (updated with strict assertions for live API pipeline and zero provider leakage).
- `docs/reports/investigation-api-real-wallet-verification.md` (created verification report).

## Issues
- None. The live end-to-end investigation pipeline executed and passed without errors.
