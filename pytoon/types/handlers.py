"""Built-in type handlers for PyToon.

This module provides type handlers for common Python types that are not
natively supported by TOON format. Each handler implements the TypeHandler
protocol with can_handle, encode, and decode methods.

Supported Types:
    - UUID: Universal Unique Identifier
    - datetime: Date and time with timezone
    - date: Calendar date
    - time: Time of day
    - timedelta: Duration between times
    - bytes: Binary data (base64 encoded)
    - Enum: Enumeration members
    - Decimal: Arbitrary precision decimal numbers
    - complex: Complex numbers
    - Path: Filesystem paths
    - set: Unordered unique collections
    - frozenset: Immutable unordered unique collections
"""

from __future__ import annotations

import base64
import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path, PurePath
from typing import Any


class UUIDHandler:
    """Handler for UUID objects.

    Format: uuid:<uuid-string>
    Example: uuid:550e8400-e29b-41d4-a716-446655440000
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a UUID instance."""
        return isinstance(obj, uuid.UUID)

    @staticmethod
    def encode(obj: uuid.UUID) -> str:
        """Encode UUID to string with prefix."""
        return f"uuid:{obj}"

    @staticmethod
    def decode(s: str, type_hint: type[uuid.UUID] | None = None) -> uuid.UUID:
        """Decode string to UUID."""
        if not s.startswith("uuid:"):
            raise ValueError(f"Invalid UUID format: {s}")
        return uuid.UUID(s[5:])


class DatetimeHandler:
    """Handler for datetime objects.

    Format: datetime:<ISO8601>
    Example: datetime:2024-01-15T10:30:45.123456+00:00
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a datetime instance (not date)."""
        return isinstance(obj, datetime) and not isinstance(obj, date) or (
            isinstance(obj, datetime) and type(obj) is datetime
        )

    @staticmethod
    def encode(obj: datetime) -> str:
        """Encode datetime to ISO8601 string with prefix."""
        return f"datetime:{obj.isoformat()}"

    @staticmethod
    def decode(s: str, type_hint: type[datetime] | None = None) -> datetime:
        """Decode string to datetime."""
        if not s.startswith("datetime:"):
            raise ValueError(f"Invalid datetime format: {s}")
        iso_str = s[9:]
        return datetime.fromisoformat(iso_str)


class DateHandler:
    """Handler for date objects.

    Format: date:<YYYY-MM-DD>
    Example: date:2024-01-15
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a date instance (not datetime)."""
        return type(obj) is date

    @staticmethod
    def encode(obj: date) -> str:
        """Encode date to ISO format string with prefix."""
        return f"date:{obj.isoformat()}"

    @staticmethod
    def decode(s: str, type_hint: type[date] | None = None) -> date:
        """Decode string to date."""
        if not s.startswith("date:"):
            raise ValueError(f"Invalid date format: {s}")
        return date.fromisoformat(s[5:])


class TimeHandler:
    """Handler for time objects.

    Format: time:<HH:MM:SS.microseconds>
    Example: time:10:30:45.123456
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a time instance."""
        return isinstance(obj, time)

    @staticmethod
    def encode(obj: time) -> str:
        """Encode time to ISO format string with prefix."""
        return f"time:{obj.isoformat()}"

    @staticmethod
    def decode(s: str, type_hint: type[time] | None = None) -> time:
        """Decode string to time."""
        if not s.startswith("time:"):
            raise ValueError(f"Invalid time format: {s}")
        return time.fromisoformat(s[5:])


class TimedeltaHandler:
    """Handler for timedelta objects.

    Format: timedelta:<total_seconds>
    Example: timedelta:86400.5 (1 day and 0.5 seconds)
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a timedelta instance."""
        return isinstance(obj, timedelta)

    @staticmethod
    def encode(obj: timedelta) -> str:
        """Encode timedelta to total seconds string with prefix."""
        return f"timedelta:{obj.total_seconds()}"

    @staticmethod
    def decode(s: str, type_hint: type[timedelta] | None = None) -> timedelta:
        """Decode string to timedelta."""
        if not s.startswith("timedelta:"):
            raise ValueError(f"Invalid timedelta format: {s}")
        seconds = float(s[10:])
        return timedelta(seconds=seconds)


class BytesHandler:
    """Handler for bytes objects.

    Format: bytes:<base64-encoded>
    Example: bytes:SGVsbG8gV29ybGQ=
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a bytes instance."""
        return isinstance(obj, bytes)

    @staticmethod
    def encode(obj: bytes) -> str:
        """Encode bytes to base64 string with prefix."""
        encoded = base64.b64encode(obj).decode("ascii")
        return f"bytes:{encoded}"

    @staticmethod
    def decode(s: str, type_hint: type[bytes] | None = None) -> bytes:
        """Decode string to bytes."""
        if not s.startswith("bytes:"):
            raise ValueError(f"Invalid bytes format: {s}")
        return base64.b64decode(s[6:])


class EnumHandler:
    """Handler for Enum members.

    Format: enum:<EnumClass>.<member_name>
    Example: enum:Color.RED

    Note: Decoding requires the type_hint parameter to resolve the Enum class.
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is an Enum member."""
        return isinstance(obj, Enum)

    @staticmethod
    def encode(obj: Enum) -> str:
        """Encode Enum member to string with prefix."""
        class_name = type(obj).__name__
        return f"enum:{class_name}.{obj.name}"

    @staticmethod
    def decode(s: str, type_hint: type[Enum] | None = None) -> Enum:
        """Decode string to Enum member.

        Requires type_hint to be the Enum class.

        Args:
            s: String in format "enum:ClassName.MEMBER"
            type_hint: The Enum class to use for reconstruction.

        Returns:
            Enum member.

        Raises:
            ValueError: If format is invalid or type_hint is missing.
        """
        if not s.startswith("enum:"):
            raise ValueError(f"Invalid enum format: {s}")
        if type_hint is None:
            raise ValueError("type_hint is required for Enum decoding")

        parts = s[5:].split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid enum format: {s}")

        class_name, member_name = parts

        # Verify class name matches (optional but recommended)
        if type_hint.__name__ != class_name:
            raise ValueError(
                f"Enum class mismatch: expected {type_hint.__name__}, got {class_name}"
            )

        return type_hint[member_name]


class DecimalHandler:
    """Handler for Decimal objects.

    Format: decimal:<decimal-string>
    Example: decimal:123.456789012345678901234567890
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a Decimal instance."""
        return isinstance(obj, Decimal)

    @staticmethod
    def encode(obj: Decimal) -> str:
        """Encode Decimal to string with prefix."""
        return f"decimal:{obj}"

    @staticmethod
    def decode(s: str, type_hint: type[Decimal] | None = None) -> Decimal:
        """Decode string to Decimal."""
        if not s.startswith("decimal:"):
            raise ValueError(f"Invalid decimal format: {s}")
        try:
            return Decimal(s[8:])
        except InvalidOperation as e:
            raise ValueError(f"Invalid decimal value: {s[8:]}") from e


class ComplexHandler:
    """Handler for complex numbers.

    Format: complex:<real>,<imag>
    Example: complex:3.5,4.2
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a complex instance."""
        return isinstance(obj, complex)

    @staticmethod
    def encode(obj: complex) -> str:
        """Encode complex number to string with prefix."""
        return f"complex:{obj.real},{obj.imag}"

    @staticmethod
    def decode(s: str, type_hint: type[complex] | None = None) -> complex:
        """Decode string to complex number."""
        if not s.startswith("complex:"):
            raise ValueError(f"Invalid complex format: {s}")
        parts = s[8:].split(",", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid complex format: {s}")
        real = float(parts[0])
        imag = float(parts[1])
        return complex(real, imag)


class PathHandler:
    """Handler for Path objects.

    Format: path:<path-string>
    Example: path:/home/user/documents/file.txt
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a Path instance."""
        return isinstance(obj, PurePath)

    @staticmethod
    def encode(obj: PurePath) -> str:
        """Encode Path to string with prefix."""
        return f"path:{obj}"

    @staticmethod
    def decode(s: str, type_hint: type[Path] | None = None) -> Path:
        """Decode string to Path."""
        if not s.startswith("path:"):
            raise ValueError(f"Invalid path format: {s}")
        return Path(s[5:])


class SetHandler:
    """Handler for set objects.

    Format: set:<json-array-of-sorted-elements>
    Example: set:[1, 2, 3, "a", "b"]

    Note: Elements are sorted for deterministic output. Complex elements
    that cannot be sorted are handled by sorting their string representation.
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a set instance."""
        return type(obj) is set

    @staticmethod
    def encode(obj: set[Any]) -> str:
        """Encode set to sorted JSON array string with prefix."""
        # Sort elements for deterministic output
        elements = list(obj)
        try:
            # Try to sort directly if all elements are comparable
            sorted_elements = sorted(elements, key=lambda x: (type(x).__name__, x))
        except TypeError:
            # Fall back to string representation sorting
            sorted_elements = sorted(elements, key=str)
        return f"set:{json.dumps(sorted_elements)}"

    @staticmethod
    def decode(s: str, type_hint: type[set[Any]] | None = None) -> set[Any]:
        """Decode string to set."""
        if not s.startswith("set:"):
            raise ValueError(f"Invalid set format: {s}")
        elements = json.loads(s[4:])
        if not isinstance(elements, list):
            raise ValueError(f"Invalid set format: expected array, got {type(elements)}")
        return set(elements)


class FrozensetHandler:
    """Handler for frozenset objects.

    Format: frozenset:<json-array-of-sorted-elements>
    Example: frozenset:[1, 2, 3, "a", "b"]

    Note: Elements are sorted for deterministic output.
    """

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if object is a frozenset instance."""
        return isinstance(obj, frozenset)

    @staticmethod
    def encode(obj: frozenset[Any]) -> str:
        """Encode frozenset to sorted JSON array string with prefix."""
        elements = list(obj)
        try:
            sorted_elements = sorted(elements, key=lambda x: (type(x).__name__, x))
        except TypeError:
            sorted_elements = sorted(elements, key=str)
        return f"frozenset:{json.dumps(sorted_elements)}"

    @staticmethod
    def decode(
        s: str, type_hint: type[frozenset[Any]] | None = None
    ) -> frozenset[Any]:
        """Decode string to frozenset."""
        if not s.startswith("frozenset:"):
            raise ValueError(f"Invalid frozenset format: {s}")
        elements = json.loads(s[10:])
        if not isinstance(elements, list):
            raise ValueError(
                f"Invalid frozenset format: expected array, got {type(elements)}"
            )
        return frozenset(elements)


# List of all built-in handlers for easy registration
BUILTIN_HANDLERS: list[type[Any]] = [
    UUIDHandler,
    DatetimeHandler,
    DateHandler,
    TimeHandler,
    TimedeltaHandler,
    BytesHandler,
    EnumHandler,
    DecimalHandler,
    ComplexHandler,
    PathHandler,
    SetHandler,
    FrozensetHandler,
]


def register_builtin_handlers(registry: Any) -> None:
    """Register all built-in handlers with a TypeRegistry.

    Args:
        registry: TypeRegistry instance to register handlers with.

    Note:
        Built-in handlers are registered in reverse order so that handlers
        listed first in BUILTIN_HANDLERS have higher priority.
    """
    # Register in reverse order so first handlers have priority
    for handler in reversed(BUILTIN_HANDLERS):
        registry.register(handler)
