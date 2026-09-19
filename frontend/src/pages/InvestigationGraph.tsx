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
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [layoutMode, setLayoutMode] = useState<'breadthfirst' | 'cose'>('breadthfirst');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;

    const elements: cytoscape.ElementDefinition[] = [];

    // Map Nodes
    graphData.nodes.forEach((n) => {
      let bg = '#1e293b'; // Intermediary slate
      let border = '#475569';
      let shape: cytoscape.Css.NodeShape = 'ellipse';
      let size = 32;

      if (n.node_type === 'SUSPECT') {
        bg = '#3b0712';
        border = '#ef4444';
        shape = 'round-rectangle';
        size = 36;
      } else if (n.node_type === 'VASP_DEPOSIT') {
        bg = '#451a03';
        border = '#f59e0b';
        shape = 'hexagon';
        size = 34;
      } else if (n.node_type === 'VASP_HOT') {
        bg = '#172554';
        border = '#3b82f6';
        shape = 'round-rectangle';
        size = 40;
      } else if (n.node_type === 'MIXER') {
        bg = '#4a044e';
        border = '#d946ef';
        shape = 'octagon';
        size = 36;
      } else if (n.node_type === 'BRIDGE') {
        bg = '#083344';
        border = '#06b6d4';
        shape = 'diamond';
        size = 36;
      }

      const displayLabel = n.entity_name 
        ? n.entity_name 
        : n.label 
          ? n.label 
          : `${n.address.slice(0, 6)}...${n.address.slice(-4)}`;

      elements.push({
        data: {
          id: n.id,
          label: displayLabel,
          address: n.address,
          type: n.node_type,
          entity_name: n.entity_name || 'Unlabeled Transit',
          confidence: n.confidence,
          isBreakpoint: n.is_breakpoint,
          bgColor: bg,
          borderColor: border,
          nodeShape: shape,
          nodeSize: size
        }
      });
    });

    // Map Edges
    graphData.edges.forEach((e) => {
      elements.push({
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          label: `${e.amount} ${e.asset}`,
          tx_id: e.tx_id,
          amount: e.amount,
          asset: e.asset,
          hop: e.hop
        }
      });
    });

    const cy = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(bgColor)',
            'border-color': 'data(borderColor)',
            'border-width': 2,
            'shape': 'data(nodeShape)' as any,
            'width': 'data(nodeSize)',
            'height': 'data(nodeSize)',
            'label': 'data(label)',
            'color': '#f8fafc',
            'font-size': '11px',
            'font-family': 'JetBrains Mono, monospace',
            'font-weight': 600,
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'text-background-opacity': 0.8,
            'text-background-color': '#090d16',
            'text-background-padding': '2px',
            'text-background-shape': 'roundrectangle'
          }
        },
        {
          selector: 'node[?isBreakpoint]',
          style: {
            'border-color': '#ef4444',
            'border-width': 4,
            'border-opacity': 1
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#38bdf8',
            'border-width': 3,
            'border-opacity': 1
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#334155',
            'target-arrow-color': '#64748b',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.1,
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'font-family': 'JetBrains Mono, monospace',
            'font-weight': 500,
            'color': '#94a3b8',
            'text-background-opacity': 0.9,
            'text-background-color': '#0b1120',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'text-rotation': 'autorotate'
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#3b82f6',
            'target-arrow-color': '#3b82f6',
            'width': 3,
            'color': '#ffffff'
          }
        }
      ],
      layout: {
        name: layoutMode,
        directed: true,
        padding: 40,
        spacingFactor: 1.3
      }
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode({
        id: node.data('id'),
        address: node.data('address'),
        label: node.data('label'),
        type: node.data('type'),
        entity_name: node.data('entity_name'),
        confidence: node.data('confidence'),
        isBreakpoint: node.data('isBreakpoint'),
        inDegree: node.incomers('edge').length,
        outDegree: node.outgoers('edge').length
      });
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphData, layoutMode]);

  const handleFit = () => {
    cyRef.current?.fit(undefined, 30);
  };

  const handleZoomIn = () => {
    cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  };

  const handleZoomOut = () => {
    cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  };

  const handleCopyAddress = (addr: string) => {
    navigator.clipboard.writeText(addr);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Check if any node in graph is a breakpoint
  const hasBreakpoint = graphData.nodes.some((n) => n.is_breakpoint);

  return (
    <div className="panel-card">
      {/* Graph Toolbar */}
      <div className="graph-toolbar">
        <div className="toolbar-group">
          <button
            className={`tool-btn ${layoutMode === 'breadthfirst' ? 'active' : ''}`}
            onClick={() => setLayoutMode('breadthfirst')}
          >
            Hierarchical Flow
          </button>
          <button
            className={`tool-btn ${layoutMode === 'cose' ? 'active' : ''}`}
            onClick={() => setLayoutMode('cose')}
          >
            Force Directed
          </button>
          <button className="tool-btn" onClick={handleFit}>
            Fit View
          </button>
          <button className="tool-btn" onClick={handleZoomIn}>
            +
          </button>
          <button className="tool-btn" onClick={handleZoomOut}>
            −
          </button>
        </div>

        <div className="legend-pills">
          <div className="legend-item">
            <span className="legend-dot suspect"></span> Suspect
          </div>
          <div className="legend-item">
            <span className="legend-dot intermediary"></span> Transit
          </div>
          <div className="legend-item">
            <span className="legend-dot deposit"></span> Deposit
          </div>
          <div className="legend-item">
            <span className="legend-dot hot"></span> VASP Hub
          </div>
          <div className="legend-item">
            <span className="legend-dot mixer"></span> Mixer/Bridge
          </div>
        </div>
      </div>

      {/* Cytoscape Canvas Container */}
      <div className="graph-canvas-container" ref={containerRef} />

      {/* Obfuscation Breakpoint Alert Bar */}
      {hasBreakpoint && (
        <div className="breakpoint-alert-strip">
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span className="breakpoint-badge">⚠️ Obfuscation Breakpoint Flagged</span>
            <span className="breakpoint-text">
              Topological anomaly detected at transit hop: rapid fan-out / layering detected.
            </span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--accent-crimson)', fontFamily: 'var(--font-mono)' }}>
            CHOKEPOINT_ID: BRK-02
          </span>
        </div>
      )}

      {/* Interactive Node Inspector Drawer */}
      {selectedNode && (
        <div className="node-inspector-drawer">
          <div>
            <div className="inspector-field-label">Selected Address</div>
            <div className="inspector-field-val" title={selectedNode.address}>
              {selectedNode.address}
            </div>
          </div>
          <div>
            <div className="inspector-field-label">Entity Classification</div>
            <div className="inspector-field-val" style={{ color: 'var(--accent-blue)' }}>
              {selectedNode.entity_name} ({selectedNode.type})
            </div>
          </div>
          <div>
            <div className="inspector-field-label">Flow Connections</div>
            <div className="inspector-field-val">
              In: {selectedNode.inDegree} | Out: {selectedNode.outDegree}
            </div>
          </div>
          <div>
            <button
              className="btn-secondary-action"
              style={{ fontSize: 11, padding: '3px 8px' }}
              onClick={() => handleCopyAddress(selectedNode.address)}
            >
              {copied ? 'Copied!' : 'Copy Address'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
