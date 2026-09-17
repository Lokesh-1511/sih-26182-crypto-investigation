// frontend/src/pages/InvestigationGraph.tsx
import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { GraphData } from '../services/api';

interface Props {
  graphData: GraphData;
}

export const InvestigationGraph: React.FC<Props> = ({ graphData }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedElement, setSelectedElement] = useState<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const elements: cytoscape.ElementDefinition[] = [];

    // Map nodes
    graphData.nodes.forEach((n) => {
      let bg = '#58a6ff'; // intermediary
      if (n.node_type === 'SUSPECT') bg = '#f85149';
      else if (n.node_type === 'VASP_DEPOSIT') bg = '#3fb950';
      else if (n.node_type === 'VASP_HOT') bg = '#238636';
      else if (n.node_type === 'MIXER') bg = '#d29922';
      else if (n.node_type === 'BRIDGE') bg = '#bc8cff';

      elements.push({
        data: {
          id: n.id,
          label: n.label || `${n.address.slice(0, 6)}...${n.address.slice(-4)}`,
          address: n.address,
          type: n.node_type,
          isBreakpoint: n.is_breakpoint,
          color: bg
        }
      });
    });

    // Map edges
    graphData.edges.forEach((e) => {
      elements.push({
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          label: `${e.amount} ${e.asset}`,
          tx_id: e.tx_id,
          amount: e.amount,
          asset: e.asset
        }
      });
    });

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'color': '#f0f6fc',
            'font-size': '11px',
            'font-family': 'JetBrains Mono',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'width': 28,
            'height': 28,
            'border-width': 2,
            'border-color': '#30363d'
          }
        },
        {
          selector: 'node[?isBreakpoint]',
          style: {
            'border-color': '#f85149',
            'border-width': 4,
            'width': 36,
            'height': 36
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#30363d',
            'target-arrow-color': '#58a6ff',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '9px',
            'color': '#8b949e',
            'text-rotation': 'autorotate',
            'text-margin-y': -8
          }
        },
        {
          selector: ':selected',
          style: {
            'border-color': '#58a6ff',
            'border-width': 4
          }
        }
      ],
      layout: {
        name: 'breadthfirst',
        directed: true,
        padding: 40,
        spacingFactor: 1.6
      }
    });

    cyRef.current.on('tap', 'node', (evt) => {
      setSelectedElement({ type: 'NODE', data: evt.target.data() });
    });

    cyRef.current.on('tap', 'edge', (evt) => {
      setSelectedElement({ type: 'EDGE', data: evt.target.data() });
    });

    return () => {
      cyRef.current?.destroy();
    };
  }, [graphData]);

  return (
    <div style={{ position: 'relative' }}>
      <div
        ref={containerRef}
        style={{
          width: '100%',
          height: '520px',
          background: 'var(--bg-input)',
          borderRadius: '8px',
          border: '1px solid var(--border-color)'
        }}
      />

      {/* Breakpoint Callout Banner if present */}
      {graphData.nodes.some(n => n.is_breakpoint) && (
        <div className="banner-danger" style={{ marginTop: 12 }}>
          <strong>⚠ OBFUSCATION BREAKPOINT DETECTED:</strong><br />
          Significant fund-flow topological shift flagged at Hop 2. The flow fans out into multiple parallel accounts to obscure downstream destinations.
        </div>
      )}

      {/* Element Inspector Drawer */}
      {selectedElement && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-title">
            <span>Inspector: {selectedElement.type}</span>
            <button className="btn-secondary" onClick={() => setSelectedElement(null)}>Close</button>
          </div>
          {selectedElement.type === 'NODE' ? (
            <div>
              <p>Address: <code className="mono">{selectedElement.data.address}</code></p>
              <p>Role: <strong>{selectedElement.data.type}</strong></p>
              {selectedElement.data.isBreakpoint && (
                <p style={{ color: 'var(--accent-red)', fontWeight: 'bold' }}>Flagged as Obfuscation Breakpoint</p>
              )}
            </div>
          ) : (
            <div>
              <p>Transaction ID: <code className="mono">{selectedElement.data.tx_id}</code></p>
              <p>Amount: <strong>{selectedElement.data.amount} {selectedElement.data.asset}</strong></p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
