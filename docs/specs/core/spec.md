# Core Module Specification

**Component ID**: CORE-001
**Version**: v1.0
**Priority**: P0
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 2, `docs/research/intel.md`

---

## 1. Overview

### Purpose and Business Value

The Core module serves as the central entry point for PyToon's encoding and decoding functionality. It provides:

- **Unified API**: Single-point access to TOON encoding/decoding operations
- **Specification Compliance**: TOON v1.5+ specification enforcement
- **Type Safety**: Full type hints with mypy strict mode compliance
- **Independence**: Zero external runtime dependencies

### Success Metrics

- **API Stability**: Public API matches documented interface exactly
- **Type Coverage**: 100% type hint coverage with mypy strict passing
- **Performance**: Encoding/decoding overhead <5ms for 1-10KB datasets
- **Roundtrip Fidelity**: `decode(encode(data)) == data` for all valid inputs

### Target Users

- **Python Developers**: Using TOON for LLM applications
- **Data Engineers**: Optimizing token usage for API costs
- **ML Engineers**: Integrating TOON into training/inference pipelines

---

## 2. Functional Requirements

### FR-1: Encoder Class

**Requirement**: The Core module SHALL provide an Encoder class that coordinates encoding operations.

**Details**:

- Accept Python objects (dict, list, primitives)
- Dispatch to specialized encoder components (TabularAnalyzer, ValueEncoder, etc.)
- Apply configuration (indent, delimiter, key_folding, strict mode)
- Return TOON-formatted string

**Acceptance Criteria**:

- [ ] Encoder class instantiates with configuration parameters
- [ ] Encoder.encode(value) returns valid TOON string
- [ ] Encoder detects and raises errors for unsupported types
- [ ] Encoder respects configuration (indent, delimiter, key_folding)

### FR-2: Decoder Class

**Requirement**: The Core module SHALL provide a Decoder class that coordinates decoding operations.

**Details**:

- Accept TOON-formatted strings
- Dispatch to Lexer → Parser → Validator → PathExpander
- Support strict/lenient validation modes
- Return reconstructed Python objects

**Acceptance Criteria**:

- [ ] Decoder class instantiates with configuration parameters
- [ ] Decoder.decode(toon_string) returns Python objects
- [ ] Decoder raises TOONDecodeError on invalid syntax
- [ ] Decoder validates array lengths and field consistency in strict mode

### FR-3: Specification Module

**Requirement**: The Core module SHALL provide a TOONSpec class encapsulating TOON v1.5+ rules.

**Details**:

- Define specification constants (VERSION, DEFAULT_INDENT, DEFAULT_DELIMITER)
- Provide regex patterns (IDENTIFIER_PATTERN, etc.)
- Document type conversions (None → null, bool → true/false)
- Expose validation rules

**Acceptance Criteria**:

- [ ] TOONSpec.VERSION == "1.5"
- [ ] TOONSpec.DEFAULT_INDENT == 2
- [ ] TOONSpec.SUPPORTED_DELIMITERS == [",", "\t", "|"]
- [ ] TOONSpec.IDENTIFIER_PATTERN validates safe identifiers

### FR-4: Public API Functions

**Requirement**: The Core module SHALL expose top-level encode() and decode() functions.

**User Stories**:

- **US-1**: As a Python developer, I want to import `from pytoon import encode, decode` so that I have a simple API
- **US-2**: As a developer, I want `encode(data)` to return a TOON string with sensible defaults
- **US-3**: As a developer, I want `decode(toon_string)` to reconstruct the original Python data

**Acceptance Criteria**:

- [ ] `encode(value, ...)` function exists with full type hints
- [ ] `decode(toon_string, ...)` function exists with full type hints
- [ ] Both functions have comprehensive docstrings
- [ ] Functions delegate to Encoder and Decoder classes

---

## 3. Non-Functional Requirements

### NFR-1: Performance

**Target**: Core module overhead <5% of total encoding/decoding time

**Metrics**:

- Encoder instantiation: <1ms
- Decoder instantiation: <1ms
- Function call overhead: <0.5ms

**Validation Approach**: pytest-benchmark tests

### NFR-2: Type Safety

**Target**: 100% mypy strict mode compliance

**Requirements**:

- All functions fully typed with return types
- No `type: ignore` comments
- Generic types properly specified
- Protocol definitions for extensibility

**Validation Approach**: `mypy --strict pytoon/core/`

### NFR-3: Zero Dependencies

**Target**: Core module has zero external runtime dependencies

**Requirements**:

- Standard library only (typing, abc, etc.)
- No imports from third-party packages
- Optional dependencies (tiktoken) isolated to utils module

**Validation Approach**: Dependency graph analysis

### NFR-4: Backward Compatibility

**Target**: Semantic versioning with 2-version deprecation grace period

**Requirements**:

- Public API stable across minor versions
- Deprecation warnings for 2 minor versions before removal
- CHANGELOG.md documents all breaking changes

**Validation Approach**: API compatibility tests

---

## 4. Features & Flows

### Feature 1: Basic Encoding Flow

**Priority**: P0
**Description**: Encode Python dict to TOON string

**Flow**:

```python
data = {"users": [{"id": 1, "name": "Alice"}]}
toon = encode(data)
# Expected output:
# users[1]{id,name}:
#   1,Alice
```

**Steps**:

1. User calls `encode(data)`
2. Core validates input type (dict, list, or primitive)
3. Core instantiates Encoder with default config
4. Encoder dispatches to ObjectEncoder
5. ObjectEncoder iterates keys, detects array, dispatches to ArrayEncoder
6. ArrayEncoder analyzes uniformity via TabularAnalyzer
7. Returns TOON string

### Feature 2: Basic Decoding Flow

**Priority**: P0
**Description**: Decode TOON string to Python dict

**Flow**:

```python
toon = "users[1]{id,name}:\n  1,Alice"
data = decode(toon)
# Expected output:
# {"users": [{"id": 1, "name": "Alice"}]}
```

**Steps**:

1. User calls `decode(toon_string)`
2. Core instantiates Decoder with default config
3. Decoder passes string to Lexer for tokenization
4. Parser builds hierarchical structure from tokens
5. Validator checks array lengths and field consistency
6. PathExpander reverses key folding if enabled
7. Returns Python dict

### Feature 3: Configuration Options

**Priority**: P0
**Description**: Support configurable encoding/decoding parameters

**Input/Output**:

```python
# Tab-delimited encoding
toon = encode(data, delimiter='\t')

# Key folding enabled
toon = encode(data, key_folding='safe')

# Lenient decoding
data = decode(toon, strict=False)
```

**Parameters**:

- `indent: int = 2` - Spaces per indentation level
- `delimiter: Literal[',', '\t', '|'] = ','` - Array delimiter
- `key_folding: Literal['off', 'safe'] = 'off'` - Key folding mode
- `strict: bool = True` - Validation strictness

---

## 5. Acceptance Criteria

### Definition of Done

- [ ] All functional requirements (FR-1 through FR-4) implemented
- [ ] All non-functional requirements (NFR-1 through NFR-4) met
- [ ] Unit tests achieve 85%+ code coverage
- [ ] mypy --strict passes with zero errors
- [ ] Roundtrip fidelity: `decode(encode(data)) == data` for all test cases
- [ ] Performance benchmarks meet targets (<5ms overhead)
- [ ] API documentation complete with docstrings
- [ ] Integration tests with encoder/decoder modules pass

### Validation Approach

**Unit Tests**:

```python
# Test basic encoding
def test_encode_basic_dict():
    data = {"key": "value"}
    toon = encode(data)
    assert toon == "key: value"

# Test basic decoding
def test_decode_basic_toon():
    toon = "key: value"
    data = decode(toon)
    assert data == {"key": "value"}

# Test roundtrip fidelity
@given(st.dictionaries(st.text(), st.integers()))
def test_roundtrip_fidelity(data):
    toon = encode(data)
    recovered = decode(toon)
    assert recovered == data
```

**Integration Tests**:

```python
# Test with real encoder/decoder components
def test_integration_tabular_array():
    data = {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }
    toon = encode(data)
    assert "users[2]{id,name}:" in toon
    recovered = decode(toon)
    assert recovered == data
```

---

## 6. Dependencies

### Technical Assumptions

1. **Python Version**: 3.8+ with modern type hints support
2. **Standard Library**: typing, abc, re modules available
3. **Encoder/Decoder Modules**: Implemented per their specifications

### External Integrations

None (zero runtime dependencies for core module)

### Related Components

- **ENCODER-001**: Core delegates encoding to Encoder class
- **DECODER-001**: Core delegates decoding to Decoder class
- **UTILS-001**: Core may use exception classes from utils.errors

### Component Dependencies

```
CORE-001
├── Depends on: (none - foundation component)
└── Required by: ENCODER-001, DECODER-001, CLI-001, DECISION-001
```

---

## 7. Implementation Notes

### Architecture Patterns

**Facade Pattern**: Core module acts as a facade for encoder/decoder subsystems

**Strategy Pattern**: Configuration parameters enable strategy selection (delimiter, key_folding)

**Template Method**: Encoder/Decoder classes define template for subclass specialization

### Code Structure

```
pytoon/core/
├── __init__.py          # Exports encode, decode, Encoder, Decoder
├── encoder.py           # Encoder class (delegates to encoder module)
├── decoder.py           # Decoder class (delegates to decoder module)
└── spec.py              # TOONSpec class (constants, patterns, rules)
```

### Testing Strategy

- **Unit Tests**: Test each class in isolation with mocks for dependencies
- **Integration Tests**: Test encode/decode flows end-to-end
- **Property-Based Tests**: Use Hypothesis for roundtrip fidelity across random data
- **Performance Tests**: Benchmark encoding/decoding overhead

### Security Considerations

- **Input Validation**: Validate configuration parameters (indent > 0, delimiter in allowed set)
- **Type Safety**: Enforce type constraints via mypy strict mode
- **Error Handling**: Raise descriptive errors for invalid inputs (no silent failures)

---

## 8. References

### Source Documentation

- **Primary**: `docs/pytoon-system-design.md` Section 1 (Architecture), Section 2 (Component Design)
- **Strategic Context**: `docs/research/intel.md` (Performance targets, competitive analysis)
- **Specification**: TOON v1.5+ specification (embedded in `pytoon/core/spec.py`)

### API Examples

```python
from pytoon import encode, decode

# Basic usage
data = {"tags": ["a", "b", "c"]}
toon = encode(data)  # "tags[3]: a,b,c"
recovered = decode(toon)  # {"tags": ["a", "b", "c"]}

# With configuration
toon = encode(data, delimiter='\t', indent=4)
recovered = decode(toon, strict=False)
```

### Related Specifications

- **ENCODER-001**: Encoder component specification
- **DECODER-001**: Decoder component specification
- **UTILS-001**: Utilities specification (exception hierarchy)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-15
**Status**: Ready for Planning Phase
