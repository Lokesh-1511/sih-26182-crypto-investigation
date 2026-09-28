# tests/unit/test_normalization.py
from datetime import datetime
from decimal import Decimal
import pytest
from backend.app.blockchain.models.enums import (
    Chain,
    TransactionStatus,
    TransactionType,
    AssetType,
    TransferType,
)
from backend.app.blockchain.models.transaction import NormalizedTransaction, UTXOInput, UTXOOutput
from backend.app.blockchain.models.transfer import NormalizedTransfer
from backend.app.blockchain.normalization.amount import to_normalized_amount, to_raw_amount
from backend.app.blockchain.normalization.bitcoin import BitcoinNormalizer
from backend.app.blockchain.normalization.evm import EVMNormalizer
from backend.app.blockchain.normalization.tron import TronNormalizer
from backend.app.blockchain.normalization.normalizer import TransactionNormalizer

def test_decimal_amount_handling():
    # Large integer base units
    raw_wei = "1500000000000000000"  # 1.5 ETH
    norm_eth = to_normalized_amount(raw_wei, 18)
    assert norm_eth == Decimal("1.5")
    assert to_raw_amount(norm_eth, 18) == raw_wei

    # Micro units / USDT (6 decimals)
    raw_usdt = "1000000000"  # 1000 USDT
    norm_usdt = to_normalized_amount(raw_usdt, 6)
    assert norm_usdt == Decimal("1000")
    assert to_raw_amount(norm_usdt, 6) == raw_usdt

    # Bitcoin satoshis (8 decimals)
    raw_sats = "145000000"  # 1.45 BTC
    norm_btc = to_normalized_amount(raw_sats, 8)
    assert norm_btc == Decimal("1.45")
    assert to_raw_amount(norm_btc, 8) == raw_sats


def test_normalized_transfer_creation():
    transfer = NormalizedTransfer(
        transfer_id="tx123_0",
        tx_hash="0xabc123",
        chain=Chain.ETHEREUM,
        from_address="0xfrom",
        to_address="0xto",
        asset_type=AssetType.ERC20,
        asset_id="0xcontract",
        asset_symbol="USDT",
        token_contract="0xcontract",
        token_decimals=6,
        raw_amount="5000000000",
        normalized_amount=Decimal("5000.000000"),
        transfer_type=TransferType.TOKEN,
        transfer_index=0,
        timestamp=datetime(2026, 3, 14, 12, 0, 0),
        evidence_ref="tx:0xabc123#log:0"
    )

    assert transfer.tx_hash == "0xabc123"
    assert transfer.tx_id == "0xabc123"  # Compatibility property
    assert transfer.asset_symbol == "USDT"
    assert transfer.asset == "USDT"  # Compatibility property
    assert transfer.normalized_amount == Decimal("5000.000000")
    assert transfer.amount == 5000.0  # Compatibility property
    assert transfer.raw_amount == "5000000000"


def test_normalized_transaction_creation():
    tx = NormalizedTransaction(
        tx_hash="0xdeadbeef",
        chain=Chain.ETHEREUM,
        block_number=19000000,
        timestamp=datetime(2026, 3, 14, 12, 0, 0),
        status=TransactionStatus.CONFIRMED,
        transaction_type=TransactionType.NATIVE_TRANSFER,
        fee=Decimal("0.0021"),
        fee_asset="ETH",
        provider="TEST_PROVIDER"
    )

    assert tx.tx_hash == "0xdeadbeef"
    assert tx.tx_id == "0xdeadbeef"
    assert tx.status == TransactionStatus.CONFIRMED
    assert tx.provider == "TEST_PROVIDER"
    assert tx.fee == Decimal("0.0021")


def test_bitcoin_inputs_outputs_preservation():
    normalizer = BitcoinNormalizer()
    raw_btc_payload = {
        "txid": "9f83c60ca8358c2e1b4f9bcb40f3ed8d104b7632b002c72da816284de117682e",
        "block_height": 834920,
        "block_time": 1773313200,
        "fee": 15000,
        "vin": [
            {
                "txid": "prev_tx_001",
                "vout": 0,
                "prevout": {
                    "scriptpubkey_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                    "value": 200000000
                }
            }
        ],
        "vout": [
            {
                "n": 0,
                "scriptpubkey_address": "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s",
                "value": 145000000
            },
            {
                "n": 1,
                "scriptpubkey_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
                "value": 54985000
            }
        ]
    }

    norm_tx = normalizer.normalize_transaction(raw_btc_payload, provider="BITCOIN_EXPLORER")

    assert norm_tx.tx_hash == "9f83c60ca8358c2e1b4f9bcb40f3ed8d104b7632b002c72da816284de117682e"
    assert norm_tx.chain == Chain.BITCOIN
    assert len(norm_tx.inputs) == 1
    assert norm_tx.inputs[0].address == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    assert norm_tx.inputs[0].normalized_amount == Decimal("2.0")

    assert len(norm_tx.outputs) == 2
    assert norm_tx.outputs[0].address == "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s"
    assert norm_tx.outputs[0].normalized_amount == Decimal("1.45")
    assert norm_tx.outputs[1].normalized_amount == Decimal("0.54985")

    assert len(norm_tx.transfers) == 2
    assert norm_tx.transfers[0].from_address == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    assert norm_tx.transfers[0].to_address == "1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s"
    assert norm_tx.transfers[0].normalized_amount == Decimal("1.45")
    assert norm_tx.fee == Decimal("0.00015")
    assert norm_tx.raw_payload_hash is not None


def test_evm_multiple_transfers_in_one_transaction():
    normalizer = EVMNormalizer(Chain.ETHEREUM)
    raw_evm_payload = {
        "hash": "0xmulti_transfer_tx_hash",
        "blockNumber": 19482010,
        "timestamp": "2026-03-14T08:35:10Z",
        "from": "0xSenderAddress1111111111111111111111111111",
        "to": "0xRouterContract2222222222222222222222222222",
        "value": 0,
        "fee": 0.0035,
        "token_transfers": [
            {
                "from": "0xSenderAddress1111111111111111111111111111",
                "to": "0xRecipientOne3333333333333333333333333333",
                "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "symbol": "USDT",
                "decimals": 6,
                "amount": "1000000000"  # 1000 USDT
            },
            {
                "from": "0xSenderAddress1111111111111111111111111111",
                "to": "0xRecipientTwo4444444444444444444444444444",
                "contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "symbol": "USDC",
                "decimals": 6,
                "amount": "2500000000"  # 2500 USDC
            }
        ]
    }

    norm_tx = normalizer.normalize_transaction(raw_evm_payload, provider="EVM_RPC")

    assert norm_tx.tx_hash == "0xmulti_transfer_tx_hash"
    assert norm_tx.transaction_type == TransactionType.TOKEN_TRANSFER
    assert len(norm_tx.transfers) == 2
    assert norm_tx.transfers[0].asset_symbol == "USDT"
    assert norm_tx.transfers[0].normalized_amount == Decimal("1000")
    assert norm_tx.transfers[1].asset_symbol == "USDC"
    assert norm_tx.transfers[1].normalized_amount == Decimal("2500")


def test_tron_normalization():
    normalizer = TronNormalizer()
    raw_tron_payload = {
        "txID": "0xtron_tx_sample_id",
        "blockNumber": 58920101,
        "raw_data": {"timestamp": 1773576300000},
        "owner_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        "to_address": "TYDzsYUEpvnYmQk4zGP9sWWcTEd3ZiPULj",
        "fee": 1500000,  # 1.5 TRX in Sun
        "trc20_transfers": [
            {
                "from": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                "to": "TYDzsYUEpvnYmQk4zGP9sWWcTEd3ZiPULj",
                "contract_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                "symbol": "USDT",
                "decimals": 6,
                "amount": "50000000000"  # 50,000 USDT
            }
        ]
    }

    norm_tx = normalizer.normalize_transaction(raw_tron_payload, provider="TRONGRID")

    assert norm_tx.tx_hash == "0xtron_tx_sample_id"
    assert norm_tx.chain == Chain.TRON
    assert norm_tx.fee == Decimal("1.5")
    assert len(norm_tx.transfers) == 1
    assert norm_tx.transfers[0].asset_symbol == "USDT"
    assert norm_tx.transfers[0].normalized_amount == Decimal("50000")
