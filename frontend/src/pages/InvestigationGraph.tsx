// frontend/src/pages/InvestigationGraph.tsx
import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { GraphData } from '../services/api';

interface Props {
  graphData: GraphData;
  theme?: 'light' | 'dark';
  caseId?: string;
}

export const InvestigationGraph: React.FC<Props> = ({ graphData, theme = 'light', caseId }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [layoutMode, setLayoutMode] = useState<'breadthfirst' | 'cose'>('breadthfirst');
  const [copied, setCopied] = useState(false);

  const isDark = theme === 'dark';

  useEffect(() => {
    if (!containerRef.current) return;

    const elements: cytoscape.ElementDefinition[] = [];

    // Map Nodes with Palette-aligned geometry and color
    graphData.nodes.forEach((n) => {
      let bg = isDark ? '#222427' : '#ffffff';
      let border = isDark ? '#546a7b' : '#c6c5b9';
      let shape: cytoscape.Css.NodeShape = 'ellipse';
      let size = 32;

      if (n.node_type === 'SUSPECT') {
        bg = isDark ? '#361e22' : '#fdeded';
        border = isDark ? '#cf5e5e' : '#ba4747';
        shape = 'round-rectangle';
        size = 36;
      } else if (n.node_type === 'VASP_DEPOSIT') {
        bg = isDark ? '#1a272c' : '#f0f7f8';
        border = '#62929e';
        shape = 'hexagon';
        size = 36;
      } else if (n.node_type === 'VASP_HOT') {
        bg = isDark ? '#222d35' : '#eaf2f5';
        border = '#546a7b';
        shape = 'round-rectangle';
        size = 40;
      } else if (n.node_type === 'MIXER') {
        bg = isDark ? '#26282a' : '#f3f2ee';
        border = isDark ? '#c6c5b9' : '#393d3f';
        shape = 'octagon';
        size = 36;
      } else if (n.node_type === 'BRIDGE') {
        bg = isDark ? '#1f272c' : '#eff4f6';
        border = '#62929e';
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
            'color': isDark ? '#fdfdff' : '#393d3f',
            'font-size': '11px',
            'font-family': 'JetBrains Mono, monospace',
            'font-weight': 600,
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'text-background-opacity': 0.88,
            'text-background-color': isDark ? '#18191b' : '#ffffff',
            'text-background-padding': '2px',
            'text-background-shape': 'roundrectangle'
          }
        },
        {
          selector: 'node[?isBreakpoint]',
          style: {
            'border-color': isDark ? '#cf5e5e' : '#ba4747',
            'border-width': 3,
            'border-opacity': 1
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#62929e',
            'border-width': 3,
            'border-opacity': 1
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': isDark ? '#393d3f' : '#c6c5b9',
            'target-arrow-color': '#62929e',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.1,
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'font-family': 'JetBrains Mono, monospace',
            'font-weight': 600,
            'color': isDark ? '#c6c5b9' : '#546a7b',
            'text-background-opacity': 0.9,
            'text-background-color': isDark ? '#222427' : '#ffffff',
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
            'text-rotation': 'autorotate'
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#62929e',
            'target-arrow-color': '#62929e',
            'width': 2.5,
            'color': isDark ? '#fdfdff' : '#393d3f'
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

    const resizeObserver = new ResizeObserver(() => {
      if (cyRef.current) {
        cyRef.current.resize();
      }
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
      cy.destroy();
    };
  }, [graphData, layoutMode, isDark]);

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

  const hasBreakpoint = graphData.nodes.some((n) => n.is_breakpoint);

  return (
    <div className="card-box">
      {/* Graph Toolbar */}
      <div className="graph-toolbar">
        <div className="toolbar-group">
          <span style={{ fontWeight: 800, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-primary)', marginRight: 4 }}>
            Map Explorer
          </span>
          {caseId && (
            <span className="case-badge-pill" style={{ fontSize: 10, padding: '1px 6px', marginRight: 6 }}>
              {caseId}
            </span>
          )}
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
            -
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 11, color: 'var(--text-muted)' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: isDark ? '#cf5e5e' : '#ba4747' }}></span> Suspect
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: '#62929e' }}></span> Deposit
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: '#546a7b' }}></span> VASP Hub
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: isDark ? '#c6c5b9' : '#393d3f' }}></span> Mixer
          </span>
        </div>
      </div>

      {/* Cytoscape Canvas Container */}
      <div className="graph-canvas" ref={containerRef} />

      {/* Obfuscation Breakpoint Alert Bar */}
      {hasBreakpoint && (
        <div className="alert-strip">
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span className="alert-badge">BREAKPOINT DETECTED</span>
            <span className="alert-desc">
              Topological anomaly at transit hop: rapid fan-out or mixer layer identified.
            </span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--sig-critical)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
            CHOKEPOINT: BRK-02
          </span>
        </div>
      )}

      {/* Interactive Node Inspector Drawer */}
      {selectedNode && (
        <div className="inspector-drawer">
          <div>
            <div className="inspector-label">Selected Address</div>
            <div className="inspector-val" title={selectedNode.address}>
              {selectedNode.address}
            </div>
          </div>
          <div>
            <div className="inspector-label">Entity Classification</div>
            <div className="inspector-val" style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
              {selectedNode.entity_name} ({selectedNode.type})
            </div>
          </div>
          <div>
            <div className="inspector-label">Connections</div>
            <div className="inspector-val">
              Inbound: {selectedNode.inDegree} | Outbound: {selectedNode.outDegree}
            </div>
          </div>
          <div>
            <button
              className="btn-secondary"
              style={{ fontSize: 11, padding: '4px 10px' }}
              onClick={() => handleCopyAddress(selectedNode.address)}
            >
              {copied ? 'Copied' : 'Copy Address'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
export default InvestigationGraph;
