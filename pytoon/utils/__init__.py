"""PyToon utilities module."""

from pytoon.utils.errors import TOONDecodeError, TOONEncodeError, TOONError, TOONValidationError
from pytoon.utils.tokens import TokenComparison, TokenCounter
from pytoon.utils.validation import (
    is_safe_identifier,
    validate_delimiter,
    validate_expand_paths_mode,
    validate_indent,
    validate_key_folding_mode,
)

__all__ = [
    # TOON Exceptions
    "TOONError",
    "TOONEncodeError",
    "TOONDecodeError",
    "TOONValidationError",
    # Token counting
    "TokenCounter",
    "TokenComparison",
    # Validation helpers
    "validate_indent",
    "validate_delimiter",
    "is_safe_identifier",
    "validate_key_folding_mode",
    "validate_expand_paths_mode",
]
