// frontend/src/test/WalletInvestigationPage.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { WalletInvestigationPage } from '../pages/WalletInvestigationPage';
import * as api from '../services/api';
import { InvestigationResponse } from '../services/api';

const mockInvestigationResponse: InvestigationResponse = {
  investigation_id: 'inv_test_12345',
  chain: 'ethereum',
  root_address: '0x28C6c06298d514Db089934071355E5743bf21d60',
  status: 'completed',
  summary: {
    nodes: 7,
    edges: 5,
    transactions: 5,
    transfers: 5,
    hops: 1
  },
  trace: {
    direction: 'outgoing',
    requested_max_hops: 1,
    actual_max_hops: 1,
    max_hops_reached: true,
    max_transactions: 50,
    transactions_used: 5,
    transaction_limit_reached: false,
    boundary_nodes_count: 0,
    termination_reason: 'MAX_HOPS_REACHED'
  },
  graph: {
    case_id: 'inv_test_12345',
    suspect_wallet: '0x28c6c06298d514db089934071355e5743bf21d60',
    chain: 'ethereum',
    nodes: [
      {
        id: 'ethereum:0x28c6c06298d514db089934071355e5743bf21d60',
        address: '0x28c6c06298d514db089934071355e5743bf21d60',
        chain: 'ethereum',
        node_type: 'SUSPECT',
        hop_distance: 0,
        is_boundary: false,
        label: 'Binance Test Hot Wallet',
        entity_name: 'Binance Test Hot Wallet',
        entity_type: 'VASP',
        is_vasp: true,
        confidence: 1.0,
        is_breakpoint: false
      },
      {
        id: 'ethereum:0x1111111111111111111111111111111111111111',
        address: '0x1111111111111111111111111111111111111111',
        chain: 'ethereum',
        node_type: 'INTERMEDIARY',
        hop_distance: 1,
        is_boundary: false,
        label: 'Hop 1 Transit',
        entity_name: null,
        entity_type: null,
        is_vasp: false,
        confidence: 1.0,
        is_breakpoint: false
      }
    ],
    edges: [
      {
        id: 'transfer_100_0_0_0_0_0',
        transfer_id: 'transfer_100_0_0_0_0_0',
        tx_hash: '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        source: 'ethereum:0x28c6c06298d514db089934071355e5743bf21d60',
        target: 'ethereum:0x1111111111111111111111111111111111111111',
        asset_id: 'ETH',
        asset_symbol: 'ETH',
        amount: '1.500000000000000000',
        timestamp: '2026-09-28T12:00:00Z',
        transfer_type: 'NATIVE',
        hop: 1,
        is_boundary: false,
        evidence_ref: 'ev_tx_100'
      }
    ],
    total_nodes: 7,
    total_edges: 5,
    hop_depth: 1
  },
  entity_resolutions: [
    {
      chain: 'ethereum',
      address: '0x28c6c06298d514db089934071355e5743bf21d60',
      resolution_status: 'RESOLVED',
      entity_id: 'binance_test_hot_1',
      entity_name: 'Binance Test Hot Wallet',
      entity_type: 'VASP',
      vasp_status: true,
      source: 'local_registry',
      source_reference: 'tests/fixtures/intelligence/entities.json',
      resolved_at: '2026-09-29T12:00:00Z'
    },
    {
      chain: 'ethereum',
      address: '0x1111111111111111111111111111111111111111',
      resolution_status: 'NOT_FOUND',
      entity_id: null,
      entity_name: null,
      entity_type: 'UNKNOWN',
      vasp_status: false,
      source: 'local_registry',
      source_reference: null,
      resolved_at: '2026-09-29T12:00:00Z'
    }
  ],
  vasp_attributions: [
    {
      address: '0x28c6c06298d514db089934071355e5743bf21d60',
      chain: 'ethereum',
      entity_id: 'binance_test_hot_1',
      entity_name: 'Binance Test Hot Wallet',
      entity_type: 'VASP',
      vasp_status: true,
      hop_distance: 0,
      direction: 'outgoing',
      path: ['0x28c6c06298d514db089934071355e5743bf21d60'],
      relevant_transfer_ids: ['transfer_100_0_0_0_0_0'],
      resolution_status: 'RESOLVED',
      source: 'local_registry',
      source_reference: 'tests/fixtures/intelligence/entities.json'
    }
  ]
};

const mockEmptyResponse: InvestigationResponse = {
  investigation_id: 'inv_empty_999',
  chain: 'ethereum',
  root_address: '0x0000000000000000000000000000000000000000',
  status: 'completed',
  summary: {
    nodes: 1,
    edges: 0,
    transactions: 0,
    transfers: 0,
    hops: 0
  },
  trace: {
    direction: 'outgoing',
    requested_max_hops: 1,
    actual_max_hops: 0,
    max_hops_reached: false,
    max_transactions: 50,
    transactions_used: 0,
    transaction_limit_reached: false,
    boundary_nodes_count: 0,
    termination_reason: 'EMPTY_WALLET'
  },
  graph: {
    nodes: [
      {
        id: 'ethereum:0x0000000000000000000000000000000000000000',
        address: '0x0000000000000000000000000000000000000000',
        chain: 'ethereum',
        node_type: 'SUSPECT',
        hop_distance: 0,
        is_boundary: false
      }
    ],
    edges: [],
    total_nodes: 1,
    total_edges: 0,
    hop_depth: 0
  },
  entity_resolutions: [],
  vasp_attributions: []
};

describe('WalletInvestigationPage Component - Phase 8 Multi-Hop Fund-Flow Tracing', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('1. Renders compact investigation form with direction and initial ready state', () => {
    render(<WalletInvestigationPage theme="light" />);

    expect(screen.getByRole('heading', { name: /Wallet Investigation/i })).toBeInTheDocument();
    expect(screen.getByText(/Multi-hop fund-flow tracing/i)).toBeInTheDocument();
    expect(screen.getByText('Trace Direction')).toBeInTheDocument();
    expect(screen.getByText('Wallet Address')).toBeInTheDocument();
    expect(screen.getByDisplayValue('0x28C6c06298d514Db089934071355E5743bf21d60')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Investigate Wallet/i })).toBeInTheDocument();
    expect(screen.getByText('Ready to Investigate')).toBeInTheDocument();
  });

  it('2. Submits valid multi-hop investigation request with direction', async () => {
    const spy = vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockInvestigationResponse);

    render(<WalletInvestigationPage theme="light" />);

    const submitBtn = screen.getByRole('button', { name: /Investigate Wallet/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith({
        chain: 'ethereum',
        address: '0x28C6c06298d514Db089934071355E5743bf21d60',
        direction: 'outgoing',
        max_hops: 1,
        max_transactions: 50
      });
    });
  });

  it('3. Populates investigator KPI metric cards and depth reached display', async () => {
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockInvestigationResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      expect(screen.getByText('FORWARD TRACE')).toBeInTheDocument();
      expect(screen.getByText('1 / 1')).toBeInTheDocument();
      expect(screen.getByText('Depth reached')).toBeInTheDocument();
      expect(screen.getByText('Discovered wallets')).toBeInTheDocument();
      expect(screen.getByText('Fund transfers')).toBeInTheDocument();
    });
  });

  it('4. Renders root suspect wallet prominently in status bar and graph header', async () => {
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockInvestigationResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(screen.getByText('0x28C6...1d60')).toBeInTheDocument();
    });
  });

  it('5. Renders activity table with compact From → To routing and asset amounts', async () => {
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockInvestigationResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(screen.getByText('Ingested Transfer Activity')).toBeInTheDocument();
      expect(screen.getByText('1.500000000000000000')).toBeInTheDocument();
      expect(screen.getByText('NATIVE')).toBeInTheDocument();
    });
  });

  it('6. Edge selection opens structured Inspector with exact amount and transaction hash', async () => {
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockInvestigationResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(screen.getByText('Inspect')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Inspect'));

    await waitFor(() => {
      expect(screen.getByText('Fund Transfer Inspector')).toBeInTheDocument();
      expect(screen.getByText('1.500000000000000000 ETH')).toBeInTheDocument();
      expect(screen.getByText('0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')).toBeInTheDocument();
      expect(screen.getByText('ev_tx_100')).toBeInTheDocument();
    });
  });

  it('7. Displays API errors cleanly in a dismissible alert banner', async () => {
    vi.spyOn(api, 'investigateWallet').mockRejectedValue(
      new Error('Invalid wallet address format')
    );

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(screen.getByText('Investigation Error:')).toBeInTheDocument();
      expect(screen.getByText('Invalid wallet address format')).toBeInTheDocument();
    });
  });

  it('8. Handles empty investigation gracefully without error', async () => {
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockEmptyResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/No fund transfers were returned for this investigation/i)
      ).toBeInTheDocument();
    });
  });

  it('9. Preserves exact string representation of Decimal amounts in table and inspector', async () => {
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockInvestigationResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      const amountCell = screen.getByText('1.500000000000000000');
      expect(amountCell).toBeInTheDocument();
    });
  });

  it('10. Copies full un-truncated address and transaction hash on copy action', async () => {
    const writeTextSpy = vi.spyOn(navigator.clipboard, 'writeText');
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockInvestigationResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(screen.getAllByText('Copy').length).toBeGreaterThan(0);
    });

    const copyBtns = screen.getAllByText('Copy');
    fireEvent.click(copyBtns[0]);
    expect(writeTextSpy).toHaveBeenCalled();
  });

  it('11. Renders VASP node with classification and attribution context in Inspector', async () => {
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockInvestigationResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(screen.getByText('◆ VASP-ASSOCIATED')).toBeInTheDocument();
      expect(screen.getByTitle('Click to inspect root suspect wallet')).toBeInTheDocument();
    });

    // Inspect the root suspect wallet (which is resolved as Binance VASP)
    fireEvent.click(screen.getByTitle('Click to inspect root suspect wallet'));

    // Temporary debug
    // screen.debug();

    await waitFor(() => {
      expect(screen.getByText('Wallet Node Inspector')).toBeInTheDocument();
      expect(screen.getByText(/Classification/i)).toBeInTheDocument();
      expect(screen.getAllByText('Binance Test Hot Wallet').length).toBeGreaterThan(0);
      expect(screen.getAllByText('VASP').length).toBeGreaterThan(0);
      expect(screen.getByText(/Attribution Context/i)).toBeInTheDocument();
      expect(screen.getAllByText(/outgoing/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('tests/fixtures/intelligence/entities.json').length).toBeGreaterThan(0);
      expect(screen.getByText(/Association reflects fund-flow path connection/i)).toBeInTheDocument();
    });
  });

  it('12. Renders unresolved address with clean Not identified classification', async () => {
    vi.spyOn(api, 'investigateWallet').mockResolvedValue(mockEmptyResponse);

    render(<WalletInvestigationPage theme="light" />);
    fireEvent.click(screen.getByRole('button', { name: /Investigate Wallet/i }));

    await waitFor(() => {
      expect(screen.getByTitle('Click to inspect root suspect wallet')).toBeInTheDocument();
    });

    // Inspect unresolved root wallet in mockEmptyResponse
    fireEvent.click(screen.getByTitle('Click to inspect root suspect wallet'));

    await waitFor(() => {
      expect(screen.getByText('Wallet Node Inspector')).toBeInTheDocument();
      expect(screen.getByText('Not identified')).toBeInTheDocument();
      expect(screen.getByText('Not identified as VASP')).toBeInTheDocument();
      expect(screen.getByText('NOT_FOUND')).toBeInTheDocument();
    });
  });
});

