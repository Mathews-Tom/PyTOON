# Encoder Module Specification

**Component ID**: ENCODER-001
**Version**: v1.0
**Priority**: P0
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 2.1, `docs/research/intel.md`

---

## 1. Overview

### Purpose and Business Value

The Encoder module transforms Python objects into TOON-formatted strings optimized for token efficiency. It provides:

- **30-60% Token Savings**: Intelligent format selection for tabular data
- **Specification Compliance**: 100% adherence to TOON v1.5+ encoding rules
- **Context-Aware Quoting**: Minimal quoting while preserving parseability
- **Modular Design**: 6 specialized components for separation of concerns

### Success Metrics

- **Token Efficiency**: 30-60% reduction vs JSON on uniform tabular data
- **Encoding Performance**: <100ms for 1-10KB datasets
- **Test Coverage**: 85%+ code coverage
- **Roundtrip Fidelity**: 100% data preservation through encode→decode cycle

### Target Users

- **LLM Application Developers**: Reducing API token costs
- **Data Engineers**: Serializing uniform datasets efficiently
- **ML Engineers**: Preparing training data in token-optimized format

---

## 2. Functional Requirements

### FR-1: TabularAnalyzer

**Requirement**: The Encoder module SHALL analyze arrays to determine tabular format eligibility.

**Details**:

- Detect uniform arrays (all elements are dicts with identical keys)
- Reject arrays with nested objects/arrays in values
- Calculate tabular eligibility score (0-100%)
- Return field list for tabular encoding

**Acceptance Criteria**:

- [ ] Returns `(True, fields, 100.0)` for uniform arrays with primitive values
- [ ] Returns `(False, [], 0.0)` for arrays with nested structures
- [ ] Returns `(False, [], 0.0)` for heterogeneous arrays (different keys)
- [ ] Handles empty arrays correctly: `(True, [], 0.0)`

**Algorithm**:

```python
def analyze_array(array: list[Any]) -> tuple[bool, list[str], float]:
    if not array:
        return (True, [], 0.0)

    if not all(isinstance(obj, dict) for obj in array):
        return (False, [], 0.0)

    field_sets = [set(obj.keys()) for obj in array]
    if not all_equal(field_sets):
        return (False, [], 0.0)

    common_fields = list(field_sets[0])

    # Check for nested structures
    for obj in array:
        for value in obj.values():
            if isinstance(value, (dict, list)):
                return (False, common_fields, 0.0)

    return (True, common_fields, 100.0)
```

### FR-2: ValueEncoder

**Requirement**: The Encoder module SHALL normalize primitive Python values to TOON representation.

**Details**:

- Type conversions per TOON v1.5 spec:
  - `None` → `"null"`
  - `True`/`False` → `"true"`/`"false"` (lowercase)
  - Numbers → decimal notation (no scientific notation)
  - `float('nan')`, `float('inf')` → `"null"`
  - `-0.0` → `"0"` (normalized to positive zero)
- Context-aware string quoting via QuotingEngine

**Acceptance Criteria**:

- [ ] Encodes `None` as `"null"`
- [ ] Encodes booleans as lowercase `"true"`/`"false"`
- [ ] Encodes `1e6` as `"1000000"` (no scientific notation)
- [ ] Encodes `float('nan')` as `"null"`
- [ ] Encodes `-0.0` as `"0"`
- [ ] Applies quoting rules correctly via QuotingEngine

**Type Conversion Table**:

| Python Type | TOON Output | Notes |
|-------------|-------------|-------|
| `None` | `null` | JSON-compatible |
| `True` / `False` | `true` / `false` | Lowercase per spec |
| `42` | `42` | Integer as-is |
| `3.14` | `3.14` | Float as-is |
| `1e6` | `1000000` | No scientific notation |
| `float('nan')` | `null` | Non-finite → null |
| `float('inf')` | `null` | Non-finite → null |
| `-0.0` | `0` | Normalized |
| `"hello"` | `hello` (or `"hello"` if needed) | Context-aware quoting |

### FR-3: ArrayEncoder

**Requirement**: The Encoder module SHALL dispatch arrays to optimal format based on structure.

**Details**:

- **Tabular Format**: Uniform dicts → `array[N]{fields}: rows`
- **Inline Format**: All primitives → `array[N]: val1,val2,val3`
- **List Format**: Mixed/nested → `array[N]:\n  - item1\n  - item2`

**Acceptance Criteria**:

- [ ] Uses tabular format for uniform arrays with primitive values
- [ ] Uses inline format for primitive-only arrays
- [ ] Uses list format for mixed/nested arrays
- [ ] Generates correct array headers: `[N]`, `[N]{fields}`, `[N\t]{fields}`

**Format Selection Logic**:

```python
def encode_array(array: list[Any], indent_level: int) -> str:
    is_tabular, fields, _ = TabularAnalyzer.analyze(array)

    if is_tabular and fields:
        return encode_tabular_array(array, fields, indent_level)
    elif all(is_primitive(item) for item in array):
        return encode_inline_array(array)
    else:
        return encode_list_array(array, indent_level)
```

**Examples**:

```python
# Tabular
[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
# → users[2]{id,name}:
#     1,Alice
#     2,Bob

# Inline
["a", "b", "c"]
# → tags[3]: a,b,c

# List
[{"key": "value"}, "string", 42]
# → items[3]:
#     - key: value
#     - string
#     - 42
```

### FR-4: ObjectEncoder

**Requirement**: The Encoder module SHALL encode Python dicts with proper indentation and nesting.

**Details**:

- Iterate object keys and values
- Apply indentation based on nesting level (default: 2 spaces)
- Dispatch nested dicts to ObjectEncoder recursively
- Dispatch arrays to ArrayEncoder
- Delegate primitives to ValueEncoder

**Acceptance Criteria**:

- [ ] Encodes flat dicts correctly: `key: value`
- [ ] Encodes nested dicts with proper indentation
- [ ] Detects and encodes arrays via ArrayEncoder
- [ ] Preserves key order (insertion order in Python 3.7+)

**Example**:

```python
{
    "name": "Alice",
    "contact": {
        "email": "alice@example.com",
        "phone": "123-456-7890"
    },
    "tags": ["admin", "ops"]
}

# Encoded:
name: Alice
contact:
  email: alice@example.com
  phone: 123-456-7890
tags[2]: admin,ops
```

### FR-5: QuotingEngine

**Requirement**: The Encoder module SHALL apply context-aware quoting to minimize tokens while maintaining parseability.

**Details**:

- Quote strings when:
  - Empty (`""`)
  - Contains active delimiter (`,`, `\t`, or `|`)
  - Contains structural characters (`:`, `"`, `\`, newlines)
  - Looks like boolean/number/null (`"true"`, `"42"`, `"null"`)
  - Has leading/trailing whitespace (`" padded "`)
  - Starts with list marker (`"- item"`)
  - Looks like structural token (`"[5]"`, `"{key}"`)
- Escape sequences: `\"`, `\\`, `\n`, `\r`, `\t`

**Acceptance Criteria**:

- [ ] Quotes empty strings: `""`
- [ ] Quotes strings containing delimiter: `"a,b"` (when delimiter is comma)
- [ ] Quotes strings matching boolean/null/number: `"true"`, `"null"`, `"42"`
- [ ] Does NOT quote safe identifiers: `hello`, `user_id`, `value123`
- [ ] Applies escape sequences correctly: `"line1\nline2"`

**Quoting Rules Algorithm**:

```python
def needs_quoting(value: str, delimiter: str) -> bool:
    if not value:  # Empty string
        return True
    if value in ("true", "false", "null"):  # Looks like keyword
        return True
    if value.lstrip('-').replace('.', '', 1).isdigit():  # Looks like number
        return True
    if value != value.strip():  # Leading/trailing whitespace
        return True
    if delimiter in value or any(c in value for c in ':"\\\n\r\t'):
        return True
    if value.startswith("- "):  # Looks like list marker
        return True
    if re.match(r'^\[\\d+\]$', value) or value.startswith('{'):  # Structural token
        return True
    return False
```

### FR-6: KeyFoldingEngine

**Requirement**: The Encoder module SHALL optionally collapse single-key wrapper chains into dotted paths.

**Details**:

- Fold keys when `key_folding='safe'` enabled
- Only fold keys matching identifier pattern: `^[a-zA-Z_][a-zA-Z0-9_\.]*$`
- Stop at first non-single-key object
- Respect `flatten_depth` limit (default: unlimited)

**Acceptance Criteria**:

- [ ] Folds single-key chains: `data.metadata.items` instead of nested
- [ ] Stops at multi-key objects
- [ ] Does NOT fold keys containing special characters
- [ ] Respects `flatten_depth` parameter

**Example**:

```python
# Input
{"data": {"metadata": {"items": ["a", "b"]}}}

# Without key folding (key_folding='off')
data:
  metadata:
    items[2]: a,b

# With key folding (key_folding='safe')
data.metadata.items[2]: a,b
```

**Algorithm**:

```python
def fold_keys(obj: dict[str, Any], depth: int = 0, max_depth: int | None = None) -> tuple[str | None, Any]:
    if max_depth and depth >= max_depth:
        return (None, obj)

    if len(obj) != 1:  # Multi-key object
        return (None, obj)

    key, value = next(iter(obj.items()))

    if not is_safe_identifier(key):
        return (None, obj)

    if not isinstance(value, dict):
        return (key, value)

    nested_path, nested_value = fold_keys(value, depth + 1, max_depth)

    if nested_path:
        return (f"{key}.{nested_path}", nested_value)
    else:
        return (key, value)
```

---

## 3. Non-Functional Requirements

### NFR-1: Performance

**Target**: <100ms encoding time for 1-10KB datasets

**Metrics**:

- TabularAnalyzer uniformity check: O(n*m) where n=array length, m=avg field count
- Overall encoding: O(n) where n=data size
- Memory usage: O(n) for output string

**Validation Approach**: pytest-benchmark with realistic datasets

### NFR-2: Token Efficiency

**Target**: 30-60% token savings vs JSON on uniform tabular data

**Benchmarks** (from research):

- Uniform employee records: 36.3% reduction
- Time-series analytics: 34.1% reduction
- E-commerce orders: -6.4% (worse for nested data)

**Validation Approach**: Token comparison tests using tiktoken

### NFR-3: Type Safety

**Target**: 100% mypy strict mode compliance

**Requirements**:

- All encoder functions fully typed
- Generic types for array/dict handling
- No `Any` types except for input value parameter

**Validation Approach**: `mypy --strict pytoon/encoder/`

### NFR-4: Modularity

**Target**: Each encoder component independently testable

**Requirements**:

- TabularAnalyzer has no dependencies on other encoder components
- ValueEncoder, ArrayEncoder, ObjectEncoder, QuotingEngine, KeyFoldingEngine are loosely coupled
- Configuration passed via dependency injection

**Validation Approach**: Unit tests with mocked dependencies

---

## 4. Features & Flows

### Feature 1: Tabular Array Encoding

**Priority**: P0
**Description**: Encode uniform arrays in efficient tabular format

**Input/Output**:

```python
# Input
data = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin"},
        {"id": 2, "name": "Bob", "role": "user"}
    ]
}

# Output
users[2]{id,name,role}:
  1,Alice,admin
  2,Bob,user
```

**Flow**:

1. ArrayEncoder receives array
2. Calls TabularAnalyzer.analyze(array)
3. TabularAnalyzer returns `(True, ["id", "name", "role"], 100.0)`
4. ArrayEncoder generates header: `users[2]{id,name,role}:`
5. For each row, ValueEncoder encodes primitives
6. Rows joined with newlines and indentation

### Feature 2: Key Folding

**Priority**: P0
**Description**: Collapse single-key wrapper chains to reduce tokens

**Input/Output**:

```python
# Input (with key_folding='safe')
data = {
    "api": {
        "v1": {
            "users": [{"id": 1}]
        }
    }
}

# Output
api.v1.users[1]{id}:
  1
```

**Flow**:

1. ObjectEncoder encounters single-key dict `{"api": {...}}`
2. Calls KeyFoldingEngine.fold_keys(...)
3. KeyFoldingEngine recursively folds: `"api"` → `"api.v1"` → `"api.v1.users"`
4. Stops at array value
5. Returns `("api.v1.users", [{...}])`

### Feature 3: Context-Aware Quoting

**Priority**: P0
**Description**: Minimize quoted strings while preserving parseability

**Input/Output**:

```python
# Unquoted (safe identifier)
{"name": "Alice"} → name: Alice

# Quoted (contains delimiter)
{"tags": "admin,ops"} → tags: "admin,ops"

# Quoted (looks like number)
{"code": "42"} → code: "42"

# Quoted (empty string)
{"value": ""} → value: ""
```

**Flow**:

1. ValueEncoder receives string value
2. Calls QuotingEngine.needs_quoting(value, delimiter)
3. QuotingEngine checks all quoting rules
4. Returns `True` if any rule matches
5. ValueEncoder applies quotes and escape sequences

---

## 5. Acceptance Criteria

### Definition of Done

- [ ] All 6 encoder components implemented (Tabular, Value, Array, Object, Quoting, KeyFolding)
- [ ] All functional requirements (FR-1 through FR-6) met
- [ ] All non-functional requirements (NFR-1 through NFR-4) met
- [ ] Unit tests achieve 85%+ code coverage
- [ ] Encoding performance <100ms for 1-10KB datasets
- [ ] Token savings 30-60% on uniform tabular data
- [ ] mypy --strict passes with zero errors
- [ ] Integration tests with core module pass

### Validation Approach

**Unit Tests**:

```python
# Test tabular analysis
def test_tabular_analyzer_uniform():
    array = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    is_tabular, fields, score = TabularAnalyzer.analyze(array)
    assert is_tabular is True
    assert fields == ["id", "name"]
    assert score == 100.0

# Test value encoding
@pytest.mark.parametrize("value,expected", [
    (None, "null"),
    (True, "true"),
    (False, "false"),
    (42, "42"),
    (1e6, "1000000"),
    (float('nan'), "null"),
])
def test_value_encoder(value, expected):
    encoded = ValueEncoder.encode(value)
    assert encoded == expected

# Test quoting rules
def test_quoting_engine_needs_quoting():
    assert QuotingEngine.needs_quoting("", ",") is True  # Empty
    assert QuotingEngine.needs_quoting("a,b", ",") is True  # Contains delimiter
    assert QuotingEngine.needs_quoting("true", ",") is True  # Looks like boolean
    assert QuotingEngine.needs_quoting("hello", ",") is False  # Safe identifier
```

**Integration Tests**:

```python
# Test end-to-end encoding
def test_encode_tabular_array():
    data = {"users": [{"id": 1, "name": "Alice"}]}
    toon = encode(data)
    assert "users[1]{id,name}:" in toon
    assert "1,Alice" in toon

# Test key folding
def test_encode_key_folding():
    data = {"a": {"b": {"c": "value"}}}
    toon = encode(data, key_folding='safe')
    assert "a.b.c: value" in toon
```

**Performance Tests**:

```python
import pytest

@pytest.mark.benchmark
def test_encoding_performance(benchmark):
    data = generate_10kb_dataset()
    result = benchmark(encode, data)
    assert benchmark.stats.median < 0.1  # <100ms
```

---

## 6. Dependencies

### Technical Assumptions

1. **Python Version**: 3.8+ with modern type hints
2. **Standard Library**: re, typing, abc modules available
3. **Core Module**: Provides Encoder class interface

### External Integrations

None (zero runtime dependencies)

### Related Components

- **CORE-001**: Encoder class delegates to encoder module components
- **UTILS-001**: Uses exception classes (TOONEncodeError)

### Component Dependencies

```
ENCODER-001
├── Depends on: CORE-001 (Encoder class)
├── Depends on: UTILS-001 (exception hierarchy)
└── Required by: DECISION-001 (smart encoding)
```

---

## 7. Implementation Notes

### Code Structure

```plaintext
pytoon/encoder/
├── __init__.py          # Exports all encoder components
├── tabular.py           # TabularAnalyzer class
├── value.py             # ValueEncoder class
├── array.py             # ArrayEncoder class
├── object.py            # ObjectEncoder class
├── quoting.py           # QuotingEngine class
└── keyfolding.py        # KeyFoldingEngine class
```

### Testing Strategy

- **Unit Tests**: Test each encoder component in isolation
- **Integration Tests**: Test encoding flows end-to-end with core module
- **Property-Based Tests**: Use Hypothesis for random data generation
- **Performance Tests**: Benchmark encoding time with pytest-benchmark

### Security Considerations

- **Circular Reference Detection**: Prevent infinite recursion (handled in core module)
- **Data Size Limits**: Validate array lengths against MAX_ARRAY_LENGTH
- **Type Validation**: Reject unsupported types with clear error messages

---

## 8. References

### Source Documentation

- **Primary**: `docs/pytoon-system-design.md` Section 2.1 (Encoder Module)
- **Specification**: TOON v1.5+ (quoting rules, type conversions)
- **Performance**: `docs/research/intel.md` (token efficiency benchmarks)

### Related Specifications

- **CORE-001**: Core module specification
- **DECODER-001**: Decoder module specification (for roundtrip compatibility)
- **UTILS-001**: Utilities specification (exception hierarchy)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Ready for Planning Phase
