"""Kalshi Real-time Tools - 8 WebSocket subscription tools."""

import json
import logging
from typing import Any, Dict, List, Optional
import mcp.types as types

from .client_utils import set_ws_manager, get_ws_manager

logger = logging.getLogger(__name__)

async def subscribe_orderbook(ticker: str) -> Dict:
    return await get_ws_manager().subscribe("orderbook", ticker)

async def subscribe_trades(ticker: str) -> Dict:
    return await get_ws_manager().subscribe("trades", ticker)

async def subscribe_ticker(ticker: str) -> Dict:
    return await get_ws_manager().subscribe("ticker", ticker)

async def unsubscribe(channel: str, ticker: Optional[str] = None) -> Dict:
    return await get_ws_manager().unsubscribe(channel, ticker)

async def get_subscriptions() -> Dict:
    return {"subscriptions": get_ws_manager().get_subscriptions()}

async def get_latest_update(channel: str, ticker: str) -> Dict:
    return {"channel": channel, "ticker": ticker, "data": get_ws_manager().get_latest(channel, ticker)}

async def subscribe_fills() -> Dict:
    return await get_ws_manager().subscribe("fills", "user")

async def subscribe_orders() -> Dict:
    return await get_ws_manager().subscribe("orders", "user")

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
