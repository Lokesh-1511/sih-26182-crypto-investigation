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
  const [activeCaseId, setActiveCaseId] = useState<string>('CASE-2026-002B');
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [attribution, setAttribution] = useState<AttributionData | null>(null);
  const [activeTab, setActiveTab] = useState<'GRAPH' | 'REPORT' | 'CASES'>('GRAPH');
  const [loading, setLoading] = useState(false);
  const [reportResult, setReportResult] = useState<any>(null);
  const [actionPacket, setActionPacket] = useState<any>(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isActionModalOpen, setIsActionModalOpen] = useState(false);

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

  const activeCase = cases.find((c) => c.case_id === activeCaseId);

  return (
    <div className="app-container">
      {/* Header / Navbar */}
      <header className="navbar">
        <div className="navbar-brand">
          <span>SIH 26182</span>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>|</span>
          <span>CRYPTO INVESTIGATION COPILOT</span>
          <span className="navbar-badge">OFFLINE MODE (FIXTURES)</span>
        </div>
        <div className="nav-links">
          <button
            className={`nav-button ${activeTab === 'GRAPH' ? 'active' : ''}`}
            onClick={() => setActiveTab('GRAPH')}
          >
            Graph & Attribution
          </button>
          <button
            className={`nav-button ${activeTab === 'REPORT' ? 'active' : ''}`}
            onClick={() => setActiveTab('REPORT')}
          >
            Forensic Reports & Action Packet
          </button>
          <button
            className={`nav-button ${activeTab === 'CASES' ? 'active' : ''}`}
            onClick={() => setActiveTab('CASES')}
          >
            Case Management
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="content-area">
        {/* Active Case Banner with Quick Case Selector */}
        <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ flex: 1, minWidth: 280 }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>ACTIVE CASE REFERENCE</div>
            <h3 style={{ fontSize: 18, color: 'var(--accent-blue)', margin: '2px 0 4px 0' }}>
              {activeCase ? `${activeCase.case_id} — ${activeCase.title}` : activeCaseId}
            </h3>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Suspect Wallet: <code className="mono">{activeCase?.suspect_wallet || 'N/A'}</code> ({activeCase?.chain || 'ETH'}) | Investigator: {activeCase?.investigator || 'Officer'}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <select
              className="input-field"
              style={{ width: 'auto', minWidth: 220, cursor: 'pointer' }}
              value={activeCaseId}
              onChange={(e) => setActiveCaseId(e.target.value)}
            >
              {cases.map((c) => (
                <option key={c.case_id} value={c.case_id}>
                  {c.case_id} ({c.chain || 'ETH'}) - {c.title.slice(0, 20)}...
                </option>
              ))}
            </select>
            <button className="btn-primary" onClick={handleStartTrace} disabled={loading}>
              {loading ? 'Analyzing...' : '⚡ Run Multi-Hop Trace'}
            </button>
          </div>
        </div>

        {activeTab === 'GRAPH' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 20 }}>
            <div>
              <div className="card-title">
                <span>Multi-Hop Fund-Flow Graph (3-5 Hops)</span>
                {graphData && (
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    {graphData.total_nodes} Addresses, {graphData.total_edges} Transfers
                  </span>
                )}
              </div>
              {graphData ? (
                <InvestigationGraph graphData={graphData} />
              ) : (
                <p>Loading graph...</p>
              )}
            </div>

            <div>
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
          <div>
            <div className="card">
              <div className="card-title">Forensic Report & Lawful Action Packet Generator</div>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>
                Export court-admissible forensic packages with SHA-256 integrity digests or draft statutory Section 91 CrPC notices for authorized review.
              </p>
              <div style={{ display: 'flex', gap: 12 }}>
                <button className="btn-primary" onClick={handleExportReport}>
                  Generate Forensic HTML Report
                </button>
                <button className="btn-secondary" onClick={handleGenerateActionPacket}>
                  Draft Section 91 CrPC Action Packet
                </button>
              </div>
            </div>

            {reportResult && (
              <div className="card">
                <div className="card-title">Generated Forensic Report</div>
                <p>Report Path: <code className="mono">{reportResult.report_path}</code></p>
                <p>SHA-256 Hash: <code className="mono" style={{ color: 'var(--accent-green)' }}>{reportResult.report_hash}</code></p>
                <p style={{ marginTop: 8 }}>Generated At: {reportResult.generated_at}</p>
              </div>
            )}

            {actionPacket && (
              <div className="card">
                <div className="card-title">
                  <span>Lawful Action Packet: {actionPacket.packet_id}</span>
                  <span className="navbar-badge">{actionPacket.attributed_vasp}</span>
                </div>
                <div className="banner-warning">
                  {actionPacket.statutory_disclaimer}
                </div>
                <h4>Preservation Requisition Draft (Section 91 CrPC):</h4>
                <pre style={{ background: 'var(--bg-input)', padding: 12, borderRadius: 6, marginTop: 8, whiteSpace: 'pre-wrap', fontSize: 12 }}>
                  {actionPacket.preservation_notice_draft}
                </pre>
              </div>
            )}
          </div>
        )}

        {activeTab === 'CASES' && (
          <div className="card">
            <div className="card-title">Investigator Case Registry</div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Case Reference</th>
                  <th>Title</th>
                  <th>Investigator</th>
                  <th>Chain</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {cases.map((c) => (
                  <tr key={c.case_id}>
                    <td className="mono">{c.case_id}</td>
                    <td>{c.title}</td>
                    <td>{c.investigator}</td>
                    <td><span className="navbar-badge">{c.chain || 'ETH'}</span></td>
                    <td>{c.priority}</td>
                    <td>{c.status}</td>
                    <td>
                      <button
                        className="btn-secondary"
                        onClick={() => {
                          setActiveCaseId(c.case_id);
                          setActiveTab('GRAPH');
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
