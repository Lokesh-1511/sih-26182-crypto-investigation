// frontend/src/components/ExplainableCard.tsx
import React, { useState } from 'react';
import { AttributionData } from '../services/api';

interface Props {
  attribution: AttributionData;
}

export const ExplainableCard: React.FC<Props> = ({ attribution }) => {
  const [showCounterfactual, setShowCounterfactual] = useState(false);
  const cand = attribution.top_candidate;

  if (!cand) {
    return (
      <div className="card">
        <div className="card-title">VASP Attribution Analysis</div>
        <p style={{ color: 'var(--text-muted)' }}>No candidate VASP could be attributed with sufficient certainty.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">
        <span>TOP VASP ATTRIBUTION CANDIDATE</span>
        <span className="navbar-badge">{cand.confidence_band} CONFIDENCE</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 16 }}>
        <div>
          <h2 style={{ fontSize: 26, color: 'var(--accent-blue)', marginBottom: 4 }}>{cand.entity_name}</h2>
          <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
            Type: {cand.entity_type} | Shortest Path: {cand.shortest_path_hops} hops
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="score-badge">{cand.confidence_score}%</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>ATTRIBUTION SCORE</div>
        </div>
      </div>

      {/* Operator vs Beneficiary Banner */}
      <div className="banner-warning">
        <strong>OPERATOR VS BENEFICIARY DISTINCTION:</strong><br />
        Infrastructure: <strong>{attribution.operator_beneficiary.operator_attribution}</strong><br />
        Beneficiary Identity: <strong style={{ color: 'var(--accent-red)' }}>{attribution.operator_beneficiary.beneficiary_identity}</strong>
        <p style={{ fontSize: 11, marginTop: 4, opacity: 0.9 }}>{attribution.operator_beneficiary.legal_disclaimer}</p>
      </div>

      {/* Why Section */}
      <h4 style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: 8, letterSpacing: 0.5 }}>
        WHY DID THE SYSTEM ATTRIBUTE THIS WALLET TO {cand.entity_name.toUpperCase()}?
      </h4>

      <div style={{ background: 'var(--bg-input)', padding: '8px 16px', borderRadius: 6, marginBottom: 16 }}>
        {cand.factors.map((f, idx) => (
          <div key={idx} className="factor-item">
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{f.factor_name}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{f.description}</div>
            </div>
            <div className={f.contribution_points > 0 ? 'factor-pts' : 'factor-penalty'}>
              {f.contribution_points > 0 ? `+${f.contribution_points}` : f.contribution_points} pts
            </div>
          </div>
        ))}
      </div>

      {/* Counterfactual Sensitivity Toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <button
          className="btn-secondary"
          onClick={() => setShowCounterfactual(!showCounterfactual)}
        >
          {showCounterfactual ? 'Hide Counterfactual Analysis' : 'Show Counterfactual Sensitivity Analysis'}
        </button>
      </div>

      {showCounterfactual && cand.counterfactuals && (
        <div style={{ background: 'rgba(57, 197, 187, 0.08)', border: '1px solid var(--accent-cyan)', padding: 16, borderRadius: 6 }}>
          <h4 style={{ color: 'var(--accent-cyan)', marginBottom: 8 }}>Counterfactual Sensitivity Simulation</h4>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
            Simulates attribution stability when individual evidence factors are subtracted.
          </p>
          <table className="data-table">
            <thead>
              <tr>
                <th>Ablated Factor</th>
                <th>Original</th>
                <th>New Score</th>
                <th>Delta</th>
                <th>Robustness</th>
              </tr>
            </thead>
            <tbody>
              {cand.counterfactuals.map((cf, idx) => (
                <tr key={idx}>
                  <td>{cf.factor_removed}</td>
                  <td className="mono">{cf.original_score}%</td>
                  <td className="mono" style={{ color: 'var(--accent-amber)' }}>{cf.new_score}%</td>
                  <td className="mono" style={{ color: 'var(--accent-red)' }}>-{cf.score_delta}</td>
                  <td>
                    <span className="navbar-badge" style={{ borderColor: cf.robustness_evaluation === 'ROBUST' ? 'var(--accent-green)' : 'var(--accent-amber)' }}>
                      {cf.robustness_evaluation}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
