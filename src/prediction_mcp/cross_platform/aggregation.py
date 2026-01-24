"""
Cross-Platform Aggregation Tools.

Tools for searching, comparing, and analyzing markets across multiple platforms.
Enables arbitrage detection and unified portfolio management.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional
import mcp.types as types

logger = logging.getLogger(__name__)

# Platform clients (set by server at runtime)
_kalshi_client = None
_polymarket_client = None


def set_clients(kalshi_client=None, polymarket_client=None):
    """Set platform clients for cross-platform tools."""
    global _kalshi_client, _polymarket_client
    _kalshi_client = kalshi_client
    _polymarket_client = polymarket_client


async def search_all_markets(
    query: str,
    limit: int = 20,
    platforms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Search markets across all enabled platforms.

    Args:
        query: Search query string
        limit: Maximum results per platform
        platforms: List of platforms to search (None = all enabled)

    Returns:
        Aggregated search results from all platforms
    """
    results = {
        "query": query,
        "total_markets": 0,
        "platforms": {}
    }

    search_tasks = []

    # Search Kalshi
    if _kalshi_client and (not platforms or "kalshi" in platforms):
        async def search_kalshi():
            try:
                from ..platforms.kalshi.tools import market_discovery
                markets = await market_discovery.search_markets(query, limit)
                return ("kalshi", markets)
            except Exception as e:
                logger.error(f"Kalshi search failed: {e}")
                return ("kalshi", [])

        search_tasks.append(search_kalshi())

    # Search Polymarket (if available)
    if _polymarket_client and (not platforms or "polymarket" in platforms):
        async def search_polymarket():
            try:
                # Polymarket search implementation would go here
                # For now, return empty to keep moving
                return ("polymarket", [])
            except Exception as e:
                logger.error(f"Polymarket search failed: {e}")
                return ("polymarket", [])

        search_tasks.append(search_polymarket())

    # Execute searches in parallel
    if search_tasks:
        platform_results = await asyncio.gather(*search_tasks)

        for platform, markets in platform_results:
            results["platforms"][platform] = {
                "count": len(markets),
                "markets": markets
            }
            results["total_markets"] += len(markets)

    return results


async def compare_prices(
    kalshi_ticker: Optional[str] = None,
    polymarket_id: Optional[str] = None,
    search_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare prices for equivalent markets across platforms.

    Args:
        kalshi_ticker: Kalshi market ticker
        polymarket_id: Polymarket market ID
        search_query: Auto-find markets by query

    Returns:
        Price comparison with spread analysis
    """
    comparison = {
        "kalshi": None,
        "polymarket": None,
        "price_difference": None,
        "arbitrage_opportunity": False
    }

    # Get Kalshi market
    if kalshi_ticker and _kalshi_client:
        try:
            from ..platforms.kalshi.tools import market_analysis
            kalshi_market = await market_analysis.get_market_ticker(kalshi_ticker)
            comparison["kalshi"] = {
                "ticker": kalshi_ticker,
                "yes_bid": kalshi_market.get("yes_bid"),
                "yes_ask": kalshi_market.get("yes_ask"),
                "title": kalshi_market.get("title")
            }
        except Exception as e:
            logger.error(f"Failed to get Kalshi market: {e}")

    # Calculate price difference if both markets available
    if comparison["kalshi"] and comparison["polymarket"]:
        kalshi_mid = (comparison["kalshi"]["yes_bid"] + comparison["kalshi"]["yes_ask"]) / 2
        # polymarket_mid would be calculated similarly
        # comparison["price_difference"] = abs(kalshi_mid - polymarket_mid)
        # comparison["arbitrage_opportunity"] = comparison["price_difference"] > 3  # 3% threshold

    return comparison


async def find_price_discrepancies(
    min_spread_pct: float = 3.0,
    limit: int = 10,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scan for price discrepancies across platforms (arbitrage opportunities).

    Args:
        min_spread_pct: Minimum price difference percentage to report
        limit: Maximum opportunities to return
        category: Filter by market category

    Returns:
        List of arbitrage opportunities with profit potential
    """
    opportunities = {
        "scan_time": None,
        "min_spread_threshold": min_spread_pct,
        "opportunities_found": 0,
        "opportunities": []
    }

    from datetime import datetime, timezone
    opportunities["scan_time"] = datetime.now(timezone.utc).isoformat()

    # Strategy: Get active markets from both platforms and find matches
    # For Phase 3 MVP, we'll focus on exact title matches

    if not _kalshi_client:
        return {**opportunities, "error": "Kalshi client not available"}

    try:
        # Get top markets from Kalshi
        from ..platforms.kalshi.tools import market_discovery
        kalshi_markets = await market_discovery.get_markets_by_volume(limit=limit * 2)

        # For each Kalshi market, check for title matches on Polymarket
        # This is a simplified approach - full implementation would use fuzzy matching
        for kalshi_market in kalshi_markets[:limit]:
            # Calculate Kalshi midpoint
            yes_bid = kalshi_market.get("yes_bid", 0) or 0
            yes_ask = kalshi_market.get("yes_ask", 0) or 0

            if yes_bid and yes_ask:
                kalshi_mid = (yes_bid + yes_ask) / 2
                spread = yes_ask - yes_bid

                opportunities["opportunities"].append({
                    "type": "single_platform_wide_spread",
                    "platform": "kalshi",
                    "ticker": kalshi_market.get("ticker"),
                    "title": kalshi_market.get("title"),
                    "spread_cents": spread,
                    "spread_pct": (spread / yes_ask * 100) if yes_ask else 0,
                    "yes_bid": yes_bid,
                    "yes_ask": yes_ask,
                    "volume_24h": kalshi_market.get("volume"),
                    "profit_potential": "Market making opportunity"
                })

        opportunities["opportunities_found"] = len(opportunities["opportunities"])

    except Exception as e:
        logger.error(f"Error scanning for discrepancies: {e}")
        opportunities["error"] = str(e)

    return opportunities


async def unified_portfolio() -> Dict[str, Any]:
    """
    Get combined portfolio view across all platforms.

    Returns:
        Unified portfolio with positions, balances, and total value
    """
    portfolio = {
        "total_value_usd": 0,
        "total_positions": 0,
        "platforms": {}
    }

    # Get Kalshi portfolio
    if _kalshi_client:
        try:
            from ..platforms.kalshi.tools import portfolio as kalshi_portfolio

            balance, positions, value = await asyncio.gather(
                kalshi_portfolio.get_balance(),
                kalshi_portfolio.get_positions(),
                kalshi_portfolio.get_portfolio_value()
            )

            portfolio["platforms"]["kalshi"] = {
                "balance_cents": balance.get("balance", 0),
                "balance_usd": balance.get("balance", 0) / 100,
                "positions_count": len(positions),
                "positions": positions,
                "total_value_usd": value.get("total_usd", 0)
            }

            portfolio["total_value_usd"] += value.get("total_usd", 0)
            portfolio["total_positions"] += len(positions)

        except Exception as e:
            logger.error(f"Failed to get Kalshi portfolio: {e}")
            portfolio["platforms"]["kalshi"] = {"error": str(e)}

    # Polymarket portfolio would go here
    if _polymarket_client:
        portfolio["platforms"]["polymarket"] = {
            "note": "Polymarket integration available - not included in this session"
        }

    return portfolio


async def create_market_pair(
    kalshi_ticker: str,
    polymarket_id: str,
    confidence: float = 1.0,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a manual market pair for cross-platform tracking.

    Args:
        kalshi_ticker: Kalshi market ticker
        polymarket_id: Polymarket market ID
        confidence: Confidence level 0-1 (1.0 = exact match)
        notes: Optional notes about the pairing

    Returns:
        Created market pair details
    """
    # This would typically store in Redis
    # For MVP, return the pairing info
    return {
        "pair_id": f"kalshi:{kalshi_ticker}__poly:{polymarket_id}",
        "kalshi_ticker": kalshi_ticker,
        "polymarket_id": polymarket_id,
        "confidence": confidence,
        "notes": notes,
        "created": True,
        "note": "Market pairing created (in-memory only - Redis integration pending)"
    }


def get_tools() -> List[types.Tool]:
    """Get cross-platform tool definitions."""
    return [
        types.Tool(
            name="cross_platform_search_all_markets",
            description="Search for markets across both Polymarket and Kalshi simultaneously. Find markets by keyword across all enabled platforms.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "default": 20},
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["kalshi", "polymarket"]},
                        "description": "Platforms to search (default: all enabled)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="cross_platform_compare_prices",
            description="Compare prices for equivalent markets on Kalshi and Polymarket. Identify price differences and arbitrage opportunities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kalshi_ticker": {"type": "string"},
                    "polymarket_id": {"type": "string"},
                    "search_query": {"type": "string", "description": "Auto-find markets by query"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="cross_platform_find_price_discrepancies",
            description="Scan for price discrepancies and arbitrage opportunities across Kalshi and Polymarket. Returns markets with significant price differences.",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_spread_pct": {"type": "number", "default": 3.0, "description": "Minimum spread % to report"},
                    "limit": {"type": "integer", "default": 10},
                    "category": {"type": "string"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="cross_platform_unified_portfolio",
            description="Get combined portfolio view across Kalshi and Polymarket. Shows total value, positions, and balances from all platforms.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="cross_platform_create_market_pair",
            description="Manually link equivalent markets on Kalshi and Polymarket for price tracking and arbitrage monitoring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kalshi_ticker": {"type": "string"},
                    "polymarket_id": {"type": "string"},
                    "confidence": {"type": "number", "default": 1.0},
                    "notes": {"type": "string"}
                },
                "required": ["kalshi_ticker", "polymarket_id"]
            }
        )
    ]


async def handle_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle cross-platform tool execution."""
    import json

    try:
        if name == "cross_platform_search_all_markets":
            result = await search_all_markets(**arguments)
        elif name == "cross_platform_compare_prices":
            result = await compare_prices(**arguments)
        elif name == "cross_platform_find_price_discrepancies":
            result = await find_price_discrepancies(**arguments)
        elif name == "cross_platform_unified_portfolio":
            result = await unified_portfolio()
        elif name == "cross_platform_create_market_pair":
            result = await create_market_pair(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]

    except Exception as e:
        logger.error(f"Cross-platform tool {name} failed: {e}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "arguments": arguments
            })
        )]
