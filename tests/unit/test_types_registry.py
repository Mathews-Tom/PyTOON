"""Unit tests for TypeRegistry and TypeHandler protocol."""

from typing import Any

import pytest

from pytoon.types import TypeHandler, TypeRegistry


class IntHandler:
    """Handler for integers."""

    @staticmethod
    def can_handle(obj: Any) -> bool:
        return isinstance(obj, int) and not isinstance(obj, bool)

    @staticmethod
    def encode(obj: int) -> str:
        return f"int:{obj}"

    @staticmethod
    def decode(s: str, type_hint: type[int] | None = None) -> int:
        if s.startswith("int:"):
            return int(s[4:])
        raise ValueError(f"Invalid int format: {s}")


class StringHandler:
    """Handler for strings."""

    @staticmethod
    def can_handle(obj: Any) -> bool:
        return isinstance(obj, str)

    @staticmethod
    def encode(obj: str) -> str:
        return f"str:{obj}"

    @staticmethod
    def decode(s: str, type_hint: type[str] | None = None) -> str:
        if s.startswith("str:"):
            return s[4:]
        raise ValueError(f"Invalid str format: {s}")


class FloatHandler:
    """Handler for floats."""

    @staticmethod
    def can_handle(obj: Any) -> bool:
        return isinstance(obj, float)

    @staticmethod
    def encode(obj: float) -> str:
        return f"float:{obj}"

    @staticmethod
    def decode(s: str, type_hint: type[float] | None = None) -> float:
        if s.startswith("float:"):
            return float(s[6:])
        raise ValueError(f"Invalid float format: {s}")


class PriorityIntHandler:
    """Alternative int handler for testing priority."""

    @staticmethod
    def can_handle(obj: Any) -> bool:
        return isinstance(obj, int) and not isinstance(obj, bool)

    @staticmethod
    def encode(obj: int) -> str:
        return f"priority_int:{obj}"

    @staticmethod
    def decode(s: str, type_hint: type[int] | None = None) -> int:
        if s.startswith("priority_int:"):
            return int(s[13:])
        raise ValueError(f"Invalid priority_int format: {s}")


class TestTypeRegistryInit:
    """Test TypeRegistry initialization."""

    def test_empty_registry(self) -> None:
        """Registry starts with no handlers."""
        registry = TypeRegistry()
        assert registry._handlers == []

    def test_registry_is_independent(self) -> None:
        """Each registry instance is independent."""
        registry1 = TypeRegistry()
        registry2 = TypeRegistry()
        registry1.register(IntHandler)
        assert len(registry1._handlers) == 1
        assert len(registry2._handlers) == 0


class TestTypeRegistryRegister:
    """Test handler registration."""

    def test_register_single_handler(self) -> None:
        """Can register a single handler."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        assert len(registry._handlers) == 1
        assert registry._handlers[0] is IntHandler

    def test_register_multiple_handlers(self) -> None:
        """Can register multiple handlers."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(StringHandler)
        registry.register(FloatHandler)
        assert len(registry._handlers) == 3

    def test_user_handlers_prepended(self) -> None:
        """User handlers are prepended (higher priority)."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(StringHandler)
        # StringHandler should be first (prepended)
        assert registry._handlers[0] is StringHandler
        assert registry._handlers[1] is IntHandler

    def test_duplicate_handler_registration(self) -> None:
        """Same handler can be registered multiple times."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(IntHandler)
        assert len(registry._handlers) == 2
        assert registry._handlers[0] is IntHandler
        assert registry._handlers[1] is IntHandler


class TestTypeRegistryEncodeValue:
    """Test encode_value method."""

    def test_encode_no_handlers_returns_none(self) -> None:
        """Returns None when no handlers registered."""
        registry = TypeRegistry()
        result = registry.encode_value(42)
        assert result is None

    def test_encode_no_matching_handler_returns_none(self) -> None:
        """Returns None when no handler matches."""
        registry = TypeRegistry()
        registry.register(StringHandler)
        result = registry.encode_value(42)  # No int handler
        assert result is None

    def test_encode_with_matching_handler(self) -> None:
        """Encodes value when handler matches."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        result = registry.encode_value(42)
        assert result == "int:42"

    def test_encode_uses_first_matching_handler(self) -> None:
        """Uses first matching handler in priority order."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(PriorityIntHandler)  # This is now first
        result = registry.encode_value(42)
        assert result == "priority_int:42"  # PriorityIntHandler is first

    def test_encode_different_types(self) -> None:
        """Can encode different types with appropriate handlers."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(StringHandler)
        registry.register(FloatHandler)

        assert registry.encode_value(42) == "int:42"
        assert registry.encode_value("hello") == "str:hello"
        assert registry.encode_value(3.14) == "float:3.14"

    def test_encode_negative_int(self) -> None:
        """Handles negative integers."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        result = registry.encode_value(-100)
        assert result == "int:-100"

    def test_encode_empty_string(self) -> None:
        """Handles empty strings."""
        registry = TypeRegistry()
        registry.register(StringHandler)
        result = registry.encode_value("")
        assert result == "str:"


class TestTypeRegistryDecodeValue:
    """Test decode_value method."""

    def test_decode_no_handlers_returns_none(self) -> None:
        """Returns None when no handlers registered."""
        registry = TypeRegistry()
        result = registry.decode_value("int:42")
        assert result is None

    def test_decode_no_matching_handler_returns_none(self) -> None:
        """Returns None when no handler can decode."""
        registry = TypeRegistry()
        registry.register(StringHandler)
        result = registry.decode_value("int:42")  # StringHandler will fail
        assert result is None

    def test_decode_with_matching_handler(self) -> None:
        """Decodes value when handler matches."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        result = registry.decode_value("int:42")
        assert result == 42

    def test_decode_uses_first_successful_handler(self) -> None:
        """Uses first handler that successfully decodes."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(PriorityIntHandler)  # This is now first
        # PriorityIntHandler expects "priority_int:" prefix, so it fails
        # IntHandler expects "int:" prefix, so it succeeds
        result = registry.decode_value("int:42")
        assert result == 42

    def test_decode_with_priority_handler(self) -> None:
        """Priority handler is tried first."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(PriorityIntHandler)  # This is now first
        result = registry.decode_value("priority_int:99")
        assert result == 99

    def test_decode_different_types(self) -> None:
        """Can decode different types."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(StringHandler)
        registry.register(FloatHandler)

        assert registry.decode_value("int:42") == 42
        assert registry.decode_value("str:hello") == "hello"
        assert registry.decode_value("float:3.14") == 3.14

    def test_decode_with_type_hint(self) -> None:
        """Type hint is passed to handler."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        result = registry.decode_value("int:42", int)
        assert result == 42
        assert isinstance(result, int)

    def test_decode_empty_string_value(self) -> None:
        """Handles decoding empty string values."""
        registry = TypeRegistry()
        registry.register(StringHandler)
        result = registry.decode_value("str:")
        assert result == ""

    def test_decode_skips_failing_handlers(self) -> None:
        """Skips handlers that raise exceptions."""
        registry = TypeRegistry()
        registry.register(StringHandler)
        registry.register(IntHandler)
        # StringHandler tries first but fails (no "str:" prefix)
        # IntHandler succeeds
        result = registry.decode_value("int:100")
        assert result == 100


class TestTypeRegistryPriority:
    """Test handler priority semantics."""

    def test_later_registered_has_higher_priority(self) -> None:
        """Most recently registered handler has highest priority."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(PriorityIntHandler)
        # PriorityIntHandler registered last, should be first
        result = registry.encode_value(10)
        assert result == "priority_int:10"

    def test_priority_with_multiple_registrations(self) -> None:
        """Priority is maintained with multiple registrations."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        registry.register(StringHandler)
        registry.register(PriorityIntHandler)
        registry.register(FloatHandler)
        # Order should be: FloatHandler, PriorityIntHandler, StringHandler, IntHandler
        assert registry._handlers[0] is FloatHandler
        assert registry._handlers[1] is PriorityIntHandler
        assert registry._handlers[2] is StringHandler
        assert registry._handlers[3] is IntHandler


class TestTypeRegistryRoundtrip:
    """Test encode-decode roundtrip."""

    def test_int_roundtrip(self) -> None:
        """Integer roundtrip preserves value."""
        registry = TypeRegistry()
        registry.register(IntHandler)
        original = 42
        encoded = registry.encode_value(original)
        assert encoded is not None
        decoded = registry.decode_value(encoded)
        assert decoded == original

    def test_string_roundtrip(self) -> None:
        """String roundtrip preserves value."""
        registry = TypeRegistry()
        registry.register(StringHandler)
        original = "hello world"
        encoded = registry.encode_value(original)
        assert encoded is not None
        decoded = registry.decode_value(encoded)
        assert decoded == original

    def test_float_roundtrip(self) -> None:
        """Float roundtrip preserves value."""
        registry = TypeRegistry()
        registry.register(FloatHandler)
        original = 3.14159
        encoded = registry.encode_value(original)
        assert encoded is not None
        decoded = registry.decode_value(encoded)
        assert decoded == original


class TestTypeHandlerProtocolCompliance:
    """Test that handlers conform to TypeHandler protocol."""

    def test_int_handler_conforms(self) -> None:
        """IntHandler conforms to TypeHandler protocol."""
        assert hasattr(IntHandler, "can_handle")
        assert hasattr(IntHandler, "encode")
        assert hasattr(IntHandler, "decode")
        assert callable(IntHandler.can_handle)
        assert callable(IntHandler.encode)
        assert callable(IntHandler.decode)

    def test_string_handler_conforms(self) -> None:
        """StringHandler conforms to TypeHandler protocol."""
        assert hasattr(StringHandler, "can_handle")
        assert hasattr(StringHandler, "encode")
        assert hasattr(StringHandler, "decode")

    def test_can_handle_returns_bool(self) -> None:
        """can_handle returns boolean."""
        assert IntHandler.can_handle(42) is True
        assert IntHandler.can_handle("str") is False
        assert StringHandler.can_handle("hello") is True
        assert StringHandler.can_handle(42) is False

    def test_encode_returns_string(self) -> None:
        """encode returns string."""
        result = IntHandler.encode(42)
        assert isinstance(result, str)
        result = StringHandler.encode("test")
        assert isinstance(result, str)

    def test_decode_raises_on_invalid_format(self) -> None:
        """decode raises ValueError on invalid format."""
        with pytest.raises(ValueError):
            IntHandler.decode("invalid")
        with pytest.raises(ValueError):
            StringHandler.decode("invalid")
