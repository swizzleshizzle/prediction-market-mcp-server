"""Tests for Kalshi real-time tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestKalshiRealtimeTools:
    def test_get_tools_returns_8_tools(self):
        from src.prediction_mcp.platforms.kalshi.tools.realtime import get_tools
        assert len(get_tools()) == 8

    @pytest.mark.asyncio
    async def test_subscribe_ticker(self):
        from src.prediction_mcp.platforms.kalshi.tools.realtime import handle_tool, set_ws_manager
        mock_ws = MagicMock()
        mock_ws.subscribe = AsyncMock(return_value={"subscribed": True})
        set_ws_manager(mock_ws)
        result = await handle_tool("kalshi_subscribe_ticker", {"ticker": "KXTEST"})
        assert "subscribed" in result[0].text.lower()
