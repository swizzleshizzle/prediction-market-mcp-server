"""
Base adapter interface for prediction market platforms.

All platform adapters must implement this interface to ensure
consistent behavior across the multi-platform MCP server.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol
import mcp.types as types


@dataclass
class NormalizedMarket:
    """Platform-agnostic market representation."""
    id: str                          # Platform-prefixed ID
    platform: str                    # "polymarket" | "kalshi"
    native_id: str                   # Original platform ID
    title: str
    description: str
    category: str
    outcomes: List["NormalizedOutcome"]
    expiration: Optional[datetime]
    volume_24h_usd: float
    liquidity_usd: float
    status: str                      # "open" | "closed" | "resolved"

    # Platform-specific data preserved
    platform_data: Optional[Dict[str, Any]] = None


@dataclass
class NormalizedOutcome:
    """Platform-agnostic outcome representation."""
    id: str
    name: str                        # YES/NO or named outcome
    price_bid: Optional[float]
    price_ask: Optional[float]
    price_last: Optional[float]
    native_id: str                   # Platform's token/outcome ID


@dataclass
class NormalizedOrder:
    """Platform-agnostic order representation."""
    id: str                          # Platform-prefixed ID
    platform: str
    native_id: str
    market_id: str
    side: str                        # "BUY" | "SELL"
    outcome: str
    price: float
    size: int
    size_usd: float
    order_type: str                  # "limit" | "market"
    time_in_force: str               # GTC | GTD | IOC | FOK
    status: str                      # pending | open | partial | filled | cancelled
    filled_size: int
    avg_fill_price: Optional[float]
    created_at: datetime
    strategy_id: Optional[str] = None


@dataclass
class NormalizedPosition:
    """Platform-agnostic position representation."""
    id: str
    platform: str
    market_id: str
    market_title: str
    outcome: str
    size: int                        # Signed: + long, - short
    avg_entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    strategy_id: Optional[str] = None


@dataclass
class PriceQuote:
    """Current price quote for an outcome."""
    market_id: str
    outcome: str
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    timestamp: datetime


@dataclass
class Balance:
    """Account balance."""
    available_usd: float
    total_usd: float
    reserved_usd: float


@dataclass
class HealthStatus:
    """Platform health status."""
    platform: str
    connected: bool
    authenticated: bool
    last_check: datetime
    message: str


class PlatformAdapter(ABC):
    """
    Abstract base class for platform adapters.

    Each platform (Polymarket, Kalshi, etc.) implements this interface
    to provide consistent access across the MCP server.
    """

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """Unique platform identifier (e.g., 'polymarket', 'kalshi')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable platform name."""
        pass

    # === Connection Management ===

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the platform.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the platform."""
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Check platform connection and authentication status."""
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if authenticated for trading operations."""
        pass

    # === Market Data (Normalized) ===

    @abstractmethod
    async def get_market_normalized(self, market_id: str) -> NormalizedMarket:
        """Fetch market by ID and return normalized representation."""
        pass

    @abstractmethod
    async def search_markets_normalized(
        self,
        query: str,
        limit: int = 20,
        **filters
    ) -> List[NormalizedMarket]:
        """Search markets and return normalized results."""
        pass

    @abstractmethod
    async def get_price(self, market_id: str, outcome: str) -> PriceQuote:
        """Get current price quote for an outcome."""
        pass

    # === Trading (Normalized) ===

    @abstractmethod
    async def create_order(
        self,
        market_id: str,
        outcome: str,
        side: str,
        price: float,
        size: int,
        order_type: str = "limit",
        time_in_force: str = "GTC",
    ) -> NormalizedOrder:
        """Create an order and return normalized representation."""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID. Returns True if successful."""
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> NormalizedOrder:
        """Get order by ID."""
        pass

    # === Portfolio (Normalized) ===

    @abstractmethod
    async def get_positions(self) -> List[NormalizedPosition]:
        """Get all current positions."""
        pass

    @abstractmethod
    async def get_balance(self) -> Balance:
        """Get account balance."""
        pass

    # === Native Access ===

    @abstractmethod
    def get_native_client(self) -> Any:
        """
        Get the underlying native API client.

        Allows direct access to platform-specific features
        not exposed through the normalized interface.
        """
        pass

    # === Tool Definitions ===

    @abstractmethod
    def get_tools(self) -> List[types.Tool]:
        """Get MCP tool definitions for this platform."""
        pass

    @abstractmethod
    async def handle_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Handle tool execution."""
        pass
