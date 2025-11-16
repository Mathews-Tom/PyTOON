"""Comprehensive tests for built-in type handlers.

Tests cover all 12 type handlers with roundtrip fidelity, edge cases,
error handling, and integration with TypeRegistry.
"""

from __future__ import annotations

import base64
import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum, IntEnum, auto
from pathlib import Path, PosixPath, PurePath, WindowsPath

import pytest

from pytoon.types.handlers import (
    BUILTIN_HANDLERS,
    BytesHandler,
    ComplexHandler,
    DateHandler,
    DatetimeHandler,
    DecimalHandler,
    EnumHandler,
    FrozensetHandler,
    PathHandler,
    SetHandler,
    TimedeltaHandler,
    TimeHandler,
    UUIDHandler,
    register_builtin_handlers,
)
from pytoon.types.registry import TypeRegistry


# Test Enums
class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Status(IntEnum):
    PENDING = 1
    ACTIVE = 2
    COMPLETED = 3


class Priority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


# =============================================================================
# UUIDHandler Tests
# =============================================================================


class TestUUIDHandler:
    def test_can_handle_uuid(self) -> None:
        assert UUIDHandler.can_handle(uuid.UUID("12345678-1234-5678-1234-567812345678"))

    def test_can_handle_not_uuid(self) -> None:
        assert not UUIDHandler.can_handle("not-a-uuid")
        assert not UUIDHandler.can_handle(12345)
        assert not UUIDHandler.can_handle(None)

    def test_encode_uuid(self) -> None:
        uid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        result = UUIDHandler.encode(uid)
        assert result == "uuid:550e8400-e29b-41d4-a716-446655440000"

    def test_decode_uuid(self) -> None:
        result = UUIDHandler.decode("uuid:550e8400-e29b-41d4-a716-446655440000")
        assert result == uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

    def test_roundtrip_uuid(self) -> None:
        original = uuid.uuid4()
        encoded = UUIDHandler.encode(original)
        decoded = UUIDHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid UUID format"):
            UUIDHandler.decode("invalid:550e8400-e29b-41d4-a716-446655440000")

    def test_decode_invalid_uuid_string(self) -> None:
        with pytest.raises(ValueError):
            UUIDHandler.decode("uuid:not-a-valid-uuid")

    def test_uuid_versions(self) -> None:
        # Test UUID1
        uid1 = uuid.uuid1()
        assert UUIDHandler.decode(UUIDHandler.encode(uid1)) == uid1

        # Test UUID4
        uid4 = uuid.uuid4()
        assert UUIDHandler.decode(UUIDHandler.encode(uid4)) == uid4

        # Test UUID5
        uid5 = uuid.uuid5(uuid.NAMESPACE_DNS, "python.org")
        assert UUIDHandler.decode(UUIDHandler.encode(uid5)) == uid5


# =============================================================================
# DatetimeHandler Tests
# =============================================================================


class TestDatetimeHandler:
    def test_can_handle_datetime(self) -> None:
        assert DatetimeHandler.can_handle(datetime.now())
        assert DatetimeHandler.can_handle(datetime(2024, 1, 15, 10, 30, 45))

    def test_can_handle_not_datetime(self) -> None:
        assert not DatetimeHandler.can_handle(date.today())
        assert not DatetimeHandler.can_handle("2024-01-15")
        assert not DatetimeHandler.can_handle(1234567890)

    def test_encode_datetime_naive(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45, 123456)
        result = DatetimeHandler.encode(dt)
        assert result == "datetime:2024-01-15T10:30:45.123456"

    def test_encode_datetime_with_timezone(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        result = DatetimeHandler.encode(dt)
        assert result == "datetime:2024-01-15T10:30:45+00:00"

    def test_decode_datetime_naive(self) -> None:
        result = DatetimeHandler.decode("datetime:2024-01-15T10:30:45.123456")
        assert result == datetime(2024, 1, 15, 10, 30, 45, 123456)

    def test_decode_datetime_with_timezone(self) -> None:
        result = DatetimeHandler.decode("datetime:2024-01-15T10:30:45+00:00")
        assert result == datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)

    def test_roundtrip_datetime(self) -> None:
        original = datetime.now()
        encoded = DatetimeHandler.encode(original)
        decoded = DatetimeHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid datetime format"):
            DatetimeHandler.decode("date:2024-01-15T10:30:45")

    def test_datetime_no_microseconds(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 45)
        encoded = DatetimeHandler.encode(dt)
        decoded = DatetimeHandler.decode(encoded)
        assert decoded == dt


# =============================================================================
# DateHandler Tests
# =============================================================================


class TestDateHandler:
    def test_can_handle_date(self) -> None:
        assert DateHandler.can_handle(date(2024, 1, 15))
        assert DateHandler.can_handle(date.today())

    def test_can_handle_not_date(self) -> None:
        # datetime is subclass of date, but handler checks exact type
        assert not DateHandler.can_handle(datetime.now())
        assert not DateHandler.can_handle("2024-01-15")
        assert not DateHandler.can_handle(1234567890)

    def test_encode_date(self) -> None:
        d = date(2024, 1, 15)
        result = DateHandler.encode(d)
        assert result == "date:2024-01-15"

    def test_decode_date(self) -> None:
        result = DateHandler.decode("date:2024-01-15")
        assert result == date(2024, 1, 15)

    def test_roundtrip_date(self) -> None:
        original = date.today()
        encoded = DateHandler.encode(original)
        decoded = DateHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid date format"):
            DateHandler.decode("datetime:2024-01-15")

    def test_date_edge_cases(self) -> None:
        # Min date
        d = date(1, 1, 1)
        assert DateHandler.decode(DateHandler.encode(d)) == d

        # Max date
        d = date(9999, 12, 31)
        assert DateHandler.decode(DateHandler.encode(d)) == d

        # Leap year
        d = date(2024, 2, 29)
        assert DateHandler.decode(DateHandler.encode(d)) == d


# =============================================================================
# TimeHandler Tests
# =============================================================================


class TestTimeHandler:
    def test_can_handle_time(self) -> None:
        assert TimeHandler.can_handle(time(10, 30, 45))

    def test_can_handle_not_time(self) -> None:
        assert not TimeHandler.can_handle(datetime.now())
        assert not TimeHandler.can_handle("10:30:45")
        assert not TimeHandler.can_handle(3600)

    def test_encode_time(self) -> None:
        t = time(10, 30, 45, 123456)
        result = TimeHandler.encode(t)
        assert result == "time:10:30:45.123456"

    def test_decode_time(self) -> None:
        result = TimeHandler.decode("time:10:30:45.123456")
        assert result == time(10, 30, 45, 123456)

    def test_roundtrip_time(self) -> None:
        original = time(23, 59, 59, 999999)
        encoded = TimeHandler.encode(original)
        decoded = TimeHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid time format"):
            TimeHandler.decode("datetime:10:30:45")

    def test_time_with_timezone(self) -> None:
        t = time(10, 30, 45, tzinfo=timezone.utc)
        encoded = TimeHandler.encode(t)
        decoded = TimeHandler.decode(encoded)
        assert decoded == t

    def test_time_no_microseconds(self) -> None:
        t = time(10, 30, 45)
        assert TimeHandler.decode(TimeHandler.encode(t)) == t


# =============================================================================
# TimedeltaHandler Tests
# =============================================================================


class TestTimedeltaHandler:
    def test_can_handle_timedelta(self) -> None:
        assert TimedeltaHandler.can_handle(timedelta(days=1))
        assert TimedeltaHandler.can_handle(timedelta(seconds=3600))

    def test_can_handle_not_timedelta(self) -> None:
        assert not TimedeltaHandler.can_handle(3600)
        assert not TimedeltaHandler.can_handle("1 day")

    def test_encode_timedelta_days(self) -> None:
        td = timedelta(days=1)
        result = TimedeltaHandler.encode(td)
        assert result == "timedelta:86400.0"

    def test_encode_timedelta_complex(self) -> None:
        td = timedelta(days=1, hours=2, minutes=3, seconds=4, microseconds=500000)
        result = TimedeltaHandler.encode(td)
        expected_seconds = 86400 + 7200 + 180 + 4 + 0.5
        assert result == f"timedelta:{expected_seconds}"

    def test_decode_timedelta(self) -> None:
        result = TimedeltaHandler.decode("timedelta:86400.0")
        assert result == timedelta(days=1)

    def test_roundtrip_timedelta(self) -> None:
        original = timedelta(days=5, hours=3, minutes=20, seconds=15, microseconds=123456)
        encoded = TimedeltaHandler.encode(original)
        decoded = TimedeltaHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid timedelta format"):
            TimedeltaHandler.decode("time:86400")

    def test_negative_timedelta(self) -> None:
        td = timedelta(days=-1)
        assert TimedeltaHandler.decode(TimedeltaHandler.encode(td)) == td

    def test_zero_timedelta(self) -> None:
        td = timedelta()
        assert TimedeltaHandler.decode(TimedeltaHandler.encode(td)) == td


# =============================================================================
# BytesHandler Tests
# =============================================================================


class TestBytesHandler:
    def test_can_handle_bytes(self) -> None:
        assert BytesHandler.can_handle(b"hello")
        assert BytesHandler.can_handle(bytes([1, 2, 3]))

    def test_can_handle_not_bytes(self) -> None:
        assert not BytesHandler.can_handle("hello")
        assert not BytesHandler.can_handle([1, 2, 3])
        assert not BytesHandler.can_handle(bytearray(b"hello"))

    def test_encode_bytes(self) -> None:
        data = b"Hello World"
        result = BytesHandler.encode(data)
        assert result == "bytes:SGVsbG8gV29ybGQ="

    def test_decode_bytes(self) -> None:
        result = BytesHandler.decode("bytes:SGVsbG8gV29ybGQ=")
        assert result == b"Hello World"

    def test_roundtrip_bytes(self) -> None:
        original = b"Binary data: \x00\xff\x10"
        encoded = BytesHandler.encode(original)
        decoded = BytesHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid bytes format"):
            BytesHandler.decode("base64:SGVsbG8gV29ybGQ=")

    def test_empty_bytes(self) -> None:
        data = b""
        assert BytesHandler.decode(BytesHandler.encode(data)) == data

    def test_large_bytes(self) -> None:
        data = bytes(range(256)) * 10
        assert BytesHandler.decode(BytesHandler.encode(data)) == data

    def test_binary_data(self) -> None:
        # Non-printable characters
        data = bytes([0, 127, 255, 128, 64])
        assert BytesHandler.decode(BytesHandler.encode(data)) == data


# =============================================================================
# EnumHandler Tests
# =============================================================================


class TestEnumHandler:
    def test_can_handle_enum(self) -> None:
        assert EnumHandler.can_handle(Color.RED)
        assert EnumHandler.can_handle(Status.ACTIVE)
        assert EnumHandler.can_handle(Priority.HIGH)

    def test_can_handle_not_enum(self) -> None:
        assert not EnumHandler.can_handle("RED")
        assert not EnumHandler.can_handle(1)
        assert not EnumHandler.can_handle(Color)  # Class, not member

    def test_encode_string_enum(self) -> None:
        result = EnumHandler.encode(Color.RED)
        assert result == "enum:Color.RED"

    def test_encode_int_enum(self) -> None:
        result = EnumHandler.encode(Status.ACTIVE)
        assert result == "enum:Status.ACTIVE"

    def test_encode_auto_enum(self) -> None:
        result = EnumHandler.encode(Priority.HIGH)
        assert result == "enum:Priority.HIGH"

    def test_decode_enum_with_hint(self) -> None:
        result = EnumHandler.decode("enum:Color.GREEN", Color)
        assert result == Color.GREEN

    def test_decode_enum_without_hint(self) -> None:
        with pytest.raises(ValueError, match="type_hint is required"):
            EnumHandler.decode("enum:Color.RED")

    def test_decode_enum_wrong_class(self) -> None:
        with pytest.raises(ValueError, match="Enum class mismatch"):
            EnumHandler.decode("enum:Status.ACTIVE", Color)

    def test_roundtrip_enum(self) -> None:
        for member in Color:
            encoded = EnumHandler.encode(member)
            decoded = EnumHandler.decode(encoded, Color)
            assert decoded == member

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid enum format"):
            EnumHandler.decode("type:Color.RED", Color)

    def test_decode_invalid_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid enum format"):
            EnumHandler.decode("enum:ColorRED", Color)


# =============================================================================
# DecimalHandler Tests
# =============================================================================


class TestDecimalHandler:
    def test_can_handle_decimal(self) -> None:
        assert DecimalHandler.can_handle(Decimal("123.456"))
        assert DecimalHandler.can_handle(Decimal("0"))

    def test_can_handle_not_decimal(self) -> None:
        assert not DecimalHandler.can_handle(123.456)
        assert not DecimalHandler.can_handle("123.456")
        assert not DecimalHandler.can_handle(123)

    def test_encode_decimal(self) -> None:
        d = Decimal("123.456789012345678901234567890")
        result = DecimalHandler.encode(d)
        assert result == "decimal:123.456789012345678901234567890"

    def test_decode_decimal(self) -> None:
        result = DecimalHandler.decode("decimal:123.456789012345678901234567890")
        assert result == Decimal("123.456789012345678901234567890")

    def test_roundtrip_decimal(self) -> None:
        original = Decimal("99999999999999999999.99999999999999999999")
        encoded = DecimalHandler.encode(original)
        decoded = DecimalHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid decimal format"):
            DecimalHandler.decode("float:123.456")

    def test_decimal_infinity(self) -> None:
        d = Decimal("Infinity")
        assert DecimalHandler.decode(DecimalHandler.encode(d)) == d

    def test_decimal_negative_infinity(self) -> None:
        d = Decimal("-Infinity")
        assert DecimalHandler.decode(DecimalHandler.encode(d)) == d

    def test_decimal_nan(self) -> None:
        d = Decimal("NaN")
        decoded = DecimalHandler.decode(DecimalHandler.encode(d))
        assert decoded.is_nan()

    def test_decimal_negative(self) -> None:
        d = Decimal("-123.456")
        assert DecimalHandler.decode(DecimalHandler.encode(d)) == d

    def test_decimal_scientific_notation(self) -> None:
        d = Decimal("1.23E+10")
        assert DecimalHandler.decode(DecimalHandler.encode(d)) == d


# =============================================================================
# ComplexHandler Tests
# =============================================================================


class TestComplexHandler:
    def test_can_handle_complex(self) -> None:
        assert ComplexHandler.can_handle(complex(3, 4))
        assert ComplexHandler.can_handle(3 + 4j)

    def test_can_handle_not_complex(self) -> None:
        assert not ComplexHandler.can_handle(3.0)
        assert not ComplexHandler.can_handle("3+4j")
        assert not ComplexHandler.can_handle((3, 4))

    def test_encode_complex(self) -> None:
        c = complex(3.5, 4.2)
        result = ComplexHandler.encode(c)
        assert result == "complex:3.5,4.2"

    def test_decode_complex(self) -> None:
        result = ComplexHandler.decode("complex:3.5,4.2")
        assert result == complex(3.5, 4.2)

    def test_roundtrip_complex(self) -> None:
        original = complex(-1.5, 2.7)
        encoded = ComplexHandler.encode(original)
        decoded = ComplexHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid complex format"):
            ComplexHandler.decode("imaginary:3.5,4.2")

    def test_decode_invalid_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid complex format"):
            ComplexHandler.decode("complex:3.5")

    def test_complex_zero_imag(self) -> None:
        c = complex(5.0, 0.0)
        assert ComplexHandler.decode(ComplexHandler.encode(c)) == c

    def test_complex_zero_real(self) -> None:
        c = complex(0.0, 3.0)
        assert ComplexHandler.decode(ComplexHandler.encode(c)) == c

    def test_complex_both_negative(self) -> None:
        c = complex(-3.5, -4.2)
        assert ComplexHandler.decode(ComplexHandler.encode(c)) == c


# =============================================================================
# PathHandler Tests
# =============================================================================


class TestPathHandler:
    def test_can_handle_path(self) -> None:
        assert PathHandler.can_handle(Path("/home/user/file.txt"))
        assert PathHandler.can_handle(Path("relative/path"))

    def test_can_handle_not_path(self) -> None:
        assert not PathHandler.can_handle("/home/user/file.txt")
        assert not PathHandler.can_handle(["path", "parts"])

    def test_encode_absolute_path(self) -> None:
        p = Path("/home/user/documents/file.txt")
        result = PathHandler.encode(p)
        assert result == "path:/home/user/documents/file.txt"

    def test_encode_relative_path(self) -> None:
        p = Path("relative/path/to/file.txt")
        result = PathHandler.encode(p)
        assert result == "path:relative/path/to/file.txt"

    def test_decode_path(self) -> None:
        result = PathHandler.decode("path:/home/user/file.txt")
        assert result == Path("/home/user/file.txt")

    def test_roundtrip_path(self) -> None:
        original = Path("/var/log/application.log")
        encoded = PathHandler.encode(original)
        decoded = PathHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid path format"):
            PathHandler.decode("file:/home/user/file.txt")

    def test_path_with_spaces(self) -> None:
        p = Path("/home/user/My Documents/file name.txt")
        assert PathHandler.decode(PathHandler.encode(p)) == p

    def test_path_with_special_chars(self) -> None:
        p = Path("/home/user/file-name_123.txt")
        assert PathHandler.decode(PathHandler.encode(p)) == p


# =============================================================================
# SetHandler Tests
# =============================================================================


class TestSetHandler:
    def test_can_handle_set(self) -> None:
        assert SetHandler.can_handle({1, 2, 3})
        assert SetHandler.can_handle(set())

    def test_can_handle_not_set(self) -> None:
        assert not SetHandler.can_handle([1, 2, 3])
        assert not SetHandler.can_handle(frozenset([1, 2, 3]))
        assert not SetHandler.can_handle({1: "a", 2: "b"})

    def test_encode_int_set(self) -> None:
        s = {3, 1, 2}
        result = SetHandler.encode(s)
        # Should be sorted
        assert result == "set:[1, 2, 3]"

    def test_encode_string_set(self) -> None:
        s = {"c", "a", "b"}
        result = SetHandler.encode(s)
        assert result == 'set:["a", "b", "c"]'

    def test_decode_set(self) -> None:
        result = SetHandler.decode("set:[1, 2, 3]")
        assert result == {1, 2, 3}

    def test_roundtrip_set(self) -> None:
        original = {10, 20, 30, 40, 50}
        encoded = SetHandler.encode(original)
        decoded = SetHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid set format"):
            SetHandler.decode("list:[1, 2, 3]")

    def test_empty_set(self) -> None:
        s: set[int] = set()
        assert SetHandler.decode(SetHandler.encode(s)) == s

    def test_mixed_type_set(self) -> None:
        s = {1, "a", 2, "b"}
        decoded = SetHandler.decode(SetHandler.encode(s))
        assert decoded == s

    def test_set_deterministic_output(self) -> None:
        # Encoding should be deterministic
        s = {5, 3, 1, 4, 2}
        result1 = SetHandler.encode(s)
        result2 = SetHandler.encode(s)
        assert result1 == result2
        assert result1 == "set:[1, 2, 3, 4, 5]"


# =============================================================================
# FrozensetHandler Tests
# =============================================================================


class TestFrozensetHandler:
    def test_can_handle_frozenset(self) -> None:
        assert FrozensetHandler.can_handle(frozenset([1, 2, 3]))
        assert FrozensetHandler.can_handle(frozenset())

    def test_can_handle_not_frozenset(self) -> None:
        assert not FrozensetHandler.can_handle({1, 2, 3})
        assert not FrozensetHandler.can_handle([1, 2, 3])

    def test_encode_frozenset(self) -> None:
        fs = frozenset([3, 1, 2])
        result = FrozensetHandler.encode(fs)
        assert result == "frozenset:[1, 2, 3]"

    def test_decode_frozenset(self) -> None:
        result = FrozensetHandler.decode("frozenset:[1, 2, 3]")
        assert result == frozenset([1, 2, 3])

    def test_roundtrip_frozenset(self) -> None:
        original = frozenset(["x", "y", "z"])
        encoded = FrozensetHandler.encode(original)
        decoded = FrozensetHandler.decode(encoded)
        assert decoded == original

    def test_decode_invalid_prefix(self) -> None:
        with pytest.raises(ValueError, match="Invalid frozenset format"):
            FrozensetHandler.decode("set:[1, 2, 3]")

    def test_empty_frozenset(self) -> None:
        fs: frozenset[int] = frozenset()
        assert FrozensetHandler.decode(FrozensetHandler.encode(fs)) == fs


# =============================================================================
# Integration Tests with TypeRegistry
# =============================================================================


class TestTypeRegistryIntegration:
    def test_register_builtin_handlers(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        assert len(registry._handlers) == len(BUILTIN_HANDLERS)

    def test_encode_uuid_via_registry(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        uid = uuid.uuid4()
        result = registry.encode_value(uid)
        assert result is not None
        assert result.startswith("uuid:")

    def test_encode_datetime_via_registry(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        dt = datetime.now()
        result = registry.encode_value(dt)
        assert result is not None
        assert result.startswith("datetime:")

    def test_encode_bytes_via_registry(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        result = registry.encode_value(b"test data")
        assert result is not None
        assert result.startswith("bytes:")

    def test_encode_decimal_via_registry(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        result = registry.encode_value(Decimal("123.456"))
        assert result is not None
        assert result.startswith("decimal:")

    def test_encode_complex_via_registry(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        result = registry.encode_value(complex(3, 4))
        assert result is not None
        assert result.startswith("complex:")

    def test_encode_path_via_registry(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        result = registry.encode_value(Path("/tmp/test"))
        assert result is not None
        assert result.startswith("path:")

    def test_encode_set_via_registry(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        result = registry.encode_value({1, 2, 3})
        assert result is not None
        assert result.startswith("set:")

    def test_decode_uuid_via_registry(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)
        uid = uuid.uuid4()
        encoded = registry.encode_value(uid)
        assert encoded is not None
        decoded = registry.decode_value(encoded, uuid.UUID)
        assert decoded == uid

    def test_handler_priority(self) -> None:
        registry = TypeRegistry()
        register_builtin_handlers(registry)

        # Custom handler that takes priority
        class CustomUUIDHandler:
            @staticmethod
            def can_handle(obj: Any) -> bool:
                return isinstance(obj, uuid.UUID)

            @staticmethod
            def encode(obj: uuid.UUID) -> str:
                return f"custom-uuid:{obj}"

            @staticmethod
            def decode(s: str, type_hint: type[uuid.UUID] | None = None) -> uuid.UUID:
                if s.startswith("custom-uuid:"):
                    return uuid.UUID(s[12:])
                raise ValueError("Invalid format")

        registry.register(CustomUUIDHandler)
        uid = uuid.uuid4()
        result = registry.encode_value(uid)
        assert result is not None
        assert result.startswith("custom-uuid:")

    def test_builtin_handler_count(self) -> None:
        assert len(BUILTIN_HANDLERS) == 12

    def test_all_handlers_in_builtin_list(self) -> None:
        expected_handlers = [
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
        assert BUILTIN_HANDLERS == expected_handlers


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    def test_datetime_max(self) -> None:
        dt = datetime.max
        assert DatetimeHandler.decode(DatetimeHandler.encode(dt)) == dt

    def test_datetime_min(self) -> None:
        dt = datetime.min
        assert DatetimeHandler.decode(DatetimeHandler.encode(dt)) == dt

    def test_time_midnight(self) -> None:
        t = time(0, 0, 0)
        assert TimeHandler.decode(TimeHandler.encode(t)) == t

    def test_time_max(self) -> None:
        t = time(23, 59, 59, 999999)
        assert TimeHandler.decode(TimeHandler.encode(t)) == t

    def test_decimal_very_large(self) -> None:
        d = Decimal("9" * 100)
        assert DecimalHandler.decode(DecimalHandler.encode(d)) == d

    def test_decimal_very_small(self) -> None:
        d = Decimal("0." + "0" * 50 + "1")
        assert DecimalHandler.decode(DecimalHandler.encode(d)) == d

    def test_complex_infinity(self) -> None:
        c = complex(float("inf"), float("-inf"))
        assert ComplexHandler.decode(ComplexHandler.encode(c)) == c

    def test_uuid_nil(self) -> None:
        uid = uuid.UUID(int=0)
        assert UUIDHandler.decode(UUIDHandler.encode(uid)) == uid

    def test_bytes_all_zeros(self) -> None:
        data = b"\x00" * 100
        assert BytesHandler.decode(BytesHandler.encode(data)) == data

    def test_bytes_all_ones(self) -> None:
        data = b"\xff" * 100
        assert BytesHandler.decode(BytesHandler.encode(data)) == data
