"""TypeRegistry for managing custom type handlers.

This module provides the TypeRegistry class that manages registration and
lookup of type handlers for encoding and decoding custom types.
"""

from __future__ import annotations

from typing import Any

from pytoon.types.protocol import TypeHandler


class TypeRegistry:
    """Registry for managing custom type handlers.

    TypeRegistry maintains a list of type handlers and provides methods to
    encode and decode values using registered handlers. User-registered
    handlers have priority over built-in handlers.

    Attributes:
        _handlers: Private list of registered type handler classes.

    Examples:
        >>> registry = TypeRegistry()
        >>> class IntDoubler:
        ...     @staticmethod
        ...     def can_handle(obj: Any) -> bool:
        ...         return isinstance(obj, int)
        ...
        ...     @staticmethod
        ...     def encode(obj: int) -> str:
        ...         return f"doubled:{obj * 2}"
        ...
        ...     @staticmethod
        ...     def decode(s: str, type_hint: type[int] | None = None) -> int:
        ...         if s.startswith("doubled:"):
        ...             return int(s[8:]) // 2
        ...         raise ValueError("Invalid format")
        >>> registry.register(IntDoubler)
        >>> registry.encode_value(10)
        'doubled:20'
        >>> registry.decode_value("doubled:20", int)
        10
    """

    def __init__(self) -> None:
        """Initialize empty TypeRegistry."""
        self._handlers: list[type[TypeHandler[Any]]] = []

    def register(self, handler: type[TypeHandler[Any]]) -> None:
        """Register a type handler with highest priority.

        User handlers are prepended to the handlers list, giving them
        priority over previously registered and built-in handlers.

        Args:
            handler: Type handler class implementing TypeHandler protocol.

        Examples:
            >>> registry = TypeRegistry()
            >>> class MyHandler:
            ...     @staticmethod
            ...     def can_handle(obj: Any) -> bool:
            ...         return False
            ...     @staticmethod
            ...     def encode(obj: Any) -> str:
            ...         return ""
            ...     @staticmethod
            ...     def decode(s: str, type_hint: type | None = None) -> Any:
            ...         return None
            >>> registry.register(MyHandler)
            >>> len(registry._handlers)
            1
        """
        self._handlers.insert(0, handler)

    def encode_value(self, obj: Any) -> str | None:
        """Encode a value using the first matching handler.

        Iterates through registered handlers in priority order (user handlers
        first) and returns the encoded string from the first handler that
        can process the object.

        Args:
            obj: Python object to encode.

        Returns:
            Encoded string if a matching handler is found, None otherwise.

        Examples:
            >>> registry = TypeRegistry()
            >>> registry.encode_value("test")  # No handlers registered
            >>> class StringHandler:
            ...     @staticmethod
            ...     def can_handle(obj: Any) -> bool:
            ...         return isinstance(obj, str)
            ...     @staticmethod
            ...     def encode(obj: str) -> str:
            ...         return f"str:{obj}"
            ...     @staticmethod
            ...     def decode(s: str, type_hint: type | None = None) -> str:
            ...         return s[4:]
            >>> registry.register(StringHandler)
            >>> registry.encode_value("hello")
            'str:hello'
            >>> registry.encode_value(42)  # No handler for int
        """
        for handler in self._handlers:
            if handler.can_handle(obj):
                return handler.encode(obj)
        return None

    def decode_value(self, s: str, type_hint: type[Any] | None = None) -> Any | None:
        """Decode a string using registered handlers.

        Attempts to decode the string using each registered handler in
        priority order. Returns the decoded value from the first successful
        handler.

        Args:
            s: String to decode.
            type_hint: Optional type hint for disambiguation.

        Returns:
            Decoded value if a matching handler succeeds, None otherwise.

        Note:
            If decoding fails (raises exception), the handler is skipped
            and the next handler is tried.

        Examples:
            >>> registry = TypeRegistry()
            >>> registry.decode_value("str:hello")  # No handlers registered
            >>> class StringHandler:
            ...     @staticmethod
            ...     def can_handle(obj: Any) -> bool:
            ...         return isinstance(obj, str)
            ...     @staticmethod
            ...     def encode(obj: str) -> str:
            ...         return f"str:{obj}"
            ...     @staticmethod
            ...     def decode(s: str, type_hint: type | None = None) -> str:
            ...         if s.startswith("str:"):
            ...             return s[4:]
            ...         raise ValueError("Invalid format")
            >>> registry.register(StringHandler)
            >>> registry.decode_value("str:hello")
            'hello'
            >>> registry.decode_value("unknown:data")  # Handler raises, returns None
        """
        for handler in self._handlers:
            try:
                return handler.decode(s, type_hint)
            except (ValueError, TypeError, KeyError):
                # Handler couldn't decode this string, try next
                continue
        return None
