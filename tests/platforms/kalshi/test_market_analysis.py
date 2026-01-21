"""Tests for Kalshi market analysis tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestKalshiMarketAnalysisTools:
    """Test Kalshi market analysis tool definitions."""

    def test_get_tools_returns_11_tools(self):
        """Should return 11 market analysis tools."""
        from src.prediction_mcp.platforms.kalshi.tools.market_analysis import get_tools

        tools = get_tools()

        assert len(tools) == 11

        tool_names = [t.name for t in tools]
        assert "kalshi_get_market_ticker" in tool_names
        assert "kalshi_get_orderbook" in tool_names
        assert "kalshi_analyze_liquidity" in tool_names
        assert "kalshi_get_candlesticks" in tool_names
        assert "kalshi_get_trades" in tool_names
        assert "kalshi_get_spread" in tool_names
        assert "kalshi_get_series" in tool_names
        assert "kalshi_get_exchange_schedule" in tool_names

    @pytest.mark.asyncio
    async def test_get_orderbook_handler(self):
        """Should handle get_orderbook tool call."""
        from src.prediction_mcp.platforms.kalshi.tools.market_analysis import handle_tool, set_client
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient

        mock_client = MagicMock(spec=KalshiClient)
        mock_client.get_orderbook = AsyncMock(return_value={
            "yes": [[45, 100], [44, 200]],
            "no": [[55, 150], [56, 100]]
        })

        set_client(mock_client)

        result = await handle_tool(
            "kalshi_get_orderbook",
            {"ticker": "KXBTC-25JAN31-T100000"}
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "yes" in result[0].text

    @pytest.mark.asyncio
    async def test_get_spread_handler(self):
        """Should handle get_spread tool call."""
        from src.prediction_mcp.platforms.kalshi.tools.market_analysis import handle_tool, set_client
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient

        mock_client = MagicMock(spec=KalshiClient)
        mock_client.get_market = AsyncMock(return_value={
            "ticker": "KXBTC-25JAN31-T100000",
            "yes_bid": 45,
            "yes_ask": 47,
            "no_bid": 53,
            "no_ask": 55
        })

        set_client(mock_client)

        result = await handle_tool(
            "kalshi_get_spread",
            {"ticker": "KXBTC-25JAN31-T100000"}
        )

        assert len(result) == 1
        assert result[0].type == "text"
        assert "spread" in result[0].text.lower()
