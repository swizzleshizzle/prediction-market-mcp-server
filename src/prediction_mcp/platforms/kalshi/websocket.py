"""
Kalshi WebSocket Manager for real-time market data.

Manages WebSocket connection to:
- wss://api.elections.kalshi.com/trade-api/ws/v2 (production)
- wss://demo-api.kalshi.co/trade-api/ws/v2 (demo)

Supports channels:
- ticker: Real-time price updates
- orderbook_delta: Incremental orderbook changes
- orderbook_snapshot: Full orderbook state
- trades: Trade execution feed
- fills: User fill notifications (authenticated)
- positions: Position updates (authenticated)
- communications: RFQ/quote notifications (authenticated)
- order_group_updates: Order group lifecycle (authenticated)
"""
import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256

import websockets

logger = logging.getLogger(__name__)


class KalshiWebSocketManager:
    """
    Manages WebSocket connection to Kalshi real-time data feed.

    Features:
    - Single WebSocket connection with RSA authentication
    - Multiple channel subscriptions (public and private)
    - Auto-reconnect with exponential backoff
    - Latest data caching for each channel/ticker
    - Message routing and storage
    """

    # Reconnect settings
    INITIAL_RECONNECT_DELAY = 1  # seconds
    MAX_RECONNECT_DELAY = 60  # seconds
    RECONNECT_MULTIPLIER = 2

    def __init__(self, ws_url: str, api_key: str, private_key: str):
        """
        Initialize Kalshi WebSocket manager.

        Args:
            ws_url: WebSocket URL (production or demo)
            api_key: API key ID for authentication
            private_key: RSA private key (PEM format string)
        """
        self.ws_url = ws_url or "wss://api.elections.kalshi.com/trade-api/ws/v2"
        self.api_key = api_key
        self.private_key_str = private_key

        # Load RSA key for signing
        if private_key:
            try:
                self.rsa_key = RSA.import_key(private_key)
            except Exception as e:
                logger.error(f"Failed to load RSA private key: {e}")
                self.rsa_key = None
        else:
            self.rsa_key = None

        # WebSocket connection
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.authenticated = False

        # Subscriptions tracking
        # Format: {(channel, ticker): subscription_id}
        self.subscriptions: Dict[tuple, int] = {}
        self.subscription_counter = 0

        # Latest data cache
        # Format: {(channel, ticker): latest_message}
        self.latest_data: Dict[tuple, Dict[str, Any]] = {}

        # Background task
        self.background_task: Optional[asyncio.Task] = None
        self.should_run = False

        # Reconnect tracking
        self.reconnect_attempts = 0
        self.last_reconnect_time = 0

        # Statistics
        self.total_messages_received = 0
        self.messages_by_channel: Dict[str, int] = defaultdict(int)
        self.connection_errors = 0
        self.reconnect_count = 0

        logger.info(f"KalshiWebSocketManager initialized (URL: {self.ws_url})")

    def _generate_auth_headers(self) -> Dict[str, str]:
        """
        Generate authentication headers for WebSocket connection.

        Returns:
            Dict with KALSHI-ACCESS-KEY, KALSHI-ACCESS-SIGNATURE, KALSHI-ACCESS-TIMESTAMP
        """
        if not self.rsa_key:
            raise RuntimeError("RSA private key not loaded")

        # Get current timestamp in milliseconds
        timestamp = str(int(time.time() * 1000))

        # Create signature message: timestamp + method + path
        # For WebSocket: GET /trade-api/ws/v2
        path = "/trade-api/ws/v2"
        message = timestamp + "GET" + path

        # Sign with RSA-PSS
        h = SHA256.new(message.encode('utf-8'))
        signature = pss.new(self.rsa_key).sign(h)

        # Base64 encode signature
        import base64
        signature_b64 = base64.b64encode(signature).decode('utf-8')

        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature_b64,
            "KALSHI-ACCESS-TIMESTAMP": timestamp
        }

    async def connect(self) -> None:
        """Establish WebSocket connection with authentication."""
        try:
            logger.info(f"Connecting to Kalshi WebSocket: {self.ws_url}")

            # Generate auth headers
            auth_headers = self._generate_auth_headers()

            # Connect with authentication headers
            self.ws = await websockets.connect(
                self.ws_url,
                additional_headers=auth_headers,
                ping_interval=10,  # Kalshi uses 10-second ping
                ping_timeout=10
            )

            self.connected = True
            self.authenticated = True  # Kalshi authenticates on connection
            logger.info("Kalshi WebSocket connected and authenticated")

        except Exception as e:
            logger.error(f"Failed to connect to Kalshi WebSocket: {e}")
            self.connected = False
            self.authenticated = False
            self.connection_errors += 1
            raise

    async def disconnect(self) -> None:
        """Disconnect WebSocket gracefully."""
        logger.info("Disconnecting Kalshi WebSocket...")

        if self.ws and self.ws.close_code is None:
            await self.ws.close()
            logger.info("Kalshi WebSocket disconnected")

        self.connected = False
        self.authenticated = False

    async def reconnect(self) -> None:
        """Reconnect with exponential backoff."""
        self.reconnect_count += 1

        # Calculate backoff delay
        delay = min(
            self.INITIAL_RECONNECT_DELAY * (self.RECONNECT_MULTIPLIER ** self.reconnect_attempts),
            self.MAX_RECONNECT_DELAY
        )

        logger.info(f"Reconnecting in {delay}s (attempt {self.reconnect_attempts + 1})...")
        await asyncio.sleep(delay)

        try:
            # Disconnect existing connection
            await self.disconnect()

            # Reconnect
            await self.connect()

            # Resubscribe to all active subscriptions
            await self._resubscribe_all()

            # Reset reconnect counter on success
            self.reconnect_attempts = 0
            self.last_reconnect_time = time.time()
            logger.info("Reconnection successful")

        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            self.reconnect_attempts += 1

    async def _resubscribe_all(self) -> None:
        """Resubscribe to all active subscriptions after reconnect."""
        logger.info(f"Resubscribing to {len(self.subscriptions)} active subscriptions...")

        subscriptions_copy = list(self.subscriptions.items())
        self.subscriptions.clear()

        for (channel, ticker), _ in subscriptions_copy:
            try:
                await self.subscribe(channel, ticker)
            except Exception as e:
                logger.error(f"Failed to resubscribe to {channel}/{ticker}: {e}")

    async def subscribe(self, channel: str, ticker: str) -> Dict[str, Any]:
        """
        Subscribe to a WebSocket channel.

        Args:
            channel: Channel type (orderbook, trades, ticker, fills, positions, etc.)
            ticker: Market ticker (or "user" for user-specific channels)

        Returns:
            Subscription confirmation
        """
        if not self.connected:
            raise RuntimeError("WebSocket not connected. Call connect() first.")

        # Map our simplified channel names to Kalshi's exact channel names
        # Note: Kalshi docs show inconsistent naming (ticker vs market_ticker, etc.)
        # Using names from working examples in quick start guide
        channel_map = {
            "orderbook": "orderbook_delta",  # From quick start examples
            "ticker": "ticker",  # From quick start examples
            "trades": "trade",  # Kalshi uses "trade" not "trades"
            "fills": "fill",  # Kalshi uses "fill" not "fills"
            "orders": "order",  # Kalshi uses "order" for order updates
            "positions": "market_positions"  # From channel list
        }

        kalshi_channel = channel_map.get(channel, channel)

        # Build subscription message
        self.subscription_counter += 1
        sub_id = self.subscription_counter

        message = {
            "id": sub_id,
            "cmd": "subscribe",
            "params": {
                "channels": [kalshi_channel]
            }
        }

        # For market-specific subscriptions, add market_ticker
        # For user channels (fills, positions, order_group_updates), don't add market_ticker
        # For "all markets" ticker subscription, use empty list for market_tickers
        if ticker == "user":
            # User-specific channel - no market_ticker needed
            pass
        elif ticker == "all":
            # All markets - some channels might support this
            pass
        else:
            # Specific market ticker
            message["params"]["market_ticker"] = ticker

        # Send subscription
        await self.ws.send(json.dumps(message))
        logger.info(f"Subscribed to {kalshi_channel} for {ticker} (id={sub_id})")

        # Track subscription
        self.subscriptions[(channel, ticker)] = sub_id

        return {
            "success": True,
            "channel": channel,
            "ticker": ticker,
            "subscription_id": sub_id
        }

    async def unsubscribe(self, channel: str, ticker: Optional[str] = None) -> Dict[str, Any]:
        """
        Unsubscribe from a channel.

        Args:
            channel: Channel type
            ticker: Market ticker (None to unsubscribe from all tickers for this channel)

        Returns:
            Unsubscription confirmation
        """
        if ticker:
            # Unsubscribe specific channel/ticker
            key = (channel, ticker)
            if key in self.subscriptions:
                sub_id = self.subscriptions[key]

                # Kalshi uses cmd: "unsubscribe" with same params as subscribe
                message = {
                    "id": sub_id,
                    "cmd": "unsubscribe",
                    "params": {
                        "channels": [channel]
                    }
                }

                if ticker != "user":
                    message["params"]["market_ticker"] = ticker

                if self.ws and self.ws.close_code is None:
                    await self.ws.send(json.dumps(message))

                del self.subscriptions[key]
                logger.info(f"Unsubscribed from {channel}/{ticker}")

                return {"success": True, "channel": channel, "ticker": ticker}
            else:
                return {"success": False, "error": "Subscription not found"}
        else:
            # Unsubscribe all tickers for this channel
            keys_to_remove = [k for k in self.subscriptions.keys() if k[0] == channel]
            for key in keys_to_remove:
                await self.unsubscribe(key[0], key[1])

            return {"success": True, "channel": channel, "count": len(keys_to_remove)}

    def get_subscriptions(self) -> List[Dict[str, str]]:
        """Get list of active subscriptions."""
        return [
            {
                "channel": channel,
                "ticker": ticker,
                "subscription_id": str(sub_id)
            }
            for (channel, ticker), sub_id in self.subscriptions.items()
        ]

    def get_latest(self, channel: str, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get latest data from a subscribed channel.

        Args:
            channel: Channel type
            ticker: Market ticker

        Returns:
            Latest message data or None if no data received
        """
        key = (channel, ticker)
        return self.latest_data.get(key)

    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Route incoming WebSocket message.

        Args:
            message: Parsed message data
        """
        try:
            self.total_messages_received += 1

            # Handle different message types
            msg_type = message.get("type")

            if msg_type == "error":
                logger.error(f"WebSocket error: {message.get('msg')}")
                return

            # Kalshi sends channel data in "msg" field
            if "msg" in message:
                msg_data = message["msg"]

                # Determine channel from message
                # Kalshi includes channel info in the message
                if "ticker" in msg_data or "market_ticker" in msg_data:
                    channel = self._infer_channel(msg_data)
                    ticker = msg_data.get("market_ticker", msg_data.get("ticker", "unknown"))

                    # Update latest data cache
                    key = (channel, ticker)
                    self.latest_data[key] = msg_data
                    self.messages_by_channel[channel] += 1

                    logger.debug(f"Received {channel} update for {ticker}")

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    def _infer_channel(self, msg_data: Dict[str, Any]) -> str:
        """Infer channel type from message data."""
        # Kalshi messages may include channel hints
        # Try to use the 'type' or 'channel' field if present
        if "type" in msg_data:
            return msg_data["type"]
        if "channel" in msg_data:
            return msg_data["channel"]

        # Otherwise infer from content
        if "bids" in msg_data and "asks" in msg_data:
            return "orderbook"
        elif "yes_bid" in msg_data and "yes_ask" in msg_data:
            return "ticker"
        elif "trade_id" in msg_data:
            return "trades"
        elif "fill_id" in msg_data:
            return "fills"
        elif "position" in msg_data:
            return "positions"
        else:
            return "unknown"

    async def start_background_task(self) -> None:
        """Start background task to process WebSocket messages."""
        if self.background_task and not self.background_task.done():
            logger.warning("Background task already running")
            return

        self.should_run = True
        self.background_task = asyncio.create_task(self._background_loop())
        logger.info("Background WebSocket task started")

    async def stop_background_task(self) -> None:
        """Stop background task gracefully."""
        logger.info("Stopping background WebSocket task...")
        self.should_run = False

        if self.background_task:
            try:
                await asyncio.wait_for(self.background_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Background task did not stop gracefully, cancelling...")
                self.background_task.cancel()

        await self.disconnect()
        logger.info("Background task stopped")

    async def _background_loop(self) -> None:
        """Main background loop for processing WebSocket messages."""
        logger.info("Background WebSocket loop started")

        while self.should_run:
            try:
                # Ensure connection is active
                if not self.connected:
                    await self.reconnect()
                    continue

                # Receive and process messages
                if self.ws and self.ws.close_code is None:
                    try:
                        message_str = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                        message = json.loads(message_str)
                        await self.handle_message(message)
                    except asyncio.TimeoutError:
                        # No message received, continue
                        pass
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse message: {e}")
                else:
                    await asyncio.sleep(1.0)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting...")
                await self.reconnect()
            except Exception as e:
                logger.error(f"Error in background loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info("Background WebSocket loop stopped")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current WebSocket manager status.

        Returns:
            Dictionary with connection status, subscriptions, and statistics
        """
        return {
            "connection": {
                "connected": self.connected,
                "authenticated": self.authenticated,
                "url": self.ws_url
            },
            "subscriptions": {
                "total": len(self.subscriptions),
                "active": self.get_subscriptions()
            },
            "statistics": {
                "total_messages": self.total_messages_received,
                "messages_by_channel": dict(self.messages_by_channel),
                "connection_errors": self.connection_errors,
                "reconnect_count": self.reconnect_count,
                "last_reconnect": self.last_reconnect_time
            },
            "background_task": {
                "running": self.should_run,
                "task_exists": self.background_task is not None
            }
        }
