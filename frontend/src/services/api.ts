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
    shortest_path_hops?: number;
    terminal_deposit_address?: string;
    hot_wallet_cluster?: string;
    uncertainty_penalties?: number;
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

// ---------------------------------------------------------------------------
// Phase 7 Investigation API Types & Client (Strictly typed to InvestigationResponse)
// ---------------------------------------------------------------------------

export interface TraceMetadata {
  direction: string;
  requested_max_hops: number;
  actual_max_hops: number;
  max_hops_reached: boolean;
  max_transactions: number;
  transactions_used: number;
  transaction_limit_reached: boolean;
  boundary_nodes_count: number;
  termination_reason: string;
}

export interface InvestigationSummary {
  nodes: number;
  edges: number;
  transactions: number;
  transfers: number;
  hops: number;
}

export type ResolutionStatus = 'RESOLVED' | 'NOT_FOUND' | 'AMBIGUOUS';

export type EntityType =
  | 'VASP'
  | 'EXCHANGE'
  | 'CUSTODIAN'
  | 'PAYMENT_PROVIDER'
  | 'MINER'
  | 'BRIDGE'
  | 'PROTOCOL'
  | 'UNKNOWN';

export interface EntityCandidate {
  entity_id: string;
  entity_name: string;
  entity_type: EntityType;
  vasp_status: boolean;
  source: string;
  source_reference: string;
  confidence?: number | null;
  notes?: string | null;
}

export interface EntityResolution {
  chain: string;
  address: string;
  entity_id?: string | null;
  entity_name?: string | null;
  entity_type?: EntityType | null;
  vasp_status: boolean;
  source?: string | null;
  source_reference?: string | null;
  resolution_status: ResolutionStatus;
  resolved_at: string;
  candidates?: EntityCandidate[];
}

export interface VaspAttribution {
  address: string;
  chain: string;
  entity_id: string;
  entity_name: string;
  entity_type: EntityType;
  vasp_status: boolean;
  hop_distance: number;
  direction: string;
  path: string[];
  resolution_status: ResolutionStatus;
  source: string;
  source_reference: string;
  relevant_transfer_ids?: string[];
  attributed_at?: string;
}

export interface InvestigationNode {
  id: string;
  address: string;
  chain: string;
  node_type: string; // SUSPECT, INTERMEDIARY, VASP_DEPOSIT, VASP_HOT, MIXER, BRIDGE, BOUNDARY
  label?: string | null;
  entity_name?: string | null;
  entity_type?: string | null;
  is_vasp?: boolean;
  confidence?: number;
  hop_distance?: number;
  is_boundary?: boolean;
  boundary_reason?: string | null;
  is_breakpoint?: boolean;
  breakpoint?: boolean;
  cluster_id?: string | null;
  risk_score?: number;
  metadata?: Record<string, any>;
}

export interface InvestigationEdge {
  id: string;
  transfer_id: string;
  tx_hash: string;
  source: string;
  target: string;
  asset_id: string;
  asset_symbol: string;
  amount: string; // Exact Decimal representation preserved as string
  timestamp?: string | null;
  transfer_type: string; // NATIVE, TOKEN, INTERNAL, UTXO_INPUT, UTXO_OUTPUT
  edge_type?: string;
  hop?: number;
  is_boundary?: boolean;
  evidence_ref?: string | null;
  metadata?: Record<string, any>;
}

export interface InvestigationGraphData {
  case_id?: string;
  suspect_wallet?: string;
  chain?: string;
  nodes: InvestigationNode[];
  edges: InvestigationEdge[];
  breakpoints?: any[];
  hop_depth?: number;
  total_nodes?: number;
  total_edges?: number;
}

export type EvidenceClass = 'OBSERVED' | 'DERIVED' | 'RESOLVED' | 'INFERRED' | 'UNKNOWN';

export interface EvidenceItem {
  evidence_id: string;
  evidence_class: EvidenceClass;
  evidence_type: string;
  title: string;
  description: string;
  source: string;
  source_reference?: string | null;
  tx_hash?: string | null;
  transfer_id?: string | null;
  source_address?: string | null;
  destination_address?: string | null;
  asset?: string | null;
  amount?: string | null;
  timestamp?: string | null;
  hop_distance?: number | null;
  graph_relationship?: string | null;
  entity_association?: string | null;
  vasp_association?: string | null;
  confidence_qualification?: string | null;
  provenance_metadata?: Record<string, any>;
}

export interface CaseDossier {
  dossier_id: string;
  investigation_id: string;
  chain: string;
  root_wallet: string;
  direction: string;
  requested_max_hops: number;
  actual_depth_reached: number;
  trace_termination_reason: string;
  summary: InvestigationSummary;
  nodes_count: number;
  edges_count: number;
  transactions_count: number;
  transfers_count: number;
  entity_resolutions: EntityResolution[];
  vasp_attributions: VaspAttribution[];
  evidence_items: EvidenceItem[];
  operator_vs_beneficiary_notice: string;
  limitations_disclaimer: string;
  generated_at: string;
  dossier_hash_sha256: string;
}

export interface LawfulActionPacketData {
  packet_id: string;
  case_id: string;
  suspect_wallet: string;
  chain: string;
  attributed_vasp: string;
  attribution_confidence: string;
  operator_role: string;
  beneficiary_identity: string;
  integrity_hash_sha256: string;
  preservation_notice_draft: string;
  disclosure_request_draft: string;
  statutory_disclaimer: string;
  generated_at?: string;
  investigator?: string;
  terminal_deposit_address?: string;
  formal_disclosure_draft?: string;
}

export interface InvestigationResponse {
  investigation_id: string;
  chain: string;
  root_address: string;
  status: string;
  summary: InvestigationSummary;
  graph: InvestigationGraphData;
  trace?: TraceMetadata;
  entity_resolutions?: EntityResolution[];
  vasp_attributions?: VaspAttribution[];
  evidence_items?: EvidenceItem[];
  created_at?: string;
}

export interface InvestigationCreateRequest {
  chain: string;
  address: string;
  direction?: 'outgoing' | 'incoming' | string;
  max_hops?: number;
  max_transactions?: number;
}


/**
 * Centralized API client function to initiate a wallet investigation via POST /api/v1/investigations.
 */
export async function investigateWallet(
  data: InvestigationCreateRequest
): Promise<InvestigationResponse> {
  const url = `${API_BASE}/v1/investigations`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json'
      },
      body: JSON.stringify({
        chain: data.chain.toLowerCase(),
        address: data.address.trim(),
        direction: data.direction || 'outgoing',
        max_hops: data.max_hops ?? 1,
        max_transactions: data.max_transactions ?? 50
      })
    });
  } catch (err) {
    throw new Error('Unable to connect to investigation service. Please ensure the backend is running.');
  }

  if (!res.ok) {
    let errorDetail = `Investigation failed with HTTP ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson.detail) {
        if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
        }
      }
    } catch {
      // Fall back to status text
      if (res.status === 400) errorDetail = 'Invalid wallet address or unsupported blockchain format.';
      else if (res.status === 422) errorDetail = 'Invalid request parameters (check address, max hops, or max transactions).';
      else if (res.status === 429) errorDetail = 'Upstream blockchain provider rate limit exceeded. Please wait a moment.';
      else if (res.status === 502) errorDetail = 'Upstream blockchain provider communication error.';
      else if (res.status === 503) errorDetail = 'Blockchain intelligence provider service currently unavailable.';
      else if (res.status === 504) errorDetail = 'Blockchain provider query timed out.';
    }
    throw new Error(errorDetail);
  }

  const result: InvestigationResponse = await res.json();
  return result;
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

/**
 * Phase 10 — Case Dossier & Export API Client Endpoints
 */
export async function fetchInvestigationDossier(
  investigation: InvestigationResponse
): Promise<CaseDossier> {
  const res = await fetch(`${API_BASE}/v1/investigations/dossier`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(investigation)
  });
  if (!res.ok) {
    throw new Error(`Failed to generate case dossier: ${res.statusText}`);
  }
  return res.json();
}

export async function generateInvestigationReport(
  investigation: InvestigationResponse,
  investigator: string = 'Authorized Investigating Officer'
): Promise<{ report_path: string; report_hash: string; html_content: string }> {
  const res = await fetch(`${API_BASE}/v1/investigations/pdf?investigator=${encodeURIComponent(investigator)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(investigation)
  });
  if (!res.ok) {
    throw new Error(`Failed to generate forensic report: ${res.statusText}`);
  }
  return res.json();
}

export async function generateInvestigationActionPacket(
  investigation: InvestigationResponse,
  investigator: string = 'Authorized Investigating Officer'
): Promise<LawfulActionPacketData> {
  const res = await fetch(`${API_BASE}/v1/investigations/action-packet?investigator=${encodeURIComponent(investigator)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(investigation)
  });
  if (!res.ok) {
    throw new Error(`Failed to draft action packet: ${res.statusText}`);
  }
  return res.json();
}

export function downloadJsonFile(data: any, filename: string): void {
  const jsonStr = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function downloadHtmlFile(htmlContent: string, filename: string): void {
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

