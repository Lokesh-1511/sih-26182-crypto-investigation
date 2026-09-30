// frontend/src/pages/WalletInvestigationPage.tsx
import React, { useState } from 'react';
import * as api from '../services/api';
import {
  InvestigationResponse,
  InvestigationNode,
  InvestigationEdge,
  InvestigationCreateRequest,
  EvidenceItem,
  EvidenceClass,
  LawfulActionPacketData
} from '../services/api';
import { WalletFundFlowGraph } from '../components/WalletFundFlowGraph';
import { ActionPacketModal } from '../components/ActionPacketModal';


interface Props {
  theme?: 'light' | 'dark';
}

export const WalletInvestigationPage: React.FC<Props> = ({ theme = 'light' }) => {
  // Form State
  const [chain, setChain] = useState<string>('ethereum');
  const [address, setAddress] = useState<string>('0x28C6c06298d514Db089934071355E5743bf21d60');
  const [direction, setDirection] = useState<'outgoing' | 'incoming'>('outgoing');
  const [maxHops, setMaxHops] = useState<number>(1);
  const [maxTransactions, setMaxTransactions] = useState<number>(50);

  // Execution & Response State
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingStep, setLoadingStep] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [investigationData, setInvestigationData] = useState<InvestigationResponse | null>(null);

  // Inspection Selection State
  const [selectedNode, setSelectedNode] = useState<InvestigationNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<InvestigationEdge | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Phase 10 Evidence & Export State
  const [evidenceFilter, setEvidenceFilter] = useState<'ALL' | EvidenceClass>('ALL');
  const [actionPacketModalOpen, setActionPacketModalOpen] = useState<boolean>(false);
  const [actionPacketData, setActionPacketData] = useState<LawfulActionPacketData | null>(null);
  const [exportLoading, setExportLoading] = useState<boolean>(false);
  const [exportStatusMessage, setExportStatusMessage] = useState<string | null>(null);


  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => {
      setCopiedKey((prev) => (prev === key ? null : prev));
    }, 2000);
  };

  const handleInvestigate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!address.trim()) {
      setError('Please enter a target wallet address.');
      return;
    }

    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setSelectedEdge(null);

    // Progressive step indicator
    setLoadingStep('Collecting multi-hop blockchain transactions...');

    const stepTimer1 = setTimeout(() => {
      setLoadingStep('Building fund-flow graph...');
    }, 600);

    const stepTimer2 = setTimeout(() => {
      setLoadingStep('Analyzing transfer relationships...');
    }, 1200);

    try {
      const req: InvestigationCreateRequest = {
        chain,
        address: address.trim(),
        direction,
        max_hops: Number(maxHops),
        max_transactions: Number(maxTransactions)
      };
      const resp = await api.investigateWallet(req);
      setInvestigationData(resp);
    } catch (err: any) {
      console.error('INVESTIGATION_ERROR_LOG:', err);
      setError(err.message || 'An unexpected error occurred during investigation.');
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setLoading(false);
      setLoadingStep('');
    }
  };

  const formatAddress = (addr: string) => {
    if (!addr) return '';
    const cleanAddr = addr.includes(':') ? addr.split(':')[1] : addr;
    if (cleanAddr.length <= 14) return cleanAddr;
    return `${cleanAddr.slice(0, 6)}...${cleanAddr.slice(-4)}`;
  };

  const formatTxHash = (hash: string) => {
    if (!hash) return '';
    if (hash.length <= 16) return hash;
    return `${hash.slice(0, 10)}...${hash.slice(-6)}`;
  };

  const handleSelectNode = (node: InvestigationNode | null) => {
    setSelectedNode(node);
    if (node) setSelectedEdge(null);
  };

  const handleSelectEdge = (edge: InvestigationEdge | null) => {
    setSelectedEdge(edge);
    if (edge) setSelectedNode(null);
  };

  const handleExportDossier = async () => {
    if (!investigationData) return;
    setExportLoading(true);
    setExportStatusMessage('Exporting Case Dossier...');
    try {
      const dossier = await api.fetchInvestigationDossier(investigationData);
      api.downloadJsonFile(dossier, `dossier_${investigationData.investigation_id}.json`);
      setExportStatusMessage('✓ Dossier JSON exported successfully');
      setTimeout(() => setExportStatusMessage(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to export case dossier');
    } finally {
      setExportLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!investigationData) return;
    setExportLoading(true);
    setExportStatusMessage('Generating Forensic Report...');
    try {
      const report = await api.generateInvestigationReport(investigationData);
      api.downloadHtmlFile(report.html_content, `report_${investigationData.investigation_id}.html`);
      setExportStatusMessage('✓ Report downloaded successfully');
      setTimeout(() => setExportStatusMessage(null), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setExportLoading(false);
    }
  };

  const handleOpenActionPacket = async () => {
    if (!investigationData) return;
    setExportLoading(true);
    setExportStatusMessage('Drafting Lawful Action Packet...');
    try {
      const packet = await api.generateInvestigationActionPacket(investigationData);
      setActionPacketData(packet);
      setActionPacketModalOpen(true);
      setExportStatusMessage(null);
    } catch (err: any) {
      setError(err.message || 'Failed to draft action packet');
    } finally {
      setExportLoading(false);
    }
  };


  const handleEvidenceInspect = (ev: EvidenceItem) => {
    if (!investigationData || !investigationData.graph) return;
    
    // 1. Try to find matching edge
    if (ev.tx_hash || ev.transfer_id) {
      const edge = investigationData.graph.edges.find(
        (e) => (ev.transfer_id && e.transfer_id === ev.transfer_id) ||
               (ev.tx_hash && e.tx_hash.toLowerCase() === ev.tx_hash.toLowerCase())
      );
      if (edge) {
        handleSelectEdge(edge);
        return;
      }
    }

    // 2. Try to find matching destination/source node
    const targetAddr = ev.destination_address || ev.source_address;
    if (targetAddr) {
      const clean = targetAddr.includes(':') ? targetAddr.split(':')[1].toLowerCase() : targetAddr.toLowerCase();
      const node = investigationData.graph.nodes.find(
        (n) => n.address.toLowerCase() === clean || n.id.toLowerCase() === targetAddr.toLowerCase()
      );
      if (node) {
        handleSelectNode(node);
        return;
      }
    }
  };

  const rawEvidence = investigationData?.evidence_items || [];
  const filteredEvidence = evidenceFilter === 'ALL'
    ? rawEvidence
    : rawEvidence.filter((item) => item.evidence_class === evidenceFilter);

  const evidenceCounts = {
    ALL: rawEvidence.length,
    OBSERVED: rawEvidence.filter((i) => i.evidence_class === 'OBSERVED').length,
    RESOLVED: rawEvidence.filter((i) => i.evidence_class === 'RESOLVED').length,
    DERIVED: rawEvidence.filter((i) => i.evidence_class === 'DERIVED').length,
    INFERRED: rawEvidence.filter((i) => i.evidence_class === 'INFERRED').length,
    UNKNOWN: rawEvidence.filter((i) => i.evidence_class === 'UNKNOWN').length,
  };

  const handleRowClick = (edge: InvestigationEdge, evt?: React.MouseEvent) => {
    if (evt && (evt.target as HTMLElement)?.closest('.address-node-link')) {
      return;
    }
    handleSelectEdge(edge);
  };



  const isEmptyResult =
    investigationData &&
    investigationData.summary.transfers === 0 &&
    investigationData.summary.edges === 0;

  // Calculate Node In/Out Degree from Graph Edges
  const getNodeDegrees = (nodeId: string) => {
    if (!investigationData || !investigationData.graph) return { inDegree: 0, outDegree: 0 };
    const normId = nodeId.toLowerCase();
    const inDegree = investigationData.graph.edges.filter(
      (e) => e.target.toLowerCase() === normId
    ).length;
    const outDegree = investigationData.graph.edges.filter(
      (e) => e.source.toLowerCase() === normId
    ).length;
    return { inDegree, outDegree };
  };

  // Traversal path from root to selected node
  const getPathFromRoot = (targetNodeId: string) => {
    if (!investigationData || !investigationData.graph) return [];
    const rootNorm = investigationData.root_address.toLowerCase();
    const targetNorm = targetNodeId.toLowerCase();

    // Check if target is root
    if (targetNorm === rootNorm || targetNorm.endsWith(rootNorm)) {
      return [{ address: investigationData.root_address, hop: 0, isRoot: true }];
    }

    // BFS shortest path in traversal direction
    const isIncoming = investigationData.trace?.direction === 'incoming';
    const queue: Array<{ id: string; path: string[] }> = [
      { id: rootNorm, path: [investigationData.root_address] }
    ];
    const visited = new Set<string>([rootNorm]);

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current.id === targetNorm || current.id.endsWith(targetNorm)) {
        return current.path.map((addr, idx) => ({
          address: addr,
          hop: idx,
          isRoot: idx === 0
        }));
      }

      // Find outgoing neighbors along traversal direction
      const neighborEdges = investigationData.graph.edges.filter((e) => {
        const srcNorm = e.source.toLowerCase();
        const tgtNorm = e.target.toLowerCase();
        if (isIncoming) {
          return tgtNorm === current.id || tgtNorm.endsWith(current.id);
        } else {
          return srcNorm === current.id || srcNorm.endsWith(current.id);
        }
      });

      for (const e of neighborEdges) {
        const nextAddr = isIncoming ? e.source : e.target;
        const nextNorm = nextAddr.toLowerCase();
        if (!visited.has(nextNorm)) {
          visited.add(nextNorm);
          queue.push({
            id: nextNorm,
            path: [...current.path, nextAddr]
          });
        }
      }
    }

    // Fallback if not directly traversable
    return [
      { address: investigationData.root_address, hop: 0, isRoot: true },
      { address: targetNodeId, hop: selectedNode?.hop_distance ?? 1, isRoot: false }
    ];
  };

  // Structured trace termination description
  const getTerminationMessage = () => {
    if (!investigationData?.trace) return '• Investigation complete';
    const t = investigationData.trace;
    switch (t.termination_reason) {
      case 'MAX_HOPS_REACHED':
        return `• Trace stopped at maximum depth of ${t.requested_max_hops} hops.`;
      case 'TRANSACTION_LIMIT_REACHED':
        return `• Trace stopped at transaction limit of ${t.max_transactions}.`;
      case 'SAFETY_LIMIT_REACHED':
        return '• Trace stopped at graph safety limit.';
      case 'EMPTY_WALLET':
      case 'NO_TRANSFERS_FOUND':
        return '• No transfers found for target wallet.';
      case 'NATURAL_TERMINATION':
      default:
        return t.direction === 'incoming'
          ? '• No additional incoming transfers found.'
          : '• No additional outgoing transfers found.';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, gap: 8, overflowY: 'auto', paddingRight: 4 }}>
      {/* 1. Header & Investigation Controls (Compact horizontal toolbar) */}
      <div className="card-box" style={{ padding: '10px 14px', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
          <div>
            <h1 style={{ fontSize: 14, fontWeight: 800, margin: 0, letterSpacing: '0.02em', textTransform: 'uppercase', color: 'var(--text-primary)' }}>
              Wallet Investigation
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 10.5, margin: '1px 0 0 0' }}>
              Multi-hop fund-flow tracing and cryptocurrency forensic analysis workspace.
            </p>
          </div>

          <button
            type="button"
            className="btn-secondary"
            style={{ fontSize: 10.5, padding: '3px 8px' }}
            onClick={() => {
              setChain('ethereum');
              setAddress('0x28C6c06298d514Db089934071355E5743bf21d60');
              setDirection('outgoing');
              setMaxHops(1);
              setMaxTransactions(50);
            }}
          >
            Load Sample Wallet (Binance Hot Wallet)
          </button>
        </div>

        {/* Clean Horizontal Investigation Toolbar */}
        <form onSubmit={handleInvestigate} style={{ display: 'grid', gridTemplateColumns: '120px 145px 1fr 90px 105px auto', gap: 6, alignItems: 'end' }}>
          <div>
            <label style={{ display: 'block', fontSize: 9, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 2, letterSpacing: '0.04em' }}>
              Blockchain
            </label>
            <select
              className="select-input"
              style={{ width: '100%', padding: '4px 6px', fontSize: 11 }}
              value={chain}
              onChange={(e) => setChain(e.target.value)}
              disabled={loading}
            >
              <option value="ethereum">Ethereum (ETH)</option>
              <option value="bitcoin">Bitcoin (BTC)</option>
              <option value="tron">Tron (TRX)</option>
              <option value="polygon">Polygon (MATIC)</option>
              <option value="arbitrum">Arbitrum (ARB)</option>
              <option value="bsc">BNB Chain (BSC)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 9, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 2, letterSpacing: '0.04em' }}>
              Trace Direction
            </label>
            <select
              className="select-input"
              style={{ width: '100%', padding: '4px 6px', fontSize: 11 }}
              value={direction}
              onChange={(e) => setDirection(e.target.value as 'outgoing' | 'incoming')}
              disabled={loading}
            >
              <option value="outgoing">Forward (Outgoing)</option>
              <option value="incoming">Backward (Incoming)</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 9, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 2, letterSpacing: '0.04em' }}>
              Wallet Address
            </label>
            <input
              type="text"
              className="select-input mono"
              style={{ width: '100%', fontSize: 11, padding: '4px 6px' }}
              placeholder="0x..."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 9, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 2, letterSpacing: '0.04em' }}>
              Max Hops
            </label>
            <select
              className="select-input"
              style={{ width: '100%', padding: '4px 6px', fontSize: 11 }}
              value={maxHops}
              onChange={(e) => setMaxHops(Number(e.target.value))}
              disabled={loading}
            >
              <option value={1}>1 Hop</option>
              <option value={2}>2 Hops</option>
              <option value={3}>3 Hops</option>
              <option value={4}>4 Hops</option>
              <option value={5}>5 Hops</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: 9, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 2, letterSpacing: '0.04em' }}>
              Max Transactions
            </label>
            <input
              type="number"
              className="select-input"
              style={{ width: '100%', padding: '4px 6px', fontSize: 11 }}
              min={1}
              max={200}
              value={maxTransactions}
              onChange={(e) => setMaxTransactions(Number(e.target.value))}
              disabled={loading}
            />
          </div>

          <div>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ height: 26, padding: '0 14px', fontSize: 11, whiteSpace: 'nowrap' }}
            >
              {loading ? 'Investigating...' : 'Investigate Wallet'}
            </button>
          </div>
        </form>
      </div>

      {/* Loading Banner */}
      {loading && (
        <div className="card-box" style={{ padding: '8px 14px', background: 'var(--accent-primary-subtle)', borderColor: 'var(--accent-primary-border)', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="status-dot-pulse" style={{ width: 7, height: 7 }} />
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent-primary)' }}>
                Investigating wallet...
              </div>
              <div style={{ fontSize: 10.5, color: 'var(--text-secondary)' }}>
                {loadingStep || 'Querying blockchain provider...'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="card-box" style={{ padding: '8px 14px', background: 'var(--sig-critical-bg)', borderColor: 'var(--sig-critical-border)', flexShrink: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--sig-critical)' }}>
              <strong style={{ fontSize: 11 }}>Investigation Error:</strong>
              <span style={{ fontSize: 11 }}>{error}</span>
            </div>
            <button
              type="button"
              className="tool-btn"
              onClick={() => setError(null)}
              style={{ border: 'none', background: 'transparent', color: 'var(--sig-critical)' }}
            >
              &times; Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Compact Ready State (Zero extra vertical padding) */}
      {!investigationData && !loading && !error && (
        <div className="card-box" style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-muted)', flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" style={{ color: 'var(--accent-primary)', opacity: 0.8 }}>
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>
            Ready to Investigate
          </div>
          <p style={{ fontSize: 11, maxWidth: 440, margin: 0 }}>
            Enter a target cryptocurrency wallet address above or click <strong>Load Sample Wallet</strong> to start forensic fund-flow analysis.
          </p>
        </div>
      )}

      {/* 2. Investigation Results Workspace (Immediately follows controls) */}
      {investigationData && (
        <>
          {/* Metadata Status Bar */}
          <div className="metadata-status-bar" style={{ flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 10.5, fontWeight: 800, color: 'var(--sig-positive)', letterSpacing: '0.04em' }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--sig-positive)' }}></span>
                {investigationData.status.toUpperCase()}
              </span>
              <span className="badge-pill eth" style={{ fontSize: 9.5 }}>
                {investigationData.chain.toUpperCase()}
              </span>
              <span className="badge-pill info" style={{ fontSize: 9.5 }}>
                {investigationData.trace?.direction === 'incoming' ? 'BACKWARD TRACE' : 'FORWARD TRACE'}
              </span>
              {investigationData.vasp_attributions && investigationData.vasp_attributions.length > 0 && (
                <span className="badge-pill counterfactual" style={{ fontSize: 9.5 }}>◆ VASP-ASSOCIATED</span>
              )}
              <span style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>
                Root: <span
                  className="mono"
                  style={{ color: 'var(--accent-primary)', fontWeight: 700, cursor: 'pointer', textDecoration: 'underline' }}
                  title="Click to inspect root suspect wallet"
                  onClick={() => {
                    const rootClean = investigationData.root_address.toLowerCase();
                    const rootNode = investigationData.graph.nodes.find(
                      (n) => n.address.toLowerCase() === rootClean ||
                             n.id.toLowerCase() === rootClean ||
                             n.id.toLowerCase().endsWith(rootClean)
                    );
                    if (rootNode) handleSelectNode(rootNode);
                  }}
                >
                  {formatAddress(investigationData.root_address)}
                </span>
              </span>

              <button
                type="button"
                className="tool-btn"
                style={{ padding: '0 4px', fontSize: 9 }}
                onClick={() => copyToClipboard(investigationData.root_address, 'root_addr')}
              >
                {copiedKey === 'root_addr' ? '✓' : 'Copy'}
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 10, color: investigationData.trace?.max_hops_reached || investigationData.trace?.transaction_limit_reached ? 'var(--sig-warning)' : 'var(--sig-positive)', fontWeight: 600 }}>
                {getTerminationMessage()}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>ID:</span>
                <span className="mono" style={{ fontSize: 10.5, color: 'var(--text-primary)', fontWeight: 600 }}>
                  {investigationData.investigation_id}
                </span>
                <button
                  type="button"
                  className="tool-btn"
                  style={{ padding: '0 4px', fontSize: 9 }}
                  onClick={() => copyToClipboard(investigationData.investigation_id, 'inv_id')}
                >
                  {copiedKey === 'inv_id' ? '✓' : 'Copy'}
                </button>
              </div>
            </div>
          </div>

          {/* 5 Compact Investigator KPI Cards */}
          <section className="kpi-row" style={{ gridTemplateColumns: 'repeat(5, 1fr)', gap: 6, marginBottom: 0, flexShrink: 0 }}>
            <div className="kpi-card" style={{ padding: '6px 10px' }}>
              <div className="kpi-value" style={{ fontSize: 16, margin: 0 }}>{investigationData.summary.nodes}</div>
              <div className="kpi-title" style={{ fontSize: 8.5, marginTop: 1, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Discovered wallets</div>
            </div>

            <div className="kpi-card" style={{ padding: '6px 10px' }}>
              <div className="kpi-value" style={{ fontSize: 16, margin: 0 }}>{investigationData.summary.transfers}</div>
              <div className="kpi-title" style={{ fontSize: 8.5, marginTop: 1, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Fund transfers</div>
            </div>

            <div className="kpi-card" style={{ padding: '6px 10px' }}>
              <div className="kpi-value" style={{ fontSize: 16, margin: 0 }}>{investigationData.summary.transactions}</div>
              <div className="kpi-title" style={{ fontSize: 8.5, marginTop: 1, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Transactions</div>
            </div>

            <div className="kpi-card" style={{ padding: '6px 10px' }}>
              <div className="kpi-value" style={{ fontSize: 16, margin: 0 }}>{investigationData.summary.edges}</div>
              <div className="kpi-title" style={{ fontSize: 8.5, marginTop: 1, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Fund-flow connections</div>
            </div>

            <div className="kpi-card" style={{ padding: '6px 10px' }}>
              <div className="kpi-value" style={{ fontSize: 16, margin: 0 }}>
                {investigationData.trace
                  ? `${investigationData.trace.actual_max_hops} / ${investigationData.trace.requested_max_hops}`
                  : investigationData.summary.hops}
              </div>
              <div className="kpi-title" style={{ fontSize: 8.5, marginTop: 1, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Depth reached</div>
            </div>
          </section>

          {/* Empty Investigation Notice */}
          {isEmptyResult && (
            <div className="card-box" style={{ padding: '8px 12px', background: 'var(--bg-hover)', borderStyle: 'dashed', flexShrink: 0 }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: 10.5 }}>
                ℹ️ <strong>Notice:</strong> No fund transfers were returned for this investigation. The root wallet is represented as a single suspect node.
              </div>
            </div>
          )}

          {/* 70% / 30% Main Workspace Grid (Graph + Inspector) */}
          <section className="investigation-workspace-grid" style={{ flexShrink: 0 }}>
            {/* Left: Fund-Flow Graph (70%) */}
            <div style={{ height: '100%', minHeight: 0 }}>
              <WalletFundFlowGraph
                graphData={investigationData.graph}
                rootAddress={investigationData.root_address}
                theme={theme}
                selectedNodeId={selectedNode?.id}
                selectedEdgeId={selectedEdge?.id || selectedEdge?.transfer_id}
                onSelectNode={handleSelectNode}
                onSelectEdge={handleSelectEdge}
              />
            </div>

            {/* Right: Forensic Inspector (30%) */}
            <div className="card-box" style={{ height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column' }}>
              <div className="card-box-header">
                <span className="card-box-title" style={{ fontSize: 11 }}>
                  {selectedNode ? 'Wallet Node Inspector' : selectedEdge ? 'Fund Transfer Inspector' : 'Forensic Inspector'}
                </span>
                <span style={{ fontSize: 9.5, color: 'var(--text-muted)' }}>
                  {selectedNode ? 'Node Selected' : selectedEdge ? 'Edge Selected' : 'Click node/edge/table'}
                </span>
              </div>

              <div className="card-content-scroll" style={{ padding: 8, gap: 6 }}>
                {selectedNode ? (
                  <>
                    {/* Identity & Topological Depth */}
                    <div className="inspector-section">
                      <div className="inspector-section-title">Identity & Topological Depth</div>
                      <div className="inspector-field-group">
                        <div className="inspector-field-label">Address</div>
                        <div className="mono" style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--text-primary)', wordBreak: 'break-all' }}>
                          {selectedNode.address}
                        </div>
                        <button
                          type="button"
                          className="btn-secondary"
                          style={{ marginTop: 2, padding: '1px 6px', fontSize: 9.5, width: 'fit-content' }}
                          onClick={() => copyToClipboard(selectedNode.address, 'node_addr')}
                        >
                          {copiedKey === 'node_addr' ? '✓ Copied' : 'Copy Address'}
                        </button>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4, marginTop: 2 }}>
                        <div className="inspector-field-group">
                          <div className="inspector-field-label">Network</div>
                          <div className="inspector-field-value" style={{ fontWeight: 600 }}>
                            {selectedNode.chain.toUpperCase()}
                          </div>
                        </div>
                        <div className="inspector-field-group">
                          <div className="inspector-field-label">Hop Distance</div>
                          <div className="mono" style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--accent-primary)' }}>
                            Hop {selectedNode.hop_distance ?? 0}
                          </div>
                        </div>
                        <div className="inspector-field-group">
                          <div className="inspector-field-label">Trace Role</div>
                          <div>
                            {selectedNode.is_boundary ? (
                              <span className="badge-pill medium" style={{ fontSize: 8.5 }}>
                                BOUNDARY
                              </span>
                            ) : (
                              <span className={`badge-pill ${selectedNode.node_type === 'SUSPECT' ? 'urgent' : 'high'}`} style={{ fontSize: 8.5 }}>
                                {selectedNode.node_type}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {selectedNode.is_boundary && (
                        <div className="inspector-field-group" style={{ marginTop: 3, padding: '3px 5px', background: 'var(--bg-hover)', borderRadius: 4 }}>
                          <div className="inspector-field-label" style={{ color: 'var(--sig-warning)', fontSize: 8.5 }}>Boundary Classification</div>
                          <div style={{ fontSize: 9.5, color: 'var(--text-secondary)' }}>
                            {selectedNode.boundary_reason === 'MAX_HOPS_REACHED'
                              ? 'Max hops exploration boundary. Unexpanded destination.'
                              : selectedNode.boundary_reason || 'Boundary Node'}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Traversal Path from Root */}
                    <div className="inspector-section">
                      <div className="inspector-section-title">Path from Root</div>
                      {(() => {
                        const pathNodes = getPathFromRoot(selectedNode.id || selectedNode.address);
                        return (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                            {pathNodes.map((p, idx) => (
                              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 9.5 }}>
                                <span className={`badge-pill ${p.isRoot ? 'urgent' : 'eth'}`} style={{ fontSize: 8, padding: '1px 4px' }}>
                                  {p.isRoot ? 'ROOT' : `HOP ${p.hop}`}
                                </span>
                                <span className="mono" style={{ color: p.isRoot ? 'var(--sig-critical)' : 'var(--text-primary)', fontWeight: 600 }}>
                                  {formatAddress(p.address)}
                                </span>
                                {idx < pathNodes.length - 1 && (
                                  <span style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>&darr;</span>
                                )}
                              </div>
                            ))}
                            <div style={{ fontSize: 8.5, color: 'var(--text-muted)', marginTop: 2 }}>
                              Hop distance: {selectedNode.hop_distance ?? 0} ({investigationData.trace?.direction === 'incoming' ? 'predecessor funding path' : 'forward fund flow'})
                            </div>
                          </div>
                        );
                      })()}
                    </div>

                    {/* Classification Section */}
                    {(() => {
                      const addrNorm = selectedNode.address.toLowerCase();
                      const resolution = investigationData.entity_resolutions?.find(
                        (r) => r.address.toLowerCase() === addrNorm
                      );
                      const attribution = investigationData.vasp_attributions?.find(
                        (a) => a.address.toLowerCase() === addrNorm
                      );

                      const isAmbiguous = resolution?.resolution_status === 'AMBIGUOUS';
                      const isResolved = resolution?.resolution_status === 'RESOLVED';
                      const isVasp = Boolean(attribution || resolution?.vasp_status || selectedNode.is_vasp);

                      return (
                        <>
                          <div className="inspector-section">
                            <div className="inspector-section-title">Classification</div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                              <div className="inspector-field-group">
                                <div className="inspector-field-label">Entity Name</div>
                                <div className="inspector-field-value" style={{ color: isResolved ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: isResolved ? 700 : 400 }}>
                                  {isAmbiguous ? 'Multiple candidates' : resolution?.entity_name || selectedNode.entity_name || 'Not identified'}
                                </div>
                              </div>
                              <div className="inspector-field-group">
                                <div className="inspector-field-label">Entity Type</div>
                                <div className="inspector-field-value" style={{ color: 'var(--text-secondary)' }}>
                                  {resolution?.entity_type || selectedNode.entity_type || (isResolved ? 'VASP' : '—')}
                                </div>
                              </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, marginTop: 2 }}>
                              <div className="inspector-field-group">
                                <div className="inspector-field-label">VASP Status</div>
                                <div>
                                  {isAmbiguous ? (
                                    <span className="badge-pill medium" style={{ fontSize: 8.5 }}>AMBIGUOUS</span>
                                  ) : isVasp ? (
                                    <span className="badge-pill verified" style={{ fontSize: 8.5 }}>VASP</span>
                                  ) : (
                                    <span style={{ fontSize: 10.5, color: 'var(--text-muted)' }}>Not identified as VASP</span>
                                  )}
                                </div>
                              </div>
                              <div className="inspector-field-group">
                                <div className="inspector-field-label">Resolution Status</div>
                                <div className="inspector-field-value" style={{ fontSize: 10, color: 'var(--text-secondary)' }}>
                                  {resolution?.resolution_status || (isResolved ? 'RESOLVED' : 'NOT_FOUND')}
                                </div>
                              </div>
                            </div>

                            {resolution?.source && (
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, marginTop: 2 }}>
                                <div className="inspector-field-group">
                                  <div className="inspector-field-label">Source</div>
                                  <div className="inspector-field-value" style={{ fontSize: 9.5, color: 'var(--text-muted)' }}>
                                    {resolution.source}
                                  </div>
                                </div>
                                <div className="inspector-field-group">
                                  <div className="inspector-field-label">Reference</div>
                                  <div className="inspector-field-value mono" style={{ fontSize: 9, color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                                    {resolution.source_reference || '—'}
                                  </div>
                                </div>
                              </div>
                            )}

                            {isAmbiguous && resolution?.candidates && resolution.candidates.length > 0 && (
                              <div style={{ marginTop: 4, padding: '4px 6px', background: 'var(--bg-hover)', borderRadius: 4 }}>
                                <div className="inspector-field-label" style={{ color: 'var(--sig-alert)', fontSize: 8.5 }}>Candidate Entities ({resolution.candidates.length})</div>
                                <ul style={{ margin: '2px 0 0 14px', padding: 0, fontSize: 9.5, color: 'var(--text-secondary)' }}>
                                  {resolution.candidates.map((c, i) => (
                                    <li key={i}>{c.entity_name} ({c.entity_type})</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>

                          {/* Attribution Context (when VASP-associated) */}
                          {attribution && (
                            <div className="inspector-section" style={{ borderColor: 'var(--accent-primary-border)', background: 'var(--accent-primary-subtle)' }}>
                              <div className="inspector-section-title" style={{ color: 'var(--accent-primary)' }}>Attribution Context</div>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                                <div className="inspector-field-group">
                                  <div className="inspector-field-label">Trace Direction</div>
                                  <div className="inspector-field-value" style={{ fontWeight: 600, textTransform: 'uppercase' }}>
                                    {attribution.direction}
                                  </div>
                                </div>
                                <div className="inspector-field-group">
                                  <div className="inspector-field-label">Path Distance</div>
                                  <div className="mono" style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--accent-primary)' }}>
                                    {attribution.hop_distance} {attribution.hop_distance === 1 ? 'Hop' : 'Hops'}
                                  </div>
                                </div>
                              </div>

                              <div className="inspector-field-group" style={{ marginTop: 3 }}>
                                <div className="inspector-field-label">Path From Root</div>
                                <div className="mono" style={{ fontSize: 9.5, color: 'var(--text-primary)', wordBreak: 'break-all' }}>
                                  {attribution.path.map((addr) => formatAddress(addr)).join(' → ')}
                                </div>
                              </div>

                              <div style={{ fontSize: 8.5, color: 'var(--text-muted)', marginTop: 2 }}>
                                ℹ️ Association reflects fund-flow path connection; does not prove address ownership.
                              </div>
                            </div>
                          )}
                        </>
                      );
                    })()}

                    {/* Network Connections */}
                    <div className="inspector-section">
                      <div className="inspector-section-title">Network Connections</div>
                      {(() => {
                        const deg = getNodeDegrees(selectedNode.id);
                        return (
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
                            <div className="inspector-field-group">
                              <div className="inspector-field-label">Inbound Transfers</div>
                              <div className="mono" style={{ fontSize: 12, fontWeight: 700 }}>{deg.inDegree}</div>
                            </div>
                            <div className="inspector-field-group">
                              <div className="inspector-field-label">Outbound Transfers</div>
                              <div className="mono" style={{ fontSize: 12, fontWeight: 700 }}>{deg.outDegree}</div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  </>
                ) : selectedEdge ? (
                  <>
                    {/* Fund Flow */}
                    <div className="inspector-section">
                      <div className="inspector-section-title">Fund Flow</div>
                      <div className="inspector-field-group">
                        <div className="inspector-field-label">Exact Amount</div>
                        <div className="mono" style={{ fontSize: 13, fontWeight: 800, color: 'var(--sig-positive)' }}>
                          {selectedEdge.amount} {selectedEdge.asset_symbol || selectedEdge.asset_id}
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 4, marginTop: 2 }}>
                        <div className="inspector-field-group">
                          <div className="inspector-field-label">Mechanism</div>
                          <div>
                            <span className="badge-pill verified" style={{ fontSize: 8.5 }}>
                              {selectedEdge.transfer_type}
                            </span>
                          </div>
                        </div>
                        <div className="inspector-field-group">
                          <div className="inspector-field-label">Hop Level</div>
                          <div className="mono" style={{ fontSize: 10.5, fontWeight: 700 }}>
                            Hop {selectedEdge.hop ?? 1}
                          </div>
                        </div>
                        <div className="inspector-field-group">
                          <div className="inspector-field-label">Transfer ID</div>
                          <div className="mono" style={{ fontSize: 9.5, color: 'var(--text-muted)' }}>
                            {selectedEdge.transfer_id || selectedEdge.id}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Routing */}
                    <div className="inspector-section">
                      <div className="inspector-section-title">Routing</div>
                      <div className="inspector-field-group">
                        <div className="inspector-field-label">From (Source)</div>
                        <div className="mono" style={{ fontSize: 9.5, wordBreak: 'break-all' }}>
                          {selectedEdge.source}
                        </div>
                        <button
                          type="button"
                          className="tool-btn"
                          style={{ marginTop: 2, padding: '1px 5px', fontSize: 8.5, width: 'fit-content' }}
                          onClick={() => copyToClipboard(selectedEdge.source, 'edge_src')}
                        >
                          {copiedKey === 'edge_src' ? '✓ Copied' : 'Copy From'}
                        </button>
                      </div>

                      <div className="inspector-field-group" style={{ marginTop: 3 }}>
                        <div className="inspector-field-label">To (Target)</div>
                        <div className="mono" style={{ fontSize: 9.5, wordBreak: 'break-all' }}>
                          {selectedEdge.target}
                        </div>
                        <button
                          type="button"
                          className="tool-btn"
                          style={{ marginTop: 2, padding: '1px 5px', fontSize: 8.5, width: 'fit-content' }}
                          onClick={() => copyToClipboard(selectedEdge.target, 'edge_tgt')}
                        >
                          {copiedKey === 'edge_tgt' ? '✓ Copied' : 'Copy To'}
                        </button>
                      </div>
                    </div>

                    {/* On-Chain Transaction */}
                    <div className="inspector-section">
                      <div className="inspector-section-title">On-Chain Transaction</div>
                      <div className="inspector-field-group">
                        <div className="inspector-field-label">Transaction Hash</div>
                        <div className="mono" style={{ fontSize: 9.5, wordBreak: 'break-all', fontWeight: 600 }}>
                          {selectedEdge.tx_hash}
                        </div>
                        <button
                          type="button"
                          className="tool-btn"
                          style={{ marginTop: 2, padding: '1px 5px', fontSize: 8.5, width: 'fit-content' }}
                          onClick={() => copyToClipboard(selectedEdge.tx_hash, 'edge_tx')}
                        >
                          {copiedKey === 'edge_tx' ? '✓ Copied' : 'Copy Tx Hash'}
                        </button>
                      </div>

                      {selectedEdge.timestamp && (
                        <div className="inspector-field-group" style={{ marginTop: 3 }}>
                          <div className="inspector-field-label">Timestamp (UTC)</div>
                          <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>
                            {new Date(selectedEdge.timestamp).toUTCString()}
                          </div>
                        </div>
                      )}

                      {selectedEdge.evidence_ref && (
                        <div className="inspector-field-group" style={{ marginTop: 3 }}>
                          <div className="inspector-field-label">Evidence Reference</div>
                          <div className="mono" style={{ fontSize: 9.5, color: 'var(--text-muted)' }}>
                            {selectedEdge.evidence_ref}
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', textAlign: 'center', gap: 4 }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" style={{ opacity: 0.6 }}>
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="16" x2="12" y2="12" />
                      <line x1="12" y1="8" x2="12.01" y2="8" />
                    </svg>
                    <div style={{ fontSize: 10.5, fontWeight: 600 }}>Forensic Inspector</div>
                    <span style={{ fontSize: 9.5, maxWidth: 200 }}>
                      Select a wallet node or fund transfer to inspect forensic details.
                    </span>
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* 3. Formal Evidence Matrix Panel (Phase 10) */}
          <div className="card-box" style={{ flexShrink: 0, marginBottom: 8 }} data-testid="evidence-matrix-panel">
            <div className="card-box-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 6 }}>
              <div>
                <span className="card-box-title" style={{ fontSize: 11 }}>Structured Forensic Evidence Matrix</span>
                <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 8 }}>
                  {filteredEvidence.length} of {rawEvidence.length} evidence records
                </span>
              </div>

              {/* Evidence Classification Filter Tabs */}
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {(['ALL', 'OBSERVED', 'RESOLVED', 'DERIVED', 'INFERRED', 'UNKNOWN'] as const).map((filterKey) => {
                  const count = evidenceCounts[filterKey];
                  const isActive = evidenceFilter === filterKey;
                  return (
                    <button
                      key={filterKey}
                      type="button"
                      className={`tool-btn ${isActive ? 'active' : ''}`}
                      style={{ fontSize: 8.5, padding: '2px 6px', display: 'flex', alignItems: 'center', gap: 4 }}
                      onClick={() => setEvidenceFilter(filterKey)}
                    >
                      <span>{filterKey}</span>
                      <span style={{
                        background: isActive ? 'rgba(255,255,255,0.2)' : 'var(--bg-input)',
                        padding: '0 4px',
                        borderRadius: 8,
                        fontSize: 8,
                        fontWeight: 700
                      }}>
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="registry-table-container" style={{ maxHeight: 220, overflowY: 'auto' }}>
              <table className="registry-table">
                <thead>
                  <tr>
                    <th style={{ width: '12%' }}>Evidence ID</th>
                    <th style={{ width: '11%' }}>Class</th>
                    <th>Forensic Finding</th>
                    <th style={{ width: '15%' }}>Amount / Asset</th>
                    <th style={{ width: '22%' }}>Tx Hash / Ref</th>
                    <th style={{ width: '6%' }}>Hop</th>
                    <th style={{ width: '14%' }}>Association</th>
                    <th style={{ width: '8%' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvidence.length === 0 ? (
                    <tr>
                      <td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '16px' }}>
                        No evidence records matching classification '{evidenceFilter}'.
                      </td>
                    </tr>
                  ) : (
                    filteredEvidence.map((ev, idx) => {
                      const badgeClass =
                        ev.evidence_class === 'OBSERVED' ? 'verified' :
                        ev.evidence_class === 'RESOLVED' ? 'eth' :
                        ev.evidence_class === 'DERIVED' ? 'urgent' :
                        ev.evidence_class === 'INFERRED' ? 'counterfactual' : 'subtle';

                      return (
                        <tr key={ev.evidence_id || `ev_${idx}`}>
                          <td className="mono" style={{ fontSize: 9.5, fontWeight: 700, color: 'var(--text-primary)' }}>
                            {ev.evidence_id}
                          </td>
                          <td>
                            <span className={`badge-pill ${badgeClass}`} style={{ fontSize: 8.5 }}>
                              {ev.evidence_class}
                            </span>
                          </td>
                          <td>
                            <div style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-primary)' }}>
                              {ev.title}
                            </div>
                            <div style={{ fontSize: 9.5, color: 'var(--text-muted)', marginTop: 1, lineHeight: 1.3 }}>
                              {ev.description}
                            </div>
                          </td>
                          <td className="mono" style={{ fontSize: 10, fontWeight: 700, color: 'var(--sig-positive)', whiteSpace: 'nowrap' }}>
                            {ev.amount ? `${ev.amount} ${ev.asset || ''}` : '—'}
                          </td>
                          <td className="mono" style={{ fontSize: 9.5, color: 'var(--accent-primary)', whiteSpace: 'nowrap' }}>
                            {ev.tx_hash ? (
                              <>
                                <span title={ev.tx_hash}>{formatTxHash(ev.tx_hash)}</span>
                                <button
                                  type="button"
                                  className="tool-btn"
                                  style={{ marginLeft: 4, padding: '0 3px', fontSize: 8.5 }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    copyToClipboard(ev.tx_hash!, `ev_tx_${idx}`);
                                  }}
                                >
                                  {copiedKey === `ev_tx_${idx}` ? '✓' : 'Copy'}
                                </button>
                              </>
                            ) : (
                              <span style={{ color: 'var(--text-muted)' }}>{ev.source_reference || ev.source || '—'}</span>
                            )}
                          </td>
                          <td style={{ fontSize: 10, textAlign: 'center' }}>
                            {ev.hop_distance !== null && ev.hop_distance !== undefined ? (
                              <span className="badge-pill subtle" style={{ fontSize: 8.5 }}>
                                Hop {ev.hop_distance}
                              </span>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td style={{ fontSize: 10, color: 'var(--text-secondary)' }}>
                            {ev.entity_association || ev.vasp_association || '—'}
                          </td>
                          <td>
                            <button
                              type="button"
                              className="tool-btn"
                              style={{ fontSize: 8.5, padding: '1px 5px' }}
                              onClick={() => handleEvidenceInspect(ev)}
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* 4. Case Dossier Export & Action Packet Toolbar (Phase 10) */}
          <div className="card-box" style={{ flexShrink: 0, marginBottom: 8, padding: '10px 14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Case Dossier Export & Statutory Requisition
                </div>
                <div style={{ fontSize: 9.5, color: 'var(--text-muted)', marginTop: 2 }}>
                  Operator vs Beneficiary: Blockchain evidence reflects infrastructure path proximity; does not establish natural person beneficiary identity without off-chain KYC records.
                </div>
              </div>

              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                {exportStatusMessage && (
                  <span style={{ fontSize: 9.5, color: 'var(--sig-positive)', fontWeight: 600 }}>
                    {exportStatusMessage}
                  </span>
                )}
                
                <button
                  type="button"
                  data-testid="export-dossier-btn"
                  className="tool-btn"
                  disabled={exportLoading}
                  style={{ fontSize: 10, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 5 }}
                  onClick={handleExportDossier}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  Export Dossier (JSON)
                </button>

                <button
                  type="button"
                  data-testid="download-report-btn"
                  className="tool-btn"
                  disabled={exportLoading}
                  style={{ fontSize: 10, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 5 }}
                  onClick={handleDownloadReport}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                    <polyline points="10 9 9 9 8 9" />
                  </svg>
                  Download Report (HTML/PDF)
                </button>

                <button
                  type="button"
                  data-testid="generate-action-packet-btn"
                  className="tool-btn active"
                  disabled={exportLoading}
                  style={{ fontSize: 10, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 5 }}
                  onClick={handleOpenActionPacket}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                  Draft Action Packet (Sec 91 CrPC)
                </button>
              </div>
            </div>
          </div>

          {/* 5. Ingested Transfer Activity Table (Immediately below workspace) */}
          <div className="card-box" style={{ flexShrink: 0, marginBottom: 8 }}>
            <div className="card-box-header">
              <span className="card-box-title" style={{ fontSize: 11 }}>Ingested Transfer Activity</span>
              <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                {investigationData.graph.edges.length} transfers recorded
              </span>
            </div>

            <div className="registry-table-container" style={{ maxHeight: 220, overflowY: 'auto' }}>
              <table className="registry-table">
                <thead>
                  <tr>
                    <th>Time (UTC)</th>
                    <th>Asset & Amount</th>
                    <th>From → To</th>
                    <th>Transaction Hash</th>
                    <th>Mechanism</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {investigationData.graph.edges.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '16px' }}>
                        No fund transfer records found for this wallet.
                      </td>
                    </tr>
                  ) : (
                    investigationData.graph.edges.map((e, idx) => {
                      const isSelected = selectedEdge?.id === e.id || selectedEdge?.transfer_id === e.transfer_id;
                      return (
                        <tr
                          key={e.id || `${e.tx_hash}_${idx}`}
                          style={{
                            cursor: 'pointer',
                            backgroundColor: isSelected ? 'var(--accent-primary-subtle)' : undefined
                          }}
                          onClick={(evt) => handleRowClick(e, evt)}
                        >
                          <td style={{ fontSize: 10.5, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                            {e.timestamp ? new Date(e.timestamp).toISOString().replace('T', ' ').slice(0, 19) : 'N/A'}
                          </td>
                          <td className="mono" style={{ fontWeight: 700, color: 'var(--sig-positive)', whiteSpace: 'nowrap' }}>
                            <span className="badge-pill eth" style={{ marginRight: 4, fontSize: 8.5 }}>
                              {e.asset_symbol || e.asset_id}
                            </span>
                            {e.amount}
                          </td>
                          <td
                            className="mono"
                            style={{ fontSize: 10.5, whiteSpace: 'nowrap' }}
                            onClick={(evt) => evt.stopPropagation()}
                          >
                            <span
                              className="address-node-link"
                              style={{ cursor: 'pointer', textDecoration: 'underline' }}
                              title={`Click to inspect ${e.source}`}
                              onClick={(evt) => {
                                evt.stopPropagation();
                                const srcClean = e.source.includes(':') ? e.source.split(':')[1].toLowerCase() : e.source.toLowerCase();
                                const srcNode = investigationData.graph.nodes.find(
                                  (n) => n.address.toLowerCase() === srcClean ||
                                         n.id.toLowerCase() === e.source.toLowerCase() ||
                                         n.address.toLowerCase() === e.source.toLowerCase()
                                );
                                if (srcNode) handleSelectNode(srcNode);
                              }}
                            >
                              {formatAddress(e.source)}
                            </span>
                            <span style={{ color: 'var(--accent-primary)', margin: '0 4px' }}>&rarr;</span>
                            <span
                              className="address-node-link"
                              style={{ cursor: 'pointer', textDecoration: 'underline' }}
                              title={`Click to inspect ${e.target}`}
                              onClick={(evt) => {
                                evt.stopPropagation();
                                const tgtClean = e.target.includes(':') ? e.target.split(':')[1].toLowerCase() : e.target.toLowerCase();
                                const tgtNode = investigationData.graph.nodes.find(
                                  (n) => n.address.toLowerCase() === tgtClean ||
                                         n.id.toLowerCase() === e.target.toLowerCase() ||
                                         n.address.toLowerCase() === e.target.toLowerCase()
                                );
                                if (tgtNode) handleSelectNode(tgtNode);
                              }}
                            >
                              {formatAddress(e.target)}
                            </span>
                          </td>
                          <td className="mono" style={{ fontSize: 10.5, color: 'var(--accent-primary)', whiteSpace: 'nowrap' }}>
                            <span title={e.tx_hash}>{formatTxHash(e.tx_hash)}</span>
                            <button
                              type="button"
                              className="tool-btn"
                              style={{ marginLeft: 4, padding: '0 3px', fontSize: 8.5 }}
                              onClick={(evt) => {
                                evt.stopPropagation();
                                copyToClipboard(e.tx_hash, `tx_${idx}`);
                              }}
                            >
                              {copiedKey === `tx_${idx}` ? '✓' : 'Copy'}
                            </button>
                          </td>
                          <td>
                            <span className="badge-pill verified" style={{ fontSize: 8.5 }}>
                              {e.transfer_type}
                            </span>
                          </td>
                          <td onClick={(evt) => evt.stopPropagation()}>
                            <button
                              type="button"
                              className={`tool-btn ${isSelected ? 'active' : ''}`}
                              style={{ fontSize: 9, padding: '1px 6px' }}
                              onClick={(evt) => {
                                evt.stopPropagation();
                                handleRowClick(e);
                              }}
                            >
                              {isSelected ? 'Selected' : 'Inspect'}
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Action Packet Modal for Review-Ready Statutory Drafts */}
      <ActionPacketModal
        isOpen={actionPacketModalOpen}
        onClose={() => setActionPacketModalOpen(false)}
        packetData={actionPacketData}
      />
    </div>
  );
};

export default WalletInvestigationPage;

