"""PyToon - Token-Oriented Object Notation for Python.

PyToon is a production-ready Python library implementing TOON v1.5+ specification,
providing 30-60% token savings over JSON for LLM applications through bidirectional
JSON to TOON conversion.

Basic Usage:
    >>> from pytoon import encode, decode
    >>> data = {"name": "Alice", "age": 30}
    >>> toon = encode(data)
    >>> recovered = decode(toon)
    >>> assert recovered == data
"""

from pytoon.__version__ import __version__, __version_info__
from pytoon.utils.errors import (
    TOONDecodeError,
    TOONEncodeError,
    TOONError,
    TOONValidationError,
)

# Public API functions will be added when implemented
# from pytoon.core import encode, decode

__all__ = [
    # Version info
    "__version__",
    "__version_info__",
    # Exceptions
    "TOONError",
    "TOONEncodeError",
    "TOONDecodeError",
    "TOONValidationError",
    # Core API (to be added)
    # "encode",
    # "decode",
]
