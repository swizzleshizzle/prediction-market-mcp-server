"""
Kalshi RSA-PSS Authentication.

Kalshi uses RSA-PSS signatures for API authentication.
Each request must be signed with the user's private key.
"""

import base64
import time
from typing import Dict, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend


class KalshiAuth:
    """
    Kalshi API authentication handler.

    Uses RSA-PSS signatures as required by Kalshi's API.
    """

    def __init__(
        self,
        api_key_id: str = "",
        private_key: Optional[str] = None,
        private_key_path: Optional[str] = None,
        demo_mode: bool = False,
    ):
        """
        Initialize Kalshi authentication.

        Args:
            api_key_id: Kalshi API key ID
            private_key: RSA private key content (PEM format)
            private_key_path: Path to RSA private key file
            demo_mode: If True, skip authentication
        """
        self.api_key_id = api_key_id
        self.demo_mode = demo_mode
        self._private_key: Optional[rsa.RSAPrivateKey] = None

        if not demo_mode:
            self._load_private_key(private_key, private_key_path)

    def _load_private_key(
        self,
        private_key: Optional[str],
        private_key_path: Optional[str]
    ) -> None:
        """Load RSA private key from content or file."""
        key_data: Optional[bytes] = None

        if private_key:
            key_data = private_key.encode('utf-8')
        elif private_key_path:
            with open(private_key_path, 'rb') as f:
                key_data = f.read()

        if key_data:
            self._private_key = serialization.load_pem_private_key(
                key_data,
                password=None,
                backend=default_backend()
            )

    def sign_request(
        self,
        timestamp: str,
        method: str,
        path: str,
        body: str = ""
    ) -> str:
        """
        Generate RSA-PSS signature for request.

        Args:
            timestamp: Unix timestamp as string
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., /trade-api/v2/markets)
            body: Request body (empty for GET)

        Returns:
            Base64-encoded signature
        """
        if self.demo_mode or not self._private_key:
            return ""

        # Build message to sign: timestamp + method + path + body
        message = f"{timestamp}{method}{path}{body}"
        message_bytes = message.encode('utf-8')

        # Sign with RSA-PSS
        signature = self._private_key.sign(
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Return base64-encoded signature
        return base64.b64encode(signature).decode('utf-8')

    def get_auth_headers(
        self,
        method: str,
        path: str,
        body: str = ""
    ) -> Dict[str, str]:
        """
        Generate authentication headers for request.

        Args:
            method: HTTP method
            path: Request path
            body: Request body

        Returns:
            Dictionary of authentication headers
        """
        if self.demo_mode:
            return {"Content-Type": "application/json"}

        timestamp = str(int(time.time() * 1000))
        signature = self.sign_request(timestamp, method, path, body)

        return {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
        }

    def is_authenticated(self) -> bool:
        """Check if authentication is configured."""
        return self.demo_mode or (
            bool(self.api_key_id) and self._private_key is not None
        )
