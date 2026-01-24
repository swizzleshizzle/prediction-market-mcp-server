"""Kalshi Real-time Tools - 8 WebSocket subscription tools."""

import json
import logging
from typing import Any, Dict, List, Optional
import mcp.types as types

from .client_utils import set_ws_manager, get_ws_manager
from .tool_utils import tool_handler, validate_ticker

logger = logging.getLogger(__name__)

async def subscribe_orderbook(ticker: str) -> Dict:
    """Subscribe to live orderbook updates for a market via WebSocket."""
    validate_ticker(ticker)
    return await get_ws_manager().subscribe("orderbook", ticker)

async def subscribe_trades(ticker: str) -> Dict:
    """Subscribe to live trade feed for a market."""
    validate_ticker(ticker)
    return await get_ws_manager().subscribe("trades", ticker)

async def subscribe_ticker(ticker: str) -> Dict:
    """Subscribe to live price ticker updates for a market."""
    validate_ticker(ticker)
    return await get_ws_manager().subscribe("ticker", ticker)

async def unsubscribe(channel: str, ticker: Optional[str] = None) -> Dict:
    """Unsubscribe from a WebSocket channel to stop receiving updates."""
    if ticker:
        validate_ticker(ticker)
    return await get_ws_manager().unsubscribe(channel, ticker)

async def get_subscriptions() -> Dict:
    """List all active WebSocket subscriptions."""
    return {"subscriptions": get_ws_manager().get_subscriptions()}

async def get_latest_update(channel: str, ticker: str) -> Dict:
    """Retrieve the most recent data from a subscribed channel."""
    validate_ticker(ticker)
    return {"channel": channel, "ticker": ticker, "data": get_ws_manager().get_latest(channel, ticker)}

async def subscribe_fills() -> Dict:
    """Subscribe to personal fill notifications in real-time."""
    return await get_ws_manager().subscribe("fills", "user")

async def subscribe_orders() -> Dict:
    """Subscribe to personal order status updates in real-time."""
    return await get_ws_manager().subscribe("orders", "user")

def get_tools() -> List[types.Tool]:
    return [
        types.Tool(name="kalshi_subscribe_orderbook", description="Subscribe to live orderbook updates for a market. Receive real-time bid/ask changes and depth updates via WebSocket.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_subscribe_trades", description="Subscribe to live trade feed for a market. Get notified immediately when trades execute with price, size, and side.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_subscribe_ticker", description="Subscribe to live price ticker updates for a market. Receive best bid/ask and last trade price in real-time.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_unsubscribe", description="Unsubscribe from a WebSocket channel (orderbook, trades, ticker) to stop receiving live updates for a market.", inputSchema={"type": "object", "properties": {"channel": {"type": "string"}, "ticker": {"type": "string"}}, "required": ["channel"]}),
        types.Tool(name="kalshi_get_subscriptions", description="List all active WebSocket subscriptions showing which markets and data feeds you're currently monitoring.", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_get_latest_update", description="Retrieve the most recent data update from a subscribed channel without waiting for next WebSocket message.", inputSchema={"type": "object", "properties": {"channel": {"type": "string"}, "ticker": {"type": "string"}}, "required": ["channel", "ticker"]}),
        types.Tool(name="kalshi_subscribe_fills", description="Subscribe to your personal fill notifications. Get real-time alerts when your orders are executed.", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_subscribe_orders", description="Subscribe to your personal order status updates. Receive notifications when orders are placed, canceled, or filled.", inputSchema={"type": "object", "properties": {}, "required": []}),
    ]

@tool_handler
async def handle_tool(name: str, arguments: Dict[str, Any]) -> Dict:
    handlers = {
        "kalshi_subscribe_orderbook": lambda: subscribe_orderbook(**arguments),
        "kalshi_subscribe_trades": lambda: subscribe_trades(**arguments),
        "kalshi_subscribe_ticker": lambda: subscribe_ticker(**arguments),
        "kalshi_unsubscribe": lambda: unsubscribe(**arguments),
        "kalshi_get_subscriptions": lambda: get_subscriptions(),
        "kalshi_get_latest_update": lambda: get_latest_update(**arguments),
        "kalshi_subscribe_fills": lambda: subscribe_fills(),
        "kalshi_subscribe_orders": lambda: subscribe_orders(),
    }
    return await handlers[name]()
