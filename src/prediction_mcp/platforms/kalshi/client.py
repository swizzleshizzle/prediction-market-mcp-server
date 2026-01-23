"""
Kalshi API Client.

Provides async access to Kalshi's Trading API v2.
Handles authentication, rate limiting, and response parsing.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from .auth import KalshiAuth
from .config import KalshiConfig

logger = logging.getLogger(__name__)


class KalshiClient:
    """
    Async client for Kalshi Trading API.

    Supports:
    - Market data (public)
    - Events and series
    - Order management (authenticated)
    - Portfolio queries (authenticated)
    """

    def __init__(self, config: KalshiConfig):
        """
        Initialize Kalshi client.

        Args:
            config: KalshiConfig instance with credentials
        """
        self.config = config
        self.base_url = config.KALSHI_API_URL

        # Initialize auth
        self.auth = KalshiAuth(
            api_key_id=config.KALSHI_API_KEY_ID,
            private_key=config.get_private_key(),
            demo_mode=config.KALSHI_DEMO_MODE,
        )

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated API request.

        Args:
            method: HTTP method
            path: API path (without base URL)
            params: Query parameters
            json: JSON body

        Returns:
            Response JSON
        """
        # Get auth headers
        # IMPORTANT: Kalshi does NOT include body in signature
        content = None
        if json:
            import json as json_lib
            content = json_lib.dumps(json, separators=(',', ':')).encode('utf-8')

        # Signature must use full path including /trade-api/v2 prefix
        # Note: Body is NOT included in Kalshi signature
        full_path = f"/trade-api/v2{path}"
        headers = self.auth.get_auth_headers(method, full_path, "")

        client = await self._get_client()
        response = await client.request(
            method=method,
            url=path,
            params=params,
            content=content,
            headers=headers,
        )

        if response.status_code >= 400:
            logger.error(f"Kalshi API error: {response.status_code} - {response.text}")
            response.raise_for_status()

        return response.json()

    # === Market Data ===

    async def get_markets(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get markets with optional filters.

        Args:
            limit: Maximum number of markets
            cursor: Pagination cursor
            event_ticker: Filter by event
            series_ticker: Filter by series
            status: Filter by status (open, closed, settled)

        Returns:
            List of market dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}

        if cursor:
            params["cursor"] = cursor
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker
        if status:
            params["status"] = status

        result = await self._request("GET", "/markets", params=params)
        return result.get("markets", [])

    async def get_market(self, ticker: str) -> Dict[str, Any]:
        """
        Get single market by ticker.

        Args:
            ticker: Market ticker (e.g., KXBTC-25JAN31-T100000)

        Returns:
            Market dictionary
        """
        result = await self._request("GET", f"/markets/{ticker}")
        return result.get("market", result)

    async def get_orderbook(
        self,
        ticker: str,
        depth: int = 10
    ) -> Dict[str, Any]:
        """
        Get orderbook for a market.

        Args:
            ticker: Market ticker
            depth: Orderbook depth

        Returns:
            Orderbook with yes/no sides
        """
        params = {"depth": depth}
        result = await self._request("GET", f"/markets/{ticker}/orderbook", params=params)
        return result.get("orderbook", result)

    async def get_market_candlesticks(
        self,
        ticker: str,
        period: str = "1h",
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get OHLC candlestick data for a market.

        Args:
            ticker: Market ticker
            period: Candle period (1m, 5m, 1h, 1d)
            start_ts: Start timestamp
            end_ts: End timestamp

        Returns:
            List of candlestick dictionaries
        """
        params: Dict[str, Any] = {"period": period}
        if start_ts:
            params["start_ts"] = start_ts
        if end_ts:
            params["end_ts"] = end_ts

        result = await self._request(
            "GET",
            f"/markets/{ticker}/candlesticks",
            params=params
        )
        return result.get("candlesticks", [])

    async def get_trades(
        self,
        ticker: str,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades for a market.

        Args:
            ticker: Market ticker
            limit: Maximum trades
            cursor: Pagination cursor

        Returns:
            List of trade dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        result = await self._request("GET", f"/markets/{ticker}/trades", params=params)
        return result.get("trades", [])

    # === Events ===

    async def get_events(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
        series_ticker: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get events with optional filters.

        Events are groups of related markets.

        Args:
            limit: Maximum events
            cursor: Pagination cursor
            status: Filter by status
            series_ticker: Filter by series

        Returns:
            List of event dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if status:
            params["status"] = status
        if series_ticker:
            params["series_ticker"] = series_ticker

        result = await self._request("GET", "/events", params=params)
        return result.get("events", [])

    async def get_event(self, event_ticker: str) -> Dict[str, Any]:
        """
        Get single event by ticker.

        Args:
            event_ticker: Event ticker

        Returns:
            Event dictionary
        """
        result = await self._request("GET", f"/events/{event_ticker}")
        return result.get("event", result)

    # === Series ===

    async def get_series(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get market series.

        Series are recurring market templates (e.g., daily BTC price).

        Returns:
            List of series dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        result = await self._request("GET", "/series", params=params)
        return result.get("series", [])

    # === Exchange Info ===

    async def get_exchange_status(self) -> Dict[str, Any]:
        """
        Get exchange status and health.

        Returns:
            Status dictionary
        """
        result = await self._request("GET", "/exchange/status")
        return result

    async def get_exchange_schedule(self) -> Dict[str, Any]:
        """
        Get exchange trading schedule.

        Returns:
            Schedule dictionary with trading hours
        """
        result = await self._request("GET", "/exchange/schedule")
        return result

    # === Authenticated: Orders ===

    async def create_order(
        self,
        ticker: str,
        side: str,
        action: str,
        type: str,
        count: int,
        price: Optional[int] = None,
        expiration_ts: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            ticker: Market ticker
            side: "yes" or "no"
            action: "buy" or "sell"
            type: "limit" or "market"
            count: Number of contracts
            price: Price in cents (1-99 for limit orders)
            expiration_ts: Order expiration timestamp
            client_order_id: Client-provided order ID

        Returns:
            Order dictionary
        """
        body: Dict[str, Any] = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "type": type,
            "count": count,
        }

        if price is not None:
            # Kalshi requires exactly ONE of yes_price or no_price
            if side == "yes":
                body["yes_price"] = price
            else:
                body["no_price"] = price

        if expiration_ts:
            body["expiration_ts"] = expiration_ts
        if client_order_id:
            body["client_order_id"] = client_order_id

        result = await self._request("POST", "/portfolio/orders", json=body)
        return result.get("order", result)

    async def get_orders(
        self,
        ticker: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get user's orders.

        Args:
            ticker: Filter by market ticker
            status: Filter by status (open, closed, etc.)
            limit: Maximum orders

        Returns:
            List of order dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if status:
            params["status"] = status

        result = await self._request("GET", "/portfolio/orders", params=params)
        return result.get("orders", [])

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get a single order by ID.

        Args:
            order_id: Order ID to retrieve

        Returns:
            Order dictionary
        """
        result = await self._request("GET", f"/portfolio/orders/{order_id}")
        return result.get("order", result)

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            Cancellation result
        """
        result = await self._request("DELETE", f"/portfolio/orders/{order_id}")
        return result

    async def batch_cancel_orders(
        self,
        order_ids: Optional[List[str]] = None,
        ticker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel multiple orders.

        Args:
            order_ids: List of order IDs to cancel
            ticker: Cancel all orders for this market

        Returns:
            Batch cancellation result
        """
        body: Dict[str, Any] = {}
        if order_ids:
            body["order_ids"] = order_ids
        if ticker:
            body["ticker"] = ticker

        result = await self._request("DELETE", "/portfolio/orders", json=body)
        return result

    # === Authenticated: Portfolio ===

    async def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance.

        Returns:
            Balance dictionary
        """
        result = await self._request("GET", "/portfolio/balance")
        return result

    async def get_positions(
        self,
        ticker: Optional[str] = None,
        settlement_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get user's positions.

        Args:
            ticker: Filter by market ticker
            settlement_status: Filter by settlement status

        Returns:
            List of position dictionaries
        """
        params: Dict[str, Any] = {}
        if ticker:
            params["ticker"] = ticker
        if settlement_status:
            params["settlement_status"] = settlement_status

        result = await self._request("GET", "/portfolio/positions", params=params)
        return result.get("market_positions", [])

    async def get_fills(
        self,
        ticker: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get user's fills (executed trades).

        Args:
            ticker: Filter by market ticker
            limit: Maximum fills
            cursor: Pagination cursor

        Returns:
            List of fill dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if cursor:
            params["cursor"] = cursor

        result = await self._request("GET", "/portfolio/fills", params=params)
        return result.get("fills", [])

    # === Helpers ===

    def is_authenticated(self) -> bool:
        """Check if client is authenticated for trading."""
        return self.auth.is_authenticated()


def create_kalshi_client(config: KalshiConfig) -> KalshiClient:
    """
    Factory function to create KalshiClient.

    Args:
        config: KalshiConfig instance

    Returns:
        Configured KalshiClient
    """
    return KalshiClient(config)
