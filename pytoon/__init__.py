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

from typing import Any, Literal

from pytoon.__version__ import __version__, __version_info__
from pytoon.core.decoder import Decoder
from pytoon.core.encoder import Encoder
from pytoon.core.spec import TOONSpec
from pytoon.utils.errors import (
    TOONDecodeError,
    TOONEncodeError,
    TOONError,
    TOONValidationError,
)


def encode(
    value: Any,
    *,
    indent: int = TOONSpec.DEFAULT_INDENT,
    delimiter: Literal[",", "\t", "|"] = ",",
    key_folding: Literal["off", "safe"] = "off",
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> str:
    """Encode a Python object to TOON format.

    Converts Python objects (dicts, lists, primitives) to TOON-formatted strings,
    providing significant token savings over JSON for LLM applications.

    Args:
        value: Python object to encode (dict, list, or primitive).
        indent: Number of spaces per indentation level (default: 2).
        delimiter: Field delimiter for tabular arrays - ',', '\\t', or '|' (default: ',').
        key_folding: Key folding mode - 'off' or 'safe' (default: 'off').
        ensure_ascii: Escape non-ASCII characters (default: False).
        sort_keys: Sort dictionary keys alphabetically (default: False).

    Returns:
        TOON-formatted string representation of the input value.

    Raises:
        TOONEncodeError: If value cannot be encoded (unsupported type, circular reference).
        ValueError: If configuration parameters are invalid.

    Examples:
        >>> encode({"name": "Alice", "age": 30})
        'name: Alice\\nage: 30'
        >>> encode([1, 2, 3])
        '[3]: 1,2,3'
        >>> encode({"key": "value"}, indent=4)
        'key: value'
        >>> encode(None)
        'null'
        >>> encode(True)
        'true'

    Note:
        TOON format typically achieves 30-60% token savings compared to JSON.
    """
    encoder = Encoder(
        indent=indent,
        delimiter=delimiter,
        key_folding=key_folding,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
    )
    return encoder.encode(value)


def decode(
    toon_string: str,
    *,
    strict: bool = True,
    expand_paths: Literal["off", "safe"] = "off",
) -> Any:
    """Decode a TOON string to Python object.

    Parses TOON-formatted strings back into Python objects (dicts, lists, primitives).
    Supports strict validation mode for ensuring data integrity.

    Args:
        toon_string: TOON-formatted string to decode.
        strict: Enable strict validation mode (default: True).
            In strict mode, array length declarations are enforced.
        expand_paths: Path expansion mode - 'off' or 'safe' (default: 'off').

    Returns:
        Python object (dict, list, or primitive) reconstructed from TOON string.

    Raises:
        TOONDecodeError: If string cannot be parsed (invalid syntax).
        TOONValidationError: If validation fails in strict mode (length mismatch).
        ValueError: If configuration parameters are invalid.

    Examples:
        >>> decode('name: Alice')
        {'name': 'Alice'}
        >>> decode('[3]: 1,2,3')
        [1, 2, 3]
        >>> decode('null')
        >>> decode('true')
        True
        >>> decode('42')
        42

    Note:
        Roundtrip fidelity is guaranteed: decode(encode(data)) == data
        for all valid TOON inputs.
    """
    decoder = Decoder(strict=strict, expand_paths=expand_paths)
    return decoder.decode(toon_string)


__all__ = [
    # Version info
    "__version__",
    "__version_info__",
    # Core API
    "encode",
    "decode",
    # Exceptions
    "TOONError",
    "TOONEncodeError",
    "TOONDecodeError",
    "TOONValidationError",
]
