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
  const [activeNav, setActiveNav] = useState<'DASHBOARD' | 'GRAPH' | 'STATISTICS' | 'DOSSIER' | 'REGISTRY'>('DASHBOARD');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [loading, setLoading] = useState(false);
  const [reportResult, setReportResult] = useState<any>(null);
  const [actionPacket, setActionPacket] = useState<any>(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isActionModalOpen, setIsActionModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeDateIndex, setActiveDateIndex] = useState(0);

  const dates = ['19 Sep 2026', '18 Sep 2026', '17 Sep 2026'];

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

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

  const filteredCases = cases.filter(
    (c) =>
      c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.suspect_wallet && c.suspect_wallet.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Compute stats for the 4 KPI Cards
  const totalAmount = graphData?.edges?.[0]
    ? `${graphData.edges[0].amount} ${graphData.edges[0].asset}`
    : '1.45 BTC';

  const attributedVaspName = attribution?.top_candidate?.entity_name || 'Binance';
  const confidenceScore = attribution?.top_candidate?.confidence_score
    ? `${attribution.top_candidate.confidence_score.toFixed(1)}%`
    : '95.0%';

  const hopDistance = attribution?.top_candidate?.shortest_path_hops
    ? `${attribution.top_candidate.shortest_path_hops} Hops`
    : '2 Hops';

  const totalAddresses = graphData?.total_nodes ? `${graphData.total_nodes} Wallets` : '7 Wallets';
  const totalTransfers = graphData?.total_edges ? `${graphData.total_edges} Transfers` : '8 Transfers';

  return (
    <div className="app-shell">
      {/* Left Sidebar (Matching Reference Screenshot) */}
      <aside className="app-sidebar">
        <div className="sidebar-top">
          <div className="sidebar-brand">
            <div className="brand-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div className="brand-text">
              <span className="brand-title">VASP INTEL</span>
              <span className="brand-subtitle">SIH 26182</span>
            </div>
          </div>

          <nav className="sidebar-nav">
            <button
              className={`nav-link ${activeNav === 'DASHBOARD' ? 'active' : ''}`}
              onClick={() => setActiveNav('DASHBOARD')}
            >
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                </svg>
              </span>
              Dashboard
            </button>

            <button
              className={`nav-link ${activeNav === 'GRAPH' ? 'active' : ''}`}
              onClick={() => setActiveNav('GRAPH')}
            >
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="6" cy="6" r="3" />
                  <circle cx="18" cy="18" r="3" />
                  <path d="M8.5 8.5l7 7" />
                  <circle cx="18" cy="6" r="3" />
                  <path d="M15.5 8.5l-7 7" />
                </svg>
              </span>
              Graph Explorer
            </button>

            <button
              className={`nav-link ${activeNav === 'STATISTICS' ? 'active' : ''}`}
              onClick={() => setActiveNav('STATISTICS')}
            >
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
              </span>
              Statistics
            </button>

            <button
              className={`nav-link ${activeNav === 'DOSSIER' ? 'active' : ''}`}
              onClick={() => setActiveNav('DOSSIER')}
            >
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
              </span>
              Case Dossier
            </button>

            <button
              className={`nav-link ${activeNav === 'REGISTRY' ? 'active' : ''}`}
              onClick={() => setActiveNav('REGISTRY')}
            >
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                </svg>
              </span>
              Case Registry
            </button>
          </nav>
        </div>

        <div className="sidebar-bottom">
          <div className="mode-status-badge">
            <span className="status-dot-pulse"></span>
            Evaluation Mode
          </div>

          <div className="sidebar-divider"></div>

          <button className="theme-toggle-btn" onClick={toggleTheme}>
            <span>{theme === 'light' ? 'Light Theme' : 'Dark Theme'}</span>
            <span>
              {theme === 'light' ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
            </span>
          </button>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="main-viewport">
        {/* Header Bar */}
        <header className="dashboard-header">
          <div className="header-top-row">
            <div className="view-title-group">
              <h1>Information</h1>
            </div>

            <div className="header-actions-group">
              <div className="date-stepper">
                <button
                  className="stepper-btn"
                  onClick={() => setActiveDateIndex((prev) => (prev > 0 ? prev - 1 : dates.length - 1))}
                >
                  &lt;
                </button>
                <span className="stepper-date">{dates[activeDateIndex]}</span>
                <button
                  className="stepper-btn"
                  onClick={() => setActiveDateIndex((prev) => (prev < dates.length - 1 ? prev + 1 : 0))}
                >
                  &gt;
                </button>
              </div>

              <select
                className="select-input"
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
                {loading ? 'Analyzing...' : 'Execute BFS Trace'}
              </button>
            </div>
          </div>

          {/* Region / Case Navigation Tabs (Underline Active Style from Screenshot) */}
          <div className="case-tabs-bar">
            {cases.map((c) => (
              <button
                key={c.case_id}
                className={`case-tab-btn ${activeCaseId === c.case_id ? 'active' : ''}`}
                onClick={() => {
                  setActiveCaseId(c.case_id);
                  setActiveNav('DASHBOARD');
                }}
              >
                {c.title.split('-')[1]?.trim() || c.title} ({c.chain || 'BTC'})
              </button>
            ))}
            <button
              className={`case-tab-btn ${activeNav === 'REGISTRY' ? 'active' : ''}`}
              onClick={() => setActiveNav('REGISTRY')}
            >
              All Registry Cases
            </button>
          </div>
        </header>

        {/* Top 4 KPI Stat Cards Row (Matching Screenshot Infected / Bankrupts / Unemployment / Tests) */}
        <section className="kpi-row">
          <div className="kpi-card">
            <div className="kpi-title">Suspect Outflow</div>
            <div className="kpi-value">{totalAmount}</div>
            <div className="kpi-delta critical">
              <span className="delta-pill critical">+ 0.35 trace</span>
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-title">Attributed VASP</div>
            <div className="kpi-value">{attributedVaspName}</div>
            <div className="kpi-delta positive">
              <span className="delta-pill positive">+ {confidenceScore}</span>
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-title">Shortest Path</div>
            <div className="kpi-value">{hopDistance}</div>
            <div className="kpi-delta neutral">
              <span className="delta-pill neutral">Peeling Breakpoint</span>
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-title">Cluster Density</div>
            <div className="kpi-value">{totalAddresses}</div>
            <div className="kpi-delta positive">
              <span className="delta-pill positive">+ {totalTransfers}</span>
            </div>
          </div>
        </section>

        {/* Dynamic Views */}
        {activeNav === 'DASHBOARD' && (
          <section className="dashboard-grid-2col">
            {/* Left Column: Map Equivalent (Fund-Flow Graph) */}
            <div>
              <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Map</h2>
                <span className="case-badge-pill">{activeCase?.case_id || activeCaseId}</span>
              </div>
              {graphData ? (
                <InvestigationGraph graphData={graphData} theme={theme} />
              ) : (
                <div className="card-box" style={{ height: 480, alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                  Loading topological graph...
                </div>
              )}
            </div>

            {/* Right Column: Statistics Table & Diagram Visualization */}
            <div>
              {attribution && (
                <ExplainableCard
                  attribution={attribution}
                  onOpenReport={handleExportReport}
                  onOpenActionPacket={handleGenerateActionPacket}
                />
              )}
            </div>
          </section>
        )}

        {activeNav === 'GRAPH' && (
          <section style={{ width: '100%' }}>
            <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ fontSize: 18, fontWeight: 700 }}>Topological Graph Explorer</h2>
              <span className="case-badge-pill">{activeCase?.case_id}</span>
            </div>
            {graphData && <InvestigationGraph graphData={graphData} theme={theme} />}
          </section>
        )}

        {activeNav === 'STATISTICS' && (
          <section style={{ maxWidth: 900, margin: '0 auto', width: '100%' }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Attribution Evidence Matrix</h2>
            {attribution && (
              <ExplainableCard
                attribution={attribution}
                onOpenReport={handleExportReport}
                onOpenActionPacket={handleGenerateActionPacket}
              />
            )}
          </section>
        )}

        {activeNav === 'DOSSIER' && (
          <section style={{ maxWidth: 950, margin: '0 auto', width: '100%' }}>
            <div className="card-box" style={{ padding: 24, marginBottom: 20 }}>
              <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
                Court-Admissible Dossiers & Statutory Requisitions
              </h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 20, fontSize: 13, lineHeight: 1.6 }}>
                Generate evidentiary investigation summaries verified with SHA-256 integrity digests (admissible under Section 65B of the Indian Evidence Act), or draft formal legal requisition notices under Section 91 CrPC for exchange compliance officers.
              </p>
              <div style={{ display: 'flex', gap: 12 }}>
                <button className="btn-secondary" onClick={handleExportReport} disabled={loading}>
                  Generate Forensic Dossier
                </button>
                <button className="btn-primary" onClick={handleGenerateActionPacket} disabled={loading}>
                  Draft Section 91 CrPC Notice
                </button>
              </div>
            </div>

            {reportResult && (
              <div className="card-box" style={{ padding: 20, marginBottom: 20 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--sig-positive)', marginBottom: 8 }}>
                  Cryptographically Sealed Forensic Report Generated
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 12, fontSize: 12 }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Case Reference:</span>
                    <div className="mono" style={{ fontWeight: 600 }}>{reportResult.case_id}</div>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Tamper-Evident SHA-256 Digest:</span>
                    <div className="mono" style={{ color: 'var(--accent-primary)', wordBreak: 'break-all' }}>
                      {reportResult.report_hash}
                    </div>
                  </div>
                </div>
                <div style={{ marginTop: 14 }}>
                  <a
                    href={`file:///${reportResult.report_path.replace(/\\/g, '/')}`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-secondary"
                    style={{ textDecoration: 'none', display: 'inline-flex' }}
                  >
                    Open Dossier in Browser
                  </a>
                </div>
              </div>
            )}
          </section>
        )}

        {activeNav === 'REGISTRY' && (
          <section style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 700 }}>Investigator Case Registry</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  Master active blockchain intelligence cases and evidentiary dossiers.
                </p>
              </div>
              <input
                type="text"
                className="select-input"
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
                      <td className="mono" style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
                        {c.case_id}
                      </td>
                      <td style={{ fontWeight: 600 }}>{c.title}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{c.investigator}</td>
                      <td>
                        <span className={`badge-pill ${(c.chain || 'eth').toLowerCase()}`}>
                          {c.chain || 'ETH'}
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                        {c.suspect_wallet ? `${c.suspect_wallet.slice(0, 8)}...${c.suspect_wallet.slice(-6)}` : 'N/A'}
                      </td>
                      <td>
                        <span className={`badge-pill ${c.priority === 'URGENT' ? 'urgent' : 'high'}`}>
                          {c.priority}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--sig-positive)' }}>
                          Active
                        </span>
                      </td>
                      <td>
                        <button
                          className="tool-btn"
                          onClick={() => {
                            setActiveCaseId(c.case_id);
                            setActiveNav('DASHBOARD');
                          }}
                        >
                          Load Case
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
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
