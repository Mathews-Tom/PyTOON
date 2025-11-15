# Sparse Arrays Module Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/sparse/spec.md`
**Component ID:** SPARSE-001
**Priority:** P2 (v1.2 Feature - Advanced Data Structures)

---

## Context & Documentation

### Traceability Chain

1. **Formal Specification:** docs/specs/sparse/spec.md
   - SparseArrayEncoder: Optional field markers (`field?`)
   - PolymorphicArrayEncoder: Discriminator-based sub-tables (`@type:`)
   - Automatic sparsity detection (30%+ missing values)

2. **Research & Intelligence:** docs/research/intel.md
   - Handles real-world data with optional fields
   - Polymorphic collections (different object types in same array)
   - Token efficiency for sparse data

---

## Executive Summary

### Business Alignment

- **Purpose:** Efficiently encode arrays with optional/varying fields
- **Value Proposition:** Token savings for sparse data, support for polymorphic collections
- **Target Users:** Developers with heterogeneous or optional data

### Technical Approach

- **Architecture Pattern:** Discriminated union encoding
- **Technology Stack:** Python 3.8+, sparsity analysis
- **Implementation Timeline:** Weeks 9-11 (v1.2 release)

---

## Core Implementation

### SparseArrayEncoder

```python
class SparseArrayEncoder:
    """Encode arrays with optional fields.

    Sparse Format (30%+ missing):
    users[3]{id,name,email?}:
      1,Alice,alice@example.com
      2,Bob,
      3,Charlie,charlie@example.com

    The '?' marks optional fields, empty means null.
    """

    def analyze_sparsity(self, array: list[dict[str, Any]]) -> dict[str, float]:
        """Calculate presence rate for each field."""
        if not array:
            return {}

        all_keys = set()
        for obj in array:
            all_keys.update(obj.keys())

        presence: dict[str, float] = {}
        for key in all_keys:
            count = sum(1 for obj in array if key in obj and obj[key] is not None)
            presence[key] = count / len(array) * 100

        return presence

    def encode_sparse(self, array: list[dict[str, Any]]) -> str:
        """Encode with optional field markers."""
        presence = self.analyze_sparsity(array)

        # Mark optional fields (< 100% presence)
        fields = []
        for key in sorted(presence.keys()):
            if presence[key] < 100:
                fields.append(f"{key}?")
            else:
                fields.append(key)

        # Encode rows
        rows = []
        for obj in array:
            values = []
            for field in fields:
                key = field.rstrip("?")
                value = obj.get(key)
                if value is None:
                    values.append("")  # Empty for null
                else:
                    values.append(str(value))
            rows.append(",".join(values))

        header = f"[{len(array)}]{{{','.join(fields)}}}:"
        return header + "\n" + "\n".join(f"  {row}" for row in rows)


class PolymorphicArrayEncoder:
    """Encode arrays with different object types.

    Polymorphic Format:
    items[3]:
      @type:Product
      [1]{id,name,price}:
        101,Widget,9.99
      @type:Service
      [2]{id,name,hourly_rate}:
        201,Consulting,150
        202,Support,75
    """

    def encode_polymorphic(
        self, array: list[dict[str, Any]], type_field: str = "type"
    ) -> str:
        """Group by type and encode as sub-tables."""
        groups: dict[str, list[dict[str, Any]]] = {}

        for obj in array:
            obj_type = obj.get(type_field, "Unknown")
            if obj_type not in groups:
                groups[obj_type] = []
            # Remove type field from object
            obj_copy = {k: v for k, v in obj.items() if k != type_field}
            groups[obj_type].append(obj_copy)

        # Encode each group as sub-table
        lines = [f"[{len(array)}]:"]
        for type_name, items in groups.items():
            lines.append(f"  @type:{type_name}")
            sub_encoder = SparseArrayEncoder()
            sub_toon = sub_encoder.encode_sparse(items)
            # Indent sub-table
            for line in sub_toon.split("\n"):
                lines.append(f"  {line}")

        return "\n".join(lines)
```

---

## Implementation Roadmap

### Phase 1: Sparsity Analysis (Week 9, Days 1-2)

**Tasks:**

- [ ] Create `pytoon/sparse/__init__.py`
- [ ] Implement analyze_sparsity()
- [ ] Determine optimal threshold (30% missing → sparse format)
- [ ] Unit tests for sparsity detection

### Phase 2: Sparse Encoding (Week 9, Days 3-4)

**Tasks:**

- [ ] SparseArrayEncoder with optional markers
- [ ] Empty-as-null convention
- [ ] Integration with ArrayEncoder dispatch
- [ ] Token savings benchmarks

### Phase 3: Polymorphic Arrays (Weeks 10-11)

**Tasks:**

- [ ] PolymorphicArrayEncoder with discriminator
- [ ] Sub-table grouping logic
- [ ] decode support for polymorphic format
- [ ] Integration tests with mixed types

---

## API Surface

```python
from pytoon import encode

# Automatic sparse detection
data = [
    {"id": 1, "name": "Alice", "email": "a@example.com"},
    {"id": 2, "name": "Bob"},  # No email
    {"id": 3, "name": "Charlie", "email": "c@example.com"},
]
# Automatically uses sparse format if >30% missing
toon = encode(data)

# Polymorphic arrays
items = [
    {"type": "Product", "id": 101, "name": "Widget", "price": 9.99},
    {"type": "Service", "id": 201, "name": "Consulting", "hourly_rate": 150},
]
toon = encode(items)  # Groups by type field
```

---

## Quality Assurance

```python
class TestSparseArrays:
    def test_optional_field_marker(self) -> None:
        """Test ? marker for optional fields."""
        encoder = SparseArrayEncoder()
        data = [{"id": 1, "email": "a@x.com"}, {"id": 2}]
        toon = encoder.encode_sparse(data)
        assert "email?" in toon  # Optional marker

    def test_sparsity_threshold(self) -> None:
        """Test 30% threshold for sparse format."""
        encoder = SparseArrayEncoder()
        # 50% sparse = should mark as optional
        data = [{"id": 1, "x": 1}, {"id": 2}]
        presence = encoder.analyze_sparsity(data)
        assert presence["x"] == 50.0

    def test_polymorphic_grouping(self) -> None:
        """Test type-based grouping."""
        encoder = PolymorphicArrayEncoder()
        data = [
            {"type": "A", "value": 1},
            {"type": "B", "value": 2},
        ]
        toon = encoder.encode_polymorphic(data)
        assert "@type:A" in toon
        assert "@type:B" in toon
```

---

## References & Traceability

**Specification:** docs/specs/sparse/spec.md
**Dependencies:** ENCODER-001 (ArrayEncoder dispatch)
**Version:** v1.2 feature

---

**Document Version**: 1.0
**Implementation Status**: Ready for v1.2 Ticket Generation
