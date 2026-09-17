// frontend/src/services/api.ts
const API_BASE = 'http://localhost:8000/api';

export interface CaseData {
  case_id: string;
  title: string;
  investigator: string;
  description?: string;
  status: string;
  priority: string;
  suspect_wallet?: string;
  chain?: string;
  created_at: string;
}

export interface GraphData {
  case_id: string;
  suspect_wallet: string;
  chain: string;
  nodes: Array<{
    id: string;
    address: string;
    node_type: string;
    label?: string;
    entity_name?: string;
    confidence: number;
    is_breakpoint: boolean;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    tx_id: string;
    asset: string;
    amount: number;
    timestamp: string;
    hop: number;
  }>;
  total_nodes: number;
  total_edges: number;
}

export interface AttributionData {
  case_id: string;
  suspect_wallet: string;
  chain: string;
  top_candidate?: {
    rank: number;
    entity_name: string;
    entity_type: string;
    confidence_score: number;
    confidence_band: string;
    factors: Array<{
      factor_name: string;
      contribution_points: number;
      factor_type: string;
      description: string;
      supporting_tx_ids: string[];
    }>;
    counterfactuals?: Array<{
      factor_removed: string;
      original_score: number;
      new_score: number;
      score_delta: number;
      robustness_evaluation: string;
    }>;
    supporting_tx_ids: string[];
  };
  operator_beneficiary: {
    operator_attribution: string;
    operator_confidence: string;
    beneficiary_identity: string;
    legal_disclaimer: string;
  };
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchCases(): Promise<CaseData[]> {
  const res = await fetch(`${API_BASE}/cases`);
  return res.json();
}

export async function createCase(data: {
  title: string;
  investigator: string;
  suspect_wallet: string;
  chain: string;
}): Promise<CaseData> {
  const res = await fetch(`${API_BASE}/cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function startTrace(caseId: string) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/trace`, { method: 'POST' });
  return res.json();
}

export async function fetchGraph(caseId: string): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/graph`);
  return res.json();
}

export async function fetchAttribution(caseId: string): Promise<AttributionData> {
  const res = await fetch(`${API_BASE}/cases/${caseId}/attribution`);
  return res.json();
}

export async function fetchRisk(caseId: string) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/risk`);
  return res.json();
}

export async function exportReport(caseId: string) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/report`, { method: 'POST' });
  return res.json();
}

export async function generateActionPacket(caseId: string) {
  const res = await fetch(`${API_BASE}/cases/${caseId}/action-packet`, { method: 'POST' });
  return res.json();
}
