"""
Kalshi Market Analysis Tools.

Provides tools for analyzing Kalshi markets:
- kalshi_get_market_ticker - Current prices
- kalshi_get_orderbook - Full orderbook
- kalshi_analyze_liquidity - Liquidity metrics
- kalshi_get_candlesticks - OHLC history
- kalshi_analyze_market_opportunity - AI analysis
- kalshi_compare_markets - Multi-market comparison
- kalshi_get_trades - Recent trades
- kalshi_get_spread - Current spread
- kalshi_assess_market_risk - Risk scoring
- kalshi_get_series - Series data
- kalshi_get_exchange_schedule - Trading hours
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import mcp.types as types

from .client_utils import set_client, get_client
from .tool_utils import validate_ticker

logger = logging.getLogger(__name__)


# === Helper Functions ===

def calculate_spread(yes_bid: Optional[int], yes_ask: Optional[int]) -> tuple[Optional[int], Optional[float]]:
    """
    Calculate spread in cents and percentage.

    Args:
        yes_bid: Best yes bid price (cents)
        yes_ask: Best yes ask price (cents)

    Returns:
        Tuple of (spread_cents, spread_percent)
    """
    if not yes_bid or not yes_ask:
        return None, None

    spread_cents = yes_ask - yes_bid
    spread_pct = (spread_cents / yes_ask * 100) if yes_ask else None

    return spread_cents, spread_pct


# === Tool Implementation Functions ===

async def get_market_ticker(ticker: str) -> Dict[str, Any]:
    """
    Get current price ticker for a market.

    Args:
        ticker: Market ticker

    Returns:
        Price information including bid, ask, last
    """
    validate_ticker(ticker)
    client = get_client()
    market = await client.get_market(ticker)

    return {
        "ticker": market.get("ticker"),
        "title": market.get("title"),
        "yes_bid": market.get("yes_bid"),
        "yes_ask": market.get("yes_ask"),
        "no_bid": market.get("no_bid"),
        "no_ask": market.get("no_ask"),
        "last_price": market.get("last_price"),
        "volume": market.get("volume"),
        "open_interest": market.get("open_interest"),
        "status": market.get("status"),
    }


async def get_orderbook(
    ticker: str,
    depth: int = 10
) -> Dict[str, Any]:
    """
    Get full orderbook for a market.

    Args:
        ticker: Market ticker
        depth: Orderbook depth

    Returns:
        Orderbook with yes/no sides
    """
    validate_ticker(ticker)
    client = get_client()
    return await client.get_orderbook(ticker, depth)


async def analyze_liquidity(ticker: str) -> Dict[str, Any]:
    """
    Analyze market liquidity.

    Args:
        ticker: Market ticker

    Returns:
        Liquidity metrics including spread, depth, volume
    """
    validate_ticker(ticker)
    client = get_client()

    market, orderbook = await asyncio.gather(
        client.get_market(ticker),
        client.get_orderbook(ticker, depth=10)
    )

    yes_bid = market.get("yes_bid", 0) or 0
    yes_ask = market.get("yes_ask", 0) or 0

    # Calculate spread
    spread, spread_pct = calculate_spread(yes_bid, yes_ask)

    # Calculate depth at best prices
    yes_depth = sum(level[1] for level in orderbook.get("yes", [])) if orderbook.get("yes") else 0
    no_depth = sum(level[1] for level in orderbook.get("no", [])) if orderbook.get("no") else 0

    return {
        "ticker": ticker,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "spread_cents": spread,
        "spread_percent": round(spread_pct, 2) if spread_pct else None,
        "yes_depth_contracts": yes_depth,
        "no_depth_contracts": no_depth,
        "total_depth_contracts": yes_depth + no_depth,
        "volume_24h": market.get("volume"),
        "open_interest": market.get("open_interest"),
        "liquidity_score": _calculate_liquidity_score(spread, yes_depth + no_depth),
    }


def _calculate_liquidity_score(spread: Optional[float], depth: int) -> str:
    """Calculate a simple liquidity score."""
    if spread is None or depth == 0:
        return "low"

    # Lower spread and higher depth = better liquidity
    if spread <= 2 and depth >= 1000:
        return "excellent"
    elif spread <= 5 and depth >= 500:
        return "good"
    elif spread <= 10 and depth >= 100:
        return "moderate"
    else:
        return "low"


async def get_candlesticks(
    ticker: str,
    period: str = "1h",
    limit: int = 24
) -> List[Dict[str, Any]]:
    """
    Get OHLC candlestick data.

    Args:
        ticker: Market ticker
        period: Candle period (1m, 5m, 1h, 1d)
        limit: Maximum candles

    Returns:
        List of candlestick data
    """
    validate_ticker(ticker)
    client = get_client()
    candles = await client.get_market_candlesticks(ticker, period)
    return candles[:limit]


async def analyze_market_opportunity(ticker: str) -> Dict[str, Any]:
    """
    Analyze market for trading opportunities.

    Args:
        ticker: Market ticker

    Returns:
        Analysis including price, liquidity, and opportunity assessment
    """
    validate_ticker(ticker)
    client = get_client()

    market, orderbook = await asyncio.gather(
        client.get_market(ticker),
        client.get_orderbook(ticker, depth=5)
    )

    yes_bid = market.get("yes_bid", 0) or 0
    yes_ask = market.get("yes_ask", 0) or 0
    spread, _ = calculate_spread(yes_bid, yes_ask)
    spread = spread or 0

    # Simple opportunity analysis
    opportunities = []

    # Check for wide spreads (potential market making opportunity)
    if spread >= 5:
        opportunities.append({
            "type": "wide_spread",
            "description": f"Spread of {spread} cents may offer market making opportunity",
            "risk": "medium"
        })

    # Check for extreme prices
    if yes_bid and yes_bid <= 10:
        opportunities.append({
            "type": "low_price_yes",
            "description": f"YES trading at {yes_bid} cents - high payout if correct",
            "risk": "high"
        })
    if yes_ask and yes_ask >= 90:
        opportunities.append({
            "type": "high_price_yes",
            "description": f"YES trading at {yes_ask} cents - NO offers value if event unlikely",
            "risk": "high"
        })

    return {
        "ticker": ticker,
        "title": market.get("title"),
        "current_prices": {
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "spread": spread,
        },
        "volume_24h": market.get("volume"),
        "close_time": market.get("close_time"),
        "opportunities": opportunities,
        "opportunity_count": len(opportunities),
    }


async def compare_markets(tickers: List[str]) -> Dict[str, Any]:
    """
    Compare multiple markets.

    Args:
        tickers: List of market tickers to compare

    Returns:
        Comparison data for all markets
    """
    client = get_client()

    # Fetch all markets in parallel
    limited_tickers = tickers[:10]  # Limit to 10 markets
    market_tasks = [client.get_market(ticker) for ticker in limited_tickers]
    results = await asyncio.gather(*market_tasks, return_exceptions=True)

    # Process results
    comparisons = []
    for ticker, result in zip(limited_tickers, results):
        if isinstance(result, Exception):
            logger.warning(f"Failed to fetch market {ticker}: {result}")
            comparisons.append({
                "ticker": ticker,
                "error": str(result)
            })
        else:
            comparisons.append({
                "ticker": ticker,
                "title": result.get("title"),
                "yes_bid": result.get("yes_bid"),
                "yes_ask": result.get("yes_ask"),
                "volume": result.get("volume"),
                "open_interest": result.get("open_interest"),
                "status": result.get("status"),
            })

    return {
        "markets_compared": len(comparisons),
        "markets": comparisons,
    }


async def get_trades(
    ticker: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get recent trades for a market.

    Args:
        ticker: Market ticker
        limit: Maximum trades

    Returns:
        List of recent trades
    """
    validate_ticker(ticker)
    client = get_client()
    return await client.get_trades(ticker, limit)


async def get_spread(ticker: str) -> Dict[str, Any]:
    """
    Get current bid-ask spread for a market.

    Args:
        ticker: Market ticker

    Returns:
        Spread information
    """
    validate_ticker(ticker)
    client = get_client()
    market = await client.get_market(ticker)

    yes_bid = market.get("yes_bid", 0) or 0
    yes_ask = market.get("yes_ask", 0) or 0
    no_bid = market.get("no_bid", 0) or 0
    no_ask = market.get("no_ask", 0) or 0

    yes_spread, _ = calculate_spread(yes_bid, yes_ask)
    no_spread = no_ask - no_bid if no_ask and no_bid else None

    return {
        "ticker": ticker,
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "yes_spread_cents": yes_spread,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "no_spread_cents": no_spread,
        "effective_spread": yes_spread,  # YES spread is typically the reference
    }


async def assess_market_risk(ticker: str) -> Dict[str, Any]:
    """
    Assess risk factors for a market.

    Args:
        ticker: Market ticker

    Returns:
        Risk assessment including liquidity, time, and price risks
    """
    validate_ticker(ticker)
    client = get_client()

    market = await client.get_market(ticker)
    orderbook = await client.get_orderbook(ticker, depth=5)

    risks = []

    # Liquidity risk
    yes_depth = sum(level[1] for level in orderbook.get("yes", [])) if orderbook.get("yes") else 0
    if yes_depth < 100:
        risks.append({
            "type": "liquidity",
            "level": "high",
            "description": "Low orderbook depth may cause slippage"
        })

    # Time risk
    close_time = market.get("close_time")
    if close_time:
        try:
            close_dt = datetime.fromtimestamp(int(close_time), tz=timezone.utc)
            hours_until_close = (close_dt - datetime.now(timezone.utc)).total_seconds() / 3600
            if hours_until_close < 24:
                risks.append({
                    "type": "time",
                    "level": "medium",
                    "description": f"Market closes in {hours_until_close:.1f} hours"
                })
        except (ValueError, OSError):
            pass

    # Price volatility risk (based on spread)
    yes_bid = market.get("yes_bid", 0) or 0
    yes_ask = market.get("yes_ask", 0) or 0
    spread, _ = calculate_spread(yes_bid, yes_ask)
    spread = spread or 0
    if spread > 10:
        risks.append({
            "type": "volatility",
            "level": "high",
            "description": f"Wide spread of {spread} cents indicates price uncertainty"
        })

    # Determine overall risk level
    high_risks = sum(1 for r in risks if r["level"] == "high")
    overall_risk = "high" if high_risks >= 2 else "medium" if high_risks == 1 or len(risks) >= 2 else "low"

    return {
        "ticker": ticker,
        "title": market.get("title"),
        "overall_risk": overall_risk,
        "risk_factors": risks,
        "risk_count": len(risks),
    }


async def get_series(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get market series data.

    Series are recurring market templates (e.g., daily BTC price).

    Args:
        limit: Maximum series

    Returns:
        List of series
    """
    client = get_client()
    return await client.get_series(limit)


async def get_exchange_schedule() -> Dict[str, Any]:
    """
    Get exchange trading schedule.

    Returns:
        Trading hours and schedule information
    """
    client = get_client()
    return await client.get_exchange_schedule()


# === MCP Tool Definitions ===

def get_tools() -> List[types.Tool]:
    """Get market analysis tool definitions."""
    return [
        types.Tool(
            name="kalshi_get_market_ticker",
            description="Get current price ticker for a Kalshi market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_get_orderbook",
            description="Get full orderbook for a Kalshi market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Orderbook depth (default: 10)",
                        "default": 10
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_analyze_liquidity",
            description="Analyze liquidity metrics for a Kalshi market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_get_candlesticks",
            description="Get OHLC candlestick data for a Kalshi market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["1m", "5m", "1h", "1d"],
                        "description": "Candle period",
                        "default": "1h"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum candles",
                        "default": 24
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_analyze_market_opportunity",
            description="Analyze a Kalshi market for trading opportunities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_compare_markets",
            description="Compare multiple Kalshi markets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of market tickers to compare"
                    }
                },
                "required": ["tickers"]
            }
        ),
        types.Tool(
            name="kalshi_get_trades",
            description="Get recent trades for a Kalshi market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum trades",
                        "default": 50
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_get_spread",
            description="Get current bid-ask spread for a Kalshi market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_assess_market_risk",
            description="Assess risk factors for a Kalshi market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_get_series",
            description="Get Kalshi market series (recurring market templates).",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum series",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_exchange_schedule",
            description="Get Kalshi exchange trading schedule and hours.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


# === Tool Handler ===

async def handle_tool(
    name: str,
    arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """
    Handle tool execution.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of TextContent with JSON results
    """
    try:
        if name == "kalshi_get_market_ticker":
            result = await get_market_ticker(**arguments)
        elif name == "kalshi_get_orderbook":
            result = await get_orderbook(**arguments)
        elif name == "kalshi_analyze_liquidity":
            result = await analyze_liquidity(**arguments)
        elif name == "kalshi_get_candlesticks":
            result = await get_candlesticks(**arguments)
        elif name == "kalshi_analyze_market_opportunity":
            result = await analyze_market_opportunity(**arguments)
        elif name == "kalshi_compare_markets":
            result = await compare_markets(**arguments)
        elif name == "kalshi_get_trades":
            result = await get_trades(**arguments)
        elif name == "kalshi_get_spread":
            result = await get_spread(**arguments)
        elif name == "kalshi_assess_market_risk":
            result = await assess_market_risk(**arguments)
        elif name == "kalshi_get_series":
            result = await get_series(**arguments)
        elif name == "kalshi_get_exchange_schedule":
            result = await get_exchange_schedule()
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]

    except Exception as e:
        logger.error(f"Tool execution failed for {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]
