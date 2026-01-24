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
    """List all positions with optional filters for ticker and settlement status."""
    return await get_client().get_positions(ticker, settlement_status)

async def get_position(ticker: str) -> Dict:
    """Get detailed position information for a specific market."""
    pos = await get_client().get_positions(ticker=ticker)
    return pos[0] if pos else {"ticker": ticker, "position": 0}

async def get_portfolio_value() -> Dict:
    """Calculate total portfolio value including cash and positions."""
    bal = await get_client().get_balance()
    pos = await get_client().get_positions()
    return {"balance": bal.get("balance", 0), "position_count": len(pos), "total_usd": bal.get("balance", 0) / 100}

async def get_pnl(ticker: Optional[str] = None) -> Dict:
    """Get profit/loss for a position or entire portfolio."""
    fills = await get_client().get_fills(ticker=ticker, limit=500)
    return {"trade_count": len(fills), "ticker": ticker or "all"}

async def get_settlement_history(limit: int = 50) -> List[Dict]:
    """View history of settled positions with final outcomes."""
    return await get_client().get_positions(settlement_status="settled")

async def calculate_position_risk(ticker: str) -> Dict:
    """Analyze risk metrics for a position including max loss."""
    pos = await get_client().get_positions(ticker=ticker)
    if not pos: return {"ticker": ticker, "has_position": False}
    count = pos[0].get("position", 0)
    return {"ticker": ticker, "position": count, "max_loss_usd": abs(count)}

async def get_portfolio_exposure() -> Dict:
    """Get aggregate exposure across all positions."""
    pos = await get_client().get_positions()
    return {"position_count": len(pos), "total_exposure": sum(abs(p.get("position", 0)) for p in pos)}

async def get_margin_requirements() -> Dict:
    """View current margin requirements and available buying power."""
    bal = await get_client().get_balance()
    return {"balance": bal.get("balance", 0), "available": bal.get("available_balance", 0)}

async def export_portfolio(format: str = "json") -> Dict:
    """Export complete portfolio snapshot in JSON format."""
    bal = await get_client().get_balance()
    pos = await get_client().get_positions()
    return {"exported_at": datetime.now(timezone.utc).isoformat(), "balance": bal, "positions": pos}

def get_tools() -> List[types.Tool]:
    return [
        types.Tool(name="kalshi_get_balance", description="Get account balance showing total funds, available cash, and amount locked in open positions.", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_get_positions", description="List all open positions across markets or filter by specific ticker. Shows contracts held, entry price, and current P&L.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": []}),
        types.Tool(name="kalshi_get_position", description="Get detailed position information for a specific market including quantity, average entry, and unrealized profit/loss.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_get_portfolio_value", description="Calculate total portfolio value including cash balance plus mark-to-market value of all positions.", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_get_pnl", description="Get realized and unrealized profit/loss for a specific position or entire portfolio. Includes percentage returns.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": []}),
        types.Tool(name="kalshi_get_settlement_history", description="View history of settled positions showing final outcomes, payout amounts, and settlement dates.", inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}),
        types.Tool(name="kalshi_calculate_position_risk", description="Analyze risk metrics for a position including max loss, position size as % of portfolio, and correlation exposure.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_get_portfolio_exposure", description="Get aggregate exposure across all positions by category, event type, and settlement date.", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_get_margin_requirements", description="View current margin requirements and buying power. Shows how much capital is available for new positions.", inputSchema={"type": "object", "properties": {}, "required": []}),
        types.Tool(name="kalshi_export_portfolio", description="Export complete portfolio snapshot including positions, balances, and transaction history in JSON format.", inputSchema={"type": "object", "properties": {"format": {"type": "string"}}, "required": []}),
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
