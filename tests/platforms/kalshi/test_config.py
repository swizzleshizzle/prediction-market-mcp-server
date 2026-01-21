"""Tests for Kalshi configuration."""

import os
import pytest
from unittest.mock import patch


class TestKalshiConfig:
    """Test Kalshi configuration loading and validation."""

    def test_config_loads_from_env(self):
        """Config should load from environment variables."""
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        # Use demo mode to avoid file path validation
        with patch.dict(os.environ, {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
            "KALSHI_EMAIL": "test@example.com",
            "KALSHI_API_KEY_ID": "key123",
        }, clear=True):
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

        # Production mode - use KALSHI_PRIVATE_KEY (content) to avoid path validation
        with patch.dict(os.environ, {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "false",
            "KALSHI_EMAIL": "test@example.com",
            "KALSHI_API_KEY_ID": "key123",
            "KALSHI_PRIVATE_KEY": "test-key-content",
        }, clear=True):
            config = KalshiConfig()
            assert "trading-api.kalshi.com" in config.KALSHI_API_URL
