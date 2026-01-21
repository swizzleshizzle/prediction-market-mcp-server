"""Tests for unified configuration."""

import os
import pytest
from unittest.mock import patch


class TestUnifiedConfig:
    """Test unified configuration."""

    def test_loads_from_env(self):
        """Should load configuration from environment."""
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict(os.environ, {
            "POLYMARKET_ENABLED": "true",
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
            "REDIS_URL": "redis://localhost:6379",
        }, clear=True):
            config = UnifiedConfig()

            assert config.POLYMARKET_ENABLED is True
            assert config.KALSHI_ENABLED is True
            assert config.REDIS_URL == "redis://localhost:6379"

    def test_get_enabled_platforms(self):
        """Should return list of enabled platforms."""
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict(os.environ, {
            "POLYMARKET_ENABLED": "true",
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = UnifiedConfig()
            platforms = config.get_enabled_platforms()

            assert "polymarket" in platforms
            assert "kalshi" in platforms

    def test_kalshi_only(self):
        """Should work with only Kalshi enabled."""
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict(os.environ, {
            "POLYMARKET_ENABLED": "false",
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = UnifiedConfig()
            platforms = config.get_enabled_platforms()

            assert "kalshi" in platforms
            assert "polymarket" not in platforms

    def test_safety_limits(self):
        """Should have global safety limits."""
        from src.prediction_mcp.core.config import UnifiedConfig

        config = UnifiedConfig()

        assert hasattr(config, "MAX_ORDER_SIZE_USD")
        assert hasattr(config, "MAX_POSITION_SIZE_USD")
        assert config.MAX_ORDER_SIZE_USD > 0
        assert config.MAX_POSITION_SIZE_USD > 0


class TestLoadConfig:
    """Test config loading function."""

    def test_load_config_returns_unified_config(self):
        """Should return UnifiedConfig instance."""
        from src.prediction_mcp.core.config import load_config

        config = load_config()

        assert config is not None
        assert hasattr(config, "get_enabled_platforms")
