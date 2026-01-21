"""Tests for Kalshi API client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


class TestKalshiClient:
    """Test Kalshi API client."""

    @pytest.mark.asyncio
    async def test_get_markets(self):
        """Should fetch markets from API."""
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        # Mock config
        config = MagicMock(spec=KalshiConfig)
        config.KALSHI_DEMO_MODE = True
        config.KALSHI_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
        config.KALSHI_API_KEY_ID = ""
        config.get_private_key.return_value = None

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "markets": [
                {
                    "ticker": "KXBTC-25JAN31-T100000",
                    "title": "Bitcoin above $100,000 on January 31?",
                    "status": "open",
                    "yes_bid": 0.45,
                    "yes_ask": 0.47,
                }
            ],
            "cursor": None
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = KalshiClient(config)
            markets = await client.get_markets(limit=10)

            assert len(markets) == 1
            assert markets[0]["ticker"] == "KXBTC-25JAN31-T100000"

    @pytest.mark.asyncio
    async def test_get_market_by_ticker(self):
        """Should fetch single market by ticker."""
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        config = MagicMock(spec=KalshiConfig)
        config.KALSHI_DEMO_MODE = True
        config.KALSHI_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
        config.KALSHI_API_KEY_ID = ""
        config.get_private_key.return_value = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "market": {
                "ticker": "KXBTC-25JAN31-T100000",
                "title": "Bitcoin above $100,000 on January 31?",
                "status": "open",
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = KalshiClient(config)
            market = await client.get_market("KXBTC-25JAN31-T100000")

            assert market["ticker"] == "KXBTC-25JAN31-T100000"

    @pytest.mark.asyncio
    async def test_get_orderbook(self):
        """Should fetch orderbook for a market."""
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig

        config = MagicMock(spec=KalshiConfig)
        config.KALSHI_DEMO_MODE = True
        config.KALSHI_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
        config.KALSHI_API_KEY_ID = ""
        config.get_private_key.return_value = None

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "orderbook": {
                "yes": [[0.45, 100], [0.44, 200]],
                "no": [[0.55, 150], [0.56, 100]]
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            client = KalshiClient(config)
            orderbook = await client.get_orderbook("KXBTC-25JAN31-T100000")

            assert "yes" in orderbook
            assert "no" in orderbook
            assert len(orderbook["yes"]) == 2
