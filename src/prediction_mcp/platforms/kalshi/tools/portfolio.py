"""Kalshi Portfolio Tools - 10 tools for portfolio management."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import mcp.types as types

from .client_utils import set_client, get_client

logger = logging.getLogger(__name__)

async def get_balance() -> Dict:
    return await get_client().get_balance()

async def get_positions(ticker: Optional[str] = None, settlement_status: Optional[str] = None) -> List[Dict]:
    return await get_client().get_positions(ticker, settlement_status)

async def get_position(ticker: str) -> Dict:
    pos = await get_client().get_positions(ticker=ticker)
    return pos[0] if pos else {"ticker": ticker, "position": 0}

async def get_portfolio_value() -> Dict:
    bal = await get_client().get_balance()
    pos = await get_client().get_positions()
    return {"balance": bal.get("balance", 0), "position_count": len(pos), "total_usd": bal.get("balance", 0) / 100}

async def get_pnl(ticker: Optional[str] = None) -> Dict:
    fills = await get_client().get_fills(ticker=ticker, limit=500)
    return {"trade_count": len(fills), "ticker": ticker or "all"}

async def get_settlement_history(limit: int = 50) -> List[Dict]:
    return await get_client().get_positions(settlement_status="settled")

async def calculate_position_risk(ticker: str) -> Dict:
    pos = await get_client().get_positions(ticker=ticker)
    if not pos: return {"ticker": ticker, "has_position": False}
    count = pos[0].get("position", 0)
    return {"ticker": ticker, "position": count, "max_loss_usd": abs(count)}

async def get_portfolio_exposure() -> Dict:
    pos = await get_client().get_positions()
    return {"position_count": len(pos), "total_exposure": sum(abs(p.get("position", 0)) for p in pos)}

async def get_margin_requirements() -> Dict:
    bal = await get_client().get_balance()
    return {"balance": bal.get("balance", 0), "available": bal.get("available_balance", 0)}

async def export_portfolio(format: str = "json") -> Dict:
    bal = await get_client().get_balance()
    pos = await get_client().get_positions()
    return {"exported_at": datetime.now(timezone.utc).isoformat(), "balance": bal, "positions": pos}

def get_tools() -> List[types.Tool]:
    return [
        types.Tool(name="kalshi_get_balance", description="Get balance", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_get_positions", description="Get positions", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": []}),
        types.Tool(name="kalshi_get_position", description="Get single position", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_get_portfolio_value", description="Get portfolio value", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_get_pnl", description="Get PnL", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": []}),
        types.Tool(name="kalshi_get_settlement_history", description="Get settlements", inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}),
        types.Tool(name="kalshi_calculate_position_risk", description="Calculate risk", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_get_portfolio_exposure", description="Get exposure", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_get_margin_requirements", description="Get margin", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_export_portfolio", description="Export portfolio", inputSchema={"type": "object", "properties": {"format": {"type": "string"}}, "required": []}),
    ]

async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    try:
        handlers = {
            "kalshi_get_balance": lambda: get_balance(),
            "kalshi_get_positions": lambda: get_positions(**arguments),
            "kalshi_get_position": lambda: get_position(**arguments),
            "kalshi_get_portfolio_value": lambda: get_portfolio_value(),
            "kalshi_get_pnl": lambda: get_pnl(**arguments),
            "kalshi_get_settlement_history": lambda: get_settlement_history(**arguments),
            "kalshi_calculate_position_risk": lambda: calculate_position_risk(**arguments),
            "kalshi_get_portfolio_exposure": lambda: get_portfolio_exposure(),
            "kalshi_get_margin_requirements": lambda: get_margin_requirements(),
            "kalshi_export_portfolio": lambda: export_portfolio(**arguments),
        }
        result = await handlers[name]()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]
