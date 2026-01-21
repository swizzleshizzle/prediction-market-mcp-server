"""Tests for main MCP server."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestPredictionMCPServer:
    """Test main MCP server."""

    def test_server_initialization(self):
        """Should initialize server with configuration."""
        from src.prediction_mcp.server import PredictionMCPServer
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict('os.environ', {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = UnifiedConfig()
            server = PredictionMCPServer(config)

            assert server is not None
            assert server.config is config

    def test_get_tools_includes_kalshi(self):
        """Should include Kalshi tools when enabled."""
        from src.prediction_mcp.server import PredictionMCPServer
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict('os.environ', {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = UnifiedConfig()
            server = PredictionMCPServer(config)
            tools = server.get_tools()

            tool_names = [t.name for t in tools]
            assert any("kalshi" in name for name in tool_names)

    def test_get_tools_count_kalshi_only(self):
        """Should return expected tool count with Kalshi only."""
        from src.prediction_mcp.server import PredictionMCPServer
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict('os.environ', {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
            "POLYMARKET_ENABLED": "false",
        }, clear=True):
            config = UnifiedConfig()
            server = PredictionMCPServer(config)
            tools = server.get_tools()

            # 10 discovery + 11 analysis = 21 Kalshi tools
            kalshi_tools = [t for t in tools if "kalshi" in t.name]
            assert len(kalshi_tools) >= 21


class TestServerMain:
    """Test server main entry point."""

    def test_main_exists(self):
        """Should have main entry point."""
        from src.prediction_mcp.server import main

        assert callable(main)
