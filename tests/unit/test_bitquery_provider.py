# tests/unit/test_bitquery_provider.py
from datetime import datetime, timezone
from decimal import Decimal
import json
import pytest
import httpx

from backend.app.blockchain.models.enums import (
    Chain,
    TransferDirection,
    TransactionStatus,
    TransactionType,
    AssetType,
    TransferType,
)
from backend.app.blockchain.models.provider import AddressValidation, ProviderCapabilities
from backend.app.blockchain.models.pagination import TransactionPage, TransferPage
from backend.app.blockchain.models.transaction import NormalizedTransaction
from backend.app.blockchain.models.transfer import NormalizedTransfer
from backend.app.blockchain.models.block import BlockMetadata
from backend.app.blockchain.models.asset import AssetMetadata

from backend.app.blockchain.providers.bitquery.client import BitqueryClient
from backend.app.blockchain.providers.bitquery.provider import BitqueryProvider
from backend.app.blockchain.providers.bitquery.pagination import encode_cursor, decode_cursor
from backend.app.blockchain.providers.bitquery.mapper import BitqueryEVMMapper
from backend.app.blockchain.exceptions import (
    UnsupportedChainError,
    InvalidAddressError,
    AuthenticationError,
    RateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderResponseError,
)

# --- 1. Address Validation Tests ---

@pytest.mark.anyio
async def test_bitquery_validate_address_ethereum():
    provider = BitqueryProvider(access_token="test_mock_token")

    # Valid EIP-55
    res1 = await provider.validate_address(Chain.ETHEREUM, "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed")
    assert isinstance(res1, AddressValidation)
    assert res1.valid is True
    assert res1.checksum_valid is True

    # Valid lowercase (normalized)
    res2 = await provider.validate_address(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")
    assert res2.valid is True
    assert res2.normalized_address.startswith("0x")

    # Invalid address format
    res3 = await provider.validate_address(Chain.ETH, "0xInvalidHexAddress")
    assert res3.valid is False

    # Unsupported chain raises UnsupportedChainError
    with pytest.raises(UnsupportedChainError):
        await provider.validate_address(Chain.BITCOIN, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

    with pytest.raises(UnsupportedChainError):
        await provider.validate_address(Chain.TRON, "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")


# --- 2. Authentication & Client Tests ---

@pytest.mark.anyio
async def test_bitquery_authentication_token_missing():
    # When token is empty and environment variable is unset, should raise AuthenticationError
    provider = BitqueryProvider(access_token="")
    with pytest.raises(AuthenticationError) as exc_info:
        await provider.get_transactions(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")
    assert "BITQUERY_ACCESS_TOKEN" in str(exc_info.value)


@pytest.mark.anyio
async def test_bitquery_auth_header_and_no_leak():
    mock_token = "secret_jwt_token_12345"
    client = BitqueryClient(access_token=mock_token)
    headers = client._get_headers()

    assert headers["Authorization"] == f"Bearer {mock_token}"
    assert headers["Content-Type"] == "application/json"

    # Token must not appear in string representation of the client
    assert mock_token not in repr(client)


# --- 3. Pagination Encoding & Decoding Tests ---

def test_bitquery_pagination_cursor():
    cursor = encode_cursor(100, kind="transactions")
    assert isinstance(cursor, str)
    assert len(cursor) > 0

    decoded_offset = decode_cursor(cursor, expected_kind="transactions")
    assert decoded_offset == 100

    # None or empty cursor returns 0
    assert decode_cursor(None) == 0
    assert decode_cursor("") == 0

    # Tampered / invalid cursor raises ProviderResponseError
    with pytest.raises(ProviderResponseError):
        decode_cursor("not_valid_base64_json!!!")


# --- 4. Mock HTTP Transport Fixture & Handlers ---

def create_mock_transport(handler):
    return httpx.MockTransport(handler)


@pytest.mark.anyio
async def test_bitquery_get_transactions_success():
    sample_tx_hash = "0x9f83c60ca8358c2e1b4f9bcb40f3ed8d104b7632b002c72da816284de117682e"
    
    def handler(request: httpx.Request):
        payload = json.loads(request.content)
        query = payload.get("query", "")

        if "GetTransactions" in query:
            resp_body = {
                "data": {
                    "EVM": {
                        "Transactions": [
                            {
                                "Block": {
                                    "Number": 19482010,
                                    "Hash": "0xblockhash123",
                                    "Time": "2026-03-14T08:35:10Z"
                                },
                                "Transaction": {
                                    "Hash": sample_tx_hash,
                                    "From": "0x71C83e20e8F468a3E282241F8C936f4521487439",
                                    "To": "0x3a9B552f4c91E606132D9eD9D5FaD79f18B57062",
                                    "Value": "12.5",
                                    "Cost": "0.0021",
                                    "Type": "Legacy",
                                    "Index": 0,
                                    "Gas": 21000,
                                    "GasPrice": "100000000000"
                                },
                                "Receipt": {
                                    "ContractAddress": None,
                                    "GasUsed": 21000,
                                    "CumulativeGasUsed": 21000,
                                    "Status": 1
                                },
                                "TransactionStatus": {
                                    "Success": True,
                                    "EndError": None
                                },
                                "Fee": {
                                    "Sender": "0x71C83e20e8F468a3E282241F8C936f4521487439",
                                    "Receiver": "0x0000000000000000000000000000000000000000",
                                    "Burnt": "0",
                                    "EffectiveGasPrice": "100000000000"
                                }
                            }
                        ]
                    }
                }
            }
            return httpx.Response(200, json=resp_body)
        elif "GetTransfersByTxHashes" in query:
            resp_body = {
                "data": {
                    "EVM": {
                        "Transfers": []
                    }
                }
            }
            return httpx.Response(200, json=resp_body)
        
        return httpx.Response(404, json={"errors": [{"message": "Query not matched in mock"}]})

    async with httpx.AsyncClient(transport=create_mock_transport(handler)) as mock_http:
        client = BitqueryClient(access_token="mock_token", http_client=mock_http)
        provider = BitqueryProvider(client=client)

        page = await provider.get_transactions(
            chain=Chain.ETHEREUM,
            address="0x71C83e20e8F468a3E282241F8C936f4521487439",
            direction=TransferDirection.ANY,
            limit=10
        )

        assert isinstance(page, TransactionPage)
        assert len(page.transactions) == 1
        tx = page.transactions[0]
        assert tx.tx_hash == sample_tx_hash
        assert tx.chain == Chain.ETHEREUM
        assert tx.status == TransactionStatus.CONFIRMED
        assert tx.block_number == 19482010
        assert tx.fee == Decimal("0.0021")
        assert tx.provider == "bitquery"
        assert tx.raw_payload_hash is not None
        assert len(tx.inputs) == 0
        assert len(tx.outputs) == 0
        assert len(tx.transfers) == 1
        assert tx.transfers[0].normalized_amount == Decimal("12.5")
        assert tx.transfers[0].asset_symbol == "ETH"


@pytest.mark.anyio
async def test_bitquery_get_transfers_erc20_and_precision():
    sample_tx_hash = "0xerc20txhash001"
    contract_addr = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

    def handler(request: httpx.Request):
        resp_body = {
            "data": {
                "EVM": {
                    "Transfers": [
                        {
                            "Block": {
                                "Number": 19482015,
                                "Hash": "0xblockhash456",
                                "Time": "2026-03-14T08:36:00Z"
                            },
                            "Transaction": {
                                "Hash": sample_tx_hash,
                                "Index": 1,
                                "From": "0x71C83e20e8F468a3E282241F8C936f4521487439",
                                "To": contract_addr,
                                "Cost": "0.0035"
                            },
                            "Transfer": {
                                "Id": "transfer_id_001",
                                "Index": 0,
                                "Sender": "0x71C83e20e8F468a3E282241F8C936f4521487439",
                                "Receiver": "0x3a9B552f4c91E606132D9eD9D5FaD79f18B57062",
                                "Amount": "50000.123456",
                                "Type": "Transfer",
                                "Success": True,
                                "Data": "",
                                "Currency": {
                                    "Name": "Tether USD",
                                    "Symbol": "USDT",
                                    "SmartContract": contract_addr,
                                    "Decimals": 6,
                                    "Native": False,
                                    "Fungible": True,
                                    "ProtocolName": "erc20"
                                }
                            },
                            "Log": {
                                "Index": 12,
                                "Signature": {
                                    "Name": "Transfer",
                                    "Parsed": True
                                }
                            }
                        }
                    ]
                }
            }
        }
        return httpx.Response(200, json=resp_body)

    async with httpx.AsyncClient(transport=create_mock_transport(handler)) as mock_http:
        client = BitqueryClient(access_token="mock_token", http_client=mock_http)
        provider = BitqueryProvider(client=client)

        page = await provider.get_transfers(
            chain=Chain.ETHEREUM,
            address="0x71C83e20e8F468a3E282241F8C936f4521487439",
            direction=TransferDirection.OUTGOING,
            asset_id=f"ethereum:{contract_addr.lower()}"
        )

        assert isinstance(page, TransferPage)
        assert len(page.transfers) == 1
        t = page.transfers[0]
        assert t.tx_hash == sample_tx_hash
        assert t.chain == Chain.ETHEREUM
        assert t.asset_type == AssetType.ERC20
        assert t.asset_id == f"ethereum:{contract_addr.lower()}"
        assert t.asset_symbol == "USDT"
        assert t.token_contract == contract_addr
        assert t.token_decimals == 6
        assert isinstance(t.normalized_amount, Decimal)
        assert t.normalized_amount == Decimal("50000.123456")
        assert t.raw_amount == "50000123456"
        assert t.transfer_id == f"ethereum:{sample_tx_hash}:log_12"
        assert t.evidence_ref == f"bitquery://evm/eth/tx/{sample_tx_hash}#transfer:log_12"


@pytest.mark.anyio
async def test_bitquery_get_transaction_direct():
    sample_tx_hash = "0xsingle_tx_lookup_hash"

    def handler(request: httpx.Request):
        payload = json.loads(request.content)
        query = payload.get("query", "")

        if "GetTransactionByHash" in query:
            resp_body = {
                "data": {
                    "EVM": {
                        "Transactions": [
                            {
                                "Block": {
                                    "Number": 19482020,
                                    "Hash": "0xblockhash789",
                                    "Time": "2026-03-14T08:40:00Z"
                                },
                                "Transaction": {
                                    "Hash": sample_tx_hash,
                                    "From": "0xFromAddress",
                                    "To": "0xToAddress",
                                    "Value": "1.0",
                                    "Cost": "0.0015",
                                    "Type": "EIP-1559",
                                    "Index": 5
                                },
                                "Receipt": {
                                    "ContractAddress": None,
                                    "GasUsed": 21000,
                                    "Status": 1
                                },
                                "TransactionStatus": {
                                    "Success": True
                                },
                                "Fee": {
                                    "EffectiveGasPrice": "50000000000"
                                }
                            }
                        ]
                    }
                }
            }
            return httpx.Response(200, json=resp_body)
        elif "GetTransfersByTxHashes" in query:
            return httpx.Response(200, json={"data": {"EVM": {"Transfers": []}}})

        return httpx.Response(404)

    async with httpx.AsyncClient(transport=create_mock_transport(handler)) as mock_http:
        client = BitqueryClient(access_token="mock_token", http_client=mock_http)
        provider = BitqueryProvider(client=client)

        tx = await provider.get_transaction(Chain.ETHEREUM, sample_tx_hash)
        assert tx is not None
        assert tx.tx_hash == sample_tx_hash
        assert tx.status == TransactionStatus.CONFIRMED

        # Lookup unknown transaction returns None
        def not_found_handler(request: httpx.Request):
            return httpx.Response(200, json={"data": {"EVM": {"Transactions": []}}})

        async with httpx.AsyncClient(transport=create_mock_transport(not_found_handler)) as not_found_http:
            nf_client = BitqueryClient(access_token="mock_token", http_client=not_found_http)
            nf_provider = BitqueryProvider(client=nf_client)
            res_nf = await nf_provider.get_transaction(Chain.ETHEREUM, "0x0000000000000000000000000000000000000000000000000000000000000000")
            assert res_nf is None


@pytest.mark.anyio
async def test_bitquery_get_block_and_asset_metadata():
    def handler(request: httpx.Request):
        payload = json.loads(request.content)
        query = payload.get("query", "")

        if "GetBlockByNumber" in query:
            return httpx.Response(200, json={
                "data": {
                    "EVM": {
                        "Blocks": [
                            {
                                "Block": {
                                    "Number": 19482010,
                                    "Hash": "0xblock19482010hash",
                                    "Time": "2026-03-14T08:35:10Z"
                                }
                            }
                        ]
                    }
                }
            })
        elif "GetAssetMetadata" in query:
            return httpx.Response(200, json={
                "data": {
                    "EVM": {
                        "Transfers": [
                            {
                                "Transfer": {
                                    "Currency": {
                                        "Name": "USD Coin",
                                        "Symbol": "USDC",
                                        "SmartContract": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                                        "Decimals": 6,
                                        "Native": False,
                                        "Fungible": True
                                    }
                                }
                            }
                        ]
                    }
                }
            })

        return httpx.Response(404)

    async with httpx.AsyncClient(transport=create_mock_transport(handler)) as mock_http:
        client = BitqueryClient(access_token="mock_token", http_client=mock_http)
        provider = BitqueryProvider(client=client)

        # Get block
        block = await provider.get_block(Chain.ETHEREUM, block_number=19482010)
        assert block is not None
        assert block.block_number == 19482010
        assert block.block_hash == "0xblock19482010hash"

        # Get ETH native metadata
        eth_meta = await provider.get_asset_metadata(Chain.ETHEREUM, "ETH")
        assert eth_meta is not None
        assert eth_meta.symbol == "ETH"
        assert eth_meta.decimals == 18
        assert eth_meta.asset_type == AssetType.NATIVE

        # Get ERC20 token metadata
        token_meta = await provider.get_asset_metadata(Chain.ETHEREUM, "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
        assert token_meta is not None
        assert token_meta.symbol == "USDC"
        assert token_meta.decimals == 6
        assert token_meta.asset_type == AssetType.ERC20


@pytest.mark.anyio
async def test_bitquery_error_mappings():
    # 401 Unauthorized -> AuthenticationError
    async with httpx.AsyncClient(transport=create_mock_transport(lambda req: httpx.Response(401, text="Unauthorized"))) as http_401:
        client = BitqueryClient(access_token="invalid_token", http_client=http_401, max_retries=1)
        provider = BitqueryProvider(client=client)
        with pytest.raises(AuthenticationError):
            await provider.get_transactions(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")

    # 429 Rate Limit -> RateLimitError
    async with httpx.AsyncClient(transport=create_mock_transport(lambda req: httpx.Response(429, text="Rate Limit Exceeded"))) as http_429:
        client = BitqueryClient(access_token="token", http_client=http_429, max_retries=1)
        provider = BitqueryProvider(client=client)
        with pytest.raises(RateLimitError):
            await provider.get_transactions(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")

    # 500 Server Error -> ProviderUnavailableError
    async with httpx.AsyncClient(transport=create_mock_transport(lambda req: httpx.Response(500, text="Internal Server Error"))) as http_500:
        client = BitqueryClient(access_token="token", http_client=http_500, max_retries=1)
        provider = BitqueryProvider(client=client)
        with pytest.raises(ProviderUnavailableError):
            await provider.get_transactions(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")

    # GraphQL error in body -> ProviderResponseError
    gql_err_body = {"errors": [{"message": "Field 'InvalidField' does not exist on type 'EVM'"}]}
    async with httpx.AsyncClient(transport=create_mock_transport(lambda req: httpx.Response(200, json=gql_err_body))) as http_gql_err:
        client = BitqueryClient(access_token="token", http_client=http_gql_err, max_retries=1)
        provider = BitqueryProvider(client=client)
        with pytest.raises(ProviderResponseError):
            await provider.get_transactions(Chain.ETH, "0xd8da6bf26964af9d7eed9e03e53415d37aa96045")


@pytest.mark.anyio
async def test_bitquery_capabilities():
    provider = BitqueryProvider(access_token="mock_token")
    caps = provider.capabilities()
    assert isinstance(caps, ProviderCapabilities)
    assert caps.chains == [Chain.ETHEREUM]
    assert caps.supports_transactions is True
    assert caps.supports_transfers is True
    assert caps.supports_token_metadata is True
    assert caps.supports_blocks is True
    assert caps.supports_historical_data is False
    assert caps.supports_internal_transfers is True


def test_bitquery_duplicate_transfer_index_regression():
    """
    Regression test: Multiple native/call transfers in the same transaction
    returning Call.Index = 0 / Transfer.Index = 0 must produce unique, deterministic transfer_ids.
    Repeated mapping of the same raw data must be 100% idempotent.
    """
    sample_tx = "0xmulti_call_tx_1234567890abcdef1234567890abcdef1234567890abcdef123456"
    raw_transfers = [
        {
            "Block": {"Number": 19500000, "Hash": "0xb01", "Time": "2026-03-14T09:00:00Z"},
            "Transaction": {"Hash": sample_tx, "Index": 0, "From": "0xFrom1", "To": "0xTo1", "Cost": "0.001"},
            "Transfer": {
                "Id": None,
                "Index": 0,
                "Sender": "0xSender1",
                "Receiver": "0xReceiver1",
                "Amount": "0.5",
                "Type": "call",
                "Success": True,
                "Currency": {"Name": "Ether", "Symbol": "ETH", "SmartContract": "", "Decimals": 18, "Native": True, "Fungible": True}
            },
            "Call": {"Index": 0},
            "Log": None
        },
        {
            "Block": {"Number": 19500000, "Hash": "0xb01", "Time": "2026-03-14T09:00:00Z"},
            "Transaction": {"Hash": sample_tx, "Index": 0, "From": "0xFrom1", "To": "0xTo2", "Cost": "0.001"},
            "Transfer": {
                "Id": None,
                "Index": 0,
                "Sender": "0xSender1",
                "Receiver": "0xReceiver2",
                "Amount": "0.25",
                "Type": "call",
                "Success": True,
                "Currency": {"Name": "Ether", "Symbol": "ETH", "SmartContract": "", "Decimals": 18, "Native": True, "Fungible": True}
            },
            "Call": {"Index": 0},
            "Log": None
        },
        {
            "Block": {"Number": 19500000, "Hash": "0xb01", "Time": "2026-03-14T09:00:00Z"},
            "Transaction": {"Hash": sample_tx, "Index": 0, "From": "0xFrom1", "To": "0xTo3", "Cost": "0.001"},
            "Transfer": {
                "Id": None,
                "Index": 0,
                "Sender": "0xSender1",
                "Receiver": "0xReceiver3",
                "Amount": "0.1",
                "Type": "call",
                "Success": True,
                "Currency": {"Name": "Ether", "Symbol": "ETH", "SmartContract": "", "Decimals": 18, "Native": True, "Fungible": True}
            },
            "Call": {"Index": 0},
            "Log": None
        }
    ]

    mapped1 = BitqueryEVMMapper.map_transfers(raw_transfers)
    assert len(mapped1) == 3

    # All transfer IDs must be distinct and deterministic
    transfer_ids1 = [t.transfer_id for t in mapped1]
    assert len(set(transfer_ids1)) == 3
    assert transfer_ids1[0] == f"ethereum:{sample_tx}:call_0"
    assert transfer_ids1[1] == f"ethereum:{sample_tx}:call_0_1"
    assert transfer_ids1[2] == f"ethereum:{sample_tx}:call_0_2"

    # All amounts must be exact Decimals
    assert mapped1[0].normalized_amount == Decimal("0.5")
    assert mapped1[1].normalized_amount == Decimal("0.25")
    assert mapped1[2].normalized_amount == Decimal("0.1")

    # Call types are classified as INTERNAL while preserving AssetType.NATIVE
    assert mapped1[0].transfer_type == TransferType.INTERNAL
    assert mapped1[0].asset_type == AssetType.NATIVE

    # Idempotence: repeated mapping of identical raw records produces identical IDs
    mapped2 = BitqueryEVMMapper.map_transfers(raw_transfers)
    transfer_ids2 = [t.transfer_id for t in mapped2]
    assert transfer_ids1 == transfer_ids2


def test_bitquery_token_vs_call_transfers_distinguishable():
    """
    Verifies that ERC-20 token transfers and native call transfers within the same
    transaction remain clearly distinguishable in transfer_type, asset_type, and transfer_id.
    """
    sample_tx = "0xcombo_tx_9999999999999999999999999999999999999999999999999999999999999999"
    usdt_contract = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    raw_transfers = [
        # 1. Native internal call transfer
        {
            "Block": {"Number": 19500000, "Hash": "0xb01", "Time": "2026-03-14T09:00:00Z"},
            "Transaction": {"Hash": sample_tx, "Index": 1, "From": "0xSender1", "To": "0xContract", "Cost": "0.002"},
            "Transfer": {
                "Id": None,
                "Index": 0,
                "Sender": "0xContract",
                "Receiver": "0xUserA",
                "Amount": "2.5",
                "Type": "call",
                "Success": True,
                "Currency": {"Name": "Ether", "Symbol": "ETH", "SmartContract": "", "Decimals": 18, "Native": True, "Fungible": True}
            },
            "Call": {"Index": 3},
            "Log": None
        },
        # 2. ERC-20 token transfer log
        {
            "Block": {"Number": 19500000, "Hash": "0xb01", "Time": "2026-03-14T09:00:00Z"},
            "Transaction": {"Hash": sample_tx, "Index": 1, "From": "0xSender1", "To": "0xContract", "Cost": "0.002"},
            "Transfer": {
                "Id": None,
                "Index": 1,
                "Sender": "0xUserA",
                "Receiver": "0xUserB",
                "Amount": "5000",
                "Type": "transfer",
                "Success": True,
                "Currency": {"Name": "Tether USD", "Symbol": "USDT", "SmartContract": usdt_contract, "Decimals": 6, "Native": False, "Fungible": True}
            },
            "Call": None,
            "Log": {"Index": 15}
        }
    ]

    mapped = BitqueryEVMMapper.map_transfers(raw_transfers)
    assert len(mapped) == 2

    # 1. Native internal call
    native_call = mapped[0]
    assert native_call.transfer_type == TransferType.INTERNAL
    assert native_call.asset_type == AssetType.NATIVE
    assert native_call.asset_id == "ETH"
    assert native_call.transfer_id == f"ethereum:{sample_tx}:call_3"

    # 2. ERC-20 token transfer
    token_t = mapped[1]
    assert token_t.transfer_type == TransferType.TOKEN
    assert token_t.asset_type == AssetType.ERC20
    assert token_t.asset_id == f"ethereum:{usdt_contract.lower()}"
    assert token_t.transfer_id == f"ethereum:{sample_tx}:log_15"




@pytest.mark.anyio
async def test_bitquery_collector_to_graph_pipeline():
    from backend.app.blockchain.ingestion.collector import TransactionCollector
    from backend.app.graph.builder import GraphBuilder

    seed_address = "0x71C83e20e8F468a3E282241F8C936f4521487439"
    dest_address = "0x3a9B552f4c91E606132D9eD9D5FaD79f18B57062"
    tx_hash = "0xdeadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678"

    def handler(request: httpx.Request):
        payload = json.loads(request.content)
        query = payload.get("query", "")
        variables = payload.get("variables", {})

        if "GetTransactions" in query:
            if variables.get("address") == seed_address or "0x71c8" in variables.get("address", "").lower():
                return httpx.Response(200, json={
                    "data": {
                        "EVM": {
                            "Transactions": [
                                {
                                    "Block": {"Number": 19000000, "Hash": "0xb01", "Time": "2026-03-14T08:00:00Z"},
                                    "Transaction": {
                                        "Hash": tx_hash,
                                        "Index": 0,
                                        "From": seed_address,
                                        "To": dest_address,
                                        "Value": "100.5",
                                        "Cost": "0.001",
                                        "Type": "Legacy"
                                    },
                                    "Receipt": {"Status": 1},
                                    "TransactionStatus": {"Success": True},
                                    "Fee": {"EffectiveGasPrice": "1000000000"}
                                }
                            ]
                        }
                    }
                })
            else:
                return httpx.Response(200, json={"data": {"EVM": {"Transactions": []}}})
        elif "GetTransfersByTxHashes" in query:
            return httpx.Response(200, json={"data": {"EVM": {"Transfers": []}}})
        elif "GetTransfers" in query:
            return httpx.Response(200, json={"data": {"EVM": {"Transfers": []}}})
        return httpx.Response(200, json={"data": {"EVM": {"Transfers": [], "Transactions": []}}})

    async with httpx.AsyncClient(transport=create_mock_transport(handler)) as mock_http:
        client = BitqueryClient(access_token="mock_token", http_client=mock_http)
        provider = BitqueryProvider(client=client)

        collector = TransactionCollector(provider=provider)
        batch = await collector.collect_case_transactions(
            case_id="case_test_001",
            suspect_wallet=seed_address,
            chain=Chain.ETHEREUM,
            max_hops=1,
            max_transactions=10
        )

        assert len(batch.transactions) == 1
        tx = batch.transactions[0]
        assert tx.tx_hash == tx_hash
        assert len(tx.transfers) == 1
        transfer = tx.transfers[0]
        assert transfer.from_address == seed_address
        assert transfer.to_address == dest_address
        assert transfer.normalized_amount == Decimal("100.5")

        builder = GraphBuilder()
        graph_data = builder.build_from_transfers("case_test_001", seed_address, Chain.ETH, tx.transfers)
        assert graph_data.total_nodes >= 2
        assert graph_data.total_edges == 1
        assert graph_data.edges[0].source == seed_address.lower()
        assert graph_data.edges[0].target == dest_address.lower()
        assert graph_data.edges[0].amount == Decimal("100.5")


