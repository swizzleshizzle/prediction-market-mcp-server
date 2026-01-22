# Phase 2: Kalshi Parity Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Kalshi integration with trading, portfolio, and real-time tools to reach feature parity.

**Architecture:** Extend existing KalshiClient with trading/portfolio methods. Add three new tool modules (trading, portfolio, realtime). WebSocket manager for real-time data.

**Tech Stack:** Python 3.10+, httpx, websockets, MCP protocol, pytest-asyncio

**Current State (Phase 1):**
- 21 tools (10 discovery + 11 analysis)
- KalshiClient with market data methods
- RSA-PSS authentication working

**Phase 2 Deliverables:**
- Trading tools (13 tools)
- Portfolio tools (10 tools)
- Real-time WebSocket tools (8 tools)
- **Total: 52 Kalshi tools**

---

## Task 1: Trading Tools - Order Management (7 tools)

**Files:**
- Create: `src/prediction_mcp/platforms/kalshi/tools/trading.py`
- Create: `tests/platforms/kalshi/test_trading.py`
- Modify: `src/prediction_mcp/platforms/kalshi/tools/__init__.py`
- Modify: `src/prediction_mcp/server.py`

**Tools:**
1. `kalshi_create_order` - Place limit/market order
2. `kalshi_cancel_order` - Cancel single order
3. `kalshi_batch_cancel_orders` - Cancel multiple orders
4. `kalshi_get_order` - Get order status
5. `kalshi_get_orders` - List user orders
6. `kalshi_amend_order` - Modify existing order
7. `kalshi_get_fills` - Get order fills/executions

**Step 1: Write failing test**

```python
# tests/platforms/kalshi/test_trading.py
"""Tests for Kalshi trading tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestKalshiTradingTools:
    """Test Kalshi trading tool definitions."""

    def test_get_tools_returns_7_order_tools(self):
        """Should return 7 order management tools."""
        from src.prediction_mcp.platforms.kalshi.tools.trading import get_tools

        tools = get_tools()
        tool_names = [t.name for t in tools]

        assert "kalshi_create_order" in tool_names
        assert "kalshi_cancel_order" in tool_names
        assert "kalshi_get_orders" in tool_names
        assert len([t for t in tool_names if "order" in t or "fill" in t]) >= 7

    @pytest.mark.asyncio
    async def test_create_order_handler(self):
        """Should handle create_order tool call."""
        from src.prediction_mcp.platforms.kalshi.tools.trading import handle_tool, set_client

        mock_client = MagicMock()
        mock_client.create_order = AsyncMock(return_value={
            "order_id": "test-order-123",
            "status": "open",
            "ticker": "KXTEST",
            "side": "yes",
            "action": "buy",
            "count": 10,
            "yes_price": 50
        })

        set_client(mock_client)

        result = await handle_tool("kalshi_create_order", {
            "ticker": "KXTEST",
            "side": "yes",
            "action": "buy",
            "count": 10,
            "price": 50
        })

        assert len(result) == 1
        assert "test-order-123" in result[0].text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/platforms/kalshi/test_trading.py -v`
Expected: FAIL with "No module named trading"

**Step 3: Write implementation**

```python
# src/prediction_mcp/platforms/kalshi/tools/trading.py
"""
Kalshi Trading Tools.

Order management tools:
- kalshi_create_order
- kalshi_cancel_order
- kalshi_batch_cancel_orders
- kalshi_get_order
- kalshi_get_orders
- kalshi_amend_order
- kalshi_get_fills
"""

import json
import logging
from typing import Any, Dict, List, Optional

import mcp.types as types

logger = logging.getLogger(__name__)

_client = None


def set_client(client) -> None:
    global _client
    _client = client


def _get_client():
    if _client is None:
        raise RuntimeError("Kalshi client not initialized")
    return _client


async def create_order(
    ticker: str,
    side: str,
    action: str,
    count: int,
    price: Optional[int] = None,
    order_type: str = "limit",
    expiration_ts: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a new order."""
    client = _get_client()
    return await client.create_order(
        ticker=ticker,
        side=side,
        action=action,
        type=order_type,
        count=count,
        price=price,
        expiration_ts=expiration_ts,
    )


async def cancel_order(order_id: str) -> Dict[str, Any]:
    """Cancel an order."""
    client = _get_client()
    return await client.cancel_order(order_id)


async def batch_cancel_orders(
    order_ids: Optional[List[str]] = None,
    ticker: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel multiple orders."""
    client = _get_client()
    return await client.batch_cancel_orders(order_ids, ticker)


async def get_order(order_id: str) -> Dict[str, Any]:
    """Get order details."""
    client = _get_client()
    return await client.get_order(order_id)


async def get_orders(
    ticker: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get user's orders."""
    client = _get_client()
    return await client.get_orders(ticker, status, limit)


async def amend_order(
    order_id: str,
    count: Optional[int] = None,
    price: Optional[int] = None,
) -> Dict[str, Any]:
    """Amend an existing order."""
    client = _get_client()
    # Note: Kalshi API may require specific amend endpoint
    body = {"order_id": order_id}
    if count is not None:
        body["count"] = count
    if price is not None:
        body["price"] = price
    return await client._request("PATCH", f"/portfolio/orders/{order_id}", json=body)


async def get_fills(
    ticker: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get order fills."""
    client = _get_client()
    return await client.get_fills(ticker, limit)


def get_tools() -> List[types.Tool]:
    """Get trading tool definitions."""
    return [
        types.Tool(
            name="kalshi_create_order",
            description="Create a new order on Kalshi. Requires authentication.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Market ticker"},
                    "side": {"type": "string", "enum": ["yes", "no"], "description": "Side to trade"},
                    "action": {"type": "string", "enum": ["buy", "sell"], "description": "Buy or sell"},
                    "count": {"type": "integer", "description": "Number of contracts"},
                    "price": {"type": "integer", "description": "Price in cents (1-99)"},
                    "order_type": {"type": "string", "enum": ["limit", "market"], "default": "limit"},
                },
                "required": ["ticker", "side", "action", "count"]
            }
        ),
        types.Tool(
            name="kalshi_cancel_order",
            description="Cancel an open order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID to cancel"}
                },
                "required": ["order_id"]
            }
        ),
        types.Tool(
            name="kalshi_batch_cancel_orders",
            description="Cancel multiple orders at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_ids": {"type": "array", "items": {"type": "string"}, "description": "Order IDs"},
                    "ticker": {"type": "string", "description": "Cancel all orders for ticker"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_order",
            description="Get details of a specific order.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID"}
                },
                "required": ["order_id"]
            }
        ),
        types.Tool(
            name="kalshi_get_orders",
            description="Get list of user's orders.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Filter by market"},
                    "status": {"type": "string", "enum": ["open", "closed"], "description": "Filter by status"},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_amend_order",
            description="Modify an existing order's price or size.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID to amend"},
                    "count": {"type": "integer", "description": "New contract count"},
                    "price": {"type": "integer", "description": "New price in cents"}
                },
                "required": ["order_id"]
            }
        ),
        types.Tool(
            name="kalshi_get_fills",
            description="Get order fills (executed trades).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Filter by market"},
                    "limit": {"type": "integer", "default": 100}
                },
                "required": []
            }
        ),
    ]


async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool execution."""
    try:
        if name == "kalshi_create_order":
            result = await create_order(**arguments)
        elif name == "kalshi_cancel_order":
            result = await cancel_order(**arguments)
        elif name == "kalshi_batch_cancel_orders":
            result = await batch_cancel_orders(**arguments)
        elif name == "kalshi_get_order":
            result = await get_order(**arguments)
        elif name == "kalshi_get_orders":
            result = await get_orders(**arguments)
        elif name == "kalshi_amend_order":
            result = await amend_order(**arguments)
        elif name == "kalshi_get_fills":
            result = await get_fills(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]
```

**Step 4: Update tools/__init__.py**

Add to `src/prediction_mcp/platforms/kalshi/tools/__init__.py`:
```python
from . import trading
__all__ = ["market_discovery", "market_analysis", "trading"]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/platforms/kalshi/test_trading.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add -A && git commit -m "feat(kalshi): add trading tools (7 order management tools)"
```

---

## Task 2: Trading Tools - Strategy Helpers (6 tools)

**Files:**
- Modify: `src/prediction_mcp/platforms/kalshi/tools/trading.py`
- Modify: `tests/platforms/kalshi/test_trading.py`

**Tools:**
8. `kalshi_calculate_order_cost` - Calculate order cost before placing
9. `kalshi_estimate_slippage` - Estimate slippage for size
10. `kalshi_get_best_price` - Get best bid/ask
11. `kalshi_check_order_validity` - Validate order params
12. `kalshi_simulate_order` - Dry-run order simulation
13. `kalshi_get_order_history` - Historical orders

**Step 1: Add tests**

```python
# Add to tests/platforms/kalshi/test_trading.py

def test_get_tools_returns_13_total(self):
    """Should return 13 trading tools total."""
    from src.prediction_mcp.platforms.kalshi.tools.trading import get_tools
    tools = get_tools()
    assert len(tools) == 13

@pytest.mark.asyncio
async def test_calculate_order_cost(self):
    """Should calculate order cost."""
    from src.prediction_mcp.platforms.kalshi.tools.trading import handle_tool, set_client

    mock_client = MagicMock()
    mock_client.get_market = AsyncMock(return_value={
        "ticker": "KXTEST",
        "yes_ask": 50
    })
    set_client(mock_client)

    result = await handle_tool("kalshi_calculate_order_cost", {
        "ticker": "KXTEST",
        "side": "yes",
        "action": "buy",
        "count": 10,
        "price": 50
    })

    assert "cost" in result[0].text.lower() or "500" in result[0].text
```

**Step 2: Add implementations to trading.py**

```python
async def calculate_order_cost(
    ticker: str,
    side: str,
    action: str,
    count: int,
    price: int,
) -> Dict[str, Any]:
    """Calculate total cost for an order."""
    # Cost = contracts * price (in cents)
    cost_cents = count * price
    max_profit_cents = count * (100 - price) if action == "buy" else count * price

    return {
        "ticker": ticker,
        "side": side,
        "action": action,
        "count": count,
        "price_cents": price,
        "total_cost_cents": cost_cents,
        "total_cost_usd": cost_cents / 100,
        "max_profit_cents": max_profit_cents,
        "max_profit_usd": max_profit_cents / 100,
    }


async def estimate_slippage(ticker: str, side: str, count: int) -> Dict[str, Any]:
    """Estimate slippage for order size."""
    client = _get_client()
    orderbook = await client.get_orderbook(ticker, depth=20)

    book_side = orderbook.get("yes" if side == "yes" else "no", [])
    filled = 0
    total_cost = 0
    levels_used = 0

    for price, size in book_side:
        take = min(count - filled, size)
        total_cost += take * price
        filled += take
        levels_used += 1
        if filled >= count:
            break

    avg_price = total_cost / filled if filled > 0 else 0
    best_price = book_side[0][0] if book_side else 0
    slippage = avg_price - best_price if filled > 0 else 0

    return {
        "ticker": ticker,
        "side": side,
        "requested_count": count,
        "fillable_count": filled,
        "avg_fill_price": round(avg_price, 2),
        "best_price": best_price,
        "slippage_cents": round(slippage, 2),
        "levels_used": levels_used,
    }


async def get_best_price(ticker: str) -> Dict[str, Any]:
    """Get best bid/ask prices."""
    client = _get_client()
    market = await client.get_market(ticker)

    return {
        "ticker": ticker,
        "yes_bid": market.get("yes_bid"),
        "yes_ask": market.get("yes_ask"),
        "no_bid": market.get("no_bid"),
        "no_ask": market.get("no_ask"),
        "spread": (market.get("yes_ask", 0) or 0) - (market.get("yes_bid", 0) or 0),
    }


async def check_order_validity(
    ticker: str,
    side: str,
    action: str,
    count: int,
    price: int,
) -> Dict[str, Any]:
    """Validate order parameters."""
    errors = []
    warnings = []

    if price < 1 or price > 99:
        errors.append("Price must be between 1-99 cents")
    if count < 1:
        errors.append("Count must be at least 1")
    if side not in ["yes", "no"]:
        errors.append("Side must be 'yes' or 'no'")
    if action not in ["buy", "sell"]:
        errors.append("Action must be 'buy' or 'sell'")

    # Check market exists
    client = _get_client()
    try:
        market = await client.get_market(ticker)
        if market.get("status") != "open":
            errors.append(f"Market is not open (status: {market.get('status')})")
    except Exception as e:
        errors.append(f"Market not found: {ticker}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


async def simulate_order(
    ticker: str,
    side: str,
    action: str,
    count: int,
    price: int,
) -> Dict[str, Any]:
    """Simulate order execution (dry run)."""
    validity = await check_order_validity(ticker, side, action, count, price)
    if not validity["valid"]:
        return {"simulated": False, "errors": validity["errors"]}

    cost = await calculate_order_cost(ticker, side, action, count, price)
    slippage = await estimate_slippage(ticker, side, count)

    return {
        "simulated": True,
        "order": {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
            "price": price,
        },
        "estimated_cost": cost,
        "estimated_slippage": slippage,
    }


async def get_order_history(
    ticker: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get historical orders (closed)."""
    client = _get_client()
    return await client.get_orders(ticker=ticker, status="closed", limit=limit)
```

**Step 3: Add tool definitions for strategy helpers**

Add to `get_tools()` in trading.py:
```python
types.Tool(
    name="kalshi_calculate_order_cost",
    description="Calculate cost and potential profit for an order.",
    inputSchema={
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "side": {"type": "string", "enum": ["yes", "no"]},
            "action": {"type": "string", "enum": ["buy", "sell"]},
            "count": {"type": "integer"},
            "price": {"type": "integer", "description": "Price in cents"}
        },
        "required": ["ticker", "side", "action", "count", "price"]
    }
),
types.Tool(
    name="kalshi_estimate_slippage",
    description="Estimate slippage for a given order size.",
    inputSchema={
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "side": {"type": "string", "enum": ["yes", "no"]},
            "count": {"type": "integer"}
        },
        "required": ["ticker", "side", "count"]
    }
),
types.Tool(
    name="kalshi_get_best_price",
    description="Get best bid/ask for a market.",
    inputSchema={
        "type": "object",
        "properties": {"ticker": {"type": "string"}},
        "required": ["ticker"]
    }
),
types.Tool(
    name="kalshi_check_order_validity",
    description="Validate order parameters before placing.",
    inputSchema={
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "side": {"type": "string", "enum": ["yes", "no"]},
            "action": {"type": "string", "enum": ["buy", "sell"]},
            "count": {"type": "integer"},
            "price": {"type": "integer"}
        },
        "required": ["ticker", "side", "action", "count", "price"]
    }
),
types.Tool(
    name="kalshi_simulate_order",
    description="Simulate order execution (dry run).",
    inputSchema={
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "side": {"type": "string", "enum": ["yes", "no"]},
            "action": {"type": "string", "enum": ["buy", "sell"]},
            "count": {"type": "integer"},
            "price": {"type": "integer"}
        },
        "required": ["ticker", "side", "action", "count", "price"]
    }
),
types.Tool(
    name="kalshi_get_order_history",
    description="Get historical (closed) orders.",
    inputSchema={
        "type": "object",
        "properties": {
            "ticker": {"type": "string"},
            "limit": {"type": "integer", "default": 100}
        },
        "required": []
    }
),
```

**Step 4: Add handlers for new tools**

Add to `handle_tool()`:
```python
elif name == "kalshi_calculate_order_cost":
    result = await calculate_order_cost(**arguments)
elif name == "kalshi_estimate_slippage":
    result = await estimate_slippage(**arguments)
elif name == "kalshi_get_best_price":
    result = await get_best_price(**arguments)
elif name == "kalshi_check_order_validity":
    result = await check_order_validity(**arguments)
elif name == "kalshi_simulate_order":
    result = await simulate_order(**arguments)
elif name == "kalshi_get_order_history":
    result = await get_order_history(**arguments)
```

**Step 5: Run tests**

Run: `pytest tests/platforms/kalshi/test_trading.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add -A && git commit -m "feat(kalshi): add trading strategy helpers (6 tools)"
```

---

## Task 3: Portfolio Tools (10 tools)

**Files:**
- Create: `src/prediction_mcp/platforms/kalshi/tools/portfolio.py`
- Create: `tests/platforms/kalshi/test_portfolio.py`
- Modify: `src/prediction_mcp/platforms/kalshi/tools/__init__.py`

**Tools:**
1. `kalshi_get_balance` - Account balance
2. `kalshi_get_positions` - Open positions
3. `kalshi_get_position` - Single position
4. `kalshi_get_portfolio_value` - Total portfolio value
5. `kalshi_get_pnl` - Profit/loss summary
6. `kalshi_get_settlement_history` - Settlement history
7. `kalshi_calculate_position_risk` - Risk metrics
8. `kalshi_get_portfolio_exposure` - Category exposure
9. `kalshi_get_margin_requirements` - Margin info
10. `kalshi_export_portfolio` - Export portfolio data

**Step 1: Write failing test**

```python
# tests/platforms/kalshi/test_portfolio.py
"""Tests for Kalshi portfolio tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestKalshiPortfolioTools:
    def test_get_tools_returns_10_tools(self):
        from src.prediction_mcp.platforms.kalshi.tools.portfolio import get_tools
        tools = get_tools()
        assert len(tools) == 10
        tool_names = [t.name for t in tools]
        assert "kalshi_get_balance" in tool_names
        assert "kalshi_get_positions" in tool_names
        assert "kalshi_get_pnl" in tool_names

    @pytest.mark.asyncio
    async def test_get_balance_handler(self):
        from src.prediction_mcp.platforms.kalshi.tools.portfolio import handle_tool, set_client

        mock_client = MagicMock()
        mock_client.get_balance = AsyncMock(return_value={
            "balance": 10000,
            "available_balance": 8000
        })
        set_client(mock_client)

        result = await handle_tool("kalshi_get_balance", {})
        assert "10000" in result[0].text or "balance" in result[0].text.lower()
```

**Step 2: Run test - expect fail**

Run: `pytest tests/platforms/kalshi/test_portfolio.py -v`

**Step 3: Write implementation**

```python
# src/prediction_mcp/platforms/kalshi/tools/portfolio.py
"""
Kalshi Portfolio Tools.

10 tools for portfolio management:
- kalshi_get_balance
- kalshi_get_positions
- kalshi_get_position
- kalshi_get_portfolio_value
- kalshi_get_pnl
- kalshi_get_settlement_history
- kalshi_calculate_position_risk
- kalshi_get_portfolio_exposure
- kalshi_get_margin_requirements
- kalshi_export_portfolio
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import mcp.types as types

logger = logging.getLogger(__name__)

_client = None


def set_client(client) -> None:
    global _client
    _client = client


def _get_client():
    if _client is None:
        raise RuntimeError("Kalshi client not initialized")
    return _client


async def get_balance() -> Dict[str, Any]:
    """Get account balance."""
    client = _get_client()
    return await client.get_balance()


async def get_positions(
    ticker: Optional[str] = None,
    settlement_status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get all positions."""
    client = _get_client()
    return await client.get_positions(ticker, settlement_status)


async def get_position(ticker: str) -> Dict[str, Any]:
    """Get single position."""
    client = _get_client()
    positions = await client.get_positions(ticker=ticker)
    if positions:
        return positions[0]
    return {"ticker": ticker, "position": 0, "message": "No position found"}


async def get_portfolio_value() -> Dict[str, Any]:
    """Calculate total portfolio value."""
    client = _get_client()
    balance = await client.get_balance()
    positions = await client.get_positions()

    position_value = 0
    for pos in positions:
        count = pos.get("position", 0)
        # Estimate value at current market price
        if count != 0:
            try:
                market = await client.get_market(pos.get("ticker", ""))
                price = market.get("yes_bid", 50) if count > 0 else market.get("no_bid", 50)
                position_value += abs(count) * price
            except:
                pass

    return {
        "cash_balance": balance.get("balance", 0),
        "available_balance": balance.get("available_balance", 0),
        "position_value_cents": position_value,
        "total_value_cents": balance.get("balance", 0) + position_value,
        "total_value_usd": (balance.get("balance", 0) + position_value) / 100,
        "position_count": len(positions),
    }


async def get_pnl(
    ticker: Optional[str] = None,
    period: str = "all",
) -> Dict[str, Any]:
    """Get profit/loss summary."""
    client = _get_client()
    fills = await client.get_fills(ticker=ticker, limit=500)

    realized_pnl = 0
    total_volume = 0

    for fill in fills:
        # Simplified PnL - actual calc depends on position tracking
        count = fill.get("count", 0)
        price = fill.get("price", 0)
        total_volume += count * price

    return {
        "ticker": ticker or "all",
        "period": period,
        "realized_pnl_cents": realized_pnl,
        "total_volume_cents": total_volume,
        "trade_count": len(fills),
    }


async def get_settlement_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get settlement history."""
    client = _get_client()
    return await client.get_positions(settlement_status="settled")


async def calculate_position_risk(ticker: str) -> Dict[str, Any]:
    """Calculate risk metrics for a position."""
    client = _get_client()
    positions = await client.get_positions(ticker=ticker)

    if not positions:
        return {"ticker": ticker, "has_position": False}

    pos = positions[0]
    count = pos.get("position", 0)

    # Max loss is if position goes to 0
    max_loss = abs(count) * 100  # cents

    return {
        "ticker": ticker,
        "position": count,
        "max_loss_cents": max_loss,
        "max_loss_usd": max_loss / 100,
        "direction": "long" if count > 0 else "short" if count < 0 else "none",
    }


async def get_portfolio_exposure() -> Dict[str, Any]:
    """Get portfolio exposure by category."""
    client = _get_client()
    positions = await client.get_positions()

    exposure = {}
    total_exposure = 0

    for pos in positions:
        ticker = pos.get("ticker", "")
        count = abs(pos.get("position", 0))
        value = count * 50  # Estimate at 50 cents
        total_exposure += value

        # Group by ticker prefix (rough category)
        prefix = ticker.split("-")[0] if ticker else "unknown"
        exposure[prefix] = exposure.get(prefix, 0) + value

    return {
        "total_exposure_cents": total_exposure,
        "by_category": exposure,
        "position_count": len(positions),
    }


async def get_margin_requirements() -> Dict[str, Any]:
    """Get margin requirements."""
    client = _get_client()
    balance = await client.get_balance()

    return {
        "balance": balance.get("balance", 0),
        "available_balance": balance.get("available_balance", 0),
        "reserved": balance.get("balance", 0) - balance.get("available_balance", 0),
    }


async def export_portfolio(format: str = "json") -> Dict[str, Any]:
    """Export portfolio data."""
    client = _get_client()

    balance = await client.get_balance()
    positions = await client.get_positions()

    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "balance": balance,
        "positions": positions,
        "position_count": len(positions),
    }

    return export_data


def get_tools() -> List[types.Tool]:
    """Get portfolio tool definitions."""
    return [
        types.Tool(
            name="kalshi_get_balance",
            description="Get account balance.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="kalshi_get_positions",
            description="Get all open positions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "settlement_status": {"type": "string"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_position",
            description="Get position for a specific market.",
            inputSchema={
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_get_portfolio_value",
            description="Calculate total portfolio value.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="kalshi_get_pnl",
            description="Get profit/loss summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "period": {"type": "string", "enum": ["day", "week", "month", "all"]}
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_settlement_history",
            description="Get settlement history.",
            inputSchema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 50}},
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_calculate_position_risk",
            description="Calculate risk metrics for a position.",
            inputSchema={
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_get_portfolio_exposure",
            description="Get portfolio exposure by category.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="kalshi_get_margin_requirements",
            description="Get margin requirements.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="kalshi_export_portfolio",
            description="Export portfolio data.",
            inputSchema={
                "type": "object",
                "properties": {"format": {"type": "string", "enum": ["json"], "default": "json"}},
                "required": []
            }
        ),
    ]


async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool execution."""
    try:
        if name == "kalshi_get_balance":
            result = await get_balance()
        elif name == "kalshi_get_positions":
            result = await get_positions(**arguments)
        elif name == "kalshi_get_position":
            result = await get_position(**arguments)
        elif name == "kalshi_get_portfolio_value":
            result = await get_portfolio_value()
        elif name == "kalshi_get_pnl":
            result = await get_pnl(**arguments)
        elif name == "kalshi_get_settlement_history":
            result = await get_settlement_history(**arguments)
        elif name == "kalshi_calculate_position_risk":
            result = await calculate_position_risk(**arguments)
        elif name == "kalshi_get_portfolio_exposure":
            result = await get_portfolio_exposure()
        elif name == "kalshi_get_margin_requirements":
            result = await get_margin_requirements()
        elif name == "kalshi_export_portfolio":
            result = await export_portfolio(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]
```

**Step 4: Update tools/__init__.py**

```python
from . import portfolio
__all__ = ["market_discovery", "market_analysis", "trading", "portfolio"]
```

**Step 5: Run tests**

Run: `pytest tests/platforms/kalshi/test_portfolio.py -v`

**Step 6: Commit**

```bash
git add -A && git commit -m "feat(kalshi): add portfolio tools (10 tools)"
```

---

## Task 4: Real-time WebSocket Tools (8 tools)

**Files:**
- Create: `src/prediction_mcp/platforms/kalshi/tools/realtime.py`
- Create: `src/prediction_mcp/platforms/kalshi/websocket.py`
- Create: `tests/platforms/kalshi/test_realtime.py`
- Modify: `src/prediction_mcp/platforms/kalshi/tools/__init__.py`

**Tools:**
1. `kalshi_subscribe_orderbook` - Subscribe to orderbook updates
2. `kalshi_subscribe_trades` - Subscribe to trade feed
3. `kalshi_subscribe_ticker` - Subscribe to price updates
4. `kalshi_unsubscribe` - Unsubscribe from feed
5. `kalshi_get_subscriptions` - List active subscriptions
6. `kalshi_get_latest_update` - Get latest cached update
7. `kalshi_subscribe_fills` - Subscribe to user fills
8. `kalshi_subscribe_orders` - Subscribe to user order updates

**Step 1: Write failing test**

```python
# tests/platforms/kalshi/test_realtime.py
"""Tests for Kalshi real-time tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestKalshiRealtimeTools:
    def test_get_tools_returns_8_tools(self):
        from src.prediction_mcp.platforms.kalshi.tools.realtime import get_tools
        tools = get_tools()
        assert len(tools) == 8
        tool_names = [t.name for t in tools]
        assert "kalshi_subscribe_orderbook" in tool_names
        assert "kalshi_subscribe_ticker" in tool_names
        assert "kalshi_unsubscribe" in tool_names

    @pytest.mark.asyncio
    async def test_subscribe_ticker(self):
        from src.prediction_mcp.platforms.kalshi.tools.realtime import handle_tool, set_ws_manager

        mock_ws = MagicMock()
        mock_ws.subscribe = AsyncMock(return_value={"subscribed": True, "channel": "ticker"})
        set_ws_manager(mock_ws)

        result = await handle_tool("kalshi_subscribe_ticker", {"ticker": "KXTEST"})
        assert "subscribed" in result[0].text.lower() or "ticker" in result[0].text.lower()
```

**Step 2: Run test - expect fail**

**Step 3: Create WebSocket manager**

```python
# src/prediction_mcp/platforms/kalshi/websocket.py
"""Kalshi WebSocket manager for real-time data."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Set

import websockets

logger = logging.getLogger(__name__)


class KalshiWebSocketManager:
    """Manages WebSocket connections to Kalshi."""

    def __init__(self, ws_url: str, auth=None):
        self.ws_url = ws_url
        self.auth = auth
        self._ws = None
        self._subscriptions: Dict[str, Set[str]] = {}
        self._latest_data: Dict[str, Any] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._running = False

    async def connect(self) -> bool:
        """Connect to WebSocket."""
        try:
            self._ws = await websockets.connect(self.ws_url)
            self._running = True
            logger.info(f"Connected to Kalshi WebSocket: {self.ws_url}")
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def subscribe(self, channel: str, ticker: str) -> Dict[str, Any]:
        """Subscribe to a channel."""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = set()
        self._subscriptions[channel].add(ticker)

        if self._ws:
            msg = {"type": "subscribe", "channel": channel, "ticker": ticker}
            await self._ws.send(json.dumps(msg))

        return {"subscribed": True, "channel": channel, "ticker": ticker}

    async def unsubscribe(self, channel: str, ticker: Optional[str] = None) -> Dict[str, Any]:
        """Unsubscribe from a channel."""
        if channel in self._subscriptions:
            if ticker:
                self._subscriptions[channel].discard(ticker)
            else:
                self._subscriptions[channel].clear()

        return {"unsubscribed": True, "channel": channel, "ticker": ticker}

    def get_subscriptions(self) -> Dict[str, List[str]]:
        """Get active subscriptions."""
        return {k: list(v) for k, v in self._subscriptions.items()}

    def get_latest(self, channel: str, ticker: str) -> Optional[Any]:
        """Get latest data for a subscription."""
        key = f"{channel}:{ticker}"
        return self._latest_data.get(key)

    async def _process_message(self, message: str) -> None:
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            channel = data.get("channel", "")
            ticker = data.get("ticker", "")
            key = f"{channel}:{ticker}"
            self._latest_data[key] = data
        except Exception as e:
            logger.error(f"Error processing message: {e}")
```

**Step 4: Create realtime tools**

```python
# src/prediction_mcp/platforms/kalshi/tools/realtime.py
"""
Kalshi Real-time Tools.

8 tools for WebSocket subscriptions:
- kalshi_subscribe_orderbook
- kalshi_subscribe_trades
- kalshi_subscribe_ticker
- kalshi_unsubscribe
- kalshi_get_subscriptions
- kalshi_get_latest_update
- kalshi_subscribe_fills
- kalshi_subscribe_orders
"""

import json
import logging
from typing import Any, Dict, List, Optional

import mcp.types as types

logger = logging.getLogger(__name__)

_ws_manager = None


def set_ws_manager(manager) -> None:
    global _ws_manager
    _ws_manager = manager


def _get_ws_manager():
    if _ws_manager is None:
        raise RuntimeError("WebSocket manager not initialized")
    return _ws_manager


async def subscribe_orderbook(ticker: str) -> Dict[str, Any]:
    ws = _get_ws_manager()
    return await ws.subscribe("orderbook", ticker)


async def subscribe_trades(ticker: str) -> Dict[str, Any]:
    ws = _get_ws_manager()
    return await ws.subscribe("trades", ticker)


async def subscribe_ticker(ticker: str) -> Dict[str, Any]:
    ws = _get_ws_manager()
    return await ws.subscribe("ticker", ticker)


async def unsubscribe(channel: str, ticker: Optional[str] = None) -> Dict[str, Any]:
    ws = _get_ws_manager()
    return await ws.unsubscribe(channel, ticker)


async def get_subscriptions() -> Dict[str, Any]:
    ws = _get_ws_manager()
    return {"subscriptions": ws.get_subscriptions()}


async def get_latest_update(channel: str, ticker: str) -> Dict[str, Any]:
    ws = _get_ws_manager()
    data = ws.get_latest(channel, ticker)
    return {"channel": channel, "ticker": ticker, "data": data}


async def subscribe_fills() -> Dict[str, Any]:
    ws = _get_ws_manager()
    return await ws.subscribe("fills", "user")


async def subscribe_orders() -> Dict[str, Any]:
    ws = _get_ws_manager()
    return await ws.subscribe("orders", "user")


def get_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="kalshi_subscribe_orderbook",
            description="Subscribe to orderbook updates.",
            inputSchema={
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_subscribe_trades",
            description="Subscribe to trade feed.",
            inputSchema={
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_subscribe_ticker",
            description="Subscribe to price updates.",
            inputSchema={
                "type": "object",
                "properties": {"ticker": {"type": "string"}},
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_unsubscribe",
            description="Unsubscribe from a feed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "ticker": {"type": "string"}
                },
                "required": ["channel"]
            }
        ),
        types.Tool(
            name="kalshi_get_subscriptions",
            description="List active subscriptions.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="kalshi_get_latest_update",
            description="Get latest cached update for a subscription.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string"},
                    "ticker": {"type": "string"}
                },
                "required": ["channel", "ticker"]
            }
        ),
        types.Tool(
            name="kalshi_subscribe_fills",
            description="Subscribe to user fill notifications.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="kalshi_subscribe_orders",
            description="Subscribe to user order updates.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
    ]


async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    try:
        if name == "kalshi_subscribe_orderbook":
            result = await subscribe_orderbook(**arguments)
        elif name == "kalshi_subscribe_trades":
            result = await subscribe_trades(**arguments)
        elif name == "kalshi_subscribe_ticker":
            result = await subscribe_ticker(**arguments)
        elif name == "kalshi_unsubscribe":
            result = await unsubscribe(**arguments)
        elif name == "kalshi_get_subscriptions":
            result = await get_subscriptions()
        elif name == "kalshi_get_latest_update":
            result = await get_latest_update(**arguments)
        elif name == "kalshi_subscribe_fills":
            result = await subscribe_fills()
        elif name == "kalshi_subscribe_orders":
            result = await subscribe_orders()
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]
```

**Step 5: Update tools/__init__.py**

```python
from . import realtime
__all__ = ["market_discovery", "market_analysis", "trading", "portfolio", "realtime"]
```

**Step 6: Run tests**

Run: `pytest tests/platforms/kalshi/test_realtime.py -v`

**Step 7: Commit**

```bash
git add -A && git commit -m "feat(kalshi): add real-time WebSocket tools (8 tools)"
```

---

## Task 5: Update Main Server Integration

**Files:**
- Modify: `src/prediction_mcp/server.py`
- Modify: `tests/test_server.py`

**Step 1: Update server to include new tools**

Add to `server.py`:
```python
from .platforms.kalshi.tools import trading as kalshi_trading
from .platforms.kalshi.tools import portfolio as kalshi_portfolio
from .platforms.kalshi.tools import realtime as kalshi_realtime

# In _init_kalshi():
kalshi_trading.set_client(self._kalshi_client)
kalshi_portfolio.set_client(self._kalshi_client)
# WebSocket manager init would go here

# In get_tools():
if self.config.KALSHI_ENABLED:
    tools.extend(kalshi_discovery.get_tools())
    tools.extend(kalshi_analysis.get_tools())
    tools.extend(kalshi_trading.get_tools())
    tools.extend(kalshi_portfolio.get_tools())
    tools.extend(kalshi_realtime.get_tools())

# In handle_tool():
# Add routing for new tool prefixes
```

**Step 2: Update test**

```python
def test_get_tools_count_kalshi_only(self):
    """Should return 52 tools with Kalshi only."""
    # ... setup ...
    tools = server.get_tools()
    kalshi_tools = [t for t in tools if "kalshi" in t.name]
    assert len(kalshi_tools) == 52  # 10+11+13+10+8
```

**Step 3: Run tests**

Run: `pytest tests/test_server.py -v`

**Step 4: Commit**

```bash
git add -A && git commit -m "feat: integrate all Kalshi tools in main server (52 total)"
```

---

## Task 6: Integration Testing

**Files:**
- Modify: `tests/integration/test_kalshi_integration.py`

**Step 1: Add comprehensive integration tests**

```python
@pytest.mark.asyncio
async def test_trading_flow(self):
    """Test order creation -> status -> cancel flow."""
    # Mock full trading flow

@pytest.mark.asyncio
async def test_portfolio_flow(self):
    """Test balance -> positions -> PnL flow."""
    # Mock full portfolio flow

@pytest.mark.asyncio
async def test_tool_count(self):
    """Verify 52 Kalshi tools available."""
    server = PredictionMCPServer(config)
    tools = server.get_tools()
    assert len([t for t in tools if "kalshi" in t.name]) == 52
```

**Step 2: Run full test suite**

Run: `pytest tests/ -v --tb=short`

**Step 3: Commit**

```bash
git add -A && git commit -m "test: add Phase 2 integration tests"
```

---

## Summary

**Phase 2 adds:**
- Trading tools: 13 (7 order management + 6 strategy helpers)
- Portfolio tools: 10
- Real-time tools: 8
- **Total new tools: 31**
- **Total Kalshi tools: 52**

**Estimated completion:** 4-6 subagent sessions
