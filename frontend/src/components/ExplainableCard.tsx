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
      <div className="intel-card">
        <div className="panel-title">VASP Attribution Matrix</div>
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
  const scoreClass = currentBand === 'HIGH' ? 'high' : currentBand === 'MEDIUM' ? 'medium' : 'low';

  return (
    <div className="intel-card">
      {/* Header: Candidate & Score */}
      <div className="intel-card-header">
        <div className="vasp-title-group">
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Primary Attributed VASP
          </div>
          <h2>
            {cand.entity_name}
            <span className={`priority-pill ${currentBand === 'HIGH' ? 'high' : 'urgent'}`} style={{ fontSize: 10 }}>
              {currentBand} CONFIDENCE
            </span>
          </h2>
          <div className="vasp-type-pill">
            Type: {cand.entity_type} | Shortest Path: <strong>{cand.shortest_path_hops || 1} hops</strong>
          </div>
        </div>

        <div className="score-display-box">
          <div className={`score-number ${scoreClass}`}>
            {simulatedScore.toFixed(1)}%
          </div>
          <div className="score-label">
            {isAblated ? 'Ablated Score' : 'Confidence Score'}
          </div>
        </div>
      </div>

      {/* Terminal Deposit Information if available */}
      {cand.terminal_deposit_address && (
        <div style={{ background: 'var(--bg-input)', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--border-subtle)', marginBottom: 12, fontSize: 11 }}>
          <span style={{ color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.04em' }}>
            Terminal Deposit Wallet:
          </span>
          <code className="mono" style={{ color: 'var(--accent-emerald)', marginLeft: 6 }}>
            {cand.terminal_deposit_address}
          </code>
        </div>
      )}

      {/* Statutory Legal Demarcation Notice */}
      <div className="legal-demarcation-card">
        <div className="demarcation-header">
          ⚖️ Statutory Evidentiary Demarcation Notice
        </div>
        <div className="demarcation-row">
          <span style={{ color: 'var(--text-secondary)' }}>Infrastructure Control:</span>
          <strong style={{ color: 'var(--text-white)' }}>
            {attribution.operator_beneficiary.operator_attribution}
          </strong>
        </div>
        <div className="demarcation-row">
          <span style={{ color: 'var(--text-secondary)' }}>Beneficiary Identity:</span>
          <strong style={{ color: 'var(--accent-crimson)' }}>
            {attribution.operator_beneficiary.beneficiary_identity}
          </strong>
        </div>
        <div className="demarcation-desc">
          On-chain clustering attributes infrastructure ownership to {cand.entity_name}. 
          Individual user identity requires legal subpoena under Section 91 CrPC / MLAT treaties.
        </div>
      </div>

      {/* Factor Breakdown */}
      <div className="factor-section-title">
        Attribution Evidence Factors ("Why {cand.entity_name}?")
      </div>
      <div className="factor-rows">
        {cand.factors.map((f, idx) => {
          const ablated = ablatedFactors.has(f.factor_name);
          return (
            <div key={idx} className="factor-card-item" style={{ opacity: ablated ? 0.45 : 1 }}>
              <div className="factor-left">
                <div className="factor-name">{f.factor_name}</div>
                <div className="factor-subtext">{f.description}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className={`factor-score-pill ${f.contribution_points >= 0 ? 'positive' : 'penalty'}`}>
                  {f.contribution_points >= 0 ? `+${f.contribution_points}` : f.contribution_points} pts
                </span>
                <button
                  className="tool-btn"
                  style={{ fontSize: 10, padding: '2px 5px' }}
                  title="Simulate factor ablation"
                  onClick={() => toggleAblation(f.factor_name)}
                >
                  {ablated ? 'Restore' : 'Ablate'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Counterfactual Sensitivity View */}
      <div style={{ marginTop: 12 }}>
        <button
          className="btn-secondary-action"
          style={{ width: '100%', justifyContent: 'center', fontSize: 11 }}
          onClick={() => setShowCounterfactual(!showCounterfactual)}
        >
          {showCounterfactual ? 'Hide Counterfactual Matrix' : '📊 View Counterfactual Sensitivity Matrix'}
        </button>
      </div>

      {showCounterfactual && cand.counterfactuals && (
        <div className="counterfactual-box">
          <div className="cf-header">
            <span className="cf-title">Algorithmic Evidence Factor Ablation</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>STABILITY SIMULATOR</span>
          </div>
          <table className="cf-table">
            <thead>
              <tr>
                <th>Factor Removed</th>
                <th>Base</th>
                <th>Ablated</th>
                <th>Delta</th>
                <th>Assessment</th>
              </tr>
            </thead>
            <tbody>
              {cand.counterfactuals.map((cf, idx) => (
                <tr key={idx}>
                  <td style={{ color: 'var(--text-white)' }}>{cf.factor_removed}</td>
                  <td className="mono">{cf.original_score}%</td>
                  <td className="mono" style={{ color: 'var(--accent-amber)' }}>{cf.new_score}%</td>
                  <td className="mono" style={{ color: 'var(--accent-crimson)' }}>-{cf.score_delta}</td>
                  <td>
                    <span className="priority-pill" style={{
                      background: cf.robustness_evaluation === 'ROBUST' ? 'var(--accent-emerald-subtle)' : 'var(--accent-amber-subtle)',
                      color: cf.robustness_evaluation === 'ROBUST' ? 'var(--accent-emerald)' : 'var(--accent-amber)',
                      border: '1px solid currentColor'
                    }}>
                      {cf.robustness_evaluation}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 16 }}>
        {onOpenReport && (
          <button className="btn-secondary-action" style={{ justifyContent: 'center' }} onClick={onOpenReport}>
            📄 Export Forensic Dossier
          </button>
        )}
        {onOpenActionPacket && (
          <button className="btn-trace" style={{ justifyContent: 'center' }} onClick={onOpenActionPacket}>
            ⚖️ Draft Sec 91 CrPC Notice
          </button>
        )}
      </div>
    </div>
  );
};
