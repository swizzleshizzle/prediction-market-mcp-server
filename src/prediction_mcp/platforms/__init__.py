"""
Platform adapters for prediction market exchanges.

Each platform module provides:
- Client: API communication
- Config: Platform-specific settings
- Tools: MCP tool definitions and handlers
"""

from typing import Dict, Type
from .base import PlatformAdapter

# Registry populated by platform modules
_adapters: Dict[str, Type[PlatformAdapter]] = {}


def register_adapter(name: str, adapter_class: Type[PlatformAdapter]) -> None:
    """Register a platform adapter."""
    _adapters[name] = adapter_class


def get_adapter(name: str) -> Type[PlatformAdapter]:
    """Get adapter class by platform name."""
    if name not in _adapters:
        raise KeyError(f"Unknown platform: {name}. Available: {list(_adapters.keys())}")
    return _adapters[name]


def list_adapters() -> list[str]:
    """List registered platform names."""
    return list(_adapters.keys())


__all__ = ["PlatformAdapter", "register_adapter", "get_adapter", "list_adapters"]
