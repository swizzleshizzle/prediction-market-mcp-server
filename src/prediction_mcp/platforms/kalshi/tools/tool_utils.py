"""
Shared utilities for tool handling.

Provides common patterns like error handling for tool execution.
"""

import json
import logging
import re
from functools import wraps
from typing import Any, Callable, Dict, List

import mcp.types as types

logger = logging.getLogger(__name__)

# Ticker validation pattern: alphanumeric, hyphens, underscores only
TICKER_PATTERN = re.compile(r'^[A-Z0-9_-]{3,100}$')


def validate_ticker(ticker: str) -> None:
    """
    Validate a Kalshi market ticker.

    Args:
        ticker: Market ticker to validate

    Raises:
        ValueError: If ticker is invalid
    """
    if not ticker:
        raise ValueError("Ticker cannot be empty")

    if not isinstance(ticker, str):
        raise ValueError(f"Ticker must be a string, got {type(ticker).__name__}")

    if not TICKER_PATTERN.match(ticker):
        raise ValueError(
            f"Invalid ticker format '{ticker}'. "
            "Tickers must be 3-100 uppercase alphanumeric characters, hyphens, or underscores"
        )


def tool_handler(func: Callable) -> Callable:
    """
    Decorator for tool handler functions.

    Standardizes error handling and response formatting:
    - Catches exceptions and returns formatted error response
    - Formats successful results as JSON
    - Logs errors for debugging

    Args:
        func: Async function that handles tool execution

    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        try:
            result = await func(name, arguments)
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}", exc_info=True)
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "tool": name,
                    "arguments": arguments
                })
            )]

    return wrapper
