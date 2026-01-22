"""Quick validation script for .env configuration."""
import asyncio
import sys
from pathlib import Path

async def validate():
    try:
        # Load config
        from src.prediction_mcp.core.config import UnifiedConfig
        config = UnifiedConfig()

        print("[OK] Config loaded successfully")
        print(f"  - Kalshi enabled: {config.KALSHI_ENABLED}")
        print(f"  - Demo mode: {config.KALSHI_DEMO_MODE}")
        print(f"  - Email: {config.KALSHI_EMAIL}")
        print(f"  - API key ID: {config.KALSHI_API_KEY_ID[:8]}...")

        # Check private key
        if config.KALSHI_PRIVATE_KEY_PATH:
            key_path = Path(config.KALSHI_PRIVATE_KEY_PATH)
            if key_path.exists():
                print(f"[OK] Private key file found: {key_path.name}")
                # Try to read it
                key_content = key_path.read_text()
                if "BEGIN RSA PRIVATE KEY" in key_content or "BEGIN PRIVATE KEY" in key_content:
                    print("[OK] Private key format looks valid")
                else:
                    print("[WARN] Private key format may be invalid")
            else:
                print(f"[FAIL] Private key file NOT found at: {config.KALSHI_PRIVATE_KEY_PATH}")
                return False

        # Try to initialize Kalshi client
        from src.prediction_mcp.platforms.kalshi.config import KalshiConfig
        from src.prediction_mcp.platforms.kalshi.client import KalshiClient

        kalshi_config = KalshiConfig(
            KALSHI_ENABLED=config.KALSHI_ENABLED,
            KALSHI_DEMO_MODE=config.KALSHI_DEMO_MODE,
            KALSHI_EMAIL=config.KALSHI_EMAIL,
            KALSHI_API_KEY_ID=config.KALSHI_API_KEY_ID,
            KALSHI_PRIVATE_KEY_PATH=config.KALSHI_PRIVATE_KEY_PATH,
            KALSHI_PRIVATE_KEY=config.KALSHI_PRIVATE_KEY,
        )

        print("[OK] Kalshi config created")
        print(f"  - API URL: {kalshi_config.KALSHI_API_URL}")

        # Initialize client and test connection
        client = KalshiClient(kalshi_config)
        print("[OK] Kalshi client initialized")

        # Try a simple API call
        print("\nTesting API connection...")
        markets = await client.get_markets(limit=1)

        if markets:
            print(f"[OK] API call successful! Found {len(markets)} market(s)")
            print(f"  Sample: {markets[0].get('ticker', 'N/A')}")
        else:
            print("[WARN] API call returned no markets")

        await client.close()

        print("\n[SUCCESS] All validation checks passed!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(validate())
    sys.exit(0 if success else 1)
