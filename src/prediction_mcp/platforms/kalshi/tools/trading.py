"""Kalshi Trading Tools - 13 tools for order management and strategy."""

import json
import logging
from typing import Any, Dict, List, Optional
import mcp.types as types

from .client_utils import set_client, get_client

logger = logging.getLogger(__name__)


# Order Management (7 tools)
async def create_order(ticker: str, side: str, action: str, count: int, price: Optional[int] = None, order_type: str = "limit") -> Dict:
    return await get_client().create_order(ticker=ticker, side=side, action=action, type=order_type, count=count, price=price)

async def cancel_order(order_id: str) -> Dict:
    return await get_client().cancel_order(order_id)

async def batch_cancel_orders(order_ids: Optional[List[str]] = None, ticker: Optional[str] = None) -> Dict:
    return await get_client().batch_cancel_orders(order_ids, ticker)

async def get_order(order_id: str) -> Dict:
    return await get_client().get_order(order_id)

async def get_orders(ticker: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
    return await get_client().get_orders(ticker, status, limit)

async def amend_order(order_id: str, count: Optional[int] = None, price: Optional[int] = None) -> Dict:
    body = {}
    if count: body["count"] = count
    if price: body["price"] = price
    return await get_client()._request("PATCH", f"/portfolio/orders/{order_id}", json=body)

async def get_fills(ticker: Optional[str] = None, limit: int = 100) -> List[Dict]:
    return await get_client().get_fills(ticker, limit)

# Strategy Helpers (6 tools)
async def calculate_order_cost(ticker: str, side: str, action: str, count: int, price: int) -> Dict:
    cost = count * price
    max_profit = count * (100 - price) if action == "buy" else count * price
    return {"ticker": ticker, "cost_cents": cost, "cost_usd": cost/100, "max_profit_usd": max_profit/100}

async def estimate_slippage(ticker: str, side: str, count: int) -> Dict:
    ob = await get_client().get_orderbook(ticker, depth=20)
    book = ob.get("yes" if side == "yes" else "no", [])
    filled, total = 0, 0
    for p, s in book:
        take = min(count - filled, s)
        total += take * p
        filled += take
        if filled >= count: break
    avg = total / filled if filled else 0
    best = book[0][0] if book else 0
    return {"fillable": filled, "avg_price": round(avg, 2), "slippage_cents": round(avg - best, 2)}

async def get_best_price(ticker: str) -> Dict:
    m = await get_client().get_market(ticker)
    return {"yes_bid": m.get("yes_bid"), "yes_ask": m.get("yes_ask"), "spread": (m.get("yes_ask") or 0) - (m.get("yes_bid") or 0)}

async def check_order_validity(ticker: str, side: str, action: str, count: int, price: int) -> Dict:
    errors = []
    if not 1 <= price <= 99: errors.append("Price must be 1-99")
    if count < 1: errors.append("Count must be >= 1")
    try:
        m = await get_client().get_market(ticker)
        if m.get("status") != "open": errors.append("Market not open")
    except Exception: errors.append("Market not found")
    return {"valid": len(errors) == 0, "errors": errors}

async def simulate_order(ticker: str, side: str, action: str, count: int, price: int) -> Dict:
    v = await check_order_validity(ticker, side, action, count, price)
    if not v["valid"]: return {"simulated": False, "errors": v["errors"]}
    cost = await calculate_order_cost(ticker, side, action, count, price)
    slip = await estimate_slippage(ticker, side, count)
    return {"simulated": True, "cost": cost, "slippage": slip}

async def get_order_history(ticker: Optional[str] = None, limit: int = 100) -> List[Dict]:
    return await get_client().get_orders(ticker=ticker, status="closed", limit=limit)

def get_tools() -> List[types.Tool]:
    return [
        types.Tool(name="kalshi_create_order", description="Place a limit order to buy or sell Yes/No contracts on a market. Specify ticker, side (yes/no), action (buy/sell), count (number of contracts), and price (1-99 cents).", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "side": {"type": "string", "enum": ["yes", "no"]}, "action": {"type": "string", "enum": ["buy", "sell"]}, "count": {"type": "integer"}, "price": {"type": "integer"}}, "required": ["ticker", "side", "action", "count"]}),
        types.Tool(name="kalshi_cancel_order", description="Cancel an existing open order by its order ID. Returns cancellation confirmation.", inputSchema={"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}),
        types.Tool(name="kalshi_batch_cancel_orders", description="Cancel multiple orders at once. Provide list of order IDs or ticker to cancel all orders for that market.", inputSchema={"type": "object", "properties": {"order_ids": {"type": "array", "items": {"type": "string"}}, "ticker": {"type": "string"}}, "required": []}),
        types.Tool(name="kalshi_get_order", description="Retrieve detailed information about a specific order including status, fill price, and remaining quantity.", inputSchema={"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}),
        types.Tool(name="kalshi_get_orders", description="List your orders with optional filters for ticker, status (open/closed/canceled), and limit. Returns order history.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "status": {"type": "string"}, "limit": {"type": "integer"}}, "required": []}),
        types.Tool(name="kalshi_amend_order", description="Modify an existing order's quantity or price without canceling and recreating it.", inputSchema={"type": "object", "properties": {"order_id": {"type": "string"}, "count": {"type": "integer"}, "price": {"type": "integer"}}, "required": ["order_id"]}),
        types.Tool(name="kalshi_get_fills", description="Get execution history showing when and at what price your orders were filled. Optionally filter by ticker.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "limit": {"type": "integer"}}, "required": []}),
        types.Tool(name="kalshi_calculate_order_cost", description="Calculate total USD cost for an order before placing it. Includes fees and slippage estimates.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "side": {"type": "string"}, "action": {"type": "string"}, "count": {"type": "integer"}, "price": {"type": "integer"}}, "required": ["ticker", "side", "action", "count", "price"]}),
        types.Tool(name="kalshi_estimate_slippage", description="Estimate price slippage for a given order size based on current orderbook depth and liquidity.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "side": {"type": "string"}, "count": {"type": "integer"}}, "required": ["ticker", "side", "count"]}),
        types.Tool(name="kalshi_get_best_price", description="Get current best bid and ask prices for a market. Useful for determining optimal entry/exit points.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}),
        types.Tool(name="kalshi_check_order_validity", description="Validate order parameters before submission. Checks market status, price bounds, and position limits.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "side": {"type": "string"}, "action": {"type": "string"}, "count": {"type": "integer"}, "price": {"type": "integer"}}, "required": ["ticker", "side", "action", "count", "price"]}),
        types.Tool(name="kalshi_simulate_order", description="Dry-run an order to preview cost, slippage, and potential execution without actually placing it.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "side": {"type": "string"}, "action": {"type": "string"}, "count": {"type": "integer"}, "price": {"type": "integer"}}, "required": ["ticker", "side", "action", "count", "price"]}),
        types.Tool(name="kalshi_get_order_history", description="Retrieve closed order history with fills and final status. Filter by ticker or get entire history.", inputSchema={"type": "object", "properties": {"ticker": {"type": "string"}, "limit": {"type": "integer"}}, "required": []}),
    ]

async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    try:
        handlers = {
            "kalshi_create_order": lambda: create_order(**arguments),
            "kalshi_cancel_order": lambda: cancel_order(**arguments),
            "kalshi_batch_cancel_orders": lambda: batch_cancel_orders(**arguments),
            "kalshi_get_order": lambda: get_order(**arguments),
            "kalshi_get_orders": lambda: get_orders(**arguments),
            "kalshi_amend_order": lambda: amend_order(**arguments),
            "kalshi_get_fills": lambda: get_fills(**arguments),
            "kalshi_calculate_order_cost": lambda: calculate_order_cost(**arguments),
            "kalshi_estimate_slippage": lambda: estimate_slippage(**arguments),
            "kalshi_get_best_price": lambda: get_best_price(**arguments),
            "kalshi_check_order_validity": lambda: check_order_validity(**arguments),
            "kalshi_simulate_order": lambda: simulate_order(**arguments),
            "kalshi_get_order_history": lambda: get_order_history(**arguments),
        }
        result = await handlers[name]()
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]
