"""Kalshi Real-time Tools - 8 WebSocket subscription tools."""

import json
import logging
from typing import Any, Dict, List, Optional
import mcp.types as types

logger = logging.getLogger(__name__)
_ws_manager = None

def set_ws_manager(manager) -> None:
    global _ws_manager
    _ws_manager = manager

def _get_ws():
    if _ws_manager is None:
        raise RuntimeError("WebSocket manager not initialized")
    return _ws_manager

async def subscribe_orderbook(ticker: str) -> Dict:
    return await _get_ws().subscribe("orderbook", ticker)

async def subscribe_trades(ticker: str) -> Dict:
    return await _get_ws().subscribe("trades", ticker)

async def subscribe_ticker(ticker: str) -> Dict:
    return await _get_ws().subscribe("ticker", ticker)

async def unsubscribe(channel: str, ticker: Optional[str] = None) -> Dict:
    return await _get_ws().unsubscribe(channel, ticker)

async def get_subscriptions() -> Dict:
    return {"subscriptions": _get_ws().get_subscriptions()}

async def get_latest_update(channel: str, ticker: str) -> Dict:
    return {"channel": channel, "ticker": ticker, "data": _get_ws().get_latest(channel, ticker)}

async def subscribe_fills() -> Dict:
    return await _get_ws().subscribe("fills", "user")

async def subscribe_orders() -> Dict:
    return await _get_ws().subscribe("orders", "user")

def get_tools() -> List[types.Tool]:
    return [
        types.Tool(name="kalshi_subscribe_orderbook", description="Subscribe to orderbook", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_subscribe_trades", description="Subscribe to trades", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_subscribe_ticker", description="Subscribe to ticker", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_unsubscribe", description="Unsubscribe", inputSchema={"type": "object", "properties": {"channel": {"type": "string"}, "ticker": {"type": "string"}}, "required": ["channel"]}),
        types.Tool(name="kalshi_get_subscriptions", description="List subscriptions", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_get_latest_update", description="Get latest update", inputSchema={"type": "object", "properties": {"channel": {"type": "string"}, "ticker": {"type": "string"}}, "required": ["channel", "ticker"]}),
        types.Tool(name="kalshi_subscribe_fills", description="Subscribe to fills", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_subscribe_orders", description="Subscribe to orders", inputSchema={"type": "object", "properties": {}, "required": []}),
    ]

async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    try:
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
        result = await handlers[name]()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]
