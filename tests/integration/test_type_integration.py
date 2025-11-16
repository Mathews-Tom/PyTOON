"""Integration tests for TypeRegistry integration with encoder/decoder."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import pytest

from pytoon import (
    decode,
    encode,
    get_type_registry,
    register_type_handler,
)
from pytoon.types import TypeRegistry


class TestTypeRegistryGlobalAccess:
    """Test global TypeRegistry access."""

    def test_get_type_registry_returns_registry(self) -> None:
        """get_type_registry returns TypeRegistry instance."""
        registry = get_type_registry()
        assert isinstance(registry, TypeRegistry)

    def test_get_type_registry_singleton(self) -> None:
        """get_type_registry returns same instance each time."""
        registry1 = get_type_registry()
        registry2 = get_type_registry()
        assert registry1 is registry2

    def test_registry_has_builtin_handlers(self) -> None:
        """Global registry has built-in handlers registered."""
        registry = get_type_registry()
        # Should handle UUID
        u = uuid.uuid4()
        result = registry.encode_value(u)
        assert result is not None
        assert result.startswith("uuid:")


class TestEncoderTypeRegistryIntegration:
    """Test encoder integration with TypeRegistry."""

    def test_encode_uuid(self) -> None:
        """encode() automatically handles UUID objects."""
        u = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        encoded = encode(u)
        assert "uuid:550e8400-e29b-41d4-a716-446655440000" in encoded

    def test_encode_datetime(self) -> None:
        """encode() automatically handles datetime objects."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        encoded = encode(dt)
        assert "datetime:2024-01-15T10:30:45" in encoded

    def test_encode_date(self) -> None:
        """encode() automatically handles date objects."""
        d = date(2024, 1, 15)
        encoded = encode(d)
        assert "date:2024-01-15" in encoded

    def test_encode_time(self) -> None:
        """encode() automatically handles time objects."""
        t = time(10, 30, 45)
        encoded = encode(t)
        assert "time:10:30:45" in encoded

    def test_encode_timedelta(self) -> None:
        """encode() automatically handles timedelta objects."""
        td = timedelta(days=1, hours=2, minutes=3)
        encoded = encode(td)
        assert "timedelta:" in encoded
        # 1 day + 2 hours + 3 minutes = 86400 + 7200 + 180 = 93780 seconds
        assert "93780" in encoded

    def test_encode_bytes(self) -> None:
        """encode() automatically handles bytes objects."""
        b = b"Hello World"
        encoded = encode(b)
        assert "bytes:" in encoded
        # "Hello World" in base64 is "SGVsbG8gV29ybGQ="
        assert "SGVsbG8gV29ybGQ=" in encoded

    def test_encode_decimal(self) -> None:
        """encode() automatically handles Decimal objects."""
        d = Decimal("123.456789012345678901234567890")
        encoded = encode(d)
        assert "decimal:123.456789012345678901234567890" in encoded

    def test_encode_complex(self) -> None:
        """encode() automatically handles complex numbers."""
        c = complex(3.5, 4.2)
        encoded = encode(c)
        assert "complex:3.5,4.2" in encoded

    def test_encode_path(self) -> None:
        """encode() automatically handles Path objects."""
        p = Path("/home/user/file.txt")
        encoded = encode(p)
        assert "path:/home/user/file.txt" in encoded

    def test_encode_set(self) -> None:
        """encode() automatically handles set objects."""
        s = {1, 2, 3}
        encoded = encode(s)
        assert "set:" in encoded
        # Elements are sorted
        assert "[1, 2, 3]" in encoded

    def test_encode_frozenset(self) -> None:
        """encode() automatically handles frozenset objects."""
        fs = frozenset([1, 2, 3])
        encoded = encode(fs)
        assert "frozenset:" in encoded
        assert "[1, 2, 3]" in encoded


class TestEncoderWithMixedTypes:
    """Test encoder with mixed primitive and custom types."""

    def test_dict_with_uuid(self) -> None:
        """encode() handles dict containing UUID."""
        data = {
            "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
            "name": "Alice",
        }
        encoded = encode(data)
        assert "id:" in encoded
        assert "uuid:550e8400-e29b-41d4-a716-446655440000" in encoded
        assert "name: Alice" in encoded

    def test_dict_with_datetime(self) -> None:
        """encode() handles dict containing datetime."""
        data = {
            "event": "login",
            "timestamp": datetime(2024, 1, 15, 10, 30, 45),
        }
        encoded = encode(data)
        assert "event: login" in encoded
        assert "timestamp:" in encoded
        assert "datetime:2024-01-15T10:30:45" in encoded

    def test_list_with_custom_types(self) -> None:
        """encode() handles list containing custom types."""
        data = [
            uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
            datetime(2024, 1, 15, 10, 30, 45),
            Decimal("123.45"),
        ]
        encoded = encode(data)
        assert "[3]:" in encoded
        assert "uuid:" in encoded
        assert "datetime:" in encoded
        assert "decimal:" in encoded

    def test_nested_dict_with_custom_types(self) -> None:
        """encode() handles nested dicts with custom types."""
        data = {
            "user": {
                "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
                "profile": {
                    "created_at": date(2024, 1, 15),
                    "settings": {"theme": "dark"},
                },
            },
        }
        encoded = encode(data)
        assert "user:" in encoded
        assert "id:" in encoded
        assert "uuid:" in encoded
        assert "profile:" in encoded
        assert "created_at:" in encoded
        assert "date:2024-01-15" in encoded
        assert "theme: dark" in encoded


class TestEncoderStringQuoting:
    """Test that type-encoded strings are properly quoted when needed."""

    def test_uuid_string_quoted_when_needed(self) -> None:
        """UUID strings are quoted if they contain special chars."""
        u = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        data = {"id": u}
        encoded = encode(data)
        # The colon in "uuid:..." triggers quoting
        assert '"uuid:550e8400-e29b-41d4-a716-446655440000"' in encoded

    def test_datetime_string_quoted(self) -> None:
        """datetime strings are quoted due to colons."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        data = {"timestamp": dt}
        encoded = encode(data)
        # Contains colons, should be quoted
        assert '"datetime:' in encoded


class TestCustomHandlerRegistration:
    """Test custom handler registration."""

    def test_register_custom_handler(self) -> None:
        """register_type_handler() registers custom handler."""

        class Point:
            def __init__(self, x: float, y: float) -> None:
                self.x = x
                self.y = y

            def __eq__(self, other: object) -> bool:
                if not isinstance(other, Point):
                    return False
                return self.x == other.x and self.y == other.y

        class PointHandler:
            @staticmethod
            def can_handle(obj: Any) -> bool:
                return isinstance(obj, Point)

            @staticmethod
            def encode(obj: Point) -> str:
                return f"point:{obj.x},{obj.y}"

            @staticmethod
            def decode(s: str, type_hint: type[Point] | None = None) -> Point:
                if not s.startswith("point:"):
                    raise ValueError(f"Invalid point format: {s}")
                parts = s[6:].split(",", 1)
                return Point(float(parts[0]), float(parts[1]))

        # Register custom handler
        register_type_handler(PointHandler)

        # Now encode should work with Point
        p = Point(3.5, 4.2)
        encoded = encode(p)
        assert "point:3.5,4.2" in encoded

        # Can also encode in dict
        data = {"location": p}
        encoded = encode(data)
        assert "location:" in encoded
        assert "point:3.5,4.2" in encoded

    def test_custom_handler_priority(self) -> None:
        """Custom handlers have priority over built-in."""
        # Save original registry state
        registry = get_type_registry()
        original_handlers = list(registry._handlers)

        try:
            # Override UUID handler with custom version
            class CustomUUIDHandler:
                @staticmethod
                def can_handle(obj: Any) -> bool:
                    return isinstance(obj, uuid.UUID)

                @staticmethod
                def encode(obj: uuid.UUID) -> str:
                    # Custom format
                    return f"custom-uuid:{obj.hex}"

                @staticmethod
                def decode(s: str, type_hint: type[uuid.UUID] | None = None) -> uuid.UUID:
                    if not s.startswith("custom-uuid:"):
                        raise ValueError("Invalid custom UUID format")
                    return uuid.UUID(s[12:])

            register_type_handler(CustomUUIDHandler)

            u = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
            encoded = encode(u)
            # Should use custom handler
            assert "custom-uuid:" in encoded
            assert "550e8400e29b41d4a716446655440000" in encoded

        finally:
            # Restore original handlers
            registry._handlers = original_handlers


class TestEnumEncoding:
    """Test Enum type encoding."""

    def test_encode_enum_member(self) -> None:
        """encode() handles Enum members."""

        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        data = {"color": Color.RED}
        encoded = encode(data)
        assert "color:" in encoded
        assert "enum:Color.RED" in encoded

    def test_encode_enum_in_list(self) -> None:
        """encode() handles Enums in lists."""

        class Status(Enum):
            PENDING = "pending"
            ACTIVE = "active"
            COMPLETED = "completed"

        data = [Status.PENDING, Status.ACTIVE, Status.COMPLETED]
        encoded = encode(data)
        assert "[3]:" in encoded
        assert "enum:Status.PENDING" in encoded
        assert "enum:Status.ACTIVE" in encoded
        assert "enum:Status.COMPLETED" in encoded


class TestComplexDataStructures:
    """Test complex data structures with mixed types."""

    def test_api_response_with_custom_types(self) -> None:
        """API response pattern with custom types."""
        data = {
            "request_id": uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
            "timestamp": datetime(2024, 1, 15, 10, 30, 45),
            "data": {
                "users": [
                    {
                        "id": 1,
                        "name": "Alice",
                        "balance": Decimal("1234.56"),
                    },
                    {
                        "id": 2,
                        "name": "Bob",
                        "balance": Decimal("789.01"),
                    },
                ],
            },
        }
        encoded = encode(data)
        assert "request_id:" in encoded
        assert "uuid:" in encoded
        assert "timestamp:" in encoded
        assert "datetime:" in encoded
        assert "decimal:" in encoded
        assert "1234.56" in encoded
        assert "789.01" in encoded

    def test_config_with_paths(self) -> None:
        """Configuration with Path objects."""
        data = {
            "paths": {
                "config": Path("/etc/app/config.toml"),
                "data": Path("/var/lib/app/data"),
                "logs": Path("/var/log/app"),
            },
        }
        encoded = encode(data)
        assert "config:" in encoded
        assert "path:/etc/app/config.toml" in encoded
        assert "data:" in encoded
        assert "path:/var/lib/app/data" in encoded
        assert "logs:" in encoded
        assert "path:/var/log/app" in encoded


class TestTypeRegistryDecoding:
    """Test TypeRegistry decoding capabilities (v1.2+ feature preview)."""

    def test_decode_uuid_string_with_registry(self) -> None:
        """TypeRegistry can decode UUID strings."""
        registry = get_type_registry()
        result = registry.decode_value("uuid:550e8400-e29b-41d4-a716-446655440000")
        assert isinstance(result, uuid.UUID)
        assert str(result) == "550e8400-e29b-41d4-a716-446655440000"

    def test_decode_datetime_string_with_registry(self) -> None:
        """TypeRegistry can decode datetime strings."""
        registry = get_type_registry()
        result = registry.decode_value("datetime:2024-01-15T10:30:45")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_decode_bytes_string_with_registry(self) -> None:
        """TypeRegistry can decode bytes strings."""
        registry = get_type_registry()
        result = registry.decode_value("bytes:SGVsbG8gV29ybGQ=")
        assert isinstance(result, bytes)
        assert result == b"Hello World"

    def test_decode_decimal_string_with_registry(self) -> None:
        """TypeRegistry can decode Decimal strings."""
        registry = get_type_registry()
        result = registry.decode_value("decimal:123.456789")
        assert isinstance(result, Decimal)
        assert result == Decimal("123.456789")

    def test_decode_returns_none_for_unknown_format(self) -> None:
        """TypeRegistry returns None for unknown formats."""
        registry = get_type_registry()
        result = registry.decode_value("unknown:something")
        assert result is None

    def test_decode_returns_none_for_plain_string(self) -> None:
        """TypeRegistry returns None for plain strings."""
        registry = get_type_registry()
        result = registry.decode_value("just a plain string")
        assert result is None


class TestPublicAPIExports:
    """Test that public API exports are correct."""

    def test_register_type_handler_exported(self) -> None:
        """register_type_handler is exported from pytoon."""
        from pytoon import register_type_handler as rth

        assert callable(rth)

    def test_get_type_registry_exported(self) -> None:
        """get_type_registry is exported from pytoon."""
        from pytoon import get_type_registry as gtr

        assert callable(gtr)

    def test_exports_in_all(self) -> None:
        """Functions are in __all__."""
        import pytoon

        assert "register_type_handler" in pytoon.__all__
        assert "get_type_registry" in pytoon.__all__
