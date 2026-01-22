"""
Multi-Platform Prediction Market MCP Server.

Main entry point that aggregates platform adapters and tools.
Supports Polymarket and Kalshi with unified interface.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .core.config import UnifiedConfig, load_config
from .platforms.kalshi.config import KalshiConfig
from .platforms.kalshi.client import KalshiClient
from .platforms.kalshi.tools import market_discovery as kalshi_discovery
from .platforms.kalshi.tools import market_analysis as kalshi_analysis
from .platforms.kalshi.tools import trading as kalshi_trading
from .platforms.kalshi.tools import portfolio as kalshi_portfolio
from .platforms.kalshi.tools import realtime as kalshi_realtime

logger = logging.getLogger(__name__)


class PredictionMCPServer:
    """
    Multi-platform prediction market MCP server.

    Aggregates tools from enabled platforms and provides
    unified tool handling.
    """

    def __init__(self, config: Optional[UnifiedConfig] = None):
        """
        Initialize server with configuration.

        Args:
            config: UnifiedConfig instance (loads from env if None)
        """
        self.config = config or load_config()
        self._kalshi_client: Optional[KalshiClient] = None
        self._tools_cache: Optional[List[types.Tool]] = None

        # Initialize platform clients
        self._init_platforms()

    def _init_platforms(self) -> None:
        """Initialize enabled platform clients."""
        if self.config.KALSHI_ENABLED:
            self._init_kalshi()

    def _init_kalshi(self) -> None:
        """Initialize Kalshi client and tools."""
        kalshi_config = KalshiConfig(
            KALSHI_ENABLED=self.config.KALSHI_ENABLED,
            KALSHI_DEMO_MODE=self.config.KALSHI_DEMO_MODE,
            KALSHI_EMAIL=self.config.KALSHI_EMAIL,
            KALSHI_API_KEY_ID=self.config.KALSHI_API_KEY_ID,
            KALSHI_PRIVATE_KEY_PATH=self.config.KALSHI_PRIVATE_KEY_PATH,
            KALSHI_PRIVATE_KEY=self.config.KALSHI_PRIVATE_KEY,
        )

        self._kalshi_client = KalshiClient(kalshi_config)

        # Set client for tool modules
        kalshi_discovery.set_client(self._kalshi_client)
        kalshi_analysis.set_client(self._kalshi_client)
        kalshi_trading.set_client(self._kalshi_client)
        kalshi_portfolio.set_client(self._kalshi_client)

        logger.info("Kalshi platform initialized")

    def get_tools(self) -> List[types.Tool]:
        """
        Get all available tools from enabled platforms.

        Returns:
            List of MCP tool definitions
        """
        if self._tools_cache is not None:
            return self._tools_cache

        tools: List[types.Tool] = []

        # Add Kalshi tools
        if self.config.KALSHI_ENABLED:
            tools.extend(kalshi_discovery.get_tools())
            tools.extend(kalshi_analysis.get_tools())
            tools.extend(kalshi_trading.get_tools())
            tools.extend(kalshi_portfolio.get_tools())
            tools.extend(kalshi_realtime.get_tools())

        # TODO: Add Polymarket tools when platform adapter is complete
        # if self.config.POLYMARKET_ENABLED:
        #     tools.extend(polymarket_tools.get_tools())

        self._tools_cache = tools
        logger.info(f"Loaded {len(tools)} tools from enabled platforms")

        return tools

    async def handle_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """
        Handle tool execution.

        Routes tool calls to appropriate platform handlers.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            List of TextContent with results
        """
        # Route Kalshi tools
        if name.startswith("kalshi_"):
            if name in [t.name for t in kalshi_discovery.get_tools()]:
                return await kalshi_discovery.handle_tool(name, arguments)
            elif name in [t.name for t in kalshi_analysis.get_tools()]:
                return await kalshi_analysis.handle_tool(name, arguments)
            elif name in [t.name for t in kalshi_trading.get_tools()]:
                return await kalshi_trading.handle_tool(name, arguments)
            elif name in [t.name for t in kalshi_portfolio.get_tools()]:
                return await kalshi_portfolio.handle_tool(name, arguments)
            elif name in [t.name for t in kalshi_realtime.get_tools()]:
                return await kalshi_realtime.handle_tool(name, arguments)

        # TODO: Route Polymarket tools
        # if name.startswith("polymarket_"):
        #     return await polymarket_tools.handle_tool(name, arguments)

        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

    async def close(self) -> None:
        """Cleanup resources."""
        if self._kalshi_client:
            await self._kalshi_client.close()


async def serve(config: Optional[UnifiedConfig] = None) -> None:
    """
    Run the MCP server.

    Args:
        config: Optional configuration (loads from env if None)
    """
    # Create server instance
    prediction_server = PredictionMCPServer(config)

    # Create MCP server
    server = Server("prediction-mcp")

    @server.list_tools()
    async def list_tools() -> List[types.Tool]:
        """List available tools."""
        return prediction_server.get_tools()

    @server.call_tool()
    async def call_tool(
        name: str,
        arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        """Execute a tool."""
        return await prediction_server.handle_tool(name, arguments)

    # Run server
    logger.info("Starting Prediction Market MCP Server")
    logger.info(f"Enabled platforms: {prediction_server.config.get_enabled_platforms()}")
    logger.info(f"Available tools: {len(prediction_server.get_tools())}")

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    finally:
        await prediction_server.close()


def main() -> None:
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run server
    asyncio.run(serve())


if __name__ == "__main__":
    main()
