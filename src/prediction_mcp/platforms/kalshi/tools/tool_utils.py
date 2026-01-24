"""
Shared utilities for tool handling.

Provides common patterns like error handling for tool execution.
"""

import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, List

import mcp.types as types

logger = logging.getLogger(__name__)


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
                    "tool": name
                })
            )]

    return wrapper
