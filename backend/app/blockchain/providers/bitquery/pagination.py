# backend/app/blockchain/providers/bitquery/pagination.py
import base64
import json
from typing import Optional
from ...exceptions import ProviderResponseError

def encode_cursor(offset: int, kind: str = "transactions") -> str:
    """
    Encode pagination offset and query kind into an opaque URL-safe cursor string.
    Hides vendor-specific offset mechanics from the collector.
    """
    payload = {
        "offset": max(0, int(offset)),
        "kind": kind
    }
    raw_json = json.dumps(payload, separators=(",", ":"))
    return base64.urlsafe_b64encode(raw_json.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: Optional[str] = None, kind: str = "transactions", expected_kind: Optional[str] = None) -> int:
    """
    Safely decode opaque cursor string into an integer offset.
    Rejects tampered, malformed, or mismatched cursor tokens safely.
    """
    if not cursor or not isinstance(cursor, str) or not cursor.strip():
        return 0

    target_kind = expected_kind or kind

    try:
        raw_bytes = base64.urlsafe_b64decode(cursor.strip().encode("ascii"))
        payload = json.loads(raw_bytes.decode("utf-8"))

        if not isinstance(payload, dict):
            raise ValueError("Cursor payload must be a JSON object")

        offset = payload.get("offset", 0)
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Cursor offset must be a non-negative integer")

        return offset
    except Exception as e:
        raise ProviderResponseError(
            f"Invalid or malformed pagination cursor: {cursor}",
            details={"cursor": cursor, "error": str(e)}
        )
