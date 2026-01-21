"""
Unified Configuration for Multi-Platform Prediction Market MCP Server.

Combines platform-specific configs and provides global settings.
"""

import logging
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class UnifiedConfig(BaseSettings):
    """
    Unified configuration for all prediction market platforms.

    Loads from environment variables and .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # === Platform Enablement ===

    POLYMARKET_ENABLED: bool = Field(
        default=False,
        description="Enable Polymarket platform"
    )

    KALSHI_ENABLED: bool = Field(
        default=False,
        description="Enable Kalshi platform"
    )

    # === Kalshi Settings ===

    KALSHI_DEMO_MODE: bool = Field(
        default=False,
        description="Use Kalshi demo environment"
    )

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
        description="Path to Kalshi RSA private key"
    )

    KALSHI_PRIVATE_KEY: Optional[str] = Field(
        default=None,
        description="Kalshi RSA private key content"
    )

    # === Polymarket Settings ===

    POLYGON_PRIVATE_KEY: str = Field(
        default="",
        description="Polygon wallet private key"
    )

    POLYGON_ADDRESS: str = Field(
        default="",
        description="Polygon wallet address"
    )

    POLYMARKET_CHAIN_ID: int = Field(
        default=137,
        description="Polygon chain ID (137 for mainnet)"
    )

    # === Redis Settings ===

    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )

    REDIS_DB: int = Field(
        default=0,
        description="Redis database number"
    )

    REDIS_ENABLED: bool = Field(
        default=False,
        description="Enable Redis caching"
    )

    # === Global Safety Limits ===

    MAX_ORDER_SIZE_USD: float = Field(
        default=1000.0,
        description="Maximum order size in USD (global)"
    )

    MAX_POSITION_SIZE_USD: float = Field(
        default=5000.0,
        description="Maximum position size per market in USD (global)"
    )

    MAX_DAILY_VOLUME_USD: float = Field(
        default=10000.0,
        description="Maximum daily trading volume in USD"
    )

    # === Server Settings ===

    SERVER_HOST: str = Field(
        default="127.0.0.1",
        description="Server bind host"
    )

    SERVER_PORT: int = Field(
        default=8000,
        description="Server bind port"
    )

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )

    # === Methods ===

    def get_enabled_platforms(self) -> List[str]:
        """Get list of enabled platform names."""
        platforms = []

        if self.POLYMARKET_ENABLED:
            platforms.append("polymarket")

        if self.KALSHI_ENABLED:
            platforms.append("kalshi")

        return platforms

    def has_polymarket_credentials(self) -> bool:
        """Check if Polymarket credentials are configured."""
        return bool(self.POLYGON_PRIVATE_KEY and self.POLYGON_ADDRESS)

    def has_kalshi_credentials(self) -> bool:
        """Check if Kalshi credentials are configured."""
        if self.KALSHI_DEMO_MODE:
            return True

        has_key = bool(self.KALSHI_PRIVATE_KEY or self.KALSHI_PRIVATE_KEY_PATH)
        return bool(self.KALSHI_API_KEY_ID and has_key)

    def to_dict(self, mask_secrets: bool = True) -> dict:
        """
        Convert to dictionary.

        Args:
            mask_secrets: Whether to mask sensitive values

        Returns:
            Configuration dictionary
        """
        data = self.model_dump()

        if mask_secrets:
            # Mask sensitive fields
            secret_fields = [
                "POLYGON_PRIVATE_KEY",
                "KALSHI_PRIVATE_KEY",
                "KALSHI_PRIVATE_KEY_PATH",
                "KALSHI_API_KEY_ID",
            ]
            for field in secret_fields:
                if data.get(field):
                    data[field] = "***HIDDEN***"

        return data


def load_config() -> UnifiedConfig:
    """
    Load unified configuration from environment.

    Returns:
        UnifiedConfig instance
    """
    config = UnifiedConfig()
    logger.info(f"Loaded config with platforms: {config.get_enabled_platforms()}")
    return config


# Singleton instance (lazy loaded)
_config: Optional[UnifiedConfig] = None


def get_config() -> UnifiedConfig:
    """
    Get singleton config instance.

    Returns:
        UnifiedConfig instance
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset singleton config (for testing)."""
    global _config
    _config = None
