"""TypeHandler protocol for pluggable type extensions.

This module defines the TypeHandler protocol that all custom type handlers
must implement to integrate with PyToon's type system.
"""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class TypeHandler(Protocol[T]):
    """Protocol for custom type handlers in PyToon.

    Type handlers enable encoding and decoding of custom types (UUID, datetime,
    bytes, etc.) that are not natively supported by TOON format.

    Each handler must implement three static methods:
        - can_handle: Check if this handler can process a given object
        - encode: Convert the object to a TOON-compatible string with type prefix
        - decode: Parse the string back to the original type

    Examples:
        >>> class UUIDHandler:
        ...     @staticmethod
        ...     def can_handle(obj: Any) -> bool:
        ...         import uuid
        ...         return isinstance(obj, uuid.UUID)
        ...
        ...     @staticmethod
        ...     def encode(obj: uuid.UUID) -> str:
        ...         return f"uuid:{obj}"
        ...
        ...     @staticmethod
        ...     def decode(s: str, type_hint: type[uuid.UUID] | None = None) -> uuid.UUID:
        ...         import uuid
        ...         if s.startswith("uuid:"):
        ...             return uuid.UUID(s[5:])
        ...         raise ValueError(f"Invalid UUID format: {s}")
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if this handler can process the given object.

        Args:
            obj: Any Python object to check.

        Returns:
            True if this handler can encode the object, False otherwise.
        """
        ...

    @staticmethod
    def encode(obj: T) -> str:
        """Encode object to TOON-compatible string with type prefix.

        Args:
            obj: Object of type T to encode.

        Returns:
            String representation with type prefix (e.g., "uuid:...", "date:...").

        Raises:
            ValueError: If object cannot be encoded by this handler.
        """
        ...

    @staticmethod
    def decode(s: str, type_hint: type[T] | None = None) -> T:
        """Decode string back to object of type T.

        Args:
            s: String to decode, typically with type prefix.
            type_hint: Optional type hint for disambiguation.

        Returns:
            Reconstructed object of type T.

        Raises:
            ValueError: If string cannot be decoded by this handler.
        """
        ...
