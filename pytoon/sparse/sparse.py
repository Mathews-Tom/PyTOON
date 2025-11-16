"""SparseArrayEncoder class for PyToon.

This module provides functionality to encode arrays with optional fields
using sparse format with optional field markers (field? syntax).
"""

from typing import Any

from pytoon.encoder.quoting import QuotingEngine
from pytoon.encoder.value import ValueEncoder


class SparseArrayEncoder:
    """Encode arrays with optional fields using sparse format.

    The SparseArrayEncoder analyzes field presence across array elements
    and encodes arrays with optional field markers (?) when fields have
    less than 100% presence rate.

    Sparse Format Example (30%+ missing values):
        users[3]{id,name,email?}:
          1,Alice,alice@example.com
          2,Bob,
          3,Charlie,charlie@example.com

    The '?' marks optional fields, empty string represents null/missing.

    Examples:
        >>> encoder = SparseArrayEncoder()
        >>> presence = encoder.analyze_sparsity([
        ...     {"id": 1, "email": "a@x.com"},
        ...     {"id": 2}
        ... ])
        >>> presence["id"]
        100.0
        >>> presence["email"]
        50.0
    """

    def __init__(
        self,
        *,
        delimiter: str = ",",
        indent: int = 2,
    ) -> None:
        """Initialize SparseArrayEncoder.

        Args:
            delimiter: Field delimiter for encoded output.
            indent: Number of spaces for indentation.

        Raises:
            ValueError: If delimiter is not supported.
            ValueError: If indent is not positive.
        """
        if delimiter not in (",", "\t", "|"):
            msg = f"Invalid delimiter: {delimiter!r}. Must be ',', '\\t', or '|'"
            raise ValueError(msg)
        if indent <= 0:
            msg = f"Invalid indent: {indent}. Must be positive"
            raise ValueError(msg)

        self._delimiter = delimiter
        self._indent = indent
        self._value_encoder = ValueEncoder()
        self._quoting_engine = QuotingEngine()

    def analyze_sparsity(
        self, array: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate presence rate for each field across array elements.

        Analyzes all dictionaries in the array to compute what percentage
        of elements contain each field with a non-None value.

        Args:
            array: List of dictionaries to analyze.

        Returns:
            Dictionary mapping field names to presence rates (0.0-100.0).
            Empty dict if array is empty.

        Examples:
            >>> encoder = SparseArrayEncoder()
            >>> encoder.analyze_sparsity([])
            {}

            >>> encoder.analyze_sparsity([{"id": 1}])
            {'id': 100.0}

            >>> result = encoder.analyze_sparsity([
            ...     {"id": 1, "email": "a@x.com"},
            ...     {"id": 2},
            ...     {"id": 3}
            ... ])
            >>> result["id"]
            100.0
            >>> result["email"]
            33.333333333333336

            >>> result = encoder.analyze_sparsity([
            ...     {"id": 1, "value": None},
            ...     {"id": 2, "value": 100}
            ... ])
            >>> result["value"]
            50.0
        """
        if not array:
            return {}

        # Collect all unique keys across all dictionaries
        all_keys: set[str] = set()
        for obj in array:
            if not isinstance(obj, dict):
                msg = f"Expected dict, got {type(obj).__name__}"
                raise TypeError(msg)
            all_keys.update(obj.keys())

        # Calculate presence rate for each key
        presence: dict[str, float] = {}
        array_len = len(array)

        for key in all_keys:
            count = sum(
                1
                for obj in array
                if key in obj and obj[key] is not None
            )
            presence[key] = count / array_len * 100

        return presence

    def is_sparse_eligible(
        self, array: list[dict[str, Any]], threshold: float = 30.0
    ) -> bool:
        """Determine if array should use sparse encoding format.

        An array is sparse-eligible when at least one field has
        30% or more missing values (presence rate <= 70%).

        Args:
            array: List of dictionaries to analyze.
            threshold: Minimum percentage of missing values to qualify as sparse.

        Returns:
            True if array should use sparse format, False otherwise.

        Examples:
            >>> encoder = SparseArrayEncoder()
            >>> # 33% missing email = sparse eligible
            >>> encoder.is_sparse_eligible([
            ...     {"id": 1, "email": "a@x.com"},
            ...     {"id": 2},
            ...     {"id": 3}
            ... ])
            True

            >>> # 0% missing = not sparse eligible
            >>> encoder.is_sparse_eligible([
            ...     {"id": 1, "name": "Alice"},
            ...     {"id": 2, "name": "Bob"}
            ... ])
            False
        """
        if not array:
            return False

        presence = self.analyze_sparsity(array)

        # Check if any field has presence rate below (100 - threshold)
        for rate in presence.values():
            if rate <= (100.0 - threshold):
                return True

        return False

    def get_sparse_fields(
        self, array: list[dict[str, Any]]
    ) -> tuple[list[str], list[str]]:
        """Get lists of required and optional fields.

        Args:
            array: List of dictionaries to analyze.

        Returns:
            Tuple of (required_fields, optional_fields) both sorted.
            Required fields have 100% presence, optional have < 100%.

        Examples:
            >>> encoder = SparseArrayEncoder()
            >>> required, optional = encoder.get_sparse_fields([
            ...     {"id": 1, "email": "a@x.com"},
            ...     {"id": 2}
            ... ])
            >>> required
            ['id']
            >>> optional
            ['email']
        """
        if not array:
            return [], []

        presence = self.analyze_sparsity(array)

        required: list[str] = []
        optional: list[str] = []

        for key in sorted(presence.keys()):
            if presence[key] >= 100.0:
                required.append(key)
            else:
                optional.append(key)

        return required, optional

    def encode_sparse(self, array: list[dict[str, Any]]) -> str:
        """Encode array with optional field markers.

        Generates TOON sparse format with ? suffix for optional fields
        and empty string for null/missing values.

        Args:
            array: List of dictionaries to encode.

        Returns:
            TOON sparse encoded string.

        Raises:
            TypeError: If array contains non-dict elements.
            ValueError: If array is empty.

        Examples:
            >>> encoder = SparseArrayEncoder()
            >>> result = encoder.encode_sparse([
            ...     {"id": 1, "name": "Alice", "email": "a@x.com"},
            ...     {"id": 2, "name": "Bob"},
            ...     {"id": 3, "name": "Charlie", "email": "c@x.com"}
            ... ])
            >>> "email?" in result
            True
            >>> "2,Bob," in result
            True
        """
        if not array:
            msg = "Cannot encode empty array in sparse format"
            raise ValueError(msg)

        presence = self.analyze_sparsity(array)

        # Build field list with optional markers
        fields: list[str] = []
        for key in sorted(presence.keys()):
            if presence[key] < 100.0:
                fields.append(f"{key}?")
            else:
                fields.append(key)

        # Generate header
        header = f"[{len(array)}]{{{self._delimiter.join(fields)}}}:"

        # Encode rows
        rows: list[str] = []
        for obj in array:
            values: list[str] = []
            for field in fields:
                key = field.rstrip("?")
                value = obj.get(key)

                if value is None:
                    # Empty string represents null/missing
                    values.append("")
                else:
                    # Encode the value
                    encoded = self._value_encoder.encode_value(value)
                    # Quote if needed
                    if self._quoting_engine.needs_quoting(
                        encoded, self._delimiter
                    ):
                        encoded = self._quoting_engine.quote_string(encoded)
                    values.append(encoded)

            row = self._delimiter.join(values)
            rows.append(row)

        # Combine header and rows with indentation
        indent_str = " " * self._indent
        lines = [header]
        for row in rows:
            lines.append(f"{indent_str}{row}")

        return "\n".join(lines)
