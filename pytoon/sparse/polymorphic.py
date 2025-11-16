"""PolymorphicArrayEncoder class for PyToon.

This module provides functionality to encode arrays containing different
object types using discriminator-based sub-tables.
"""

from typing import Any

from pytoon.sparse.sparse import SparseArrayEncoder


class PolymorphicArrayEncoder:
    """Encode arrays with different object types using sub-tables.

    The PolymorphicArrayEncoder groups array elements by discriminator
    field (typically "type") and creates optimized sub-tables for each
    type with only the fields relevant to that type.

    Polymorphic Format Example:
        items[3]:
          @type:Product
          [1]{id,name,price}:
            101,Widget,9.99
          @type:Service
          [2]{id,name,hourly_rate}:
            201,Consulting,150
            202,Support,75

    Examples:
        >>> encoder = PolymorphicArrayEncoder()
        >>> data = [
        ...     {"type": "Product", "id": 101, "name": "Widget", "price": 9.99},
        ...     {"type": "Service", "id": 201, "name": "Consulting", "hourly_rate": 150},
        ... ]
        >>> result = encoder.encode_polymorphic(data)
        >>> "@type:Product" in result
        True
    """

    def __init__(
        self,
        *,
        delimiter: str = ",",
        indent: int = 2,
    ) -> None:
        """Initialize PolymorphicArrayEncoder.

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

    def analyze_polymorphism(
        self,
        array: list[dict[str, Any]],
        type_field: str = "type",
    ) -> dict[str, int]:
        """Analyze array to count elements by type.

        Args:
            array: List of dictionaries to analyze.
            type_field: Name of the discriminator field.

        Returns:
            Dictionary mapping type names to counts.

        Examples:
            >>> encoder = PolymorphicArrayEncoder()
            >>> data = [
            ...     {"type": "A", "value": 1},
            ...     {"type": "B", "value": 2},
            ...     {"type": "A", "value": 3},
            ... ]
            >>> encoder.analyze_polymorphism(data)
            {'A': 2, 'B': 1}
        """
        counts: dict[str, int] = {}

        for obj in array:
            if not isinstance(obj, dict):
                msg = f"Expected dict, got {type(obj).__name__}"
                raise TypeError(msg)

            obj_type = str(obj.get(type_field, "Unknown"))

            if obj_type not in counts:
                counts[obj_type] = 0
            counts[obj_type] += 1

        return counts

    def is_polymorphic_eligible(
        self,
        array: list[dict[str, Any]],
        type_field: str = "type",
        min_types: int = 2,
    ) -> bool:
        """Determine if array should use polymorphic encoding format.

        An array is polymorphic-eligible when it contains elements
        of at least min_types different types.

        Args:
            array: List of dictionaries to analyze.
            type_field: Name of the discriminator field.
            min_types: Minimum number of different types required.

        Returns:
            True if array should use polymorphic format, False otherwise.

        Examples:
            >>> encoder = PolymorphicArrayEncoder()
            >>> encoder.is_polymorphic_eligible([
            ...     {"type": "A", "value": 1},
            ...     {"type": "B", "value": 2}
            ... ])
            True

            >>> encoder.is_polymorphic_eligible([
            ...     {"type": "A", "value": 1},
            ...     {"type": "A", "value": 2}
            ... ])
            False
        """
        if not array:
            return False

        counts = self.analyze_polymorphism(array, type_field)
        return len(counts) >= min_types

    def group_by_type(
        self,
        array: list[dict[str, Any]],
        type_field: str = "type",
    ) -> dict[str, list[dict[str, Any]]]:
        """Group array elements by discriminator field value.

        Args:
            array: List of dictionaries to group.
            type_field: Name of the discriminator field.

        Returns:
            Dictionary mapping type names to lists of elements (without type field).

        Examples:
            >>> encoder = PolymorphicArrayEncoder()
            >>> data = [
            ...     {"type": "A", "id": 1},
            ...     {"type": "B", "id": 2},
            ...     {"type": "A", "id": 3}
            ... ]
            >>> groups = encoder.group_by_type(data)
            >>> len(groups["A"])
            2
            >>> "type" in groups["A"][0]
            False
        """
        groups: dict[str, list[dict[str, Any]]] = {}

        for obj in array:
            if not isinstance(obj, dict):
                msg = f"Expected dict, got {type(obj).__name__}"
                raise TypeError(msg)

            obj_type = str(obj.get(type_field, "Unknown"))

            if obj_type not in groups:
                groups[obj_type] = []

            # Remove type field from object copy
            obj_copy = {k: v for k, v in obj.items() if k != type_field}
            groups[obj_type].append(obj_copy)

        return groups

    def encode_polymorphic(
        self,
        array: list[dict[str, Any]],
        type_field: str = "type",
    ) -> str:
        """Encode array with discriminator-based sub-tables.

        Groups elements by type and encodes each group with its optimal
        schema (only fields relevant to that type).

        Args:
            array: List of dictionaries to encode.
            type_field: Name of the discriminator field.

        Returns:
            TOON polymorphic encoded string.

        Raises:
            TypeError: If array contains non-dict elements.
            ValueError: If array is empty.

        Examples:
            >>> encoder = PolymorphicArrayEncoder()
            >>> data = [
            ...     {"type": "Product", "id": 101, "name": "Widget", "price": 9.99},
            ...     {"type": "Service", "id": 201, "name": "Consulting", "hourly_rate": 150},
            ... ]
            >>> result = encoder.encode_polymorphic(data)
            >>> "@type:Product" in result
            True
            >>> "@type:Service" in result
            True
            >>> "price" in result
            True
            >>> "hourly_rate" in result
            True
        """
        if not array:
            msg = "Cannot encode empty array in polymorphic format"
            raise ValueError(msg)

        groups = self.group_by_type(array, type_field)

        # Build output
        lines: list[str] = [f"[{len(array)}]:"]

        indent_str = " " * self._indent
        double_indent = indent_str * 2

        # Sort types for consistent output
        for type_name in sorted(groups.keys()):
            items = groups[type_name]

            # Add type header
            lines.append(f"{indent_str}@type:{type_name}")

            # Encode sub-table for this type
            sub_encoder = SparseArrayEncoder(
                delimiter=self._delimiter,
                indent=self._indent,
            )

            if items:
                sub_toon = sub_encoder.encode_sparse(items)

                # Indent the sub-table
                for line in sub_toon.split("\n"):
                    lines.append(f"{double_indent}{line}")

        return "\n".join(lines)
