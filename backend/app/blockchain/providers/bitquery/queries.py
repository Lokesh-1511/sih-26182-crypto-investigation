# backend/app/blockchain/providers/bitquery/queries.py
"""
Bitquery V2 GraphQL EVM (Ethereum Mainnet) query definitions.
Uses Bitquery V2 dataset: realtime and EVM schema for recent/realtime blockchain queries.
"""
from typing import Optional
from ...models.enums import TransferDirection

def build_transactions_query(
    direction: TransferDirection = TransferDirection.ANY,
    has_since: bool = False,
    has_till: bool = False
) -> str:
    """
    Build parameterized GraphQL query for EVM Transactions matching only specified filters.
    Eliminates GraphQL null variable errors from Bitquery V2.
    """
    var_defs = ["$address: String!", "$limit: Int!", "$offset: Int!"]
    time_filters = []
    
    if has_since:
        var_defs.append("$since: DateTime!")
        time_filters.append("since: $since")
    if has_till:
        var_defs.append("$till: DateTime!")
        time_filters.append("till: $till")

    var_str = ", ".join(var_defs)

    if direction == TransferDirection.OUTGOING:
        dir_filter = "Transaction: { From: { is: $address } }"
    elif direction == TransferDirection.INCOMING:
        dir_filter = "Transaction: { To: { is: $address } }"
    else:
        dir_filter = """any: [
          { Transaction: { From: { is: $address } } },
          { Transaction: { To: { is: $address } } }
        ]"""

    where_clauses = [dir_filter]
    if time_filters:
        where_clauses.append(f"Block: {{ Time: {{ {', '.join(time_filters)} }} }}")

    where_str = "\n        ".join(where_clauses)

    return f"""query GetTransactions({var_str}) {{
  EVM(dataset: realtime, network: eth) {{
    Transactions(
      where: {{
        {where_str}
      }}
      orderBy: {{ descending: Block_Number }}
      limit: {{ count: $limit, offset: $offset }}
    ) {{
      Block {{
        Number
        Hash
        Time
      }}
      Transaction {{
        Hash
        From
        To
        Value
        Cost
        Type
        Index
        Gas
        GasPrice
      }}
      Receipt {{
        ContractAddress
        GasUsed
        CumulativeGasUsed
        Status
      }}
      TransactionStatus {{
        Success
        EndError
      }}
      Fee {{
        SenderFee
        Burnt
        EffectiveGasPrice
      }}
    }}
  }}
}}"""


def build_transfers_query(
    direction: TransferDirection = TransferDirection.ANY,
    has_since: bool = False,
    has_till: bool = False,
    has_contract: bool = False
) -> str:
    """
    Build parameterized GraphQL query for EVM Transfers matching only specified filters.
    Eliminates GraphQL null variable errors from Bitquery V2.
    """
    var_defs = ["$address: String!", "$limit: Int!", "$offset: Int!"]
    time_filters = []
    
    if has_since:
        var_defs.append("$since: DateTime!")
        time_filters.append("since: $since")
    if has_till:
        var_defs.append("$till: DateTime!")
        time_filters.append("till: $till")
    if has_contract:
        var_defs.append("$contract: String!")

    var_str = ", ".join(var_defs)

    if direction == TransferDirection.OUTGOING:
        dir_filter = "Transfer: { Sender: { is: $address } }"
    elif direction == TransferDirection.INCOMING:
        dir_filter = "Transfer: { Receiver: { is: $address } }"
    else:
        dir_filter = """any: [
          { Transfer: { Sender: { is: $address } } },
          { Transfer: { Receiver: { is: $address } } }
        ]"""

    where_clauses = [dir_filter]
    if has_contract:
        where_clauses.append("Transfer: { Currency: { SmartContract: { is: $contract } } }")
    if time_filters:
        where_clauses.append(f"Block: {{ Time: {{ {', '.join(time_filters)} }} }}")

    where_str = "\n        ".join(where_clauses)

    return f"""query GetTransfers({var_str}) {{
  EVM(dataset: realtime, network: eth) {{
    Transfers(
      where: {{
        {where_str}
      }}
      orderBy: {{ descending: Block_Number }}
      limit: {{ count: $limit, offset: $offset }}
    ) {{
      Block {{
        Number
        Hash
        Time
      }}
      Transaction {{
        Hash
        Index
        From
        To
        Cost
      }}
      Transfer {{
        Id
        Index
        Sender
        Receiver
        Amount
        Type
        Success
        Data
        Currency {{
          Name
          Symbol
          SmartContract
          Decimals
          Native
          Fungible
          ProtocolName
        }}
      }}
      Log {{
        Index
        Signature {{
          Name
          Parsed
        }}
      }}
    }}
  }}
}}"""


# Query constants (for direct/static reference)
ETHEREUM_TRANSACTIONS_OUTGOING_QUERY = build_transactions_query(TransferDirection.OUTGOING)
ETHEREUM_TRANSACTIONS_INCOMING_QUERY = build_transactions_query(TransferDirection.INCOMING)
ETHEREUM_TRANSACTIONS_ANY_QUERY = build_transactions_query(TransferDirection.ANY)

ETHEREUM_TRANSFERS_OUTGOING_QUERY = build_transfers_query(TransferDirection.OUTGOING)
ETHEREUM_TRANSFERS_INCOMING_QUERY = build_transfers_query(TransferDirection.INCOMING)
ETHEREUM_TRANSFERS_ANY_QUERY = build_transfers_query(TransferDirection.ANY)

# Direct transaction lookup by hash
ETHEREUM_TRANSACTION_BY_HASH_QUERY = """
query GetTransactionByHash($txHash: String!) {
  EVM(dataset: realtime, network: eth) {
    Transactions(
      where: { Transaction: { Hash: { is: $txHash } } }
      limit: { count: 1 }
    ) {
      Block {
        Number
        Hash
        Time
      }
      Transaction {
        Hash
        From
        To
        Value
        Cost
        Type
        Index
        Gas
        GasPrice
      }
      Receipt {
        ContractAddress
        GasUsed
        CumulativeGasUsed
        Status
      }
      TransactionStatus {
        Success
        EndError
      }
      Fee {
        SenderFee
        Burnt
        EffectiveGasPrice
      }
    }
  }
}
"""

# Batch transfer lookup by transaction hashes (eliminates N+1 queries)
ETHEREUM_TRANSFERS_BY_TX_HASHES_QUERY = """
query GetTransfersByTxHashes($txHashes: [String!]!) {
  EVM(dataset: realtime, network: eth) {
    Transfers(
      where: {
        Transaction: { Hash: { in: $txHashes } }
      }
      orderBy: { ascending: Transfer_Index }
    ) {
      Block {
        Number
        Hash
        Time
      }
      Transaction {
        Hash
        Index
      }
      Transfer {
        Id
        Index
        Sender
        Receiver
        Amount
        Type
        Success
        Data
        Currency {
          Name
          Symbol
          SmartContract
          Decimals
          Native
          Fungible
          ProtocolName
        }}
    }
  }
}
"""

# Query block by block number
ETHEREUM_BLOCK_BY_NUMBER_QUERY = """
query GetBlockByNumber($blockNumber: String!) {
  EVM(dataset: realtime, network: eth) {
    Blocks(
      where: { Block: { Number: { eq: $blockNumber } } }
      limit: { count: 1 }
    ) {
      Block {
        Number
        Hash
        Time
        Header {
          Difficulty
          ExtraData
          GasLimit
          GasUsed
          Nonce
        }
      }
    }
  }
}
"""

# Query block by block hash
ETHEREUM_BLOCK_BY_HASH_QUERY = """
query GetBlockByHash($blockHash: String!) {
  EVM(dataset: realtime, network: eth) {
    Blocks(
      where: { Block: { Hash: { is: $blockHash } } }
      limit: { count: 1 }
    ) {
      Block {
        Number
        Hash
        Time
        Header {
          Difficulty
          ExtraData
          GasLimit
          GasUsed
          Nonce
        }
      }
    }
  }
}
"""

# Query token currency metadata by smart contract address
ETHEREUM_ASSET_METADATA_QUERY = """
query GetAssetMetadata($contract: String!) {
  EVM(dataset: realtime, network: eth) {
    Transfers(
      where: { Transfer: { Currency: { SmartContract: { is: $contract } } } }
      limit: { count: 1 }
    ) {
      Transfer {
        Currency {
          Name
          Symbol
          SmartContract
          Decimals
          Native
          Fungible
          ProtocolName
        }
      }
    }
  }
}
"""
