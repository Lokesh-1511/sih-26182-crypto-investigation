// frontend/src/components/ExplainableCard.tsx
import React, { useState } from 'react';
import { AttributionData } from '../services/api';

interface Props {
  attribution: AttributionData;
  onOpenReport?: () => void;
  onOpenActionPacket?: () => void;
}

export const ExplainableCard: React.FC<Props> = ({ attribution, onOpenReport, onOpenActionPacket }) => {
  const [showCounterfactual, setShowCounterfactual] = useState(false);
  const [ablatedFactors, setAblatedFactors] = useState<Set<string>>(new Set());

  const cand = attribution.top_candidate;

  if (!cand) {
    return (
      <div className="card-box" style={{ padding: 20 }}>
        <div className="card-box-title">VASP Attribution Matrix</div>
        <p style={{ color: 'var(--text-muted)', marginTop: 12 }}>
          No candidate VASP could be attributed with sufficient mathematical certainty.
        </p>
      </div>
    );
  }

  // Calculate simulated score based on client-side ablation toggles
  let simulatedScore = cand.confidence_score;
  cand.factors.forEach((f) => {
    if (ablatedFactors.has(f.factor_name)) {
      simulatedScore = Math.max(0, simulatedScore - f.contribution_points);
    }
  });

  const toggleAblation = (factorName: string) => {
    setAblatedFactors((prev) => {
      const next = new Set(prev);
      if (next.has(factorName)) {
        next.delete(factorName);
      } else {
        next.add(factorName);
      }
      return next;
    });
  };

  const [activeTab, setActiveTab] = useState<'STATS' | 'DIAGRAM'>('STATS');

  const isAblated = ablatedFactors.size > 0;
  const currentBand = simulatedScore >= 80 ? 'HIGH' : simulatedScore >= 50 ? 'MEDIUM' : 'LOW';

  return (
    <div className="card-box">
      {/* Tab Switcher Header (Matching Screenshot Card Style) */}
      <div className="card-tabs-header">
        <div className="card-tabs-list">
          <button
            className={`card-tab-btn ${activeTab === 'STATS' ? 'active' : ''}`}
            onClick={() => setActiveTab('STATS')}
          >
            Statistics
          </button>
          <button
            className={`card-tab-btn ${activeTab === 'DIAGRAM' ? 'active' : ''}`}
            onClick={() => setActiveTab('DIAGRAM')}
          >
            Diagram & Factors
          </button>
        </div>

        <span className={`badge-pill ${isAblated ? 'urgent' : 'verified'}`} style={{ fontSize: 10 }}>
          {isAblated ? `SIM: ${simulatedScore.toFixed(1)}%` : `${currentBand} (${simulatedScore.toFixed(1)}%)`}
        </span>
      </div>

      {/* Card Content Body (Scrollable inside card if needed, zero outer page scroll) */}
      <div className="card-content-scroll">
        {activeTab === 'STATS' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <table className="stats-table">
              <thead>
                <tr>
                  <th>VASP Entity</th>
                  <th>Category</th>
                  <th>Attribution</th>
                  <th>Hops</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <div style={{ fontWeight: 700 }}>{cand.entity_name}</div>
                    <div className="mono" style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      {cand.terminal_deposit_address ? `${cand.terminal_deposit_address.slice(0, 10)}...` : 'Identified Hub'}
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{cand.entity_type}</td>
                  <td>
                    <span className="mono" style={{ fontWeight: 800, color: 'var(--accent-primary)' }}>
                      {simulatedScore.toFixed(1)}%
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {cand.shortest_path_hops || 1}
                  </td>
                </tr>
              </tbody>
            </table>

            {/* Legal Demarcation Safeguard Notice */}
            <div className="legal-card" style={{ margin: '4px 0 0 0' }}>
              <div className="legal-card-title">Statutory Demarcation Notice</div>
              <div style={{ fontSize: 11, display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                <span style={{ color: 'var(--text-secondary)' }}>Infrastructure Control:</span>
                <strong>{attribution.operator_beneficiary.operator_attribution}</strong>
              </div>
              <div style={{ fontSize: 11, display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Beneficiary Identity:</span>
                <strong style={{ color: 'var(--sig-critical)' }}>{attribution.operator_beneficiary.beneficiary_identity}</strong>
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
                On-chain clustering attributes infrastructure to {cand.entity_name}. Individual identity requires Sec 91 CrPC subpoena.
              </div>
            </div>
          </div>
        )}

        {activeTab === 'DIAGRAM' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {cand.factors.map((f, idx) => {
              const ablated = ablatedFactors.has(f.factor_name);
              const percentage = Math.min(100, Math.max(5, Math.abs(f.contribution_points) * 2.2));

              return (
                <div key={idx} className="factor-bar-row" style={{ opacity: ablated ? 0.4 : 1 }}>
                  <div className="factor-bar-header">
                    <span className="factor-bar-name" style={{ fontSize: 11 }}>{f.factor_name}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span className="factor-bar-score" style={{ fontSize: 11 }}>
                        {f.contribution_points >= 0 ? `+${f.contribution_points}` : f.contribution_points} pts
                      </span>
                      <button
                        className="tool-btn"
                        style={{ padding: '0 5px', fontSize: 9 }}
                        onClick={() => toggleAblation(f.factor_name)}
                      >
                        {ablated ? 'Restore' : 'Ablate'}
                      </button>
                    </div>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        width: `${percentage}%`,
                        background: f.contribution_points < 0 ? 'var(--sig-critical)' : 'var(--accent-primary)'
                      }}
                    />
                  </div>
                </div>
              );
            })}

            <button
              className="btn-secondary"
              style={{ width: '100%', justifyContent: 'center', marginTop: 2, fontSize: 10, padding: '4px 8px' }}
              onClick={() => setShowCounterfactual(!showCounterfactual)}
            >
              {showCounterfactual ? 'Hide Counterfactual Matrix' : 'View Counterfactual Matrix'}
            </button>

            {showCounterfactual && cand.counterfactuals && (
              <div style={{ background: 'var(--bg-input)', borderRadius: 6, padding: 8, border: '1px solid var(--border-subtle)' }}>
                <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ color: 'var(--text-muted)', textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                      <th style={{ padding: '2px 4px' }}>Factor</th>
                      <th style={{ padding: '2px 4px' }}>Sim</th>
                      <th style={{ padding: '2px 4px' }}>Delta</th>
                      <th style={{ padding: '2px 4px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cand.counterfactuals.map((cf, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(0,0,0,0.04)' }}>
                        <td style={{ padding: '2px 4px', fontWeight: 600 }}>{cf.factor_removed}</td>
                        <td className="mono" style={{ padding: '2px 4px', color: 'var(--accent-primary)' }}>{cf.new_score}%</td>
                        <td className="mono" style={{ padding: '2px 4px', color: 'var(--sig-critical)' }}>-{cf.score_delta}</td>
                        <td style={{ padding: '2px 4px' }}>
                          <span className="badge-pill verified" style={{ fontSize: 8, padding: '1px 4px' }}>{cf.robustness_evaluation}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Pinned Action Buttons Footer */}
      <div style={{ padding: '8px 14px', borderTop: '1px solid var(--border-subtle)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, flexShrink: 0 }}>
        {onOpenReport && (
          <button className="btn-secondary" style={{ justifyContent: 'center', fontSize: 11, padding: '6px 10px' }} onClick={onOpenReport}>
            Export Dossier
          </button>
        )}
        {onOpenActionPacket && (
          <button className="btn-primary" style={{ justifyContent: 'center', fontSize: 11, padding: '6px 10px' }} onClick={onOpenActionPacket}>
            Sec 91 CrPC Notice
          </button>
        )}
      </div>
    </div>
  );
};
export default ExplainableCard;
