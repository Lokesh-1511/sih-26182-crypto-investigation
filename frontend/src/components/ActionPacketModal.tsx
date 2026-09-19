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
            <span className="badge-pill urgent" style={{ marginLeft: 10 }}>
              OFFICER REVIEW REQUIRED
            </span>
          </div>
          <button className="modal-close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <div className="legal-card" style={{ borderLeftColor: 'var(--sig-alert)' }}>
            <div className="legal-card-title" style={{ color: 'var(--sig-alert)' }}>
              Critical Procedural Safeguard
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {packetData.statutory_disclaimer}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
            <div style={{ background: 'var(--bg-input)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 700, marginBottom: 4 }}>
                Packet Identifier
              </div>
              <div className="mono" style={{ fontSize: 12, fontWeight: 700, color: 'var(--accent-primary)' }}>
                {packetData.packet_id}
              </div>
            </div>
            <div style={{ background: 'var(--bg-input)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 700, marginBottom: 4 }}>
                Target VASP Recipient
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                {packetData.attributed_vasp}
              </div>
            </div>
            <div style={{ background: 'var(--bg-input)', padding: 10, borderRadius: 6, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 700, marginBottom: 4 }}>
                Terminal Deposit Wallet
              </div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--accent-primary)' }}>
                {packetData.terminal_deposit_address || 'Identified in flow'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className={`tool-btn ${activeNoticeTab === 'PRESERVATION' ? 'active' : ''}`}
                onClick={() => setActiveNoticeTab('PRESERVATION')}
              >
                Urgent Preservation Notice (Sec 91 CrPC)
              </button>
              <button
                className={`tool-btn ${activeNoticeTab === 'DISCLOSURE' ? 'active' : ''}`}
                onClick={() => setActiveNoticeTab('DISCLOSURE')}
              >
                Formal Disclosure Requisition
              </button>
            </div>
            <button className="tool-btn" onClick={handleCopyNotice}>
              {copied ? 'Copied' : 'Copy Notice Text'}
            </button>
          </div>

          <pre style={{
            background: 'var(--bg-input)',
            padding: 14,
            borderRadius: 6,
            border: '1px solid var(--border-subtle)',
            fontSize: 12,
            lineHeight: 1.6,
            color: 'var(--text-primary)',
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
            {copied ? 'Copied' : 'Copy Notice Draft to Clipboard'}
          </button>
        </div>
      </div>
    </div>
  );
};
export default ActionPacketModal;
