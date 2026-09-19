// frontend/src/components/ReportModal.tsx
import React, { useState } from 'react';

interface ReportData {
  report_path: string;
  report_hash: string;
  case_id: string;
  generated_at: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  reportData: ReportData | null;
}

export const ReportModal: React.FC<Props> = ({ isOpen, onClose, reportData }) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !reportData) return null;

  const handleCopyHash = () => {
    navigator.clipboard.writeText(reportData.report_hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span>COURT-ADMISSIBLE FORENSIC REPORT</span>
            <span className="navbar-badge" style={{ color: 'var(--accent-green)', borderColor: 'var(--accent-green)' }}>
              SHA-256 SEALED
            </span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <div className="banner-warning">
            <strong>EVIDENTIARY RECORD INTEGRITY NOTICE:</strong><br />
            This forensic report package contains deterministic blockchain evidence, multi-factor attribution matrices, and topological fund-flow proofs. Prepared for compliance with Section 65B of the Indian Evidence Act.
          </div>

          <div style={{ marginBottom: 16 }}>
            <h4 style={{ color: 'var(--text-secondary)', fontSize: 12, textTransform: 'uppercase', marginBottom: 6 }}>
              Case Dossier Reference
            </h4>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-blue)' }}>
              {reportData.case_id}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Generated: {reportData.generated_at}
            </div>
          </div>

          <div style={{ background: 'var(--bg-input)', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)', marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                CRYPTOGRAPHIC TAMPER-EVIDENT EVIDENCE SEAL (SHA-256):
              </span>
              <button className="copy-badge-btn" onClick={handleCopyHash}>
                {copied ? 'Copied to Clipboard!' : 'Copy Hash'}
              </button>
            </div>
            <code className="mono" style={{ color: 'var(--accent-green)', fontSize: 13, wordBreak: 'break-all' }}>
              {reportData.report_hash}
            </code>
          </div>

          <div style={{ background: 'var(--bg-input)', padding: 14, borderRadius: 6, border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Generated HTML Report Location:
            </div>
            <code className="mono" style={{ fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-all' }}>
              {reportData.report_path}
            </code>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
          <a
            href={`file:///${reportData.report_path.replace(/\\/g, '/')}`}
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
            style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
          >
            Open HTML Report in Browser
          </a>
        </div>
      </div>
    </div>
  );
};
