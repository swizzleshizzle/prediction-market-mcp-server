"""
Kalshi Platform Adapter.

Kalshi is a US-regulated prediction market exchange offering
event contracts on politics, economics, weather, and more.

Authentication: RSA-PSS signatures with API key
API: REST + WebSocket
"""

from .config import KalshiConfig, load_kalshi_config
from .auth import KalshiAuth
from .client import KalshiClient, create_kalshi_client

__all__ = [
    "KalshiConfig",
    "load_kalshi_config",
    "KalshiAuth",
    "KalshiClient",
    "create_kalshi_client",
]
