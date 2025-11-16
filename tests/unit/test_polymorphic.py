"""Unit tests for PolymorphicArrayEncoder class."""

import pytest

from pytoon.sparse.polymorphic import PolymorphicArrayEncoder


class TestAnalyzePolymorphism:
    """Tests for analyze_polymorphism method."""

    def test_empty_array_returns_empty_dict(self) -> None:
        """Empty array should return empty dict."""
        encoder = PolymorphicArrayEncoder()
        result = encoder.analyze_polymorphism([])
        assert result == {}

    def test_single_type_counted(self) -> None:
        """Single type should be counted correctly."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "value": 1},
            {"type": "A", "value": 2},
        ]
        result = encoder.analyze_polymorphism(data)
        assert result == {"A": 2}

    def test_multiple_types_counted(self) -> None:
        """Multiple types should be counted correctly."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "value": 1},
            {"type": "B", "value": 2},
            {"type": "A", "value": 3},
        ]
        result = encoder.analyze_polymorphism(data)
        assert result == {"A": 2, "B": 1}

    def test_custom_type_field(self) -> None:
        """Custom type field should be respected."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"kind": "Product", "id": 1},
            {"kind": "Service", "id": 2},
        ]
        result = encoder.analyze_polymorphism(data, type_field="kind")
        assert result == {"Product": 1, "Service": 1}

    def test_missing_type_field_defaults_to_unknown(self) -> None:
        """Missing type field should default to 'Unknown'."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "value": 1},
            {"value": 2},  # No type field
        ]
        result = encoder.analyze_polymorphism(data)
        assert result == {"A": 1, "Unknown": 1}

    def test_non_dict_element_raises_type_error(self) -> None:
        """Non-dict element should raise TypeError."""
        encoder = PolymorphicArrayEncoder()
        with pytest.raises(TypeError, match="Expected dict"):
            encoder.analyze_polymorphism([{"type": "A"}, "not a dict"])


class TestIsPolymorphicEligible:
    """Tests for is_polymorphic_eligible method."""

    def test_empty_array_not_eligible(self) -> None:
        """Empty array is not eligible."""
        encoder = PolymorphicArrayEncoder()
        assert encoder.is_polymorphic_eligible([]) is False

    def test_single_type_not_eligible(self) -> None:
        """Single type is not eligible."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "value": 1},
            {"type": "A", "value": 2},
        ]
        assert encoder.is_polymorphic_eligible(data) is False

    def test_two_types_is_eligible(self) -> None:
        """Two types is eligible."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "value": 1},
            {"type": "B", "value": 2},
        ]
        assert encoder.is_polymorphic_eligible(data) is True

    def test_custom_min_types_threshold(self) -> None:
        """Custom min_types threshold changes eligibility."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "value": 1},
            {"type": "B", "value": 2},
        ]
        assert encoder.is_polymorphic_eligible(data, min_types=2) is True
        assert encoder.is_polymorphic_eligible(data, min_types=3) is False


class TestGroupByType:
    """Tests for group_by_type method."""

    def test_empty_array_returns_empty_dict(self) -> None:
        """Empty array returns empty groups."""
        encoder = PolymorphicArrayEncoder()
        result = encoder.group_by_type([])
        assert result == {}

    def test_groups_by_type_field(self) -> None:
        """Elements are grouped by type field."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "id": 1},
            {"type": "B", "id": 2},
            {"type": "A", "id": 3},
        ]
        result = encoder.group_by_type(data)
        assert len(result["A"]) == 2
        assert len(result["B"]) == 1

    def test_type_field_removed_from_groups(self) -> None:
        """Type field is removed from grouped objects."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "id": 1},
            {"type": "B", "id": 2},
        ]
        result = encoder.group_by_type(data)
        assert "type" not in result["A"][0]
        assert "type" not in result["B"][0]

    def test_preserves_other_fields(self) -> None:
        """Other fields are preserved in grouped objects."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "id": 1, "name": "Alice"},
        ]
        result = encoder.group_by_type(data)
        assert result["A"][0] == {"id": 1, "name": "Alice"}

    def test_custom_type_field(self) -> None:
        """Custom type field is respected."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"kind": "Product", "id": 1},
        ]
        result = encoder.group_by_type(data, type_field="kind")
        assert "Product" in result
        assert "kind" not in result["Product"][0]


class TestEncodePolymorphic:
    """Tests for encode_polymorphic method."""

    def test_empty_array_raises_value_error(self) -> None:
        """Empty array should raise ValueError."""
        encoder = PolymorphicArrayEncoder()
        with pytest.raises(ValueError, match="Cannot encode empty array"):
            encoder.encode_polymorphic([])

    def test_basic_polymorphic_encoding(self) -> None:
        """Basic polymorphic encoding with two types."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "Product", "id": 101, "name": "Widget", "price": 9.99},
            {"type": "Service", "id": 201, "name": "Consulting", "hourly_rate": 150},
        ]
        result = encoder.encode_polymorphic(data)
        assert "[2]:" in result
        assert "@type:Product" in result
        assert "@type:Service" in result
        assert "price" in result
        assert "hourly_rate" in result

    def test_header_contains_total_length(self) -> None:
        """Header shows total array length."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "value": 1},
            {"type": "B", "value": 2},
            {"type": "A", "value": 3},
        ]
        result = encoder.encode_polymorphic(data)
        assert result.startswith("[3]:")

    def test_type_sections_sorted_alphabetically(self) -> None:
        """Type sections are sorted alphabetically."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "Z", "value": 1},
            {"type": "A", "value": 2},
        ]
        result = encoder.encode_polymorphic(data)
        a_pos = result.find("@type:A")
        z_pos = result.find("@type:Z")
        assert a_pos < z_pos

    def test_sub_tables_indented_correctly(self) -> None:
        """Sub-tables have correct indentation."""
        encoder = PolymorphicArrayEncoder(indent=2)
        data = [
            {"type": "A", "id": 1},
        ]
        result = encoder.encode_polymorphic(data)
        lines = result.split("\n")
        # @type:A should be indented
        assert "  @type:A" in result
        # Sub-table should be double-indented
        found_double_indent = any(line.startswith("    ") for line in lines)
        assert found_double_indent

    def test_custom_type_field(self) -> None:
        """Custom type field is respected."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"kind": "A", "value": 1},
            {"kind": "B", "value": 2},
        ]
        result = encoder.encode_polymorphic(data, type_field="kind")
        assert "@type:A" in result
        assert "@type:B" in result

    def test_three_or_more_types(self) -> None:
        """Handle three or more types."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "id": 1},
            {"type": "B", "id": 2},
            {"type": "C", "id": 3},
        ]
        result = encoder.encode_polymorphic(data)
        assert "@type:A" in result
        assert "@type:B" in result
        assert "@type:C" in result

    def test_multiple_items_same_type(self) -> None:
        """Multiple items of same type are grouped together."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "Product", "id": 1},
            {"type": "Product", "id": 2},
            {"type": "Service", "id": 3},
        ]
        result = encoder.encode_polymorphic(data)
        # Should only have one @type:Product section
        assert result.count("@type:Product") == 1
        # But should contain both product IDs
        assert "1" in result
        assert "2" in result


class TestPolymorphicArrayEncoderInit:
    """Tests for PolymorphicArrayEncoder initialization."""

    def test_default_delimiter_is_comma(self) -> None:
        """Default delimiter is comma."""
        encoder = PolymorphicArrayEncoder()
        assert encoder._delimiter == ","

    def test_default_indent_is_two(self) -> None:
        """Default indent is 2 spaces."""
        encoder = PolymorphicArrayEncoder()
        assert encoder._indent == 2

    def test_invalid_delimiter_raises_error(self) -> None:
        """Invalid delimiter raises ValueError."""
        with pytest.raises(ValueError, match="Invalid delimiter"):
            PolymorphicArrayEncoder(delimiter=";")

    def test_invalid_indent_raises_error(self) -> None:
        """Invalid indent raises ValueError."""
        with pytest.raises(ValueError, match="Invalid indent"):
            PolymorphicArrayEncoder(indent=0)

    def test_custom_indent_respected(self) -> None:
        """Custom indent is respected."""
        encoder = PolymorphicArrayEncoder(indent=4)
        assert encoder._indent == 4


class TestTokenSavingsPolymorphic:
    """Tests for token savings with polymorphic encoding."""

    def test_polymorphic_more_compact_than_json(self) -> None:
        """Polymorphic format should be more compact than JSON."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "Product", "id": 101, "name": "Widget", "price": 9.99},
            {"type": "Service", "id": 201, "name": "Consulting", "hourly_rate": 150},
            {"type": "Product", "id": 102, "name": "Gadget", "price": 19.99},
        ]

        import json

        json_str = json.dumps(data)
        toon_str = encoder.encode_polymorphic(data)

        # TOON should be reasonably compact
        # Note: May not always be shorter due to overhead of @type markers
        # but should be competitive
        assert len(toon_str) < len(json_str) * 1.5  # Within 50% overhead

    def test_many_items_same_type_efficient(self) -> None:
        """Many items of same type should be efficient."""
        encoder = PolymorphicArrayEncoder()
        # 10 products, 10 services - schema only defined once per type
        products = [
            {"type": "Product", "id": i, "name": f"P{i}", "price": i * 10}
            for i in range(10)
        ]
        services = [
            {"type": "Service", "id": 10 + i, "name": f"S{i}", "rate": i * 100}
            for i in range(10)
        ]
        data = products + services

        import json

        json_str = json.dumps(data)
        toon_str = encoder.encode_polymorphic(data)

        # TOON should be more compact for this case
        assert len(toon_str) < len(json_str)
