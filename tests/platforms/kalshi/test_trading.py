"""Tests for Kalshi trading tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestKalshiTradingTools:
    def test_get_tools_returns_13_tools(self):
        from src.prediction_mcp.platforms.kalshi.tools.trading import get_tools
        tools = get_tools()
        assert len(tools) == 13

    @pytest.mark.asyncio
    async def test_create_order_handler(self):
        from src.prediction_mcp.platforms.kalshi.tools.trading import handle_tool, set_client

        mock_client = MagicMock()
        mock_client.create_order = AsyncMock(return_value={
            "order_id": "test-123", "status": "open"
        })
        set_client(mock_client)

        result = await handle_tool("kalshi_create_order", {
            "ticker": "KXTEST", "side": "yes", "action": "buy", "count": 10
        })
        assert "test-123" in result[0].text
