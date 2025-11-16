"""Type system module for pluggable type handlers.

This module provides extensible type handling for PyToon, enabling encoding
and decoding of custom types (UUID, datetime, bytes, Enum, etc.) beyond
the primitive types supported by TOON format.

Key Components:
    - TypeHandler: Protocol defining the interface for custom type handlers
    - TypeRegistry: Registry for managing and dispatching to type handlers
    - get_type_registry: Get the global type registry instance
    - register_type_handler: Register a custom type handler globally
"""

from typing import Any

from pytoon.types.handlers import register_builtin_handlers
from pytoon.types.protocol import TypeHandler
from pytoon.types.registry import TypeRegistry

# Global registry instance with built-in handlers
_global_registry = TypeRegistry()
register_builtin_handlers(_global_registry)


def get_type_registry() -> TypeRegistry:
    """Get the global type registry.

    Returns the singleton TypeRegistry instance that contains all registered
    type handlers, including built-in handlers for UUID, datetime, bytes, etc.

    Returns:
        The global TypeRegistry instance.

    Examples:
        >>> registry = get_type_registry()
        >>> isinstance(registry, TypeRegistry)
        True
        >>> import uuid
        >>> u = uuid.uuid4()
        >>> registry.encode_value(u)  # doctest: +SKIP
        'uuid:...'
    """
    return _global_registry


def register_type_handler(handler: type[TypeHandler[Any]]) -> None:
    """Register a custom type handler globally.

    Registers a type handler with the global registry. User-registered
    handlers have priority over built-in handlers.

    Args:
        handler: Type handler class implementing the TypeHandler protocol.
            Must have can_handle, encode, and decode static methods.

    Examples:
        >>> class CustomHandler:
        ...     @staticmethod
        ...     def can_handle(obj: Any) -> bool:
        ...         return isinstance(obj, tuple) and len(obj) == 2
        ...     @staticmethod
        ...     def encode(obj: tuple[Any, Any]) -> str:
        ...         return f"pair:{obj[0]},{obj[1]}"
        ...     @staticmethod
        ...     def decode(s: str, type_hint: type | None = None) -> tuple[Any, Any]:
        ...         if not s.startswith("pair:"):
        ...             raise ValueError("Invalid pair format")
        ...         parts = s[5:].split(",", 1)
        ...         return (parts[0], parts[1])
        >>> register_type_handler(CustomHandler)  # doctest: +SKIP

    Note:
        Handlers registered later have higher priority and are checked first.
    """
    _global_registry.register(handler)


__all__ = [
    "TypeHandler",
    "TypeRegistry",
    "get_type_registry",
    "register_type_handler",
]
