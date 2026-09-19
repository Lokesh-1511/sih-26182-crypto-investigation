// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import './styles/theme.css';
import {
  fetchCases,
  fetchGraph,
  fetchAttribution,
  startTrace,
  exportReport,
  generateActionPacket,
  CaseData,
  GraphData,
  AttributionData
} from './services/api';
import { InvestigationGraph } from './pages/InvestigationGraph';
import { ExplainableCard } from './components/ExplainableCard';
import { ReportModal } from './components/ReportModal';
import { ActionPacketModal } from './components/ActionPacketModal';

export const App: React.FC = () => {
  const [cases, setCases] = useState<CaseData[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string>('CASE-2026-001A');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [attribution, setAttribution] = useState<AttributionData | null>(null);
  const [activeTab, setActiveTab] = useState<'GRAPH' | 'REPORT' | 'CASES'>('GRAPH');
  const [loading, setLoading] = useState(false);
  const [reportResult, setReportResult] = useState<any>(null);
  const [actionPacket, setActionPacket] = useState<any>(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [copiedWallet, setCopiedWallet] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [utcTime, setUtcTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      setUtcTime(new Date().toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    loadData();
  }, [activeCaseId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const caseList = await fetchCases();
      setCases(caseList);

      const g = await fetchGraph(activeCaseId);
      setGraphData(g);

      const a = await fetchAttribution(activeCaseId);
      setAttribution(a);
    } catch (err) {
      console.error('Error fetching case data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTrace = async () => {
    setLoading(true);
    await startTrace(activeCaseId);
    await loadData();
    setLoading(false);
  };

  const handleExportReport = async () => {
    setLoading(true);
    try {
      const res = await exportReport(activeCaseId);
      setReportResult(res);
      setIsReportModalOpen(true);
    } catch (err) {
      console.error('Error generating report:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateActionPacket = async () => {
    setLoading(true);
    try {
      const res = await generateActionPacket(activeCaseId);
      setActionPacket(res);
      setIsActionModalOpen(true);
    } catch (err) {
      console.error('Error generating action packet:', err);
    } finally {
      setLoading(false);
    }
  };

  const activeCase = cases.find((c) => c.case_id === activeCaseId) || cases[0];

  const handleCopyWallet = (addr: string) => {
    navigator.clipboard.writeText(addr);
    setCopiedWallet(true);
    setTimeout(() => setCopiedWallet(false), 2000);
  };

  const filteredCases = cases.filter(
    (c) =>
      c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.suspect_wallet && c.suspect_wallet.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="app-container">
      {/* Top Institutional Header */}
      <header className="top-header">
        <div className="header-left">
          <div className="agency-emblem">⚖️</div>
          <div className="agency-titles">
            <div className="agency-main">NATIONAL CYBER CRIME INVESTIGATION PORTAL</div>
            <div className="agency-sub">Automated VASP Attribution & Forensic Fund-Flow Engine</div>
          </div>
        </div>

        <div className="header-center">
          <div className="mode-pill">
            <span className="mode-dot"></span>
            AIR-GAPPED EVALUATION MODE
          </div>
          <div className="system-clock">{utcTime || 'UTC CLOCK'}</div>
        </div>

        <div className="header-right">
          <button
            className={`nav-tab ${activeTab === 'GRAPH' ? 'active' : ''}`}
            onClick={() => setActiveTab('GRAPH')}
          >
            📊 Graph & Attribution
          </button>
          <button
            className={`nav-tab ${activeTab === 'REPORT' ? 'active' : ''}`}
            onClick={() => setActiveTab('REPORT')}
          >
            📄 Case Dossier & Sec 91
          </button>
          <button
            className={`nav-tab ${activeTab === 'CASES' ? 'active' : ''}`}
            onClick={() => setActiveTab('CASES')}
          >
            📁 Case Registry ({cases.length})
          </button>
        </div>
      </header>

      {/* Active Case Command Ribbon */}
      <div className="command-ribbon">
        <div className="ribbon-case-info">
          <span className="case-id-badge">{activeCase?.case_id || activeCaseId}</span>
          
          {activeCase?.chain && (
            <span className={`chain-tag ${activeCase.chain.toLowerCase()}`}>
              {activeCase.chain}
            </span>
          )}

          <span className="case-title-text">{activeCase?.title}</span>

          {activeCase?.suspect_wallet && (
            <div className="ribbon-wallet-box">
              <span className="wallet-label">Target:</span>
              <span className="wallet-addr">{activeCase.suspect_wallet}</span>
              <button
                className="copy-icon-btn"
                onClick={() => handleCopyWallet(activeCase.suspect_wallet || '')}
                title="Copy Address"
              >
                {copiedWallet ? '✓' : '⧉'}
              </button>
            </div>
          )}

          <span className="officer-badge">
            Investigator: <strong>{activeCase?.investigator || 'Officer'}</strong>
          </span>
        </div>

        <div className="ribbon-actions">
          <select
            className="case-select-dropdown"
            value={activeCaseId}
            onChange={(e) => setActiveCaseId(e.target.value)}
          >
            {cases.map((c) => (
              <option key={c.case_id} value={c.case_id}>
                {c.case_id} ({c.chain || 'ETH'}) — {c.title.slice(0, 24)}...
              </option>
            ))}
          </select>

          <button className="btn-trace" onClick={handleStartTrace} disabled={loading}>
            {loading ? 'Analyzing...' : '⚡ Execute BFS Trace'}
          </button>
        </div>
      </div>

      {/* Main Workspace Area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {activeTab === 'GRAPH' && (
          <div className="workspace-grid">
            {/* Left: Fund-Flow Multigraph Canvas */}
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <div className="panel-header" style={{ borderRadius: '8px 8px 0 0', border: '1px solid var(--border-subtle)', borderBottom: 'none' }}>
                <div className="panel-title">
                  <span>Directed Multi-Hop Fund-Flow Graph</span>
                </div>
                {graphData && (
                  <div className="panel-metrics">
                    {graphData.total_nodes} Addresses | {graphData.total_edges} Transfers
                  </div>
                )}
              </div>

              {graphData ? (
                <InvestigationGraph graphData={graphData} />
              ) : (
                <div className="panel-card" style={{ height: 480, alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                  Loading topological graph...
                </div>
              )}
            </div>

            {/* Right: Explainable Attribution Card */}
            <div className="intel-column">
              {attribution && (
                <ExplainableCard
                  attribution={attribution}
                  onOpenReport={handleExportReport}
                  onOpenActionPacket={handleGenerateActionPacket}
                />
              )}
            </div>
          </div>
        )}

        {activeTab === 'REPORT' && (
          <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
            <div className="panel-card" style={{ padding: 20, marginBottom: 16 }}>
              <div className="panel-header" style={{ background: 'transparent', padding: 0, marginBottom: 12 }}>
                <div className="panel-title">
                  Court-Admissible Forensic Dossiers & Statutory Requisitions
                </div>
              </div>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 16, fontSize: 13 }}>
                Generate evidentiary investigation summaries verified with SHA-256 integrity digests (admissible under Section 65B of the Indian Evidence Act), or draft formal legal requisition notices under Section 91 CrPC for exchange compliance officers.
              </p>
              <div style={{ display: 'flex', gap: 12 }}>
                <button className="btn-secondary-action" onClick={handleExportReport} disabled={loading}>
                  📄 Generate Forensic HTML Dossier
                </button>
                <button className="btn-trace" onClick={handleGenerateActionPacket} disabled={loading}>
                  ⚖️ Draft Section 91 CrPC Action Packet
                </button>
              </div>
            </div>

            {reportResult && (
              <div className="panel-card" style={{ padding: 20, marginBottom: 16 }}>
                <div className="panel-title" style={{ color: 'var(--accent-emerald)', marginBottom: 10 }}>
                  ✓ Cryptographically Sealed Forensic Report Generated
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 12, fontSize: 12 }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Case Reference:</span>
                    <div className="mono" style={{ fontWeight: 600 }}>{reportResult.case_id}</div>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Tamper-Evident SHA-256 Digest:</span>
                    <div className="mono" style={{ color: 'var(--accent-emerald)', wordBreak: 'break-all' }}>
                      {reportResult.report_hash}
                    </div>
                  </div>
                </div>
                <div style={{ marginTop: 12 }}>
                  <a
                    href={`file:///${reportResult.report_path.replace(/\\/g, '/')}`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-secondary-action"
                    style={{ textDecoration: 'none', display: 'inline-flex' }}
                  >
                    Open Generated Dossier in Browser
                  </a>
                </div>
              </div>
            )}

            {actionPacket && (
              <div className="panel-card" style={{ padding: 20 }}>
                <div className="panel-header" style={{ background: 'transparent', padding: 0, marginBottom: 12 }}>
                  <div className="panel-title">
                    Lawful Action Packet: {actionPacket.packet_id}
                  </div>
                  <span className="priority-pill high">{actionPacket.attributed_vasp}</span>
                </div>

                <div className="legal-demarcation-card">
                  <div className="demarcation-header">Statutory Safeguard Notice</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {actionPacket.statutory_disclaimer}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, marginTop: 16 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                    Section 91 CrPC Urgent Preservation Notice
                  </span>
                  <button
                    className="tool-btn"
                    onClick={() => {
                      navigator.clipboard.writeText(actionPacket.preservation_notice_draft);
                    }}
                  >
                    Copy Notice Text
                  </button>
                </div>

                <pre style={{
                  background: 'var(--bg-input)',
                  padding: 14,
                  borderRadius: 6,
                  border: '1px solid var(--border-subtle)',
                  fontSize: 11,
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                  maxHeight: 360,
                  overflowY: 'auto'
                }}>
                  {actionPacket.preservation_notice_draft}
                </pre>
              </div>
            )}
          </div>
        )}

        {activeTab === 'CASES' && (
          <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto', width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-white)' }}>
                  Investigator Case Registry
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  Master active blockchain intelligence cases and evidentiary dossiers.
                </p>
              </div>
              <input
                type="text"
                className="case-select-dropdown"
                placeholder="Search case ID, wallet or title..."
                style={{ width: 280 }}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="registry-table-container">
              <table className="registry-table">
                <thead>
                  <tr>
                    <th>Case Reference</th>
                    <th>Investigation Title</th>
                    <th>Investigator</th>
                    <th>Chain</th>
                    <th>Target Wallet</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCases.map((c) => (
                    <tr key={c.case_id}>
                      <td className="mono" style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>
                        {c.case_id}
                      </td>
                      <td style={{ fontWeight: 500 }}>{c.title}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{c.investigator}</td>
                      <td>
                        <span className={`chain-tag ${(c.chain || 'eth').toLowerCase()}`}>
                          {c.chain || 'ETH'}
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {c.suspect_wallet ? `${c.suspect_wallet.slice(0, 8)}...${c.suspect_wallet.slice(-6)}` : 'N/A'}
                      </td>
                      <td>
                        <span className={`priority-pill ${c.priority === 'URGENT' ? 'urgent' : 'high'}`}>
                          {c.priority}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: 11, color: 'var(--accent-emerald)', fontWeight: 600 }}>
                          ● {c.status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="tool-btn"
                          onClick={() => {
                            setActiveCaseId(c.case_id);
                            setActiveTab('GRAPH');
                          }}
                        >
                          Load into Workstation
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Forensic Report Modal */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        reportData={reportResult}
      />

      {/* Lawful Action Packet Modal */}
      <ActionPacketModal
        isOpen={isActionModalOpen}
        onClose={() => setIsActionModalOpen(false)}
        packetData={actionPacket}
      />
    </div>
  );
};

export default App;
