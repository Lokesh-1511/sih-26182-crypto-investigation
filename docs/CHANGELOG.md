# Changelog: SIH 26182 Crypto Investigation Platform

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-03-18
### Added
- **Monorepo Architecture**: Clean separation across Member 1 (Ingestion), Member 2 (Graph/Attribution), and Member 3 (Platform/UI).
- **Comprehensive Documentation Suite**: 16 dedicated specification documents in `/docs` covering requirements, architecture, legal boundaries, and validation plans.
- **Shared Pydantic Schemas**: Immutable schema contracts for Case, Wallet, Transaction, Graph, Attribution, Risk, and Snapshot.
- **Multi-Chain Validation**: Cryptographic checksum validation for Bitcoin (Base58Check/Bech32), Ethereum (EIP-55), and Tron (Base58Check).
- **Blockchain Adapter Interface**: Dual-mode `BlockchainProvider` supporting offline cached fixtures and extensible live APIs.
- **NetworkX Graph Engine**: 3–5 hop BFS traversal, cycle detection, and dust suppression filters.
- **Explainable VASP Attribution**: Multi-factor scoring ($w_1..w_5$), Explainable Attribution Card points breakdown, and Counterfactual Sensitivity simulation.
- **Operator vs Beneficiary Separation**: Strict legal guardrail ensuring infrastructure attribution does not overclaim customer identity.
- **Obfuscation Breakpoint Detection**: Algorithmic detection of fan-out bursts, rapid relays, and bridge hops.
- **Controlled Demo Datasets**: Case A (Direct BTC sweep), Case B (4-hop ETH layered flow), and Case C (Cross-chain bridge).
- **Forensic Reporting & Action Packets**: Automated case report generation with SHA-256 integrity hash and draft Section 91 CrPC legal notices.
- **Investigation Console UI**: Plain CSS / CSS Modules dark-mode LEA console with Cytoscape.js interactive graph rendering.
