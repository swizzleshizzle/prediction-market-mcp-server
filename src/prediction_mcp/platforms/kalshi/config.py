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
                    "https://api.elections.kalshi.com/trade-api/v2"
                )
                object.__setattr__(
                    self,
                    'KALSHI_WS_URL',
                    "wss://api.elections.kalshi.com/trade-api/ws/v2"
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
