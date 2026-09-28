# backend/app/blockchain/providers/bitquery/client.py
import asyncio
import logging
import os
import time
from typing import Dict, Any, Optional
import httpx

from ...exceptions import (
    BlockchainProviderError,
    AuthenticationError,
    RateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderResponseError,
)

logger = logging.getLogger("blockchain.bitquery")

class BitqueryClient:
    """
    Asynchronous GraphQL HTTP Client for Bitquery V2 API.
    Handles Bearer authentication, retries with exponential backoff,
    timeout handling, and provider exception mapping.
    """

    DEFAULT_API_URL = "https://streaming.bitquery.io/graphql"
    DEFAULT_TIMEOUT_SECONDS = 30.0
    DEFAULT_MAX_RETRIES = 5

    def __init__(
        self,
        api_url: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
        http_client: Optional[httpx.AsyncClient] = None
    ):
        self.api_url = (
            api_url
            if api_url is not None
            else (os.getenv("BITQUERY_API_URL") or self.DEFAULT_API_URL)
        ).strip()
        
        self.access_token = (
            access_token
            if access_token is not None
            else os.getenv("BITQUERY_ACCESS_TOKEN", "")
        ).strip()

        env_timeout = os.getenv("BITQUERY_TIMEOUT_SECONDS")
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else (float(env_timeout) if env_timeout else self.DEFAULT_TIMEOUT_SECONDS)
        )

        env_retries = os.getenv("BITQUERY_MAX_RETRIES")
        self.max_retries = (
            max_retries
            if max_retries is not None
            else (int(env_retries) if env_retries else self.DEFAULT_MAX_RETRIES)
        )

        self._external_client = http_client

    def _get_headers(self) -> Dict[str, str]:
        if not self.access_token:
            raise AuthenticationError(
                "Bitquery access token is not configured. Please set BITQUERY_ACCESS_TOKEN."
            )
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Bitquery V2 with automatic retry and error mapping.
        """
        headers = self._get_headers()
        payload = {
            "query": query.strip(),
            "variables": variables or {}
        }

        last_exception: Optional[Exception] = None
        start_time = time.monotonic()

        for attempt in range(1, self.max_retries + 1):
            try:
                if self._external_client:
                    response = await self._external_client.post(
                        self.api_url,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout_seconds
                    )
                else:
                    async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                        response = await client.post(
                            self.api_url,
                            json=payload,
                            headers=headers
                        )

                duration = time.monotonic() - start_time
                logger.debug(
                    "Bitquery query executed in %.2fs (status=%d, attempt=%d)",
                    duration, response.status_code, attempt
                )

                # HTTP Status Code Handling
                if response.status_code in (401, 403):
                    raise AuthenticationError(
                        f"Bitquery authentication failed (HTTP {response.status_code}). Check API credentials."
                    )
                elif response.status_code == 429:
                    if attempt < self.max_retries:
                        backoff = 2.0 * (2 ** (attempt - 1))
                        retry_after_hdr = response.headers.get("Retry-After")
                        if retry_after_hdr:
                            try:
                                backoff = max(float(retry_after_hdr), backoff)
                            except ValueError:
                                pass
                        logger.warning("Bitquery rate limit (429) on attempt %d. Backing off %.1fs", attempt, backoff)
                        await asyncio.sleep(backoff)
                        continue
                    raise RateLimitError("Bitquery rate limit exceeded (HTTP 429).")
                elif response.status_code >= 500:
                    if attempt < self.max_retries:
                        backoff = 0.5 * (2 ** (attempt - 1))
                        logger.warning("Bitquery 5xx error (HTTP %d). Retrying in %.1fs", response.status_code, backoff)
                        await asyncio.sleep(backoff)
                        continue
                    raise ProviderUnavailableError(
                        f"Bitquery service unavailable (HTTP {response.status_code})."
                    )
                elif response.status_code != 200:
                    raise ProviderResponseError(
                        f"Bitquery returned unexpected HTTP status {response.status_code}",
                        details={"status_code": response.status_code, "body": response.text[:500]}
                    )

                # Parse JSON
                try:
                    data = response.json()
                except Exception as json_err:
                    raise ProviderResponseError(
                        f"Bitquery returned invalid JSON response: {json_err}",
                        details={"raw_text": response.text[:500]}
                    )

                # GraphQL Errors[] Check
                if "errors" in data and data["errors"]:
                    errors = data["errors"]
                    first_msg = errors[0].get("message", "Unknown GraphQL error") if isinstance(errors, list) and errors else str(errors)
                    msg_lower = first_msg.lower()

                    if "rate limit" in msg_lower or "quota" in msg_lower or "too many requests" in msg_lower:
                        raise RateLimitError(f"Bitquery GraphQL rate limit: {first_msg}")
                    elif "unauthorized" in msg_lower or "forbidden" in msg_lower or "invalid token" in msg_lower:
                        raise AuthenticationError(f"Bitquery GraphQL authentication error: {first_msg}")
                    else:
                        raise ProviderResponseError(
                            f"Bitquery GraphQL error: {first_msg}",
                            details={"errors": errors}
                        )

                return data

            except httpx.TimeoutException as te:
                last_exception = te
                if attempt < self.max_retries:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    logger.warning("Bitquery timeout on attempt %d. Retrying in %.1fs", attempt, backoff)
                    await asyncio.sleep(backoff)
                    continue
                raise ProviderTimeoutError(
                    f"Bitquery request timed out after {self.timeout_seconds}s across {self.max_retries} attempts."
                ) from te
            except httpx.NetworkError as ne:
                last_exception = ne
                if attempt < self.max_retries:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    logger.warning("Bitquery network error on attempt %d. Retrying in %.1fs", attempt, backoff)
                    await asyncio.sleep(backoff)
                    continue
                raise ProviderUnavailableError(
                    f"Bitquery network connection error: {ne}"
                ) from ne
            except BlockchainProviderError:
                raise
            except Exception as e:
                raise ProviderResponseError(f"Unexpected error communicating with Bitquery: {e}") from e

        if last_exception:
            raise ProviderUnavailableError(f"Failed to execute Bitquery query after {self.max_retries} attempts: {last_exception}")
        raise ProviderUnavailableError("Failed to execute Bitquery query.")
