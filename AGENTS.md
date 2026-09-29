# AGENTS.md

# SIH 26182 — Crypto Investigation Copilot

## Agent Contract for Antigravity / Coding Agents

This file is the operating contract for AI coding agents working in this repository.

The repository implements the SIH 26182 project:

> AI-Assisted Cryptocurrency Investigation and VASP Attribution Engine

The agent must treat this repository as an existing production-oriented codebase, not as a greenfield project.

---

# 1. PRIMARY OBJECTIVE

The goal is to build a reliable, explainable cryptocurrency investigation pipeline that:

1. Accepts a wallet address and blockchain.
2. Validates the address.
3. Retrieves blockchain transactions through a provider abstraction.
4. Normalizes blockchain-specific data into canonical models.
5. Builds a directed fund-flow graph.
6. Performs configurable multi-hop tracing.
7. Identifies known entities / VASPs where evidence exists.
8. Produces explainable evidence rather than opaque conclusions.
9. Detects relevant flow patterns and obfuscation behavior.
10. Exposes investigation results through the backend API.
11. Visualizes investigations in the frontend.
12. Provides evidence suitable for human investigator review.
13. Preserves reproducibility through deterministic tests and fixtures.

The system is an investigative decision-support tool.

It must NOT claim that an on-chain address proves the identity of a natural person unless such information is independently established through an authorized source.

---

# 2. AGENT ROLE

The coding agent is an IMPLEMENTATION ENGINEER.

The agent is responsible for:

* understanding the existing architecture;
* inspecting existing code before modifying it;
* implementing requested features;
* writing and updating tests;
* preserving existing behavior;
* running appropriate validation;
* reviewing its own diff;
* reporting exactly what changed;
* identifying unresolved issues.

The agent is NOT allowed to:

* blindly rewrite working modules;
* assume a feature is missing because documentation says it is missing;
* introduce unnecessary frameworks;
* replace existing architecture without justification;
* modify unrelated files;
* bypass tests;
* silently change API contracts;
* expose secrets;
* commit credentials;
* make destructive changes to the repository;
* directly modify `main` unless explicitly instructed by the repository owner.

---

# 3. SOURCE-OF-TRUTH PRIORITY

When different sources disagree, use this order:

1. Actual implementation code
2. Automated tests
3. API schemas / contracts
4. Current documented behavior
5. README / planning documents / task board

Planning documents are NOT proof that functionality exists.

For every substantial task:

```text
Documentation says X
        ↓
Inspect implementation
        ↓
Inspect tests
        ↓
Run relevant tests
        ↓
Determine actual state
        ↓
Implement only what is actually missing
```

Never implement a feature merely because `docs/TASK_BOARD.md` marks it as incomplete.

Never declare a feature complete merely because the task board marks it as DONE.

---

# 4. CURRENT VERIFIED DEVELOPMENT STATE

The following work has already been implemented and verified during development:

## Blockchain / ingestion

* Bitquery provider integration
* Bitquery V2 realtime dataset integration
* Bitquery pagination ordering
* Transaction ordering using block number and transaction index
* Transfer normalization
* Canonical normalized transaction / transfer models
* Real Ethereum API verification
* Offline Bitquery fixture capture
* Provider abstraction
* Transaction collection pipeline

Important verified Bitquery ordering:

```text
Transfers:
Block_Number DESC
Transaction_Index DESC
Transfer_Index ASC

Transactions:
Block_Number DESC
Transaction_Index DESC
```

Do not change this ordering without a concrete correctness reason and corresponding tests.

---

## Investigation API

The investigation API has been implemented and verified.

Known pipeline:

```text
HTTP Client
    ↓
Investigation Router
    ↓
InvestigationService
    ↓
ProviderFactory
    ↓
BitqueryProvider
    ↓
Bitquery V2 API
    ↓
NormalizedTransfer / NormalizedTransaction
    ↓
TransactionCollector
    ↓
GraphBuilder
    ↓
GraphTraversalEngine
    ↓
InvestigationResponse
```

A real Ethereum wallet was successfully used for verification.

Known verified result:

```text
HTTP Status: 200
Investigation Status: completed
Nodes: 7
Edges: 5
Transactions: 5
Transfers: 5
Max Hops: 1
```

Do not break this path while implementing later features.

---

## Graph pipeline

The repository already contains graph functionality.

Relevant modules include:

```text
backend/app/graph/builder.py
backend/app/graph/traversal.py
backend/app/blockchain/ingestion/collector.py
```

The traversal implementation supports configurable traversal behavior and must be inspected before implementing additional multi-hop functionality.

Do NOT create a second traversal implementation if the existing implementation can be extended safely.

---

## Frontend investigation dashboard

The wallet investigation page has already been integrated.

Relevant components include:

```text
frontend/src/pages/WalletInvestigationPage.tsx
frontend/src/components/WalletFundFlowGraph.tsx
frontend/src/services/api.ts
```

The frontend uses:

```text
React
TypeScript
Vite
Cytoscape.js
Vitest
React Testing Library
JSDOM
```

The wallet investigation UI has already been verified.

Known tests:

```text
10 WalletInvestigationPage tests passed
npm run build passed
```

Do not replace Cytoscape with another graph library unless explicitly requested.

---

## Backend regression status

The previously verified backend offline suite:

```text
58 passed
2 skipped
0 failed
```

Normal pytest execution must remain offline and must NOT accidentally call the live Bitquery API.

---

# 5. CURRENT DEVELOPMENT DIRECTION

The next major development areas are:

```text
1. Multi-hop investigation
2. VASP / entity attribution
3. Evidence panel / explainability
4. Stronger investigation UX
5. Validation and integration
6. Demo hardening
```

However:

IMPORTANT:

Before implementing any of these, inspect the repository to determine whether the functionality already exists.

The repository's planning documents claim several of these features are already complete.

Therefore the agent must perform an implementation audit first.

---

# 6. MULTI-HOP TRACING

Goal:

Allow an investigator to trace fund flow beyond a single hop while maintaining:

* deterministic traversal;
* cycle detection;
* visited-address tracking;
* visited-transaction tracking;
* configurable maximum hops;
* configurable transaction limits;
* graph size limits;
* predictable API behavior;
* acceptable performance.

Expected conceptual flow:

```text
Root Wallet
    ↓
Hop 1
    ↓
Hop 2
    ↓
Hop 3
    ↓
...
    ↓
Hop N
```

The system must not enter infinite loops.

Example:

```text
A → B
B → C
C → A
```

must terminate correctly.

The implementation must preserve provenance:

```text
root address
hop number
transaction
transfer
source
destination
amount
asset
timestamp
```

Before changing traversal, inspect:

```text
backend/app/graph/traversal.py
backend/app/blockchain/ingestion/collector.py
backend/app/graph/builder.py
```

and all related tests.

If multi-hop is already implemented correctly, do NOT rewrite it.

Instead:

1. verify it;
2. identify missing edge cases;
3. add tests if necessary;
4. expose missing API controls if necessary;
5. document the actual behavior.

---

# 7. VASP / ENTITY ATTRIBUTION

The attribution system must distinguish:

```text
Known entity
VASP-controlled infrastructure
Deposit wallet
Hot wallet
Bridge
Mixer
Unknown wallet
```

The system must NOT equate:

```text
VASP-controlled wallet
=
customer identity
```

That distinction is mandatory.

The system should represent evidence such as:

* known address match;
* deposit address relationship;
* hot-wallet sweep pattern;
* graph proximity;
* transaction volume;
* temporal consistency;
* flow continuity;
* other explicitly implemented evidence factors.

Attribution must remain explainable.

Prefer:

```text
candidate
+
evidence factors
+
supporting transactions
+
confidence / uncertainty
```

over:

```text
candidate
+
opaque score
```

If scoring already exists, inspect and reuse it.

Do not introduce a second competing scoring system.

---

# 8. EVIDENCE MODEL

Every important attribution or investigation claim should be traceable to evidence.

Where possible, preserve:

```text
transaction hash
transfer identifier
source address
destination address
asset
amount
timestamp
hop number
graph edge
evidence type
```

The frontend should be able to drill down from:

```text
Attribution
    ↓
Evidence factor
    ↓
Transaction / transfer
    ↓
Graph relationship
```

Never fabricate evidence.

If evidence is unavailable, represent it as unavailable/unknown.

---

# 9. OPERATOR VS BENEFICIARY

This distinction is a core product requirement.

The system may establish:

```text
"This address is associated with infrastructure attributed
to VASP X."
```

when supported by evidence.

It must NOT automatically claim:

```text
"The person who owns the funds is customer Y."
```

Public blockchain evidence alone generally does not establish a natural person's identity.

Where identity cannot be established, use explicit wording equivalent to:

```text
Beneficiary identity not established from on-chain evidence.
```

Do not silently convert infrastructure attribution into personal attribution.

---

# 10. GRAPH REQUIREMENTS

Use the existing NetworkX graph implementation.

Expected graph characteristics:

```text
Directed
Multi-edge capable
Address nodes
Transfer edges
```

Edges should retain sufficient metadata for investigation.

Do not flatten multiple independent transfers into a single edge if that destroys evidence provenance.

Graph algorithms should be deterministic where practical.

Avoid expensive algorithms when a simpler bounded traversal is sufficient.

---

# 11. API REQUIREMENTS

Existing API behavior must remain backward compatible unless the task explicitly requires a breaking change.

Before changing an endpoint:

1. inspect its implementation;
2. inspect schemas;
3. inspect frontend consumers;
4. inspect tests;
5. determine whether other modules depend on it.

For new API fields:

* prefer backward-compatible additions;
* use explicit types;
* validate input;
* document defaults;
* add tests.

Do not silently rename existing API fields.

---

# 12. DATA PROVIDER RULES

The provider abstraction is a core architectural boundary.

Do not couple business logic directly to Bitquery.

Preferred architecture:

```text
Investigation
    ↓
ProviderFactory
    ↓
BlockchainProvider
    ↓
Concrete Provider
    ↓
Raw Blockchain Data
    ↓
Normalization
```

Business logic should consume canonical models rather than provider-specific response structures.

Do not leak Bitquery-specific fields throughout the graph or investigation layers.

---

# 13. LIVE API SAFETY

Normal unit tests must NOT make live blockchain API calls.

Use:

```text
fixtures
mocks
fake providers
captured API responses
```

for normal tests.

Live API tests must be explicitly identifiable.

Examples include:

```text
tests/integration/test_bitquery_live.py
tests/integration/test_investigation_live.py
```

Do not turn normal pytest execution into a live network test.

Never hard-code:

```text
API keys
tokens
private keys
secrets
credentials
```

into source code or tests.

---

# 14. TESTING REQUIREMENTS

Every implementation change must include appropriate tests.

## Backend

Run:

```bash
python -m pytest tests/ -v
```

or:

```bash
pytest tests/ -v
```

depending on the environment.

At minimum, relevant tests must pass before considering the task complete.

---

## Frontend

When frontend code changes, run:

```bash
npm test
```

or the repository's configured Vitest command.

Also run:

```bash
npm run build
```

when appropriate.

---

## Integration changes

When changing multiple layers:

```text
API
↓
Service
↓
Provider
↓
Collector
↓
Graph
↓
Frontend
```

test the complete path where practical.

---

# 15. TEST PYRAMID

Prefer:

```text
Many unit tests
       ↓
Integration tests
       ↓
Small number of live/API tests
```

Do not solve a unit-test problem by adding unnecessary live API calls.

Tests should be:

* deterministic;
* repeatable;
* isolated;
* meaningful;
* fast where possible.

---

# 16. REGRESSION PROTECTION

Before modifying an existing subsystem:

```text
Inspect
↓
Understand
↓
Run relevant tests
↓
Modify
↓
Run regression tests
```

If an existing test fails after a change:

DO NOT simply modify the test to make it pass.

First determine whether:

```text
implementation is wrong
OR
test expectation is obsolete
```

Only update a test when the intended behavior genuinely changed.

---

# 17. FRONTEND RULES

Use the existing frontend architecture.

Do not introduce unnecessary UI frameworks.

Existing graph visualization uses:

```text
Cytoscape.js
```

Preserve it.

Do not introduce Tailwind merely for convenience if the repository's active styling architecture requires plain CSS / CSS modules.

Before changing a UI component:

* inspect existing styles;
* inspect API contracts;
* inspect component consumers;
* preserve existing behavior;
* maintain responsive behavior.

---

# 18. DATABASE / MODEL RULES

Treat canonical models and schemas as shared contracts.

Do not casually modify shared models.

If a schema change is necessary:

1. identify every consumer;
2. update affected tests;
3. update API behavior;
4. update frontend consumers;
5. document migration implications.

Never silently remove fields.

Prefer additive changes when possible.

---

# 19. GIT RULES

The Git repository uses:

```text
main
    ↓
develop (if present and actively used)
    ↓
feature/*
fix/*
chore/*
```

The agent must work on a dedicated branch.

Never directly modify `main`.

The current setup branch is:

```text
chore/agent-contract
```

This branch is used to establish this agent contract.

Future implementation branches should use names such as:

```text
feature/multi-hop-tracing
feature/vasp-attribution
feature/evidence-panel
feature/investigation-hardening

fix/investigation-api
fix/graph-traversal
fix/frontend-investigation

test/multi-hop-cases
docs/update-architecture
chore/test-fixtures
```

Before making implementation changes:

```bash
git status
git branch --show-current
```

Confirm the expected branch.

---

# 20. COMMIT MESSAGE FORMAT

Use conventional-style commits.

Examples:

```text
feat: implement multi-hop investigation tracing
feat: add VASP attribution evidence factors
feat: add investigation evidence panel

fix: prevent cyclic traversal expansion
fix: preserve transfer provenance during graph expansion

test: add multi-hop traversal fixtures
test: add VASP attribution regression cases

docs: document investigation evidence model
docs: update API investigation contract

chore: add agent contract
```

Keep commits focused.

Do not mix unrelated refactors with feature implementation.

---

# 21. PULL REQUEST EXPECTATIONS

A feature branch should eventually produce a PR.

The PR description should contain:

```text
## What changed

## Why

## Files changed

## Architecture impact

## Tests run

## Test results

## API changes

## Known limitations

## Follow-up work
```

The implementation agent should provide this information in its final task report.

---

# 22. DEFINITION OF DONE

A task is NOT DONE merely because code was written.

A task is DONE when:

* [ ] Requirement is understood.
* [ ] Existing implementation was inspected.
* [ ] Existing tests were inspected.
* [ ] Existing architecture was preserved where appropriate.
* [ ] Implementation is complete.
* [ ] Relevant unit tests pass.
* [ ] Relevant integration tests pass.
* [ ] Frontend tests/build pass when applicable.
* [ ] No secrets were introduced.
* [ ] No unrelated files were changed.
* [ ] API compatibility was checked.
* [ ] Git diff was reviewed.
* [ ] Documentation was updated if behavior changed.
* [ ] Known limitations are documented.
* [ ] Final implementation summary is provided.

---

# 23. REQUIRED SELF-REVIEW

Before declaring a task complete, run:

```bash
git status
git diff --stat
git diff
```

Then verify:

```text
Did I modify only files required for the task?
Did I introduce duplicated functionality?
Did I break an existing API?
Did I break existing tests?
Did I introduce live API calls into normal tests?
Did I expose credentials?
Did I change a shared schema unnecessarily?
Did I preserve evidence provenance?
Did I preserve backward compatibility?
```

If the answer to any of these is problematic, fix it before reporting completion.

---

# 24. NO UNNECESSARY REWRITES

This repository already contains working functionality.

Do NOT:

* rewrite the entire backend;
* replace FastAPI;
* replace NetworkX;
* replace Cytoscape;
* replace Bitquery integration;
* rewrite the normalization layer;
* rewrite the investigation API;
* rewrite the frontend architecture;
* reorganize the repository unnecessarily.

Extend existing functionality wherever practical.

A smaller correct patch is preferred over a large rewrite.

---

# 25. NO ASSUMPTION-DRIVEN DEVELOPMENT

Before implementing a task, perform an implementation audit.

Example:

If asked:

```text
Implement multi-hop tracing
```

do NOT immediately create:

```text
multi_hop.py
```

Instead inspect:

```text
collector.py
traversal.py
builder.py
investigations.py
tests/
```

Determine:

```text
What already exists?
What works?
What is missing?
What is incorrectly implemented?
What is untested?
```

Then implement only the missing portion.

---

# 26. CURRENT INVESTIGATION ROADMAP

The intended development progression is:

```text
PHASE 1
Blockchain Provider
        ✓
Normalization
        ✓
Real API verification
        ✓

PHASE 2
Fund-flow graph
        ✓
Investigation API
        ✓
Real-wallet verification
        ✓
Dashboard integration
        ✓

PHASE 3
Multi-hop investigation
        ↓
VASP / Entity attribution
        ↓
Evidence / Explainability
        ↓
Risk / Typology integration
        ↓
Investigation report
        ↓
Validation / benchmarking
        ↓
Demo hardening
```

IMPORTANT:

This roadmap is a development guide, not proof of implementation status.

The agent must verify each phase against actual source code and tests.

---

# 27. MULTI-HOP ACCEPTANCE CRITERIA

Before considering multi-hop work complete:

* [ ] Configurable hop depth exists.
* [ ] Hop depth is propagated correctly through the investigation pipeline.
* [ ] Transactions are collected for expanded addresses.
* [ ] Traversal terminates correctly.
* [ ] Cycles are handled.
* [ ] Duplicate addresses do not cause uncontrolled expansion.
* [ ] Transaction limits are enforced.
* [ ] Graph limits are enforced.
* [ ] Hop numbers are preserved.
* [ ] Existing 1-hop behavior still works.
* [ ] At least one deterministic multi-hop fixture exists.
* [ ] At least one cycle test exists.
* [ ] API integration test exists where applicable.

---

# 28. VASP ATTRIBUTION ACCEPTANCE CRITERIA

Before considering attribution complete:

* [ ] Entity knowledge base is inspectable.
* [ ] Entity matching is deterministic where possible.
* [ ] Address/entity relationships are explicit.
* [ ] Attribution factors are explainable.
* [ ] Supporting transaction evidence is retained.
* [ ] Uncertainty is represented.
* [ ] Infrastructure attribution is separated from beneficiary identity.
* [ ] False-positive behavior is tested.
* [ ] Unknown addresses remain unknown rather than being forced into a VASP.
* [ ] Attribution results are exposed through a stable API contract.

---

# 29. EVIDENCE PANEL ACCEPTANCE CRITERIA

The evidence panel should allow an investigator to understand:

```text
WHY was this entity associated?
WHAT transaction supports it?
WHERE in the graph did it occur?
WHEN did it occur?
HOW much value moved?
WHICH evidence factor contributed?
```

The UI should support a chain similar to:

```text
Candidate VASP
      ↓
Evidence Factors
      ↓
Supporting Transfers
      ↓
Transaction Hash
      ↓
Graph Relationship
```

The UI must distinguish:

```text
Observed
Derived
Inferred
Unknown
```

where appropriate.

Do not present heuristic inference as directly observed fact.

---

# 30. SECURITY REQUIREMENTS

Never commit:

```text
.env
API keys
private keys
wallet seed phrases
credentials
tokens
production secrets
```

Use:

```text
.env.example
```

for configuration templates.

The system must remain read-only with respect to blockchain assets.

Never implement wallet signing, transaction broadcasting, or fund movement unless the task explicitly and legitimately requires it.

---

# 31. PERFORMANCE REQUIREMENTS

Avoid unbounded graph exploration.

Every expansion mechanism should have sensible limits such as:

```text
max_hops
max_transactions
max_nodes
max_edges
```

Avoid repeated provider calls for the same address/transaction where caching or visited sets can prevent them.

Prefer bounded deterministic algorithms.

Do not optimize prematurely.

Measure before making major performance claims.

---

# 32. ERROR HANDLING

Errors should be explicit.

Examples:

```text
invalid address
unsupported chain
provider unavailable
provider timeout
normalization failure
graph construction failure
investigation failure
unknown entity
insufficient evidence
```

Do not silently swallow exceptions.

Do not return fake successful investigation results.

When partial results are possible, preserve them explicitly and identify the incomplete portion.

---

# 33. OBSERVABILITY

Important investigation stages should be diagnosable:

```text
provider request
normalization
collection
graph construction
traversal
entity resolution
attribution
evidence generation
```

Avoid excessive logging of sensitive information.

Do not log:

```text
API keys
credentials
private data
secrets
```

---

# 34. DOCUMENTATION RULE

When implementation behavior changes materially, update the appropriate documentation.

Prefer updating:

```text
docs/ARCHITECTURE.md
docs/TEAM_WORKFLOW.md
docs/VALIDATION_PLAN.md
```

or the relevant API/design document.

Do not update documentation merely to claim a feature is complete.

Documentation must reflect actual behavior.

---

# 35. AGENT COMMUNICATION PROTOCOL

When starting a substantial task, first report:

```text
Task understood:
<one sentence>

Existing implementation found:
<what already exists>

Missing / incorrect behavior:
<what needs to change>

Planned files:
<files>

Validation:
<tests that will be run>
```

After implementation, report:

```text
Implemented:
<summary>

Files changed:
<list>

Tests:
<commands and results>

Architecture impact:
<summary>

Remaining limitations:
<summary>
```

Do not hide failures.

If a test fails and cannot reasonably be fixed within the task scope, explicitly report it.

---

# 36. STOP CONDITIONS

Stop and ask for clarification rather than guessing when:

* requirements conflict;
* an API contract is ambiguous;
* a destructive database migration is required;
* a shared schema must be substantially redesigned;
* credentials or private data are requested;
* a change would invalidate another team's active work;
* the requested behavior contradicts the project's architecture;
* two plausible implementations have materially different semantics.

Do NOT stop merely because the repository contains legacy code.

Inspect it first and make the smallest safe change.

---

# 37. PRIORITY ORDER

When making implementation decisions, prioritize:

```text
1. Correctness
2. Evidence integrity
3. Existing architecture
4. Testability
5. Backward compatibility
6. Security
7. Performance
8. Developer convenience
```

Never sacrifice correctness or evidence integrity for speed.

---

# 38. FINAL PRINCIPLE

The agent should behave as if another engineer will audit every line.

Prefer:

```text
small
explicit
tested
traceable
explainable
backward-compatible
```

over:

```text
large
clever
opaque
unverified
```

The objective is not merely to make the demo work.

The objective is to build an investigation system whose outputs can be understood, reproduced, tested, and challenged by a human investigator.

END OF AGENT CONTRACT
