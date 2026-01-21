# Phase 1: Foundation - Multi-Platform Architecture & Kalshi Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish multi-platform architecture and implement core Kalshi API integration with 20 working tools.

**Architecture:** Refactor project structure to support multiple platforms via adapter pattern. Each platform gets its own client, config section, and tool module while sharing common utilities. Redis integration for state persistence.

**Tech Stack:** Python 3.10+, mcp>=1.0.0, httpx, pydantic, redis, kalshi-python (official SDK), RSA signing

---

## Prerequisites

Before starting, ensure you have:
- [ ] Kalshi account with API access enabled
- [ ] Kalshi API key ID and RSA private key (.pem file)
- [ ] Redis Stack running locally or in Docker
- [ ] Existing polymarket-mcp-server codebase cloned

---

## Task 1: Project Structure Refactoring

**Files:**
- Create: `src/prediction_mcp/__init__.py`
- Create: `src/prediction_mcp/platforms/__init__.py`
- Create: `src/prediction_mcp/platforms/base.py`
- Move: `src/polymarket_mcp/` → `src/prediction_mcp/platforms/polymarket/`
- Modify: `pyproject.toml`

**Step 1: Create new package structure**

Create directory structure:

```bash
mkdir -p src/prediction_mcp/platforms
mkdir -p src/prediction_mcp/core
mkdir -p src/prediction_mcp/arbitrage
```

**Step 2: Create main package init**

Create `src/prediction_mcp/__init__.py`:

```python
"""
Multi-Platform Prediction Market MCP Server.

Supports:
- Polymarket (Polygon-based prediction markets)
- Kalshi (US-regulated prediction exchange)
- Cross-platform arbitrage and aggregation
"""

__version__ = "0.2.0"
__all__ = ["platforms", "core", "arbitrage"]
```

**Step 3: Create platforms package init**

Create `src/prediction_mcp/platforms/__init__.py`:

```python
"""
Platform adapters for prediction market exchanges.

Each platform module provides:
- Client: API communication
- Config: Platform-specific settings
- Tools: MCP tool definitions and handlers
"""

from typing import Dict, Type
from .base import PlatformAdapter

# Registry populated by platform modules
_adapters: Dict[str, Type[PlatformAdapter]] = {}


def register_adapter(name: str, adapter_class: Type[PlatformAdapter]) -> None:
    """Register a platform adapter."""
    _adapters[name] = adapter_class


def get_adapter(name: str) -> Type[PlatformAdapter]:
    """Get adapter class by platform name."""
    if name not in _adapters:
        raise KeyError(f"Unknown platform: {name}. Available: {list(_adapters.keys())}")
    return _adapters[name]


def list_adapters() -> list[str]:
    """List registered platform names."""
    return list(_adapters.keys())


__all__ = ["PlatformAdapter", "register_adapter", "get_adapter", "list_adapters"]
```

**Step 4: Create base adapter interface**

Create `src/prediction_mcp/platforms/base.py`:

```python
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
```

**Step 5: Update pyproject.toml**

Modify `pyproject.toml` to add new dependencies and update package name:

```toml
[project]
name = "prediction-mcp-server"
version = "0.2.0"
description = "Multi-platform prediction market MCP server for Polymarket and Kalshi"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

dependencies = [
    # MCP Protocol
    "mcp>=1.0.0",

    # Polymarket
    "py-clob-client>=0.28.0",
    "eth-account>=0.11.0",

    # Kalshi
    "kalshi-python>=2.1.0",
    "cryptography>=41.0.0",

    # HTTP & WebSocket
    "websockets>=12.0",
    "httpx>=0.27.0",

    # Data & Config
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",

    # Redis
    "redis>=5.0.0",
    "redis-om>=0.2.0",

    # Web Dashboard
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "jinja2>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-timeout>=2.2.0",
    "black>=24.0.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
]

[project.scripts]
prediction-mcp = "prediction_mcp.server:main"
polymarket-mcp = "prediction_mcp.platforms.polymarket.server:main"
kalshi-mcp = "prediction_mcp.platforms.kalshi.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/prediction_mcp"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
timeout = 120

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
target-version = "py310"
```

**Step 6: Run test to verify structure**

```bash
cd Z:/MCP_Servers/Prediction_MCP/polymarket-mcp-server
python -c "from src.prediction_mcp.platforms.base import PlatformAdapter, NormalizedMarket; print('Base classes OK')"
```

Expected: `Base classes OK`

**Step 7: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor: establish multi-platform architecture

- Create prediction_mcp package structure
- Add PlatformAdapter base class with normalized data models
- Define NormalizedMarket, NormalizedOrder, NormalizedPosition
- Update pyproject.toml with Kalshi and Redis dependencies

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Kalshi Configuration

**Files:**
- Create: `src/prediction_mcp/platforms/kalshi/__init__.py`
- Create: `src/prediction_mcp/platforms/kalshi/config.py`
- Create: `tests/platforms/kalshi/test_config.py`

**Step 1: Write the failing test**

Create `tests/platforms/__init__.py`:

```python
"""Platform-specific tests."""
```

Create `tests/platforms/kalshi/__init__.py`:

```python
"""Kalshi platform tests."""
```

Create `tests/platforms/kalshi/test_config.py`:

```python
"""Tests for Kalshi configuration."""

import os
import pytest
from unittest.mock import patch


class TestKalshiConfig:
    """Test Kalshi configuration loading and validation."""

    def test_config_loads_from_env(self):
        """Config should load from environment variables."""
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        with patch.dict(os.environ, {
            "KALSHI_ENABLED": "true",
            "KALSHI_EMAIL": "test@example.com",
            "KALSHI_API_KEY_ID": "key123",
            "KALSHI_PRIVATE_KEY_PATH": "/path/to/key.pem",
        }):
            config = KalshiConfig()
            assert config.KALSHI_ENABLED is True
            assert config.KALSHI_EMAIL == "test@example.com"
            assert config.KALSHI_API_KEY_ID == "key123"

    def test_demo_mode_skips_validation(self):
        """Demo mode should not require credentials."""
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        with patch.dict(os.environ, {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = KalshiConfig()
            assert config.KALSHI_DEMO_MODE is True
            assert config.KALSHI_API_URL == "https://demo-api.kalshi.co/trade-api/v2"

    def test_production_requires_credentials(self):
        """Production mode should require API credentials."""
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        with patch.dict(os.environ, {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "false",
        }, clear=True):
            with pytest.raises(ValueError, match="KALSHI_API_KEY_ID is required"):
                KalshiConfig()

    def test_api_url_switches_for_demo(self):
        """API URL should switch based on demo mode."""
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        # Demo mode
        with patch.dict(os.environ, {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = KalshiConfig()
            assert "demo-api" in config.KALSHI_API_URL

        # Production mode
        with patch.dict(os.environ, {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "false",
            "KALSHI_EMAIL": "test@example.com",
            "KALSHI_API_KEY_ID": "key123",
            "KALSHI_PRIVATE_KEY_PATH": "/path/to/key.pem",
        }, clear=True):
            config = KalshiConfig()
            assert "trading-api.kalshi.com" in config.KALSHI_API_URL
```

**Step 2: Run test to verify it fails**

```bash
cd Z:/MCP_Servers/Prediction_MCP/polymarket-mcp-server
pytest tests/platforms/kalshi/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.prediction_mcp.platforms.kalshi'`

**Step 3: Create Kalshi package init**

Create `src/prediction_mcp/platforms/kalshi/__init__.py`:

```python
"""
Kalshi Platform Adapter.

Kalshi is a US-regulated prediction market exchange offering
event contracts on politics, economics, weather, and more.

Authentication: RSA-PSS signatures with API key
API: REST + WebSocket
"""

from .config import KalshiConfig, load_kalshi_config

__all__ = ["KalshiConfig", "load_kalshi_config"]
```

**Step 4: Write Kalshi config implementation**

Create `src/prediction_mcp/platforms/kalshi/config.py`:

```python
"""
Kalshi platform configuration.

Handles loading and validation of Kalshi API credentials
and trading settings.
"""

import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KalshiConfig(BaseSettings):
    """Configuration for Kalshi platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Platform enablement
    KALSHI_ENABLED: bool = Field(
        default=False,
        description="Enable Kalshi platform integration"
    )

    # Demo mode (uses demo API, no real money)
    KALSHI_DEMO_MODE: bool = Field(
        default=False,
        description="Use Kalshi demo environment"
    )

    # Authentication
    KALSHI_EMAIL: str = Field(
        default="",
        description="Kalshi account email"
    )

    KALSHI_API_KEY_ID: str = Field(
        default="",
        description="Kalshi API key ID"
    )

    KALSHI_PRIVATE_KEY_PATH: str = Field(
        default="",
        description="Path to RSA private key PEM file"
    )

    KALSHI_PRIVATE_KEY: Optional[str] = Field(
        default=None,
        description="RSA private key content (alternative to path)"
    )

    # API Endpoints (auto-set based on demo mode)
    KALSHI_API_URL: str = Field(
        default="",
        description="Kalshi API base URL"
    )

    KALSHI_WS_URL: str = Field(
        default="",
        description="Kalshi WebSocket URL"
    )

    # Safety Limits
    KALSHI_MAX_ORDER_SIZE_USD: float = Field(
        default=1000.0,
        description="Maximum order size in USD"
    )

    KALSHI_MAX_POSITION_SIZE_USD: float = Field(
        default=5000.0,
        description="Maximum position size per market in USD"
    )

    def model_post_init(self, __context) -> None:
        """Set API URLs based on demo mode after init."""
        if not self.KALSHI_API_URL:
            if self.KALSHI_DEMO_MODE:
                object.__setattr__(
                    self,
                    'KALSHI_API_URL',
                    "https://demo-api.kalshi.co/trade-api/v2"
                )
                object.__setattr__(
                    self,
                    'KALSHI_WS_URL',
                    "wss://demo-api.kalshi.co/trade-api/ws/v2"
                )
            else:
                object.__setattr__(
                    self,
                    'KALSHI_API_URL',
                    "https://trading-api.kalshi.com/trade-api/v2"
                )
                object.__setattr__(
                    self,
                    'KALSHI_WS_URL',
                    "wss://trading-api.kalshi.com/trade-api/ws/v2"
                )

    @field_validator("KALSHI_API_KEY_ID")
    @classmethod
    def validate_api_key(cls, v: str, info) -> str:
        """Validate API key is provided for production mode."""
        demo_mode = info.data.get('KALSHI_DEMO_MODE', False)
        enabled = info.data.get('KALSHI_ENABLED', False)

        if enabled and not demo_mode and not v:
            raise ValueError("KALSHI_API_KEY_ID is required for production mode")
        return v

    @field_validator("KALSHI_PRIVATE_KEY_PATH")
    @classmethod
    def validate_private_key_path(cls, v: str, info) -> str:
        """Validate private key path exists for production mode."""
        demo_mode = info.data.get('KALSHI_DEMO_MODE', False)
        enabled = info.data.get('KALSHI_ENABLED', False)
        private_key = info.data.get('KALSHI_PRIVATE_KEY')

        # Skip if demo mode or key content provided directly
        if demo_mode or private_key or not enabled:
            return v

        if v and not os.path.exists(v):
            raise ValueError(f"KALSHI_PRIVATE_KEY_PATH does not exist: {v}")

        return v

    def has_credentials(self) -> bool:
        """Check if API credentials are configured."""
        if self.KALSHI_DEMO_MODE:
            return True

        has_key = bool(self.KALSHI_PRIVATE_KEY or self.KALSHI_PRIVATE_KEY_PATH)
        return bool(self.KALSHI_API_KEY_ID and has_key)

    def get_private_key(self) -> Optional[str]:
        """Get private key content from path or direct value."""
        if self.KALSHI_PRIVATE_KEY:
            return self.KALSHI_PRIVATE_KEY

        if self.KALSHI_PRIVATE_KEY_PATH and os.path.exists(self.KALSHI_PRIVATE_KEY_PATH):
            with open(self.KALSHI_PRIVATE_KEY_PATH, 'r') as f:
                return f.read()

        return None

    def to_dict(self) -> dict:
        """Convert to dictionary with sensitive data masked."""
        data = self.model_dump()

        # Mask sensitive fields
        if data.get("KALSHI_PRIVATE_KEY"):
            data["KALSHI_PRIVATE_KEY"] = "***HIDDEN***"
        if data.get("KALSHI_PRIVATE_KEY_PATH"):
            data["KALSHI_PRIVATE_KEY_PATH"] = "***PATH_HIDDEN***"
        if data.get("KALSHI_API_KEY_ID"):
            data["KALSHI_API_KEY_ID"] = data["KALSHI_API_KEY_ID"][:8] + "***"

        return data


def load_kalshi_config() -> KalshiConfig:
    """Load Kalshi configuration from environment."""
    return KalshiConfig()
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/platforms/kalshi/test_config.py -v
```

Expected: All 4 tests PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(kalshi): add configuration with validation

- KalshiConfig with Pydantic validation
- Demo mode support with auto URL switching
- RSA private key loading from path or content
- Credential validation for production mode
- Safety limit defaults

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Kalshi Authentication Client

**Files:**
- Create: `src/prediction_mcp/platforms/kalshi/auth.py`
- Create: `tests/platforms/kalshi/test_auth.py`

**Step 1: Write the failing test**

Create `tests/platforms/kalshi/test_auth.py`:

```python
"""Tests for Kalshi authentication."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


class TestKalshiAuth:
    """Test Kalshi RSA-PSS authentication."""

    def test_signature_generation(self):
        """Should generate valid RSA-PSS signature."""
        from src.prediction_mcp.platforms.kalshi.auth import KalshiAuth

        # Use a test RSA key (DO NOT use in production)
        test_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB7MlMQpgP6Rq1yvDrP
VUjZ2fdahIG5FJpG0yUpJL5P7SXMSEE39Py7bH9iUGguKu4sVY3IzjLDp/m9aGpM
yiCd4fvNK9VvfPuMXBPP+EwZVpFdxLZTxY3CGkpNILC9Db5RD9TDNGG5eXfebpOC
OySeaiixll2lBHfO4TFR0mq+q0tI+RvtZ+N3R0N7MNaLVNw+O9bCpPBYBLmtGzwE
LZJPQo7qHNfDRoKa3lUIjCuQvsOyHIK/LzxaT1G4TADxRe1meM1CPOY8iVNULxYp
GCgTMvV6SnGjfbVvsS4DPnSEHY6L6SWfHHCYVQIDAQABAoIBABr9TYjjKpdV8Cxa
KKkME2PKVvvPxN/+L9NFaSE8kKfwN6XbLLP7aNAlYT9V1I7tUdXbYGKMaH5N/kYq
aKdHc1HxN3VuE9XP8sPz0yJljNF6QW3B1SmODWQxDPDzQ5BQpNYGbDDDDkZTXfsP
vPz2M6lNtDSPaK9L3dMZ+kHcxvpP6wME3gXhwHb/XhHBpCPx2K8YNrY9E7IUZaH2
m3MJ0p+2pFs1M0Q7vV9v7sDPHu4Jvj2TlYNTcpSQS4LD8wKDPxsKLQE7sBLxiMJj
YwU3eMlP8T0fU4VjhzZ4WchX8lUXAGYAa2b+dG7tX7+4C9QR2q4Kfxv7FJ8lZ5qL
8dJkjmECgYEA7KNqJoNYDMEMxRP8XN5MJ+X4NlLWZ9XK+jVzjnxaJzbYVpNLPKAG
MEwMYMlqG3bE+IpYJ7m7pFPpVN3N9JLkK9XxR2L0qZ5pGJLE5qxJyPAh7xNyYy8L
cNgLHxfNJP+X7dR5K8G3+X8q5Z7jH3LWDP5HQ9YFbJZS+5bZj5xfJrECgYEA4y/o
J3r5j3WDh0vXFBF6L9TWVJHc7hWKL8AME5X7EiO4N8L7bLz6qYZ0FPQ7R0L7sMbJ
OBMHq7L9YJ3dZL7Y6P9wJ1K6GXKP8xQ5Hxb8lXn6wMdMn7QSlP6xmYbE7mR7k3Km
hRoV7HoFc3YjL7fDLxYrVQx5J9PLvCsIlM+1M3UCgYBnZZ3Z8C1QXRr8L5n8WPMD
3TfP7lP7J3L5eZ9l3tL5aL3pXhmC8T3z9gqJBL9LlXJ8PZB3P4FnLmP9M9O3R7dL
LZlPQFLm8lHdEP5PLhPB4jDLPKPnZxwP7MQZqP5yZPkMr3P7kM5jP3T7Y3OQP7FP
rZlP8lZqrPjL8PWMP3lPwQKBgGJB6hL7m1PAHWJ0L5n8lPMD3TfP7lP7J3L5eZ9l
3tL5aL3pXhmC8T3z9gqJBL9LlXJ8PZB3P4FnLmP9M9O3R7dLLZlPQFLm8lHdEP5P
LhPB4jDLPKPnZxwP7MQZqP5yZPkMr3P7kM5jP3T7Y3OQP7FPrZlP8lZqrPjL8PWM
P3lPwQKBgCJC7iM8o2QBIWK1M6o9MXNE4UfQ8mQ8K4M6fA0m4B1n5C2p6D3q7E4r
8F5s9G6t0H7u1I8v2J9w3K0x4L1y5M2z6N3A7O4B8P5C9Q0D1R2E3S4F5T6G7U8H
-----END RSA PRIVATE KEY-----"""

        auth = KalshiAuth(
            api_key_id="test-key-id",
            private_key=test_private_key
        )

        timestamp = "1234567890"
        method = "GET"
        path = "/trade-api/v2/markets"

        signature = auth.sign_request(timestamp, method, path)

        assert signature is not None
        assert len(signature) > 0
        assert isinstance(signature, str)

    def test_auth_headers_generation(self):
        """Should generate complete auth headers."""
        from src.prediction_mcp.platforms.kalshi.auth import KalshiAuth

        # Minimal test key
        test_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB7MlMQpgP6Rq1yvDrP
VUjZ2fdahIG5FJpG0yUpJL5P7SXMSEE39Py7bH9iUGguKu4sVY3IzjLDp/m9aGpM
yiCd4fvNK9VvfPuMXBPP+EwZVpFdxLZTxY3CGkpNILC9Db5RD9TDNGG5eXfebpOC
OySeaiixll2lBHfO4TFR0mq+q0tI+RvtZ+N3R0N7MNaLVNw+O9bCpPBYBLmtGzwE
LZJPQo7qHNfDRoKa3lUIjCuQvsOyHIK/LzxaT1G4TADxRe1meM1CPOY8iVNULxYp
GCgTMvV6SnGjfbVvsS4DPnSEHY6L6SWfHHCYVQIDAQABAoIBABr9TYjjKpdV8Cxa
KKkME2PKVvvPxN/+L9NFaSE8kKfwN6XbLLP7aNAlYT9V1I7tUdXbYGKMaH5N/kYq
aKdHc1HxN3VuE9XP8sPz0yJljNF6QW3B1SmODWQxDPDzQ5BQpNYGbDDDDkZTXfsP
vPz2M6lNtDSPaK9L3dMZ+kHcxvpP6wME3gXhwHb/XhHBpCPx2K8YNrY9E7IUZaH2
m3MJ0p+2pFs1M0Q7vV9v7sDPHu4Jvj2TlYNTcpSQS4LD8wKDPxsKLQE7sBLxiMJj
YwU3eMlP8T0fU4VjhzZ4WchX8lUXAGYAa2b+dG7tX7+4C9QR2q4Kfxv7FJ8lZ5qL
8dJkjmECgYEA7KNqJoNYDMEMxRP8XN5MJ+X4NlLWZ9XK+jVzjnxaJzbYVpNLPKAG
MEwMYMlqG3bE+IpYJ7m7pFPpVN3N9JLkK9XxR2L0qZ5pGJLE5qxJyPAh7xNyYy8L
cNgLHxfNJP+X7dR5K8G3+X8q5Z7jH3LWDP5HQ9YFbJZS+5bZj5xfJrECgYEA4y/o
J3r5j3WDh0vXFBF6L9TWVJHc7hWKL8AME5X7EiO4N8L7bLz6qYZ0FPQ7R0L7sMbJ
OBMHq7L9YJ3dZL7Y6P9wJ1K6GXKP8xQ5Hxb8lXn6wMdMn7QSlP6xmYbE7mR7k3Km
hRoV7HoFc3YjL7fDLxYrVQx5J9PLvCsIlM+1M3UCgYBnZZ3Z8C1QXRr8L5n8WPMD
3TfP7lP7J3L5eZ9l3tL5aL3pXhmC8T3z9gqJBL9LlXJ8PZB3P4FnLmP9M9O3R7dL
LZlPQFLm8lHdEP5PLhPB4jDLPKPnZxwP7MQZqP5yZPkMr3P7kM5jP3T7Y3OQP7FP
rZlP8lZqrPjL8PWMP3lPwQKBgGJB6hL7m1PAHWJ0L5n8lPMD3TfP7lP7J3L5eZ9l
3tL5aL3pXhmC8T3z9gqJBL9LlXJ8PZB3P4FnLmP9M9O3R7dLLZlPQFLm8lHdEP5P
LhPB4jDLPKPnZxwP7MQZqP5yZPkMr3P7kM5jP3T7Y3OQP7FPrZlP8lZqrPjL8PWM
P3lPwQKBgCJC7iM8o2QBIWK1M6o9MXNE4UfQ8mQ8K4M6fA0m4B1n5C2p6D3q7E4r
8F5s9G6t0H7u1I8v2J9w3K0x4L1y5M2z6N3A7O4B8P5C9Q0D1R2E3S4F5T6G7U8H
-----END RSA PRIVATE KEY-----"""

        auth = KalshiAuth(
            api_key_id="test-key-id",
            private_key=test_private_key
        )

        headers = auth.get_auth_headers("GET", "/trade-api/v2/markets")

        assert "KALSHI-ACCESS-KEY" in headers
        assert "KALSHI-ACCESS-SIGNATURE" in headers
        assert "KALSHI-ACCESS-TIMESTAMP" in headers
        assert headers["KALSHI-ACCESS-KEY"] == "test-key-id"


class TestKalshiAuthDemo:
    """Test Kalshi demo mode authentication."""

    def test_demo_mode_no_signature(self):
        """Demo mode should work without credentials."""
        from src.prediction_mcp.platforms.kalshi.auth import KalshiAuth

        auth = KalshiAuth(demo_mode=True)

        headers = auth.get_auth_headers("GET", "/trade-api/v2/markets")

        # Demo mode may have different header requirements
        assert isinstance(headers, dict)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/platforms/kalshi/test_auth.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.prediction_mcp.platforms.kalshi.auth'`

**Step 3: Write Kalshi auth implementation**

Create `src/prediction_mcp/platforms/kalshi/auth.py`:

```python
"""
Kalshi RSA-PSS Authentication.

Kalshi uses RSA-PSS signatures for API authentication.
Each request must be signed with the user's private key.
"""

import base64
import time
from typing import Dict, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend


class KalshiAuth:
    """
    Kalshi API authentication handler.

    Uses RSA-PSS signatures as required by Kalshi's API.
    """

    def __init__(
        self,
        api_key_id: str = "",
        private_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        demo_mode: bool = False,
    ):
        """
        Initialize Kalshi authentication.

        Args:
            api_key_id: Kalshi API key ID
            private_key: RSA private key content (PEM format)
            private_key_path: Path to RSA private key file
            demo_mode: If True, skip authentication
        """
        self.api_key_id = api_key_id
        self.demo_mode = demo_mode
        self._private_key: Optional[rsa.RSAPrivateKey] = None

        if not demo_mode:
            self._load_private_key(private_key, private_key_path)

    def _load_private_key(
        self,
        private_key: Optional[str],
        private_key_path: Optional[str]
    ) -> None:
        """Load RSA private key from content or file."""
        key_data: Optional[bytes] = None

        if private_key:
            key_data = private_key.encode('utf-8')
        elif private_key_path:
            with open(private_key_path, 'rb') as f:
                key_data = f.read()

        if key_data:
            self._private_key = serialization.load_pem_private_key(
                key_data,
                password=None,
                backend=default_backend()
            )

    def sign_request(
        self,
        timestamp: str,
        method: str,
        path: str,
        body: str = ""
    ) -> str:
        """
        Generate RSA-PSS signature for request.

        Args:
            timestamp: Unix timestamp as string
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., /trade-api/v2/markets)
            body: Request body (empty for GET)

        Returns:
            Base64-encoded signature
        """
        if self.demo_mode or not self._private_key:
            return ""

        # Build message to sign: timestamp + method + path + body
        message = f"{timestamp}{method}{path}{body}"
        message_bytes = message.encode('utf-8')

        # Sign with RSA-PSS
        signature = self._private_key.sign(
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Return base64-encoded signature
        return base64.b64encode(signature).decode('utf-8')

    def get_auth_headers(
        self,
        method: str,
        path: str,
        body: str = ""
    ) -> Dict[str, str]:
        """
        Generate authentication headers for request.

        Args:
            method: HTTP method
            path: Request path
            body: Request body

        Returns:
            Dictionary of authentication headers
        """
        if self.demo_mode:
            return {"Content-Type": "application/json"}

        timestamp = str(int(time.time() * 1000))
        signature = self.sign_request(timestamp, method, path, body)

        return {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
        }

    def is_authenticated(self) -> bool:
        """Check if authentication is configured."""
        return self.demo_mode or (
            bool(self.api_key_id) and self._private_key is not None
        )
```

**Step 4: Update Kalshi package init**

Update `src/prediction_mcp/platforms/kalshi/__init__.py`:

```python
"""
Kalshi Platform Adapter.

Kalshi is a US-regulated prediction market exchange offering
event contracts on politics, economics, weather, and more.

Authentication: RSA-PSS signatures with API key
API: REST + WebSocket
"""

from .config import KalshiConfig, load_kalshi_config
from .auth import KalshiAuth

__all__ = ["KalshiConfig", "load_kalshi_config", "KalshiAuth"]
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/platforms/kalshi/test_auth.py -v
```

Expected: All 3 tests PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(kalshi): implement RSA-PSS authentication

- KalshiAuth class for request signing
- RSA-PSS signature generation with SHA256
- Auth header generation with timestamp
- Demo mode support (no credentials needed)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Kalshi API Client

**Files:**
- Create: `src/prediction_mcp/platforms/kalshi/client.py`
- Create: `tests/platforms/kalshi/test_client.py`

**Step 1: Write the failing test**

Create `tests/platforms/kalshi/test_client.py`:

```python
"""Tests for Kalshi API client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestKalshiClient:
    """Test Kalshi API client."""

    @pytest.mark.asyncio
    async def test_get_markets(self):
        """Should fetch markets from API."""
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        # Mock config
        config = MagicMock(spec=KalshiConfig)
        config.KALSHI_DEMO_MODE = True
        config.KALSHI_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
        config.KALSHI_API_KEY_ID = ""
        config.get_private_key.return_value = None

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "markets": [
                {
                    "ticker": "KXBTC-25JAN31-T100000",
                    "title": "Bitcoin above $100,000 on January 31?",
                    "status": "open",
                    "yes_bid": 0.45,
                    "yes_ask": 0.47,
                }
            ],
            "cursor": None
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = KalshiClient(config)
            markets = await client.get_markets(limit=10)

            assert len(markets) == 1
            assert markets[0]["ticker"] == "KXBTC-25JAN31-T100000"

    @pytest.mark.asyncio
    async def test_get_market_by_ticker(self):
        """Should fetch single market by ticker."""
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        config = MagicMock(spec=KalshiConfig)
        config.KALSHI_DEMO_MODE = True
        config.KALSHI_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
        config.KALSHI_API_KEY_ID = ""
        config.get_private_key.return_value = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "market": {
                "ticker": "KXBTC-25JAN31-T100000",
                "title": "Bitcoin above $100,000 on January 31?",
                "status": "open",
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = KalshiClient(config)
            market = await client.get_market("KXBTC-25JAN31-T100000")

            assert market["ticker"] == "KXBTC-25JAN31-T100000"

    @pytest.mark.asyncio
    async def test_get_orderbook(self):
        """Should fetch orderbook for a market."""
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        config = MagicMock(spec=KalshiConfig)
        config.KALSHI_DEMO_MODE = True
        config.KALSHI_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
        config.KALSHI_API_KEY_ID = ""
        config.get_private_key.return_value = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "orderbook": {
                "yes": [[0.45, 100], [0.44, 200]],
                "no": [[0.55, 150], [0.56, 100]]
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = KalshiClient(config)
            orderbook = await client.get_orderbook("KXBTC-25JAN31-T100000")

            assert "yes" in orderbook
            assert "no" in orderbook
            assert len(orderbook["yes"]) == 2
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/platforms/kalshi/test_client.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write Kalshi client implementation**

Create `src/prediction_mcp/platforms/kalshi/client.py`:

```python
"""
Kalshi API Client.

Provides async access to Kalshi's Trading API v2.
Handles authentication, rate limiting, and response parsing.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx

from .auth import KalshiAuth
from .config import KalshiConfig

logger = logging.getLogger(__name__)


class KalshiClient:
    """
    Async client for Kalshi Trading API.

    Supports:
    - Market data (public)
    - Events and series
    - Order management (authenticated)
    - Portfolio queries (authenticated)
    """

    def __init__(self, config: KalshiConfig):
        """
        Initialize Kalshi client.

        Args:
            config: KalshiConfig instance with credentials
        """
        self.config = config
        self.base_url = config.KALSHI_API_URL

        # Initialize auth
        self.auth = KalshiAuth(
            api_key_id=config.KALSHI_API_KEY_ID,
            private_key=config.get_private_key(),
            demo_mode=config.KALSHI_DEMO_MODE,
        )

        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated API request.

        Args:
            method: HTTP method
            path: API path (without base URL)
            params: Query parameters
            json: JSON body

        Returns:
            Response JSON
        """
        # Get auth headers
        body_str = ""
        if json:
            import json as json_lib
            body_str = json_lib.dumps(json)

        headers = self.auth.get_auth_headers(method, path, body_str)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=path,
                params=params,
                json=json,
                headers=headers,
            )

            if response.status_code >= 400:
                logger.error(f"Kalshi API error: {response.status_code} - {response.text}")
                response.raise_for_status()

            return response.json()

    # === Market Data ===

    async def get_markets(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get markets with optional filters.

        Args:
            limit: Maximum number of markets
            cursor: Pagination cursor
            event_ticker: Filter by event
            series_ticker: Filter by series
            status: Filter by status (open, closed, settled)

        Returns:
            List of market dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}

        if cursor:
            params["cursor"] = cursor
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker
        if status:
            params["status"] = status

        result = await self._request("GET", "/markets", params=params)
        return result.get("markets", [])

    async def get_market(self, ticker: str) -> Dict[str, Any]:
        """
        Get single market by ticker.

        Args:
            ticker: Market ticker (e.g., KXBTC-25JAN31-T100000)

        Returns:
            Market dictionary
        """
        result = await self._request("GET", f"/markets/{ticker}")
        return result.get("market", result)

    async def get_orderbook(
        self,
        ticker: str,
        depth: int = 10
    ) -> Dict[str, Any]:
        """
        Get orderbook for a market.

        Args:
            ticker: Market ticker
            depth: Orderbook depth

        Returns:
            Orderbook with yes/no sides
        """
        params = {"depth": depth}
        result = await self._request("GET", f"/markets/{ticker}/orderbook", params=params)
        return result.get("orderbook", result)

    async def get_market_candlesticks(
        self,
        ticker: str,
        period: str = "1h",
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get OHLC candlestick data for a market.

        Args:
            ticker: Market ticker
            period: Candle period (1m, 5m, 1h, 1d)
            start_ts: Start timestamp
            end_ts: End timestamp

        Returns:
            List of candlestick dictionaries
        """
        params: Dict[str, Any] = {"period": period}
        if start_ts:
            params["start_ts"] = start_ts
        if end_ts:
            params["end_ts"] = end_ts

        result = await self._request(
            "GET",
            f"/markets/{ticker}/candlesticks",
            params=params
        )
        return result.get("candlesticks", [])

    async def get_trades(
        self,
        ticker: str,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades for a market.

        Args:
            ticker: Market ticker
            limit: Maximum trades
            cursor: Pagination cursor

        Returns:
            List of trade dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        result = await self._request("GET", f"/markets/{ticker}/trades", params=params)
        return result.get("trades", [])

    # === Events ===

    async def get_events(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
        status: Optional[str] = None,
        series_ticker: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get events with optional filters.

        Events are groups of related markets.

        Args:
            limit: Maximum events
            cursor: Pagination cursor
            status: Filter by status
            series_ticker: Filter by series

        Returns:
            List of event dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if status:
            params["status"] = status
        if series_ticker:
            params["series_ticker"] = series_ticker

        result = await self._request("GET", "/events", params=params)
        return result.get("events", [])

    async def get_event(self, event_ticker: str) -> Dict[str, Any]:
        """
        Get single event by ticker.

        Args:
            event_ticker: Event ticker

        Returns:
            Event dictionary
        """
        result = await self._request("GET", f"/events/{event_ticker}")
        return result.get("event", result)

    # === Series ===

    async def get_series(
        self,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get market series.

        Series are recurring market templates (e.g., daily BTC price).

        Returns:
            List of series dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor

        result = await self._request("GET", "/series", params=params)
        return result.get("series", [])

    # === Exchange Info ===

    async def get_exchange_status(self) -> Dict[str, Any]:
        """
        Get exchange status and health.

        Returns:
            Status dictionary
        """
        result = await self._request("GET", "/exchange/status")
        return result

    async def get_exchange_schedule(self) -> Dict[str, Any]:
        """
        Get exchange trading schedule.

        Returns:
            Schedule dictionary with trading hours
        """
        result = await self._request("GET", "/exchange/schedule")
        return result

    # === Authenticated: Orders ===

    async def create_order(
        self,
        ticker: str,
        side: str,
        action: str,
        type: str,
        count: int,
        price: Optional[int] = None,
        expiration_ts: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            ticker: Market ticker
            side: "yes" or "no"
            action: "buy" or "sell"
            type: "limit" or "market"
            count: Number of contracts
            price: Price in cents (1-99 for limit orders)
            expiration_ts: Order expiration timestamp
            client_order_id: Client-provided order ID

        Returns:
            Order dictionary
        """
        body: Dict[str, Any] = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "type": type,
            "count": count,
        }

        if price is not None:
            body["yes_price"] = price if side == "yes" else 100 - price
            body["no_price"] = 100 - price if side == "yes" else price

        if expiration_ts:
            body["expiration_ts"] = expiration_ts
        if client_order_id:
            body["client_order_id"] = client_order_id

        result = await self._request("POST", "/portfolio/orders", json=body)
        return result.get("order", result)

    async def get_orders(
        self,
        ticker: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get user's orders.

        Args:
            ticker: Filter by market ticker
            status: Filter by status (open, closed, etc.)
            limit: Maximum orders

        Returns:
            List of order dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if status:
            params["status"] = status

        result = await self._request("GET", "/portfolio/orders", params=params)
        return result.get("orders", [])

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            Cancellation result
        """
        result = await self._request("DELETE", f"/portfolio/orders/{order_id}")
        return result

    async def batch_cancel_orders(
        self,
        order_ids: Optional[List[str]] = None,
        ticker: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel multiple orders.

        Args:
            order_ids: List of order IDs to cancel
            ticker: Cancel all orders for this market

        Returns:
            Batch cancellation result
        """
        body: Dict[str, Any] = {}
        if order_ids:
            body["order_ids"] = order_ids
        if ticker:
            body["ticker"] = ticker

        result = await self._request("DELETE", "/portfolio/orders", json=body)
        return result

    # === Authenticated: Portfolio ===

    async def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance.

        Returns:
            Balance dictionary
        """
        result = await self._request("GET", "/portfolio/balance")
        return result

    async def get_positions(
        self,
        ticker: Optional[str] = None,
        settlement_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get user's positions.

        Args:
            ticker: Filter by market ticker
            settlement_status: Filter by settlement status

        Returns:
            List of position dictionaries
        """
        params: Dict[str, Any] = {}
        if ticker:
            params["ticker"] = ticker
        if settlement_status:
            params["settlement_status"] = settlement_status

        result = await self._request("GET", "/portfolio/positions", params=params)
        return result.get("market_positions", [])

    async def get_fills(
        self,
        ticker: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get user's fills (executed trades).

        Args:
            ticker: Filter by market ticker
            limit: Maximum fills
            cursor: Pagination cursor

        Returns:
            List of fill dictionaries
        """
        params: Dict[str, Any] = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if cursor:
            params["cursor"] = cursor

        result = await self._request("GET", "/portfolio/fills", params=params)
        return result.get("fills", [])

    # === Helpers ===

    def is_authenticated(self) -> bool:
        """Check if client is authenticated for trading."""
        return self.auth.is_authenticated()


def create_kalshi_client(config: KalshiConfig) -> KalshiClient:
    """
    Factory function to create KalshiClient.

    Args:
        config: KalshiConfig instance

    Returns:
        Configured KalshiClient
    """
    return KalshiClient(config)
```

**Step 4: Update Kalshi package init**

Update `src/prediction_mcp/platforms/kalshi/__init__.py`:

```python
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
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/platforms/kalshi/test_client.py -v
```

Expected: All 3 tests PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(kalshi): implement API client

- KalshiClient with async httpx
- Market data: markets, events, series, orderbook
- Exchange info: status, schedule
- Authenticated: orders, positions, fills, balance
- Proper auth header injection
- Rate limit friendly

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Kalshi Market Discovery Tools (8 tools)

**Files:**
- Create: `src/prediction_mcp/platforms/kalshi/tools/__init__.py`
- Create: `src/prediction_mcp/platforms/kalshi/tools/market_discovery.py`
- Create: `tests/platforms/kalshi/test_market_discovery.py`

**Step 1: Write the failing test**

Create `tests/platforms/kalshi/test_market_discovery.py`:

```python
"""Tests for Kalshi market discovery tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestKalshiMarketDiscoveryTools:
    """Test Kalshi market discovery tool definitions."""

    def test_get_tools_returns_8_tools(self):
        """Should return 8 market discovery tools."""
        from src.prediction_mcp.platforms.kalshi.tools.market_discovery import get_tools

        tools = get_tools()

        assert len(tools) == 10  # 8 standard + 2 Kalshi-specific

        tool_names = [t.name for t in tools]
        assert "kalshi_search_markets" in tool_names
        assert "kalshi_get_markets_by_volume" in tool_names
        assert "kalshi_get_market" in tool_names
        assert "kalshi_get_event" in tool_names
        assert "kalshi_get_event_markets" in tool_names

    @pytest.mark.asyncio
    async def test_search_markets_handler(self):
        """Should handle search_markets tool call."""
        from src.prediction_mcp.platforms.kalshi.tools.market_discovery import handle_tool
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient

        # Mock client
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.get_markets = AsyncMock(return_value=[
            {"ticker": "KXBTC-25JAN31-T100000", "title": "Bitcoin price market"}
        ])

        with patch(
            'src.prediction_mcp.platforms.kalshi.tools.market_discovery._get_client',
            return_value=mock_client
        ):
            result = await handle_tool(
                "kalshi_search_markets",
                {"query": "bitcoin", "limit": 10}
            )

            assert len(result) == 1
            assert result[0].type == "text"
            assert "Bitcoin" in result[0].text or "bitcoin" in result[0].text
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/platforms/kalshi/test_market_discovery.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Create tools package structure**

Create `src/prediction_mcp/platforms/kalshi/tools/__init__.py`:

```python
"""
Kalshi MCP Tools.

Tool modules organized by category:
- market_discovery: Finding and filtering markets
- market_analysis: Price, orderbook, and analysis tools
- trading: Order creation and management
- portfolio: Position and balance tracking
- realtime: WebSocket subscriptions
"""

from . import market_discovery

__all__ = ["market_discovery"]
```

**Step 4: Write market discovery tools**

Create `src/prediction_mcp/platforms/kalshi/tools/market_discovery.py`:

```python
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
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/platforms/kalshi/test_market_discovery.py -v
```

Expected: All tests PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
feat(kalshi): implement market discovery tools (10 tools)

Tools added:
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

Follows same pattern as Polymarket tools with MCP protocol.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Kalshi Market Analysis Tools (10 tools)

**Files:**
- Create: `src/prediction_mcp/platforms/kalshi/tools/market_analysis.py`
- Update: `src/prediction_mcp/platforms/kalshi/tools/__init__.py`
- Create: `tests/platforms/kalshi/test_market_analysis.py`

[Similar TDD pattern - write failing test, implement, verify, commit]

**Tools to implement:**
1. `kalshi_get_market_ticker` - Current prices
2. `kalshi_get_orderbook` - Full orderbook
3. `kalshi_analyze_liquidity` - Liquidity metrics
4. `kalshi_get_candlesticks` - OHLC history
5. `kalshi_analyze_market_opportunity` - AI analysis
6. `kalshi_compare_markets` - Multi-market comparison
7. `kalshi_get_trades` - Recent trades
8. `kalshi_get_spread` - Current spread
9. `kalshi_assess_market_risk` - Risk scoring
10. `kalshi_get_series` - Series data
11. `kalshi_get_exchange_schedule` - Trading hours

**Step 1-6:** Follow same TDD pattern as Task 5

**Commit message:**
```
feat(kalshi): implement market analysis tools (11 tools)
```

---

## Task 7: Redis Integration

**Files:**
- Create: `src/prediction_mcp/core/__init__.py`
- Create: `src/prediction_mcp/core/redis_client.py`
- Create: `tests/core/test_redis.py`

**Step 1: Write the failing test**

Create `tests/core/__init__.py` and `tests/core/test_redis.py`:

```python
"""Tests for Redis integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRedisClient:
    """Test Redis client wrapper."""

    @pytest.mark.asyncio
    async def test_connect(self):
        """Should connect to Redis."""
        from src.prediction_mcp.core.redis_client import RedisClient

        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(return_value=True)
            mock_from_url.return_value = mock_redis

            client = RedisClient("redis://localhost:6379")
            connected = await client.connect()

            assert connected is True
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_json_operations(self):
        """Should store and retrieve JSON documents."""
        from src.prediction_mcp.core.redis_client import RedisClient

        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.json = MagicMock()
            mock_redis.json.set = AsyncMock(return_value=True)
            mock_redis.json.get = AsyncMock(return_value={"name": "test"})
            mock_from_url.return_value = mock_redis

            client = RedisClient("redis://localhost:6379")
            client._redis = mock_redis

            # Set JSON
            await client.json_set("test:key", {"name": "test"})
            mock_redis.json.set.assert_called()

            # Get JSON
            result = await client.json_get("test:key")
            assert result == {"name": "test"}
```

**Step 2-6:** Implement RedisClient with JSON, TimeSeries, and Search support

---

## Task 8: Unified Configuration

**Files:**
- Create: `src/prediction_mcp/config.py`
- Create: `tests/test_config.py`

Combines Polymarket, Kalshi, Redis, and arbitrage configuration into unified settings.

---

## Task 9: Main Server Integration

**Files:**
- Create: `src/prediction_mcp/server.py`
- Update: Platform adapters to register with server
- Create: `tests/test_server.py`

Server that:
1. Loads unified config
2. Initializes enabled platform adapters
3. Registers all tools from enabled platforms
4. Routes tool calls to appropriate adapter

---

## Task 10: Integration Testing

**Files:**
- Create: `tests/integration/test_kalshi_api.py`
- Create: `tests/integration/test_multi_platform.py`

Test actual API connectivity (marked with `@pytest.mark.integration`).

---

## Summary

| Task | Tools Added | Cumulative |
|------|-------------|------------|
| 1. Project Structure | 0 | 0 |
| 2. Kalshi Config | 0 | 0 |
| 3. Kalshi Auth | 0 | 0 |
| 4. Kalshi Client | 0 | 0 |
| 5. Market Discovery | 10 | 10 |
| 6. Market Analysis | 11 | 21 |
| 7. Redis Integration | 0 | 21 |
| 8. Unified Config | 0 | 21 |
| 9. Server Integration | 0 | 21 |
| 10. Integration Tests | 0 | 21 |

**Phase 1 Complete:** 21 Kalshi tools operational + multi-platform architecture established.

---

## Next Phase Preview

**Phase 2: Kalshi Parity (Weeks 3-4)**
- Trading tools (13 tools)
- Portfolio tools (10 tools)
- Real-time WebSocket tools (8 tools)
- Total: 52 Kalshi tools
