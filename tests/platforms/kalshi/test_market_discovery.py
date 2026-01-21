"""Tests for Kalshi market discovery tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestKalshiMarketDiscoveryTools:
    """Test Kalshi market discovery tool definitions."""

    def test_get_tools_returns_10_tools(self):
        """Should return 10 market discovery tools."""
        from src.prediction_mcp.platforms.kalshi.tools.market_discovery import get_tools

        tools = get_tools()

        assert len(tools) == 10

        tool_names = [t.name for t in tools]
        assert "kalshi_search_markets" in tool_names
        assert "kalshi_get_markets_by_volume" in tool_names
        assert "kalshi_get_market" in tool_names
        assert "kalshi_get_event" in tool_names
        assert "kalshi_get_event_markets" in tool_names

    @pytest.mark.asyncio
    async def test_search_markets_handler(self):
        """Should handle search_markets tool call."""
        from src.prediction_mcp.platforms.kalshi.tools.market_discovery import handle_tool, set_client
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient

        # Mock client
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.get_markets = AsyncMock(return_value=[
            {"ticker": "KXBTC-25JAN31-T100000", "title": "Bitcoin price market"}
        ])

        set_client(mock_client)

        result = await handle_tool(
            "kalshi_search_markets",
            {"query": "bitcoin", "limit": 10}
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "Bitcoin" in result[0].text or "bitcoin" in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_get_market_handler(self):
        """Should handle get_market tool call."""
        from src.prediction_mcp.platforms.kalshi.tools.market_discovery import handle_tool, set_client
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient

        mock_client = MagicMock(spec=KalshiClient)
        mock_client.get_market = AsyncMock(return_value={
            "ticker": "KXBTC-25JAN31-T100000",
            "title": "Bitcoin above $100,000?",
            "status": "open"
        })

        set_client(mock_client)

        result = await handle_tool(
            "kalshi_get_market",
            {"ticker": "KXBTC-25JAN31-T100000"}
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "KXBTC-25JAN31-T100000" in result[0].text
