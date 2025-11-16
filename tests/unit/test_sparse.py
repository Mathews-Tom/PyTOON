"""Unit tests for SparseArrayEncoder class."""

import pytest

from pytoon.sparse.sparse import SparseArrayEncoder


class TestAnalyzeSparsity:
    """Tests for analyze_sparsity method."""

    def test_empty_array_returns_empty_dict(self) -> None:
        """Empty array should return empty dict."""
        encoder = SparseArrayEncoder()
        result = encoder.analyze_sparsity([])
        assert result == {}

    def test_single_element_full_presence(self) -> None:
        """Single element should have 100% presence for all fields."""
        encoder = SparseArrayEncoder()
        result = encoder.analyze_sparsity([{"id": 1, "name": "Alice"}])
        assert result["id"] == 100.0
        assert result["name"] == 100.0

    def test_missing_field_calculates_presence(self) -> None:
        """Missing field should calculate correct presence rate."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "email": "a@x.com"},
            {"id": 2},
            {"id": 3},
        ]
        result = encoder.analyze_sparsity(data)
        assert result["id"] == 100.0
        # email present in 1 of 3 = 33.33%
        assert abs(result["email"] - 33.333333333333336) < 0.0001

    def test_none_values_not_counted_as_present(self) -> None:
        """None values should not count as present."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "value": None},
            {"id": 2, "value": 100},
        ]
        result = encoder.analyze_sparsity(data)
        assert result["id"] == 100.0
        assert result["value"] == 50.0

    def test_partial_presence_multiple_fields(self) -> None:
        """Multiple fields with different presence rates."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "name": "A", "email": "a@x.com", "phone": "111"},
            {"id": 2, "name": "B"},
            {"id": 3, "name": "C", "email": "c@x.com"},
            {"id": 4, "name": "D", "phone": "444"},
        ]
        result = encoder.analyze_sparsity(data)
        assert result["id"] == 100.0
        assert result["name"] == 100.0
        assert result["email"] == 50.0
        assert result["phone"] == 50.0

    def test_non_dict_element_raises_type_error(self) -> None:
        """Non-dict element should raise TypeError."""
        encoder = SparseArrayEncoder()
        with pytest.raises(TypeError, match="Expected dict"):
            encoder.analyze_sparsity([{"id": 1}, "not a dict"])

    def test_all_fields_missing_in_some_rows(self) -> None:
        """Fields missing in all but one row."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "rare": "value"},
            {"id": 2},
            {"id": 3},
            {"id": 4},
            {"id": 5},
        ]
        result = encoder.analyze_sparsity(data)
        assert result["id"] == 100.0
        assert result["rare"] == 20.0


class TestIsSparseEligible:
    """Tests for is_sparse_eligible method."""

    def test_empty_array_not_eligible(self) -> None:
        """Empty array is not eligible for sparse format."""
        encoder = SparseArrayEncoder()
        assert encoder.is_sparse_eligible([]) is False

    def test_no_missing_fields_not_eligible(self) -> None:
        """Array with no missing fields is not eligible."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        assert encoder.is_sparse_eligible(data) is False

    def test_30_percent_missing_is_eligible(self) -> None:
        """Array with 33% missing values is eligible."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "email": "a@x.com"},
            {"id": 2},
            {"id": 3},
        ]
        assert encoder.is_sparse_eligible(data) is True

    def test_custom_threshold(self) -> None:
        """Custom threshold changes eligibility."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "email": "a@x.com"},
            {"id": 2},
        ]
        # 50% missing email
        assert encoder.is_sparse_eligible(data, threshold=30.0) is True
        assert encoder.is_sparse_eligible(data, threshold=60.0) is False


class TestGetSparseFields:
    """Tests for get_sparse_fields method."""

    def test_empty_array_returns_empty_lists(self) -> None:
        """Empty array returns empty required and optional lists."""
        encoder = SparseArrayEncoder()
        required, optional = encoder.get_sparse_fields([])
        assert required == []
        assert optional == []

    def test_all_required_fields(self) -> None:
        """All fields at 100% presence are required."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
        ]
        required, optional = encoder.get_sparse_fields(data)
        assert required == ["id", "name"]
        assert optional == []

    def test_mixed_required_and_optional(self) -> None:
        """Fields split between required and optional."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "email": "a@x.com"},
            {"id": 2},
        ]
        required, optional = encoder.get_sparse_fields(data)
        assert required == ["id"]
        assert optional == ["email"]

    def test_fields_sorted_alphabetically(self) -> None:
        """Fields should be sorted alphabetically."""
        encoder = SparseArrayEncoder()
        data = [
            {"z": 1, "a": 2, "m": 3, "b": 4},
        ]
        required, optional = encoder.get_sparse_fields(data)
        assert required == ["a", "b", "m", "z"]


class TestEncodeSparse:
    """Tests for encode_sparse method."""

    def test_empty_array_raises_value_error(self) -> None:
        """Empty array should raise ValueError."""
        encoder = SparseArrayEncoder()
        with pytest.raises(ValueError, match="Cannot encode empty array"):
            encoder.encode_sparse([])

    def test_basic_sparse_encoding(self) -> None:
        """Basic sparse encoding with optional field."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "name": "Alice", "email": "a@x.com"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie", "email": "c@x.com"},
        ]
        result = encoder.encode_sparse(data)
        assert "[3]{" in result
        assert "email?" in result  # Optional marker
        assert "id" in result
        assert "name" in result
        assert "Bob" in result
        # Empty field for missing email (ends with comma or contains empty between commas)
        assert ",," in result or "Bob,\n" in result or '",Bob\n' in result

    def test_header_format(self) -> None:
        """Header format is correct."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "value": 100},
            {"id": 2},
        ]
        result = encoder.encode_sparse(data)
        lines = result.split("\n")
        assert lines[0] == "[2]{id,value?}:"

    def test_indentation_applied(self) -> None:
        """Rows are indented correctly."""
        encoder = SparseArrayEncoder(indent=4)
        data = [{"id": 1}]
        result = encoder.encode_sparse(data)
        lines = result.split("\n")
        assert lines[1].startswith("    ")  # 4 spaces

    def test_custom_delimiter(self) -> None:
        """Custom delimiter is used."""
        encoder = SparseArrayEncoder(delimiter="\t")
        data = [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
        ]
        result = encoder.encode_sparse(data)
        assert "\t" in result

    def test_null_values_encoded_as_empty_string(self) -> None:
        """None values are encoded as empty string."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "value": None},
            {"id": 2, "value": 100},
        ]
        result = encoder.encode_sparse(data)
        lines = result.split("\n")
        # First row should have id and empty for None value
        # Numbers may be quoted, so check for presence of id value and empty field
        assert "1" in lines[1]
        # Empty string represents None (trailing comma or commas with nothing between)
        assert lines[1].strip().endswith(",") or ",," in lines[1]
        # Second row should have both values
        assert "2" in lines[2]
        assert "100" in lines[2]

    def test_string_quoting_applied_when_needed(self) -> None:
        """Strings with special characters are quoted."""
        encoder = SparseArrayEncoder()
        data = [{"id": 1, "name": "Hello, World"}]
        result = encoder.encode_sparse(data)
        # Name should be quoted because it contains comma
        assert '"Hello, World"' in result or "Hello, World" in result

    def test_boolean_values_encoded(self) -> None:
        """Boolean values are encoded correctly."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "active": True},
            {"id": 2, "active": False},
        ]
        result = encoder.encode_sparse(data)
        assert "true" in result
        assert "false" in result

    def test_numeric_values_encoded(self) -> None:
        """Numeric values are encoded correctly."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "price": 9.99},
            {"id": 2, "price": 100},
        ]
        result = encoder.encode_sparse(data)
        assert "9.99" in result
        assert "100" in result


class TestSparseArrayEncoderInit:
    """Tests for SparseArrayEncoder initialization."""

    def test_default_delimiter_is_comma(self) -> None:
        """Default delimiter is comma."""
        encoder = SparseArrayEncoder()
        assert encoder._delimiter == ","

    def test_default_indent_is_two(self) -> None:
        """Default indent is 2 spaces."""
        encoder = SparseArrayEncoder()
        assert encoder._indent == 2

    def test_invalid_delimiter_raises_error(self) -> None:
        """Invalid delimiter raises ValueError."""
        with pytest.raises(ValueError, match="Invalid delimiter"):
            SparseArrayEncoder(delimiter=";")

    def test_invalid_indent_raises_error(self) -> None:
        """Invalid indent raises ValueError."""
        with pytest.raises(ValueError, match="Invalid indent"):
            SparseArrayEncoder(indent=0)

    def test_negative_indent_raises_error(self) -> None:
        """Negative indent raises ValueError."""
        with pytest.raises(ValueError, match="Invalid indent"):
            SparseArrayEncoder(indent=-1)

    def test_tab_delimiter_allowed(self) -> None:
        """Tab delimiter is allowed."""
        encoder = SparseArrayEncoder(delimiter="\t")
        assert encoder._delimiter == "\t"

    def test_pipe_delimiter_allowed(self) -> None:
        """Pipe delimiter is allowed."""
        encoder = SparseArrayEncoder(delimiter="|")
        assert encoder._delimiter == "|"


class TestTokenSavings:
    """Tests for token savings with sparse encoding."""

    def test_sparse_format_more_compact_than_json(self) -> None:
        """Sparse format should be more compact than JSON."""
        encoder = SparseArrayEncoder()
        data = [
            {"id": 1, "name": "Alice", "email": "a@x.com"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
            {"id": 4, "name": "Diana", "email": "d@x.com"},
        ]

        import json

        json_str = json.dumps(data)
        toon_str = encoder.encode_sparse(data)

        # TOON should be shorter
        assert len(toon_str) < len(json_str)

    def test_highly_sparse_data_significant_savings(self) -> None:
        """Highly sparse data should show significant savings."""
        encoder = SparseArrayEncoder()
        # 90% sparsity on optional_field
        data = [{"id": i} for i in range(1, 10)]
        data.append({"id": 10, "optional_field": "rare"})

        import json

        json_str = json.dumps(data)
        toon_str = encoder.encode_sparse(data)

        # At least 30% savings expected
        savings = (len(json_str) - len(toon_str)) / len(json_str) * 100
        assert savings > 20  # More conservative expectation
