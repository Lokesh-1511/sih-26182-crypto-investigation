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

  const isAblated = ablatedFactors.size > 0;
  const currentBand = simulatedScore >= 80 ? 'HIGH' : simulatedScore >= 50 ? 'MEDIUM' : 'LOW';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* 1. Statistics Card (Matching Screenshot Statistics Table) */}
      <div className="card-box">
        <div className="card-box-header">
          <div className="card-box-title">Statistics</div>
          <span className="badge-pill verified">
            {currentBand} CERTAINTY ({simulatedScore.toFixed(1)}%)
          </span>
        </div>

        <table className="stats-table">
          <thead>
            <tr>
              <th>VASP Entity</th>
              <th>Category</th>
              <th>Attribution</th>
              <th>Distance</th>
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
                {cand.shortest_path_hops || 1} Hops
              </td>
            </tr>
          </tbody>
        </table>

        {/* Legal Demarcation Safeguard */}
        <div style={{ padding: '14px 18px 6px 18px' }}>
          <div className="legal-card">
            <div className="legal-card-title">Statutory Demarcation Notice</div>
            <div style={{ fontSize: 11, display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
              <span style={{ color: 'var(--text-secondary)' }}>Control:</span>
              <strong>{attribution.operator_beneficiary.operator_attribution}</strong>
            </div>
            <div style={{ fontSize: 11, display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Beneficiary:</span>
              <strong style={{ color: 'var(--sig-critical)' }}>{attribution.operator_beneficiary.beneficiary_identity}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Diagram Card (Matching Screenshot Diagram Visualization) */}
      <div className="card-box">
        <div className="card-box-header">
          <div className="card-box-title">Diagram & Factors</div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {isAblated ? 'Ablation Active' : 'Baseline Calibration'}
          </span>
        </div>

        <div className="diagram-section">
          {cand.factors.map((f, idx) => {
            const ablated = ablatedFactors.has(f.factor_name);
            const percentage = Math.min(100, Math.max(5, Math.abs(f.contribution_points) * 2.2));

            return (
              <div key={idx} className="factor-bar-row" style={{ opacity: ablated ? 0.4 : 1 }}>
                <div className="factor-bar-header">
                  <span className="factor-bar-name">{f.factor_name}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="factor-bar-score">
                      {f.contribution_points >= 0 ? `+${f.contribution_points}` : f.contribution_points} pts
                    </span>
                    <button
                      className="tool-btn"
                      style={{ padding: '1px 6px', fontSize: 10 }}
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
            style={{ width: '100%', justifyContent: 'center', marginTop: 4, fontSize: 11 }}
            onClick={() => setShowCounterfactual(!showCounterfactual)}
          >
            {showCounterfactual ? 'Hide Counterfactual Stability Matrix' : 'View Counterfactual Stability Matrix'}
          </button>

          {showCounterfactual && cand.counterfactuals && (
            <div style={{ background: 'var(--bg-input)', borderRadius: 6, padding: 10, marginTop: 4, border: '1px solid var(--border-subtle)' }}>
              <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ color: 'var(--text-muted)', textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                    <th style={{ padding: 4 }}>Factor Removed</th>
                    <th style={{ padding: 4 }}>Base</th>
                    <th style={{ padding: 4 }}>Simulated</th>
                    <th style={{ padding: 4 }}>Delta</th>
                    <th style={{ padding: 4 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {cand.counterfactuals.map((cf, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(0,0,0,0.05)' }}>
                      <td style={{ padding: 4, fontWeight: 600 }}>{cf.factor_removed}</td>
                      <td className="mono" style={{ padding: 4 }}>{cf.original_score}%</td>
                      <td className="mono" style={{ padding: 4, color: 'var(--accent-primary)' }}>{cf.new_score}%</td>
                      <td className="mono" style={{ padding: 4, color: 'var(--sig-critical)' }}>-{cf.score_delta}</td>
                      <td style={{ padding: 4 }}>
                        <span className="badge-pill verified">{cf.robustness_evaluation}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
            {onOpenReport && (
              <button className="btn-secondary" style={{ justifyContent: 'center' }} onClick={onOpenReport}>
                Export Dossier
              </button>
            )}
            {onOpenActionPacket && (
              <button className="btn-primary" style={{ justifyContent: 'center' }} onClick={onOpenActionPacket}>
                Sec 91 CrPC Notice
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
export default ExplainableCard;
