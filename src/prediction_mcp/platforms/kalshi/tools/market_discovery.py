"""
Kalshi Market Discovery Tools.

Provides tools for finding and filtering Kalshi markets:
- kalshi_search_markets
- kalshi_get_markets_by_volume
- kalshi_get_events_by_category
- kalshi_get_markets_closing_soon
- kalshi_get_featured_markets
- kalshi_get_sports_markets
- kalshi_get_crypto_markets
- kalshi_get_market
- kalshi_get_event (Kalshi-specific)
- kalshi_get_event_markets (Kalshi-specific)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import mcp.types as types

logger = logging.getLogger(__name__)

# Client instance set by adapter
_client = None


def set_client(client) -> None:
    """Set the Kalshi client instance."""
    global _client
    _client = client


def _get_client():
    """Get the Kalshi client instance."""
    if _client is None:
        raise RuntimeError("Kalshi client not initialized")
    return _client


# === Tool Implementation Functions ===

async def search_markets(
    query: str,
    limit: int = 20,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search Kalshi markets by keyword.

    Args:
        query: Search query
        limit: Maximum results
        status: Filter by status (open, closed, settled)

    Returns:
        List of matching markets
    """
    client = _get_client()

    # Kalshi doesn't have direct text search, so we fetch and filter
    markets = await client.get_markets(limit=500, status=status or "open")

    # Filter by query
    query_lower = query.lower()
    matching = [
        m for m in markets
        if query_lower in m.get("title", "").lower()
        or query_lower in m.get("ticker", "").lower()
        or query_lower in m.get("subtitle", "").lower()
    ]

    return matching[:limit]


async def get_markets_by_volume(
    timeframe: str = "24h",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get markets sorted by trading volume.

    Args:
        timeframe: Volume timeframe (24h, 7d, 30d)
        limit: Maximum results

    Returns:
        List of markets sorted by volume
    """
    client = _get_client()

    markets = await client.get_markets(limit=200, status="open")

    # Sort by volume (volume field may vary)
    volume_key = "volume_24h" if timeframe == "24h" else "volume"
    sorted_markets = sorted(
        markets,
        key=lambda m: m.get(volume_key, 0) or 0,
        reverse=True
    )

    return sorted_markets[:limit]


async def get_events_by_category(
    category: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Get events filtered by category.

    Args:
        category: Category name (e.g., Politics, Economics, Weather)
        limit: Maximum results

    Returns:
        List of events in category
    """
    client = _get_client()

    events = await client.get_events(limit=200, status="open")

    # Filter by category
    category_lower = category.lower()
    matching = [
        e for e in events
        if category_lower in e.get("category", "").lower()
        or category_lower in e.get("series_ticker", "").lower()
    ]

    return matching[:limit]


async def get_markets_closing_soon(
    hours: int = 24,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get markets closing within specified hours.

    Args:
        hours: Hours until close
        limit: Maximum results

    Returns:
        List of markets closing soon
    """
    client = _get_client()

    markets = await client.get_markets(limit=500, status="open")

    # Filter by close time
    cutoff = datetime.utcnow() + timedelta(hours=hours)
    cutoff_ts = int(cutoff.timestamp())

    closing_soon = [
        m for m in markets
        if m.get("close_time") and int(m["close_time"]) <= cutoff_ts
    ]

    # Sort by close time
    closing_soon.sort(key=lambda m: m.get("close_time", 0))

    return closing_soon[:limit]


async def get_featured_markets(
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Get featured/promoted markets.

    Returns:
        List of featured markets
    """
    client = _get_client()

    # Kalshi may have a featured flag or we use volume as proxy
    markets = await client.get_markets(limit=100, status="open")

    # Filter for featured or use high volume as proxy
    featured = [
        m for m in markets
        if m.get("featured") or m.get("is_featured")
    ]

    if not featured:
        # Fallback to high volume markets
        featured = sorted(
            markets,
            key=lambda m: m.get("volume", 0) or 0,
            reverse=True
        )

    return featured[:limit]


async def get_sports_markets(
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Get sports-related markets.

    Returns:
        List of sports markets
    """
    return await get_events_by_category("sports", limit)


async def get_crypto_markets(
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Get cryptocurrency-related markets.

    Returns:
        List of crypto markets
    """
    client = _get_client()

    # Search for crypto-related series
    markets = await client.get_markets(limit=300, status="open")

    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto"]
    matching = [
        m for m in markets
        if any(
            kw in m.get("title", "").lower()
            or kw in m.get("ticker", "").lower()
            for kw in crypto_keywords
        )
    ]

    return matching[:limit]


async def get_market(ticker: str) -> Dict[str, Any]:
    """
    Get detailed market information.

    Args:
        ticker: Market ticker

    Returns:
        Market details
    """
    client = _get_client()
    return await client.get_market(ticker)


async def get_event(event_ticker: str) -> Dict[str, Any]:
    """
    Get event details (Kalshi-specific).

    Events are groups of related markets.

    Args:
        event_ticker: Event ticker

    Returns:
        Event details
    """
    client = _get_client()
    return await client.get_event(event_ticker)


async def get_event_markets(
    event_ticker: str,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get all markets within an event (Kalshi-specific).

    Args:
        event_ticker: Event ticker
        limit: Maximum markets

    Returns:
        List of markets in the event
    """
    client = _get_client()
    return await client.get_markets(event_ticker=event_ticker, limit=limit)


# === MCP Tool Definitions ===

def get_tools() -> List[types.Tool]:
    """Get market discovery tool definitions."""
    return [
        types.Tool(
            name="kalshi_search_markets",
            description="Search Kalshi markets by keyword or topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'bitcoin', 'election')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "closed", "settled"],
                        "description": "Filter by market status"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="kalshi_get_markets_by_volume",
            description="Get Kalshi markets sorted by trading volume.",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "enum": ["24h", "7d", "30d"],
                        "description": "Volume timeframe",
                        "default": "24h"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_events_by_category",
            description="Get Kalshi events filtered by category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category (Politics, Economics, Weather, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 20
                    }
                },
                "required": ["category"]
            }
        ),
        types.Tool(
            name="kalshi_get_markets_closing_soon",
            description="Get Kalshi markets closing within specified hours.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "Hours until close (default: 24)",
                        "default": 24
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_featured_markets",
            description="Get featured/promoted Kalshi markets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_sports_markets",
            description="Get Kalshi sports prediction markets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_crypto_markets",
            description="Get Kalshi cryptocurrency prediction markets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="kalshi_get_market",
            description="Get detailed information for a specific Kalshi market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Market ticker (e.g., KXBTC-25JAN31-T100000)"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="kalshi_get_event",
            description="Get Kalshi event details. Events group related markets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_ticker": {
                        "type": "string",
                        "description": "Event ticker"
                    }
                },
                "required": ["event_ticker"]
            }
        ),
        types.Tool(
            name="kalshi_get_event_markets",
            description="Get all markets within a Kalshi event.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_ticker": {
                        "type": "string",
                        "description": "Event ticker"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum markets",
                        "default": 50
                    }
                },
                "required": ["event_ticker"]
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
        if name == "kalshi_search_markets":
            result = await search_markets(**arguments)
        elif name == "kalshi_get_markets_by_volume":
            result = await get_markets_by_volume(**arguments)
        elif name == "kalshi_get_events_by_category":
            result = await get_events_by_category(**arguments)
        elif name == "kalshi_get_markets_closing_soon":
            result = await get_markets_closing_soon(**arguments)
        elif name == "kalshi_get_featured_markets":
            result = await get_featured_markets(**arguments)
        elif name == "kalshi_get_sports_markets":
            result = await get_sports_markets(**arguments)
        elif name == "kalshi_get_crypto_markets":
            result = await get_crypto_markets(**arguments)
        elif name == "kalshi_get_market":
            result = await get_market(**arguments)
        elif name == "kalshi_get_event":
            result = await get_event(**arguments)
        elif name == "kalshi_get_event_markets":
            result = await get_event_markets(**arguments)
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
