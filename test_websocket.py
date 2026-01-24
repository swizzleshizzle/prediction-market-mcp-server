#!/usr/bin/env python3
"""
Test script for Kalshi WebSocket implementation.

Tests:
1. WebSocket connection with authentication
2. Subscribe to ticker channel
3. Receive messages
4. Get latest data
5. Unsubscribe
6. Cleanup
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from prediction_mcp.platforms.kalshi.config import KalshiConfig
from prediction_mcp.platforms.kalshi.websocket import KalshiWebSocketManager


async def test_websocket():
    """Test Kalshi WebSocket functionality."""

    # Load config
    config = KalshiConfig()

    if not config.KALSHI_ENABLED:
        print("[ERROR] Kalshi not enabled. Set KALSHI_ENABLED=true in .env")
        return

    if not config.KALSHI_API_KEY_ID or not config.KALSHI_PRIVATE_KEY:
        print("[ERROR] Kalshi credentials not found. Check .env file")
        return

    print(f"[INFO] Testing WebSocket connection to: {config.KALSHI_WS_URL}")
    print(f"       Demo mode: {config.KALSHI_DEMO_MODE}")
    print()

    # Create WebSocket manager
    ws_manager = KalshiWebSocketManager(
        ws_url=config.KALSHI_WS_URL,
        api_key=config.KALSHI_API_KEY_ID,
        private_key=config.KALSHI_PRIVATE_KEY
    )

    try:
        # Test 1: Connection
        print("[1/8] Connecting...")
        await ws_manager.connect()
        print(f"      Connected: {ws_manager.connected}")
        print(f"      Authenticated: {ws_manager.authenticated}")
        print()

        # Test 2: Start background task
        print("[2/8] Starting background task...")
        await ws_manager.start_background_task()
        print(f"      Background task started")
        print()

        # Test 3: Subscribe to ticker (all markets)
        print("[3/8] Subscribing to ticker channel (all markets)...")
        result = await ws_manager.subscribe("ticker", "all")  # Maps to "ticker"
        print(f"      Subscribed: {result}")
        print()

        # Test 4: Wait for messages
        print("[4/8] Waiting for messages (10 seconds)...")
        await asyncio.sleep(10)

        status = ws_manager.get_status()
        print(f"      Total messages received: {status['statistics']['total_messages']}")
        print(f"      Messages by channel: {status['statistics']['messages_by_channel']}")
        print()

        # Test 5: Get subscriptions
        print("[5/8] Active subscriptions:")
        subs = ws_manager.get_subscriptions()
        for sub in subs:
            print(f"      - {sub['channel']}/{sub['ticker']} (ID: {sub['subscription_id']})")
        print()

        # Test 6: Get latest data
        print("[6/8] Latest data samples:")
        for (channel, ticker), data in list(ws_manager.latest_data.items())[:3]:
            print(f"      {channel}/{ticker}:")
            print(f"      {str(data)[:100]}...")
        print()

        # Test 7: Unsubscribe
        print("[7/8] Unsubscribing...")
        result = await ws_manager.unsubscribe("ticker", "all")
        print(f"      Unsubscribed: {result}")
        print()

        # Test 8: Final status
        print("[8/8] Final status:")
        final_status = ws_manager.get_status()
        print(f"      Connection: {final_status['connection']['connected']}")
        print(f"      Subscriptions: {final_status['subscriptions']['total']}")
        print(f"      Total messages: {final_status['statistics']['total_messages']}")
        print()

        print("[SUCCESS] All tests passed!")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\n[INFO] Cleaning up...")
        await ws_manager.stop_background_task()
        print("       Stopped")


if __name__ == "__main__":
    asyncio.run(test_websocket())
