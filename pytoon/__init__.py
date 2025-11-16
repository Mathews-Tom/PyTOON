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

Intelligent Format Selection (v1.1):
    >>> from pytoon import smart_encode
    >>> data = [{"id": 1}, {"id": 2}]
    >>> encoded, decision = smart_encode(data)
    >>> decision.recommended_format
    'toon'
"""

import json
from typing import Any, Literal

from pytoon.__version__ import __version__, __version_info__
from pytoon.core.decoder import Decoder
from pytoon.core.encoder import Encoder
from pytoon.core.spec import TOONSpec
from pytoon.decision.engine import DecisionEngine, FormatDecision
from pytoon.references import GraphDecoder, GraphEncoder, ReferenceDecoder, ReferenceEncoder
from pytoon.types import get_type_registry, register_type_handler
from pytoon.utils.errors import TOONDecodeError, TOONEncodeError, TOONError, TOONValidationError


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


def smart_encode(
    value: Any,
    *,
    auto: bool = True,
    indent: int = TOONSpec.DEFAULT_INDENT,
    delimiter: Literal[",", "\t", "|"] = ",",
    key_folding: Literal["off", "safe"] = "off",
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> tuple[str, FormatDecision]:
    """Automatically select optimal format and encode data.

    Analyzes data structure to recommend the best serialization format
    (TOON, JSON, graph, or hybrid), then encodes accordingly.

    Args:
        value: Python object to encode (dict, list, or primitive).
        auto: If True, uses recommended format. If False, always uses TOON.
        indent: Number of spaces per indentation level (default: 2).
        delimiter: Field delimiter for tabular arrays - ',', '\\t', or '|' (default: ',').
        key_folding: Key folding mode - 'off' or 'safe' (default: 'off').
        ensure_ascii: Escape non-ASCII characters (default: False).
        sort_keys: Sort dictionary keys alphabetically (default: False).

    Returns:
        Tuple of (encoded_string, FormatDecision) where:
            - encoded_string: The serialized data in the chosen format
            - FormatDecision: Contains recommended format, confidence, and reasoning

    Raises:
        TOONEncodeError: If value cannot be encoded (unsupported type, circular reference).
        ValueError: If configuration parameters are invalid.

    Examples:
        >>> # Tabular data -> TOON recommended
        >>> data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        >>> encoded, decision = smart_encode(data)
        >>> decision.recommended_format
        'toon'
        >>> decision.confidence > 0.8
        True

        >>> # Override with auto=False to force TOON
        >>> encoded, decision = smart_encode(data, auto=False)
        >>> # Always uses TOON regardless of recommendation

        >>> # Access reasoning
        >>> encoded, decision = smart_encode(data)
        >>> for reason in decision.reasoning:
        ...     print(reason)
        High uniformity (100.0%) strongly favors TOON
        ...

    Note:
        - When auto=True and decision is 'json', uses json.dumps()
        - When auto=True and decision is 'toon' or 'hybrid', uses pytoon.encode()
        - When auto=True and decision is 'graph', uses pytoon.encode() (graph support v1.2+)
        - When auto=False, always uses pytoon.encode()
    """
    engine = DecisionEngine()
    decision = engine.analyze(value)

    if auto and decision.recommended_format == "json":
        # Use JSON encoding
        encoded = json.dumps(
            value,
            ensure_ascii=ensure_ascii,
            sort_keys=sort_keys,
            indent=indent if indent > 0 else None,
        )
    else:
        # Use TOON encoding (for toon, hybrid, graph, or when auto=False)
        encoded = encode(
            value,
            indent=indent,
            delimiter=delimiter,
            key_folding=key_folding,
            ensure_ascii=ensure_ascii,
            sort_keys=sort_keys,
        )

    return encoded, decision


def encode_refs(
    data: Any,
    mode: str = "schema",
    *,
    indent: int = 2,
    delimiter: str = ",",
) -> str:
    """Encode data with reference tracking using schema-based format.

    Detects shared object references in the data and encodes them using
    placeholders ($1, $2, etc.) with a schema section describing the
    shared types. This enables efficient encoding of relational data.

    Args:
        data: Python object to encode (dict, list, or primitive).
        mode: Encoding mode - currently only 'schema' is supported.
        indent: Number of spaces per indentation level (default: 2).
        delimiter: Field delimiter for tabular arrays (default: ',').

    Returns:
        TOON-formatted string with _schema section and reference placeholders.

    Raises:
        TOONEncodeError: If mode is invalid or encoding fails.
        ValueError: If configuration parameters are invalid.

    Examples:
        >>> user = {"id": 1, "name": "Alice"}
        >>> data = {"users": [user], "admins": [user]}
        >>> result = encode_refs(data)
        >>> "_schema:" in result
        True
        >>> "$1" in result
        True

        >>> # Simple case with no shared references
        >>> data = {"a": 1, "b": 2}
        >>> result = encode_refs(data)
        >>> "_schema:" not in result  # No schema if no shared refs
        True

    Note:
        This is part of the v1.1 Reference Support feature for relational data.
    """
    encoder = ReferenceEncoder()
    return encoder.encode_refs(data, mode=mode, indent=indent, delimiter=delimiter)


def decode_refs(toon_string: str, resolve: bool = True) -> Any:
    """Decode TOON string with reference resolution.

    Parses a TOON string that may contain a _schema section and reference
    placeholders ($1, $2, etc.). When resolve=True, shared objects are
    reconstructed with proper Python object identity.

    Args:
        toon_string: TOON-formatted string to decode.
        resolve: If True, resolve placeholders to actual shared objects.
                If False, keep placeholder strings in the result.

    Returns:
        Python object (dict, list, or primitive) with resolved references.
        When resolve=True, shared objects are the SAME Python object (identity).

    Raises:
        TOONDecodeError: If string cannot be parsed or references are invalid.

    Examples:
        >>> toon = '''users: [2]: $1,$2
        ... admins: [1]: $1'''
        >>> result = decode_refs(toon, resolve=True)
        >>> result["users"][0] is result["admins"][0]
        True

        >>> # Without schema, decode normally
        >>> toon = "name: Alice"
        >>> decode_refs(toon)
        {'name': 'Alice'}

        >>> # Keep placeholders as strings
        >>> toon = "items: [2]: $1,$1"
        >>> decode_refs(toon, resolve=False)
        {'items': ['$1', '$1']}

    Note:
        This is part of the v1.1 Reference Support feature for relational data.
    """
    decoder = ReferenceDecoder()
    return decoder.decode_refs(toon_string, resolve=resolve)


def encode_graph(
    data: Any,
    *,
    indent: int = 2,
    delimiter: str = ",",
) -> str:
    """Encode data with circular reference handling.

    Detects circular references in the data and encodes them using
    object ID placeholders ($ref:1, $ref:2, etc.). Adds _graph: true
    flag to indicate graph mode encoding.

    Args:
        data: Python object to encode (dict, list, or primitive).
        indent: Number of spaces per indentation level (default: 2).
        delimiter: Field delimiter for inline arrays (default: ',').

    Returns:
        TOON-formatted string with _graph: true flag and $ref:N placeholders.

    Raises:
        TOONEncodeError: If encoding fails due to unsupported types.

    Examples:
        >>> user1 = {"id": 1, "name": "Alice"}
        >>> user2 = {"id": 2, "name": "Bob"}
        >>> user1["friend"] = user2
        >>> user2["friend"] = user1  # Circular reference
        >>> result = encode_graph({"users": [user1, user2]})
        >>> "_graph: true" in result
        True
        >>> "$ref:" in result
        True

        >>> # Self-referencing object
        >>> obj = {"id": 1}
        >>> obj["self"] = obj
        >>> result = encode_graph(obj)
        >>> "_graph: true" in result
        True

    Note:
        This is part of the v1.2 Graph Support feature for circular references.
        Uses $ref:N syntax (with colon) to distinguish from $N schema references.
    """
    encoder = GraphEncoder()
    return encoder.encode_graph(data, indent=indent, delimiter=delimiter)


def decode_graph(toon_string: str) -> Any:
    """Decode TOON string with circular reference reconstruction.

    Parses a TOON string that contains _graph: true flag and $ref:N
    placeholders. Reconstructs circular references in the resulting
    Python objects.

    Args:
        toon_string: TOON-formatted string to decode.

    Returns:
        Python object (dict, list, or primitive) with circular references.
        Circular structures are properly reconstructed.

    Raises:
        TOONDecodeError: If string cannot be parsed or graph format invalid.

    Examples:
        >>> toon = '''_graph: true
        ... user1:
        ...   id: 1
        ...   friend: $ref:2
        ... user2:
        ...   id: 2
        ...   friend: $ref:1'''
        >>> result = decode_graph(toon)
        >>> result["user1"]["friend"] is result["user2"]
        True
        >>> result["user2"]["friend"] is result["user1"]
        True

        >>> # Self-referencing
        >>> toon = '''_graph: true
        ... obj:
        ...   id: 1
        ...   self: $ref:1'''
        >>> result = decode_graph(toon)
        >>> result["obj"]["self"] is result["obj"]
        True

    Note:
        This is part of the v1.2 Graph Support feature for circular references.
        Requires _graph: true flag at the beginning of the TOON string.
    """
    decoder = GraphDecoder()
    return decoder.decode_graph(toon_string)


__all__ = [
    # Version info
    "__version__",
    "__version_info__",
    # Core API
    "encode",
    "decode",
    "smart_encode",
    # Reference API (v1.1)
    "encode_refs",
    "decode_refs",
    # Graph API (v1.2)
    "encode_graph",
    "decode_graph",
    # Type System
    "register_type_handler",
    "get_type_registry",
    # Decision Engine
    "FormatDecision",
    # TOON Exceptions
    "TOONError",
    "TOONEncodeError",
    "TOONDecodeError",
    "TOONValidationError",
]
