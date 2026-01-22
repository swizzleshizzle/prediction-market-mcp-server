"""Integration tests for Kalshi platform."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestKalshiIntegration:
    """End-to-end tests for Kalshi integration."""

    @pytest.mark.asyncio
    async def test_server_tool_execution_flow(self):
        """Test complete tool execution through server."""
        from src.prediction_mcp.server import PredictionMCPServer
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict('os.environ', {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = UnifiedConfig()
            server = PredictionMCPServer(config)

            # Mock the client's get_markets method
            server._kalshi_client.get_markets = AsyncMock(return_value=[
                {"ticker": "TEST-MARKET", "title": "Test Market"}
            ])

            result = await server.handle_tool(
                "kalshi_search_markets",
                {"query": "test", "limit": 5}
            )

            assert len(result) == 1
            assert "TEST-MARKET" in result[0].text

    @pytest.mark.asyncio
    async def test_server_startup_with_kalshi(self):
        """Test server initializes Kalshi correctly."""
        from src.prediction_mcp.server import PredictionMCPServer
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict('os.environ', {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = UnifiedConfig()
            server = PredictionMCPServer(config)

            assert server._kalshi_client is not None
            assert len(server.get_tools()) == 21

            await server.close()

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test graceful error handling in tools."""
        from src.prediction_mcp.server import PredictionMCPServer
        from src.prediction_mcp.core.config import UnifiedConfig

        with patch.dict('os.environ', {
            "KALSHI_ENABLED": "true",
            "KALSHI_DEMO_MODE": "true",
        }, clear=True):
            config = UnifiedConfig()
            server = PredictionMCPServer(config)

            # Mock to raise error
            server._kalshi_client.get_market = AsyncMock(
                side_effect=Exception("API Error")
            )

            result = await server.handle_tool(
                "kalshi_get_market",
                {"ticker": "INVALID"}
            )

            assert "error" in result[0].text.lower()
