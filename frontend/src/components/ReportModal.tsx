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
            <span>COURT-ADMISSIBLE FORENSIC DOSSIER</span>
            <span className="badge-pill verified" style={{ marginLeft: 10 }}>
              SHA-256 SEALED
            </span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <div className="legal-card">
            <div className="legal-card-title">Evidentiary Record Integrity Notice</div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              This forensic report package contains deterministic blockchain evidence, multi-factor attribution matrices, and topological fund-flow proofs. Prepared for compliance with Section 65B of the Indian Evidence Act.
            </div>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4, fontWeight: 700 }}>
              Case Dossier Reference
            </div>
            <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--accent-primary)' }}>
              {reportData.case_id}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Generated: {reportData.generated_at}
            </div>
          </div>

          <div style={{ background: 'var(--bg-input)', padding: 14, borderRadius: 6, border: '1px solid var(--border-subtle)', marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                CRYPTOGRAPHIC EVIDENCE SEAL (SHA-256):
              </span>
              <button className="tool-btn" onClick={handleCopyHash}>
                {copied ? 'Copied' : 'Copy Hash'}
              </button>
            </div>
            <code className="mono" style={{ color: 'var(--accent-primary)', fontSize: 12, wordBreak: 'break-all', fontWeight: 600 }}>
              {reportData.report_hash}
            </code>
          </div>

          <div style={{ background: 'var(--bg-input)', padding: 14, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: 10, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', marginBottom: 6 }}>
              Generated HTML Report Location:
            </div>
            <code className="mono" style={{ fontSize: 11, color: 'var(--text-primary)', wordBreak: 'break-all' }}>
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
            Open Dossier in Browser
          </a>
        </div>
      </div>
    </div>
  );
};
export default ReportModal;
