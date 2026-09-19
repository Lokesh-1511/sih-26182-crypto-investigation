// frontend/src/components/ActionPacketModal.tsx
import React, { useState } from 'react';

interface ActionPacketData {
  packet_id: string;
  case_id: string;
  investigator: string;
  attributed_vasp: string;
  terminal_deposit_address?: string;
  preservation_notice_draft: string;
  formal_disclosure_draft: string;
  statutory_disclaimer: string;
  generated_at: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  packetData: ActionPacketData | null;
}

export const ActionPacketModal: React.FC<Props> = ({ isOpen, onClose, packetData }) => {
  const [activeNoticeTab, setActiveNoticeTab] = useState<'PRESERVATION' | 'DISCLOSURE'>('PRESERVATION');
  const [copied, setCopied] = useState(false);

  if (!isOpen || !packetData) return null;

  const currentText = activeNoticeTab === 'PRESERVATION'
    ? packetData.preservation_notice_draft
    : packetData.formal_disclosure_draft;

  const handleCopyNotice = () => {
    navigator.clipboard.writeText(currentText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" style={{ maxWidth: 850 }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <span>LAWFUL ACTION PACKET (STATUTORY REQUISITION)</span>
            <span className="navbar-badge" style={{ color: 'var(--accent-amber)', borderColor: 'var(--accent-amber)' }}>
              OFFICER REVIEW REQUIRED
            </span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <div className="banner-warning">
            <strong>CRITICAL PROCEDURAL SAFEGUARD:</strong><br />
            {packetData.statutory_disclaimer}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
            <div style={{ background: 'var(--bg-input)', padding: 10, borderRadius: 6, border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>PACKET IDENTIFIER</div>
              <div className="mono" style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-blue)' }}>
                {packetData.packet_id}
              </div>
            </div>
            <div style={{ background: 'var(--bg-input)', padding: 10, borderRadius: 6, border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>TARGET VASP RECIPIENT</div>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                {packetData.attributed_vasp}
              </div>
            </div>
            <div style={{ background: 'var(--bg-input)', padding: 10, borderRadius: 6, border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>TERMINAL DEPOSIT WALLET</div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--accent-green)' }}>
                {packetData.terminal_deposit_address || 'Identified in flow'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className={`nav-button ${activeNoticeTab === 'PRESERVATION' ? 'active' : ''}`}
                onClick={() => setActiveNoticeTab('PRESERVATION')}
              >
                Urgent Preservation Notice (Sec 91 CrPC)
              </button>
              <button
                className={`nav-button ${activeNoticeTab === 'DISCLOSURE' ? 'active' : ''}`}
                onClick={() => setActiveNoticeTab('DISCLOSURE')}
              >
                Formal Disclosure Requisition
              </button>
            </div>
            <button className="copy-badge-btn" onClick={handleCopyNotice}>
              {copied ? 'Copied to Clipboard!' : 'Copy Notice Text'}
            </button>
          </div>

          <pre style={{
            background: 'var(--bg-input)',
            padding: 14,
            borderRadius: 6,
            border: '1px solid var(--border-color)',
            fontSize: 12,
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            maxHeight: 320,
            overflowY: 'auto'
          }}>
            {currentText}
          </pre>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
          <button className="btn-primary" onClick={handleCopyNotice}>
            {copied ? 'Copied!' : 'Copy Notice Draft to Clipboard'}
          </button>
        </div>
      </div>
    </div>
  );
};
