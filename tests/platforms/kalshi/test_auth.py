"""Tests for Kalshi authentication."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime


@pytest.fixture
def test_private_key():
    """Generate a valid RSA private key for testing."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    return pem.decode('utf-8')


class TestKalshiAuth:
    """Test Kalshi RSA-PSS authentication."""

    def test_signature_generation(self, test_private_key):
        """Should generate valid RSA-PSS signature."""
        from src.prediction_mcp.platforms.kalshi.auth import KalshiAuth

        auth = KalshiAuth(
            api_key_id="test-key-id",
            private_key=test_private_key
        )

        timestamp = "1234567890"
        method = "GET"
        path = "/trade-api/v2/markets"

        signature = auth.sign_request(timestamp, method, path)

        assert signature is not None
        assert len(signature) > 0
        assert isinstance(signature, str)

    def test_auth_headers_generation(self, test_private_key):
        """Should generate complete auth headers."""
        from src.prediction_mcp.platforms.kalshi.auth import KalshiAuth

        auth = KalshiAuth(
            api_key_id="test-key-id",
            private_key=test_private_key
        )

        headers = auth.get_auth_headers("GET", "/trade-api/v2/markets")

        assert "KALSHI-ACCESS-KEY" in headers
        assert "KALSHI-ACCESS-SIGNATURE" in headers
        assert "KALSHI-ACCESS-TIMESTAMP" in headers
        assert headers["KALSHI-ACCESS-KEY"] == "test-key-id"


class TestKalshiAuthDemo:
    """Test Kalshi demo mode authentication."""

    def test_demo_mode_no_signature(self):
        """Demo mode should work without credentials."""
        from src.prediction_mcp.platforms.kalshi.auth import KalshiAuth

        auth = KalshiAuth(demo_mode=True)

        headers = auth.get_auth_headers("GET", "/trade-api/v2/markets")

        # Demo mode may have different header requirements
        assert isinstance(headers, dict)
