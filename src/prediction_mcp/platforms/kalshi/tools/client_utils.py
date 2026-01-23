"""
Shared utilities for Kalshi tool modules.

Provides client getter pattern used across all tool modules.
"""

from typing import Any, Optional


_client: Optional[Any] = None
_ws_manager: Optional[Any] = None


def set_client(client: Any) -> None:
    """
    Set the Kalshi client for tool modules.

    Args:
        client: KalshiClient instance
    """
    global _client
    _client = client


def get_client() -> Any:
    """
    Get the Kalshi client.

    Returns:
        KalshiClient instance

    Raises:
        RuntimeError: If client not initialized
    """
    if _client is None:
        raise RuntimeError("Kalshi client not initialized. Call set_client() first.")
    return _client


def set_ws_manager(manager: Any) -> None:
    """
    Set the WebSocket manager for realtime tools.

    Args:
        manager: WebSocket manager instance
    """
    global _ws_manager
    _ws_manager = manager


def get_ws_manager() -> Any:
    """
    Get the WebSocket manager.

    Returns:
        WebSocket manager instance

    Raises:
        RuntimeError: If manager not initialized
    """
    if _ws_manager is None:
        raise RuntimeError("WebSocket manager not initialized. Call set_ws_manager() first.")
    return _ws_manager
