# Encoder Module Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/encoder/spec.md`
**Component ID:** ENCODER-001
**Priority:** P0 (Core v1.0 Component)

---

## Context & Documentation

### Traceability Chain

1. **Formal Specification:** docs/specs/encoder/spec.md
   - FR-1: TabularAnalyzer (uniform array detection)
   - FR-2: ValueEncoder (primitive normalization)
   - FR-3: ArrayEncoder (format dispatch)
   - FR-4: ObjectEncoder (dict encoding)
   - FR-5: QuotingEngine (context-aware quoting)
   - FR-6: KeyFoldingEngine (dotted path optimization)

2. **Research & Intelligence:** docs/research/intel.md
   - Core value prop: 30-60% token savings
   - Competitive differentiator: Full v1.5+ spec compliance
   - Performance target: <100ms for 1-10KB datasets

3. **System Context:**
   - Architecture: `.sage/agent/system/architecture.md` - 6 encoder components
   - Patterns: `.sage/agent/examples/python/encoder/` - Encoder patterns

### Related Documentation

**Dependencies:**

- **CORE-001:** Encoder delegates to these components
- **UTILS-001:** Exception classes (TOONEncodeError)

**Dependents:**

- **CORE-001:** Core.Encoder uses these components
- **DECISION-001:** DataMetrics uses TabularAnalyzer scores

---

## Executive Summary

### Business Alignment

- **Purpose:** Transform Python objects into token-optimized TOON strings
- **Value Proposition:** 30-60% token savings through intelligent tabular format selection
- **Target Users:** LLM application developers optimizing API costs

### Technical Approach

- **Architecture Pattern:** Strategy Pattern (format dispatch based on data analysis)
- **Technology Stack:** Python 3.8+, zero dependencies, O(n) complexity
- **Implementation Strategy:** Bottom-up (primitives → arrays → objects → optimization)

### Key Success Metrics

**SLOs:**

- Token Efficiency: 30-60% reduction vs JSON on tabular data
- Performance: <100ms encoding for 1-10KB datasets
- Accuracy: 100% spec compliance (TOON v1.5+)

**KPIs:**

- Test Coverage: 85%+ per component
- Type Safety: mypy strict compliance
- Roundtrip Fidelity: 100% data preservation

---

## Code Examples & Patterns

### Repository Patterns

**1. ValueEncoder Pattern:** `.sage/agent/examples/python/encoder/`

```python
def encode_value(value: Any) -> str:
    """Normalize Python primitive to TOON representation.

    Args:
        value: Python primitive (None, bool, int, float, str)

    Returns:
        TOON-formatted string

    Raises:
        TOONEncodeError: If value is unsupported type

    Type Conversions:
        None → "null"
        True → "true"
        False → "false"
        int → decimal string
        float → decimal string (no scientific notation)
        float('nan') → "null"
        float('inf') → "null"
        -0.0 → "0"
        str → quoted if needed
    """
    if value is None:
        return "null"

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "null"
        if value == -0.0:
            return "0"
        # No scientific notation
        return f"{value:f}".rstrip("0").rstrip(".")

    if isinstance(value, str):
        return quote_if_needed(value)

    raise TOONEncodeError(f"Cannot encode type: {type(value)}")
```

**2. TabularAnalyzer Pattern:**

```python
def analyze_array(array: list[Any]) -> tuple[bool, list[str], float]:
    """Determine if array qualifies for tabular format.

    Returns:
        (is_tabular, field_list, uniformity_score)
    """
    if not array:
        return (True, [], 0.0)

    if not all(isinstance(obj, dict) for obj in array):
        return (False, [], 0.0)

    # Check uniform keys
    field_sets = [frozenset(obj.keys()) for obj in array]
    if len(set(field_sets)) != 1:
        return (False, [], 0.0)

    fields = list(field_sets[0])

    # Check for nested structures (disqualifies tabular)
    for obj in array:
        for val in obj.values():
            if isinstance(val, (dict, list)):
                return (False, fields, 0.0)

    return (True, fields, 100.0)
```

**3. QuotingEngine Pattern:**

```python
def quote_if_needed(s: str) -> str:
    """Apply minimal quoting for token efficiency.

    Quote required when:
    - Empty string
    - Contains delimiter or structural chars
    - Looks like bool/number/null
    - Has leading/trailing whitespace
    - Starts with "- "
    - Matches structural tokens like [5] or {key}
    """
    if not s:
        return '""'

    if s in ("null", "true", "false"):
        return f'"{s}"'

    if s.strip() != s:
        return f'"{s}"'

    if any(c in s for c in [',', '\t', '|', ':', '\n', '"', '[', ']', '{']):
        return f'"{escape_string(s)}"'

    # Looks like number?
    try:
        float(s)
        return f'"{s}"'
    except ValueError:
        pass

    return s
```

### Key Takeaways

- Pure functions with no side effects
- O(n) single-pass algorithms
- Fail-fast error handling
- Context-aware quoting minimizes token usage

---

## Technology Stack

### Recommended Stack

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| Runtime | Python | 3.8+ | Modern type hints support |
| Math | stdlib math | 3.8+ | For isnan/isinf checks |
| Regex | stdlib re | 3.8+ | Pattern matching for quoting |
| Testing | pytest + Hypothesis | Latest | Property-based testing |
| Type Checking | mypy --strict | Latest | Production-ready quality |

**Key Technology Decisions:**

1. **Single-Pass Algorithms:** O(n) complexity for encoding
2. **No External Dependencies:** stdlib only (math, re)
3. **Strategy Pattern:** ArrayEncoder dispatches to format handlers

---

## Architecture Design

### Component Breakdown

**6 Encoder Components:**

1. **TabularAnalyzer**
   - **Purpose:** Detect uniform arrays for tabular encoding
   - **Input:** `list[Any]`
   - **Output:** `tuple[bool, list[str], float]`
   - **Algorithm:** Check uniform keys, no nested structures

2. **ValueEncoder**
   - **Purpose:** Normalize primitives to TOON representation
   - **Input:** `Any` (primitive)
   - **Output:** `str`
   - **Type Conversions:** None→null, bool→true/false, numbers→decimal

3. **ArrayEncoder**
   - **Purpose:** Dispatch array encoding strategy
   - **Input:** `list[Any]`, indent level
   - **Output:** `str`
   - **Strategies:** Tabular, Inline, List formats

4. **ObjectEncoder**
   - **Purpose:** Encode dictionaries with indentation
   - **Input:** `dict[str, Any]`, indent level
   - **Output:** `str`
   - **Algorithm:** Iterate keys, encode values recursively

5. **QuotingEngine**
   - **Purpose:** Context-aware minimal quoting
   - **Input:** `str`
   - **Output:** `str` (quoted if needed)
   - **Rules:** Quote only when ambiguous or containing special chars

6. **KeyFoldingEngine**
   - **Purpose:** Collapse single-key wrapper chains
   - **Input:** `dict[str, Any]`
   - **Output:** `dict[str, Any]` (with dotted keys)
   - **Example:** `{"a": {"b": {"c": 1}}}` → `{"a.b.c": 1}`

### Data Flow

```plaintext
Python Object
    │
    ▼
ObjectEncoder (if dict)
    │
    ├─→ KeyFoldingEngine (if key_folding='safe')
    │
    ├─→ ArrayEncoder (if list value)
    │      │
    │      ├─→ TabularAnalyzer (check uniformity)
    │      │      │
    │      │      ├─→ Tabular Format: [N]{fields}:\n  row1\n  row2
    │      │      │
    │      │      ├─→ Inline Format: [N] val1,val2,val3
    │      │      │
    │      │      └─→ List Format: [N]:\n  - val1\n  - val2
    │      │
    │      └─→ ValueEncoder (for each element)
    │
    └─→ ValueEncoder (for primitive values)
           │
           └─→ QuotingEngine (for strings)
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1, Days 1-2)

**Tasks:**

- [ ] Create `pytoon/encoder/__init__.py`
- [ ] Implement `pytoon/encoder/value_encoder.py`
  - encode_value() function
  - Type conversions per spec
  - No scientific notation for floats
- [ ] Implement `pytoon/encoder/quoting_engine.py`
  - quote_if_needed() function
  - escape_string() helper
- [ ] Write unit tests (85%+ coverage)
- [ ] mypy strict compliance

**Deliverables:**

- ValueEncoder with all type conversions
- QuotingEngine with minimal quoting logic
- 100+ test cases for edge cases

### Phase 2: Array Encoding (Week 1, Days 3-4)

**Tasks:**

- [ ] Implement `pytoon/encoder/tabular_analyzer.py`
  - analyze_array() function
  - Uniformity scoring
- [ ] Implement `pytoon/encoder/array_encoder.py`
  - Tabular format: `[N]{fields}:\n  row1\n  row2`
  - Inline format: `[N] val1,val2,val3`
  - List format: `[N]:\n  - val1\n  - val2`
- [ ] Write unit tests for all array formats
- [ ] Benchmark token savings vs JSON

**Deliverables:**

- TabularAnalyzer correctly identifies uniform arrays
- ArrayEncoder dispatches to correct format
- Token savings validated (30-60% on tabular data)

### Phase 3: Object Encoding (Week 1, Day 5)

**Tasks:**

- [ ] Implement `pytoon/encoder/object_encoder.py`
  - encode_object() function
  - Indentation management
  - Recursive encoding for nested objects
- [ ] Write integration tests
- [ ] Property-based tests with Hypothesis

**Deliverables:**

- ObjectEncoder handles nested structures
- Indentation correct at all levels
- Roundtrip fidelity validated

### Phase 4: Optimization (Week 2, Days 1-2)

**Tasks:**

- [ ] Implement `pytoon/encoder/key_folding_engine.py`
  - fold_keys() function
  - Safe mode only (no special chars in keys)
- [ ] Performance benchmarking
  - <100ms for 1-10KB datasets
- [ ] Code review and documentation
- [ ] Final integration with CORE-001

**Deliverables:**

- KeyFoldingEngine working
- Performance targets met
- Full documentation complete
- Ready for production use

---

## Quality Assurance

### Testing Strategy

**Unit Tests (85%+ coverage per component):**

```python
class TestValueEncoder:
    def test_encode_none(self) -> None:
        assert encode_value(None) == "null"

    def test_encode_bool(self) -> None:
        assert encode_value(True) == "true"
        assert encode_value(False) == "false"

    def test_encode_float_no_scientific(self) -> None:
        assert encode_value(1e6) == "1000000"

    def test_encode_nan(self) -> None:
        assert encode_value(float('nan')) == "null"

    def test_encode_negative_zero(self) -> None:
        assert encode_value(-0.0) == "0"


class TestTabularAnalyzer:
    def test_uniform_array(self) -> None:
        arr = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        is_tabular, fields, score = analyze_array(arr)
        assert is_tabular is True
        assert set(fields) == {"id", "name"}
        assert score == 100.0

    def test_nested_disqualifies(self) -> None:
        arr = [{"id": 1, "meta": {"x": 1}}]
        is_tabular, _, _ = analyze_array(arr)
        assert is_tabular is False
```

**Property-Based Tests (Hypothesis):**

```python
@given(st.lists(st.dictionaries(st.text(), st.integers())))
def test_array_encoding_roundtrip(data: list[dict[str, int]]) -> None:
    encoded = encode_array(data)
    decoded = decode_array(encoded)
    assert decoded == data
```

### Code Quality Gates

- [ ] mypy --strict passes
- [ ] ruff check passes
- [ ] 85%+ test coverage per component
- [ ] No TODOs in production code
- [ ] All docstrings complete

---

## Risk Management

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Quoting logic too complex | HIGH | MEDIUM | Follow JSON stdlib pattern, extensive edge case testing |
| Performance regression | MEDIUM | LOW | Benchmark early and often, O(n) enforcement |
| Spec ambiguity | MEDIUM | LOW | Reference TOON v1.5 spec, test against spec examples |
| Token savings overestimated | HIGH | LOW | Validate with real-world datasets, benchmarks |

---

## Error Handling & Edge Cases

### Error Scenarios

1. **Unsupported Type**
   - **Cause:** Custom class without handler
   - **Handling:** Raise TOONEncodeError with type info
   - **UX:** "Cannot encode type: <class 'MyClass'>"

2. **Circular Reference**
   - **Cause:** Object references itself
   - **Handling:** Detect with id() tracking, raise TOONEncodeError
   - **UX:** "Circular reference detected in object graph"

### Edge Cases

| Edge Case | Detection | Handling | Testing |
|-----------|-----------|----------|---------|
| Empty array | `len(array) == 0` | Return `[0]:` | Unit test |
| Single-element array | TabularAnalyzer | Inline if primitive | Unit test |
| String looks like number | QuotingEngine | Quote it | Parametrized test |
| Unicode in keys | KeyFoldingEngine | Preserve encoding | Unicode test suite |
| Very deeply nested | Recursion depth | Python default limit (~1000) | Stress test |

---

## References & Traceability

### Source Documentation

**Specification:** docs/specs/encoder/spec.md

- Functional requirements FR-1 through FR-6
- Type conversion table
- Array format specifications

**Research:** docs/research/intel.md

- Token savings target: 30-60%
- Performance target: <100ms for 1-10KB
- Competitive advantage: Full spec compliance

**Code Patterns:**

- `.sage/agent/examples/python/encoder/` - Encoder component patterns
- `.sage/agent/examples/python/types/` - Type hint patterns

### Related Components

**Dependencies:**

- **UTILS-001:** TOONEncodeError exception class

**Dependents:**

- **CORE-001:** Core.Encoder delegates to these components
- **DECISION-001:** Uses TabularAnalyzer for data metrics

---

**Document Version**: 1.0
**Implementation Status**: Ready for Ticket Generation
**Next Step**: `/sage.tasks` to break down into SMART tickets
