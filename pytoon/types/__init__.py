"""Type system module for pluggable type handlers.

This module provides extensible type handling for PyToon, enabling encoding
and decoding of custom types (UUID, datetime, bytes, Enum, etc.) beyond
the primitive types supported by TOON format.

Key Components:
    - TypeHandler: Protocol defining the interface for custom type handlers
    - TypeRegistry: Registry for managing and dispatching to type handlers
"""

from pytoon.types.protocol import TypeHandler
from pytoon.types.registry import TypeRegistry

__all__ = [
    "TypeHandler",
    "TypeRegistry",
]
