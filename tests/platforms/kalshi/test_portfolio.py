"""Tests for Kalshi portfolio tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestKalshiPortfolioTools:
    def test_get_tools_returns_10_tools(self):
        from src.prediction_mcp.platforms.kalshi.tools.portfolio import get_tools
        assert len(get_tools()) == 10

    @pytest.mark.asyncio
    async def test_get_balance(self):
        from src.prediction_mcp.platforms.kalshi.tools.portfolio import handle_tool, set_client
        mock_client = MagicMock()
        mock_client.get_balance = AsyncMock(return_value={"balance": 10000})
        set_client(mock_client)
        result = await handle_tool("kalshi_get_balance", {})
        assert "10000" in result[0].text
