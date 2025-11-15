"""Unit tests for PyToon exception hierarchy."""

from __future__ import annotations

import pytest

from pytoon.utils.errors import (
    TOONDecodeError,
    TOONEncodeError,
    TOONError,
    TOONValidationError,
)


class TestTOONErrorHierarchy:
    """Test exception inheritance chain."""

    def test_toon_error_is_base_exception(self) -> None:
        """TOONError should inherit from Exception."""
        assert issubclass(TOONError, Exception)

    def test_toon_encode_error_inherits_from_toon_error(self) -> None:
        """TOONEncodeError should inherit from TOONError."""
        assert issubclass(TOONEncodeError, TOONError)
        assert issubclass(TOONEncodeError, Exception)

    def test_toon_decode_error_inherits_from_toon_error(self) -> None:
        """TOONDecodeError should inherit from TOONError."""
        assert issubclass(TOONDecodeError, TOONError)
        assert issubclass(TOONDecodeError, Exception)

    def test_toon_validation_error_inherits_from_decode_error(self) -> None:
        """TOONValidationError should inherit from TOONDecodeError."""
        assert issubclass(TOONValidationError, TOONDecodeError)
        assert issubclass(TOONValidationError, TOONError)
        assert issubclass(TOONValidationError, Exception)


class TestTOONErrorInstantiation:
    """Test exception instantiation and messages."""

    def test_toon_error_with_message(self) -> None:
        """TOONError should store message."""
        error = TOONError("Base error message")
        assert str(error) == "Base error message"

    def test_toon_encode_error_with_message(self) -> None:
        """TOONEncodeError should store message."""
        error = TOONEncodeError("Cannot encode type: <class 'object'>")
        assert str(error) == "Cannot encode type: <class 'object'>"

    def test_toon_decode_error_with_message(self) -> None:
        """TOONDecodeError should store message."""
        error = TOONDecodeError("Invalid syntax at line 1: unclosed bracket")
        assert str(error) == "Invalid syntax at line 1: unclosed bracket"

    def test_toon_validation_error_with_message(self) -> None:
        """TOONValidationError should store message."""
        error = TOONValidationError("Array declares 2 items but found 1")
        assert str(error) == "Array declares 2 items but found 1"

    def test_toon_error_without_message(self) -> None:
        """TOONError should work without message."""
        error = TOONError()
        assert str(error) == ""


class TestExceptionCatching:
    """Test exception catching behavior."""

    def test_catch_encode_error_as_toon_error(self) -> None:
        """TOONEncodeError should be catchable as TOONError."""
        with pytest.raises(TOONError):
            raise TOONEncodeError("Encoding failed")

    def test_catch_decode_error_as_toon_error(self) -> None:
        """TOONDecodeError should be catchable as TOONError."""
        with pytest.raises(TOONError):
            raise TOONDecodeError("Decoding failed")

    def test_catch_validation_error_as_decode_error(self) -> None:
        """TOONValidationError should be catchable as TOONDecodeError."""
        with pytest.raises(TOONDecodeError):
            raise TOONValidationError("Validation failed")

    def test_catch_validation_error_as_toon_error(self) -> None:
        """TOONValidationError should be catchable as TOONError."""
        with pytest.raises(TOONError):
            raise TOONValidationError("Validation failed")

    def test_catch_specific_encode_error(self) -> None:
        """TOONEncodeError should be catchable specifically."""
        with pytest.raises(TOONEncodeError):
            raise TOONEncodeError("Specific encode error")

    def test_catch_specific_decode_error(self) -> None:
        """TOONDecodeError should be catchable specifically."""
        with pytest.raises(TOONDecodeError):
            raise TOONDecodeError("Specific decode error")

    def test_catch_specific_validation_error(self) -> None:
        """TOONValidationError should be catchable specifically."""
        with pytest.raises(TOONValidationError):
            raise TOONValidationError("Specific validation error")

    def test_encode_error_not_catchable_as_decode_error(self) -> None:
        """TOONEncodeError should NOT be catchable as TOONDecodeError."""
        with pytest.raises(TOONEncodeError):
            try:
                raise TOONEncodeError("Encode specific")
            except TOONDecodeError:
                pytest.fail("TOONEncodeError should not be caught as TOONDecodeError")


class TestExceptionDocstrings:
    """Test that all exceptions have proper docstrings."""

    def test_toon_error_has_docstring(self) -> None:
        """TOONError should have a descriptive docstring."""
        assert TOONError.__doc__ is not None
        assert len(TOONError.__doc__) > 50
        assert "Base exception" in TOONError.__doc__

    def test_toon_encode_error_has_docstring(self) -> None:
        """TOONEncodeError should have a descriptive docstring."""
        assert TOONEncodeError.__doc__ is not None
        assert len(TOONEncodeError.__doc__) > 50
        assert "encoding" in TOONEncodeError.__doc__.lower()

    def test_toon_decode_error_has_docstring(self) -> None:
        """TOONDecodeError should have a descriptive docstring."""
        assert TOONDecodeError.__doc__ is not None
        assert len(TOONDecodeError.__doc__) > 50
        assert "decoding" in TOONDecodeError.__doc__.lower()

    def test_toon_validation_error_has_docstring(self) -> None:
        """TOONValidationError should have a descriptive docstring."""
        assert TOONValidationError.__doc__ is not None
        assert len(TOONValidationError.__doc__) > 50
        assert "validation" in TOONValidationError.__doc__.lower()


class TestExceptionUsagePatterns:
    """Test realistic usage patterns for exceptions."""

    def test_catch_broad_then_specific(self) -> None:
        """Test catching broad error first, then specific."""

        def operation() -> None:
            raise TOONValidationError("Field count mismatch")

        error_type = None
        try:
            operation()
        except TOONValidationError:
            error_type = "validation"
        except TOONDecodeError:
            error_type = "decode"
        except TOONError:
            error_type = "toon"

        assert error_type == "validation"

    def test_error_chaining(self) -> None:
        """Test exception chaining with cause."""
        original = ValueError("Invalid value")
        try:
            raise TOONEncodeError("Encoding failed") from original
        except TOONEncodeError as chained:
            assert chained.__cause__ is original

    def test_error_with_multiple_arguments(self) -> None:
        """Test exception with multiple arguments."""
        error = TOONDecodeError("Error at line", 10, "column", 5)
        assert "Error at line" in str(error)

    def test_repr_contains_class_name(self) -> None:
        """Test that repr includes class name."""
        error = TOONEncodeError("test")
        repr_str = repr(error)
        assert "TOONEncodeError" in repr_str
