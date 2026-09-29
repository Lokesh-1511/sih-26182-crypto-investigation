// frontend/src/components/WalletFundFlowGraph.tsx
import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { InvestigationGraphData, InvestigationNode, InvestigationEdge } from '../services/api';

interface Props {
  graphData: InvestigationGraphData;
  rootAddress: string;
  theme?: 'light' | 'dark';
  selectedNodeId?: string | null;
  selectedEdgeId?: string | null;
  onSelectNode: (node: InvestigationNode | null) => void;
  onSelectEdge: (edge: InvestigationEdge | null) => void;
}

const formatShortAddress = (addr: string) => {
  if (!addr) return '';
  if (addr.length <= 14) return addr;
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
};

const formatCompactEdgeAmount = (amountStr: string, symbol: string) => {
  if (!amountStr) return symbol || '';
  const parts = amountStr.split('.');
  if (parts.length === 2 && parts[1].length > 4) {
    const trimmedDec = parts[1].slice(0, 4).replace(/0+$/, '');
    const compactNum = trimmedDec.length > 0 ? `${parts[0]}.${trimmedDec}` : parts[0];
    return `${compactNum} ${symbol || ''}`.trim();
  }
  return `${amountStr} ${symbol || ''}`.trim();
};

export const WalletFundFlowGraph: React.FC<Props> = ({
  graphData,
  rootAddress,
  theme = 'light',
  selectedNodeId,
  selectedEdgeId,
  onSelectNode,
  onSelectEdge
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [layoutMode, setLayoutMode] = useState<'breadthfirst' | 'cose'>('breadthfirst');

  const isDark = theme === 'dark';

  useEffect(() => {
    if (!containerRef.current) return;

    const elements: cytoscape.ElementDefinition[] = [];
    const normalizedRoot = rootAddress.toLowerCase();

    // Map Nodes
    graphData.nodes.forEach((n) => {
      const isSuspect =
        n.node_type === 'SUSPECT' ||
        n.id.toLowerCase() === normalizedRoot ||
        n.address.toLowerCase() === normalizedRoot;

      const isBoundary = Boolean(n.is_boundary);
      const isVasp = Boolean(n.is_vasp || n.metadata?.is_vasp || n.node_type === 'VASP_DEPOSIT' || n.node_type === 'VASP_HOT');
      const shortAddr = formatShortAddress(n.address || n.id);
      
      let displayLabel = `ADDRESS\n${shortAddr}`;
      if (isSuspect) {
        displayLabel = `SUSPECT\n${shortAddr}`;
      } else if (isVasp) {
        const entLabel = n.entity_name ? (n.entity_name.length > 12 ? n.entity_name.slice(0, 10) + '..' : n.entity_name) : 'VASP';
        displayLabel = `◆ ${entLabel.toUpperCase()}\n${shortAddr}`;
      } else if (isBoundary) {
        displayLabel = `BOUNDARY\n${shortAddr}`;
      }

      let bg = isDark ? '#222427' : '#ffffff';
      let border = isDark ? '#546a7b' : '#c6c5b9';
      let borderWidth = 1.5;
      let borderStyle = 'solid';
      let width = 96;
      let height = 36;
      let textColor = isDark ? '#c6c5b9' : '#393d3f';

      if (isSuspect) {
        bg = isDark ? '#361e22' : '#fdeded';
        border = isDark ? '#cf5e5e' : '#ba4747';
        borderWidth = 3;
        width = 112;
        height = 42;
        textColor = isDark ? '#fdfdff' : '#ba4747';
      } else if (isVasp) {
        bg = isDark ? '#1a2930' : '#edf6f9';
        border = isDark ? '#62929e' : '#006d77';
        borderWidth = 2.5;
        width = 112;
        height = 42;
        textColor = isDark ? '#c6e2e9' : '#006d77';
      } else if (isBoundary) {
        bg = isDark ? '#292419' : '#fffdf5';
        border = isDark ? '#d4a373' : '#b08968';
        borderWidth = 2;
        borderStyle = 'dashed';
        width = 104;
        height = 38;
        textColor = isDark ? '#faedcd' : '#7f5539';
      }

      elements.push({
        data: {
          id: n.id,
          rawNode: n,
          address: n.address,
          chain: n.chain,
          nodeType: isSuspect ? 'SUSPECT' : isVasp ? 'VASP' : isBoundary ? 'BOUNDARY' : n.node_type,
          entityName: n.entity_name || null,
          entityType: n.entity_type || null,
          isSuspect: isSuspect,
          isVasp: isVasp,
          isBoundary: isBoundary,
          label: displayLabel,
          bgColor: bg,
          borderColor: border,
          borderWidth: borderWidth,
          borderStyle: borderStyle,
          nodeWidth: width,
          nodeHeight: height,
          textColor: textColor
        }
      });
    });

    // Map Edges (MultiDiGraph: separate bezier curves for multi-edge fund flows)
    graphData.edges.forEach((e) => {
      const edgeLabel = formatCompactEdgeAmount(e.amount, e.asset_symbol || e.asset_id || '');

      elements.push({
        data: {
          id: e.id || e.transfer_id,
          rawEdge: e,
          source: e.source,
          target: e.target,
          label: edgeLabel,
          amount: e.amount,
          assetSymbol: e.asset_symbol || e.asset_id,
          txHash: e.tx_hash,
          transferId: e.transfer_id,
          transferType: e.transfer_type
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
            'border-width': 'data(borderWidth)',
            'border-style': 'data(borderStyle)' as any,
            'shape': 'round-rectangle',
            'width': 'data(nodeWidth)',
            'height': 'data(nodeHeight)',
            'label': 'data(label)',
            'color': 'data(textColor)',
            'font-size': '10px',
            'font-family': 'JetBrains Mono, monospace',
            'font-weight': 600,
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap',
            'text-max-width': '100px',
            'text-background-opacity': 0
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#62929e',
            'border-width': 3,
            'border-opacity': 1,
            'underlay-color': '#62929e',
            'underlay-padding': 3,
            'underlay-opacity': 0.35
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': isDark ? '#4a535b' : '#b0b5ba',
            'target-arrow-color': '#62929e',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.3,
            'curve-style': 'bezier',
            'control-point-step-size': 45,
            'label': 'data(label)',
            'font-size': '10px',
            'font-family': 'JetBrains Mono, monospace',
            'font-weight': 700,
            'color': isDark ? '#c6c5b9' : '#393d3f',
            'text-background-opacity': 0.94,
            'text-background-color': isDark ? '#1a1c1e' : '#fdfdff',
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
            'width': 3.5,
            'color': isDark ? '#fdfdff' : '#141517'
          }
        }
      ],
      layout: {
        name: layoutMode,
        directed: true,
        padding: 35,
        spacingFactor: 1.35
      }
    });

    // Auto-fit & Center on initialization
    cy.ready(() => {
      cy.fit(undefined, 35);
      cy.center();
    });

    // Interaction Events
    cy.on('tap', 'node', (evt) => {
      const rawNode: InvestigationNode = evt.target.data('rawNode');
      onSelectNode(rawNode);
      onSelectEdge(null);
    });

    cy.on('tap', 'edge', (evt) => {
      const rawEdge: InvestigationEdge = evt.target.data('rawEdge');
      onSelectEdge(rawEdge);
      onSelectNode(null);
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        onSelectNode(null);
        onSelectEdge(null);
      }
    });

    cyRef.current = cy;

    const resizeObserver = new ResizeObserver(() => {
      if (cyRef.current) {
        cyRef.current.resize();
        cyRef.current.fit(undefined, 30);
      }
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
      cy.destroy();
    };
  }, [graphData, rootAddress, layoutMode, isDark]);

  // Sync external selections & center if edge selected
  useEffect(() => {
    if (!cyRef.current) return;
    cyRef.current.elements().unselect();
    if (selectedNodeId) {
      const nodeEl = cyRef.current.getElementById(selectedNodeId);
      nodeEl.select();
    } else if (selectedEdgeId) {
      const edgeEl = cyRef.current.getElementById(selectedEdgeId);
      edgeEl.select();
    }
  }, [selectedNodeId, selectedEdgeId]);

  const handleFit = () => {
    cyRef.current?.fit(undefined, 30);
    cyRef.current?.center();
  };

  const handleZoomIn = () => {
    cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  };

  const handleZoomOut = () => {
    cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  };

  return (
    <div className="card-box" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Graph Toolbar */}
      <div className="graph-toolbar">
        <div className="toolbar-group">
          <span style={{ fontWeight: 800, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-primary)', marginRight: 6 }}>
            Fund-Flow Graph
          </span>
          <button
            type="button"
            className={`tool-btn ${layoutMode === 'breadthfirst' ? 'active' : ''}`}
            onClick={() => setLayoutMode('breadthfirst')}
            title="Hierarchical Outgoing Flow"
          >
            Hierarchical Flow
          </button>
          <button
            type="button"
            className={`tool-btn ${layoutMode === 'cose' ? 'active' : ''}`}
            onClick={() => setLayoutMode('cose')}
            title="Force-Directed Topology"
          >
            Force Directed
          </button>
          <button type="button" className="tool-btn" onClick={handleFit} title="Fit Graph to Viewport">
            Fit View
          </button>
          <button type="button" className="tool-btn" onClick={handleZoomIn} title="Zoom In" aria-label="Zoom In">
            +
          </button>
          <button type="button" className="tool-btn" onClick={handleZoomOut} title="Zoom Out" aria-label="Zoom Out">
            -
          </button>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 11, color: 'var(--text-muted)', flexWrap: 'wrap' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 9, height: 9, borderRadius: 2, background: isDark ? '#cf5e5e' : '#ba4747' }}></span> SUSPECT
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 9, height: 9, borderRadius: 2, background: isDark ? '#546a7b' : '#c6c5b9' }}></span> ADDRESS
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 9, height: 9, borderRadius: 2, background: isDark ? '#62929e' : '#006d77' }}></span> ◆ VASP-ASSOCIATED
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 9, height: 9, borderRadius: 2, border: `1.5px dashed ${isDark ? '#d4a373' : '#b08968'}`, background: isDark ? '#292419' : '#fffdf5' }}></span> BOUNDARY
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--accent-primary)', fontWeight: 600 }}>
            <span>&rarr;</span> Fund Movement
          </span>
        </div>
      </div>

      {/* Cytoscape Canvas */}
      <div className="graph-canvas" ref={containerRef} style={{ flex: 1, minHeight: 350, width: '100%' }} />
    </div>
  );
};
