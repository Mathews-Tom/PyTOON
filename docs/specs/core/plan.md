# Core Module Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/core/spec.md`
**Component ID:** CORE-001
**Priority:** P0 (Foundation Component)

---

## Context & Documentation

### Traceability Chain

**Specification → This Plan**

1. **Formal Specification:** docs/specs/core/spec.md
   - FR-1: Encoder Class coordination
   - FR-2: Decoder Class coordination
   - FR-3: TOONSpec constants and patterns
   - FR-4: Public API functions (encode, decode)

2. **Research & Intelligence:** docs/research/intel.md
   - First-mover advantage (Week 1-4 critical)
   - Zero dependencies = minimal attack surface
   - Clean API = adoption enabler
   - 85% test coverage differentiator

3. **System Context:** .sage/agent/system/
   - Architecture: 4-layer modular design
   - Tech Stack: Python 3.8+, mypy strict, zero dependencies
   - Patterns: Facade pattern, Strategy pattern

### Related Documentation

**System Context:**

- Architecture: `.sage/agent/system/architecture.md` - Layered modular architecture
- Tech Stack: `.sage/agent/system/tech-stack.md` - Python 3.8+, hatchling backend
- Patterns: `.sage/agent/system/patterns.md` - Component interface pattern, error handling

**Code Examples:**

- `.sage/agent/examples/python/api/` - Public API pattern templates
- `.sage/agent/examples/python/errors/` - Exception hierarchy pattern
- `.sage/agent/examples/python/testing/` - pytest unit test patterns

**Dependencies:**

- **UTILS-001**: Exception classes (TOONError, TOONEncodeError, TOONDecodeError)
- **ENCODER-001**: Encoder delegates to encoder module components
- **DECODER-001**: Decoder delegates to decoder module components

---

## Executive Summary

### Business Alignment

- **Purpose:** Central entry point for TOON encoding/decoding operations
- **Value Proposition:** Unified, type-safe API with sensible defaults
- **Target Users:** Python developers building LLM applications, data engineers optimizing token costs

### Technical Approach

- **Architecture Pattern:** Facade Pattern (Core orchestrates Encoder/Decoder subsystems)
- **Technology Stack:** Python 3.8+, zero dependencies, typing module only
- **Implementation Strategy:** 3-phase approach (Foundation → Integration → Hardening)

### Key Success Metrics

**Service Level Objectives (SLOs):**

- API Overhead: <5ms for function call overhead
- Type Safety: 100% mypy strict compliance
- Roundtrip Fidelity: 100% data preservation

**Key Performance Indicators (KPIs):**

- Test Coverage: 85%+ code coverage
- API Stability: Zero breaking changes after 1.0
- Documentation: Complete docstrings for all public functions

---

## Code Examples & Patterns

### Repository Patterns

**1. Public API Pattern:** `.sage/agent/examples/python/api/`

```python
def encode(
    value: Any,
    *,
    indent: int = 2,
    delimiter: Literal[",", "\t", "|"] = ",",
    key_folding: Literal["off", "safe"] = "off",
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> str:
    """Encode Python object to TOON string.

    Args:
        value: Python object to encode (dict, list, or primitive)
        indent: Spaces per indentation level (default: 2)
        delimiter: Field delimiter for arrays (default: ',')
        key_folding: Key folding mode (default: 'off')
        ensure_ascii: Escape non-ASCII characters (default: False)
        sort_keys: Sort dictionary keys (default: False)

    Returns:
        TOON-formatted string

    Raises:
        TOONEncodeError: If value cannot be encoded

    Examples:
        >>> encode({"name": "Alice", "age": 30})
        'name: Alice\\nage: 30'
        >>> encode([{"id": 1}, {"id": 2}])
        '[2]{id}:\\n  1\\n  2'
    """
    encoder = Encoder(
        indent=indent,
        delimiter=delimiter,
        key_folding=key_folding,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
    )
    return encoder.encode(value)
```

**2. Error Handling Pattern:** `.sage/agent/examples/python/errors/`

```python
class TOONError(Exception):
    """Base exception for all TOON errors."""

class TOONEncodeError(TOONError):
    """Raised when encoding fails."""

class TOONDecodeError(TOONError):
    """Raised when decoding fails."""

class TOONValidationError(TOONDecodeError):
    """Raised when validation fails in strict mode."""
```

**3. Testing Pattern:** `.sage/agent/examples/python/testing/`

```python
import pytest
from hypothesis import given, strategies as st
from pytoon import encode, decode

class TestCoreRoundtrip:
    """Test roundtrip fidelity for Core module."""

    @given(st.dictionaries(st.text(), st.integers()))
    def test_roundtrip_dict(self, data: dict[str, int]) -> None:
        """Test encode/decode roundtrip preserves dict data."""
        toon = encode(data)
        recovered = decode(toon)
        assert recovered == data
```

### Key Takeaways

- Use keyword-only arguments (`*,`) for configuration parameters
- Full type hints with Literal for restricted values
- Google-style docstrings with Examples section
- Fail-fast error handling (explicit TOONError exceptions)

### New Patterns to Create

**1. Facade Orchestration Pattern**

- **Purpose:** Central coordinator for subsystem delegation
- **Location:** `.sage/agent/examples/python/components/facade.md`
- **Reusability:** CLI-001, DECISION-001 can reuse orchestration pattern

---

## Technology Stack

### Recommended Stack (from Research)

**Based on research from:** `docs/research/intel.md`

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| Runtime | Python | 3.8+ | Modern type hints, broad compatibility |
| Type System | typing module | stdlib | mypy strict compliance, no external deps |
| Testing | pytest + Hypothesis | Latest | Property-based testing, 85% coverage target |
| Type Checking | mypy --strict | Latest | Production-ready quality differentiator |
| Linting | ruff | Latest | Fast modern linting (from intel) |

**Key Technology Decisions:**

1. **Zero Runtime Dependencies:** Core uses only stdlib (typing, abc, re) for minimal attack surface and easy adoption
2. **Modern Type Hints:** Python 3.8+ enables `list[int]`, `dict[str, Any]`, `int | None` syntax
3. **Literal Types:** Use `Literal[",", "\t", "|"]` for delimiter constraint

**Research Citations:**

- "Zero-dependency advantage" - docs/research/intel.md Section 3.3
- "Clean API = adoption enabler" - docs/research/intel.md Customer Intelligence
- "mypy --strict = production-ready quality" - docs/research/intel.md Testing & QA

### Alignment with Existing System

**From `.sage/agent/system/tech-stack.md`:**

- **Consistent With:** Python 3.8+ requirement, typing module usage, mypy strict mode
- **New Additions:** None (Core is foundation component)
- **Migration Considerations:** None (greenfield project)

---

## Architecture Design

### System Context

**Existing System Architecture:**

Core module is the **facade layer** in PyToon's 4-layer modular architecture:

```
Layer 4: Public API (encode, decode functions) ← CORE-001
Layer 3: Intelligence Layer (DecisionEngine) - v1.1+
Layer 2: Core Logic (Encoder, Decoder classes)
Layer 1: Foundation (spec constants, exceptions)
```

**Integration Points:**

- **Encoder Module:** Core.Encoder delegates to encoder components
- **Decoder Module:** Core.Decoder delegates to decoder components
- **Utils Module:** Core uses exception classes from utils.errors
- **CLI Module:** CLI uses Core.encode() and Core.decode() functions

### Component Architecture

**Architecture Pattern:** Facade Pattern

- **Rationale:** Simplifies subsystem complexity for users
- **Alignment:** Standard pattern for library entry points

**System Design:**

```plaintext
User Code
    │
    ▼
Core Public API
┌─────────────────────────────┐
│ encode(value, **config)     │
│ decode(toon_string, **cfg)  │
└─────────┬───────────────────┘
          │
          ▼
    Core Classes
┌─────────────────────────────┐
│ Encoder Class               │
│   └─ delegates to encoder/  │
│ Decoder Class               │
│   └─ delegates to decoder/  │
│ TOONSpec Class              │
│   └─ constants, patterns    │
└─────────────────────────────┘
          │
          ▼
  Encoder/Decoder Modules
┌─────────────────────────────┐
│ TabularAnalyzer             │
│ ValueEncoder                │
│ Lexer, Parser, etc.         │
└─────────────────────────────┘
```

### Architecture Decisions

**Decision 1: Facade Pattern**

- **Choice:** Single entry point (encode/decode functions)
- **Rationale:** Clean API reduces adoption friction
- **Implementation:** Functions wrap Encoder/Decoder class instantiation
- **Trade-offs:** Slight overhead vs. direct class usage (acceptable: <5ms)

**Decision 2: Configuration via Keyword Arguments**

- **Choice:** Keyword-only args with sensible defaults
- **Rationale:** Explicit configuration, backward compatible additions
- **Implementation:** `def encode(value, *, indent=2, ...)`

**Decision 3: Delegation to Subsystems**

- **Choice:** Core delegates to Encoder/Decoder modules
- **Rationale:** Separation of concerns, independent testing
- **Implementation:** Core.Encoder uses encoder.ArrayEncoder, etc.

### Component Breakdown

**Core Components:**

1. **encode() Function**
   - **Purpose:** Public API for encoding
   - **Technology:** Pure Python, typing module
   - **Pattern:** Public API pattern
   - **Interfaces:** `encode(value, **config) -> str`
   - **Dependencies:** Encoder class

2. **decode() Function**
   - **Purpose:** Public API for decoding
   - **Technology:** Pure Python, typing module
   - **Pattern:** Public API pattern
   - **Interfaces:** `decode(toon_string, **config) -> Any`
   - **Dependencies:** Decoder class

3. **Encoder Class**
   - **Purpose:** Coordinates encoding operations
   - **Technology:** Python class with **init** and encode method
   - **Pattern:** Facade pattern
   - **Interfaces:** `Encoder(**config).encode(value) -> str`
   - **Dependencies:** encoder module components

4. **Decoder Class**
   - **Purpose:** Coordinates decoding operations
   - **Technology:** Python class with **init** and decode method
   - **Pattern:** Facade pattern
   - **Interfaces:** `Decoder(**config).decode(toon_string) -> Any`
   - **Dependencies:** decoder module components

5. **TOONSpec Class**
   - **Purpose:** TOON v1.5+ specification constants
   - **Technology:** Python class with class-level attributes
   - **Pattern:** Configuration object pattern
   - **Interfaces:** `TOONSpec.VERSION`, `TOONSpec.DEFAULT_INDENT`
   - **Dependencies:** None

### Data Flow & Boundaries

**Encoding Flow:**

1. User calls `encode(data)` → Core function
2. Core instantiates `Encoder(**config)`
3. Encoder dispatches to encoder module components
4. Returns TOON string

**Decoding Flow:**

1. User calls `decode(toon_string)` → Core function
2. Core instantiates `Decoder(**config)`
3. Decoder dispatches to decoder module (Lexer → Parser → Validator)
4. Returns Python object

**Component Boundaries:**

- **Public Interface:** `encode()`, `decode()` functions only
- **Internal Implementation:** Encoder/Decoder classes, delegation logic
- **Cross-Component Contracts:** Configuration dict structure, exception types

---

## Technical Specification

### Data Model

**Configuration Parameters:**

```python
from typing import Any, Literal

class EncoderConfig:
    indent: int  # Default: 2
    delimiter: Literal[",", "\t", "|"]  # Default: ","
    key_folding: Literal["off", "safe"]  # Default: "off"
    ensure_ascii: bool  # Default: False
    sort_keys: bool  # Default: False

class DecoderConfig:
    strict: bool  # Default: True
    expand_paths: Literal["off", "safe"]  # Default: "off"
```

**Validation Rules:**

- indent > 0
- delimiter in [",", "\t", "|"]
- key_folding in ["off", "safe"]

### API Design

**Top 2 Critical Functions:**

1. **encode()**
   - Method: Function call
   - Purpose: Python → TOON conversion
   - Request: Python object (Any)
   - Response: TOON string
   - Error handling: TOONEncodeError on failure

2. **decode()**
   - Method: Function call
   - Purpose: TOON → Python conversion
   - Request: TOON string
   - Response: Python object (Any)
   - Error handling: TOONDecodeError, TOONValidationError

### Security

**Input Validation:**

- Validate configuration parameters (indent > 0, delimiter in allowed set)
- Type constraints enforced via mypy strict
- No eval() or exec() usage (critical security requirement)

**Secrets Management:**

- N/A for library (no secrets handled)

**Data Protection:**

- No persistence layer (in-memory only)
- User data not logged

**Security Testing:**

- Bandit SAST scanning in CI/CD
- No high-severity findings allowed

### Performance

**Performance Targets (from Research):**

- **API Overhead:** <5ms for function instantiation and call
- **Encoding:** <100ms for 1-10KB datasets (delegated to encoder module)
- **Decoding:** <100ms for 1-10KB datasets (delegated to decoder module)

**Optimization Strategy:**

- Lazy instantiation where possible
- No unnecessary copies of data
- Direct delegation to specialized components

**Resource Usage:**

- Memory: O(n) for input/output data
- CPU: O(n) time complexity enforced in subsystems

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1, Days 1-3)

**Tasks:**

- [ ] Create `pytoon/core/__init__.py` with exports
- [ ] Implement `pytoon/core/spec.py` (TOONSpec class)
  - VERSION = "1.5"
  - DEFAULT_INDENT = 2
  - SUPPORTED_DELIMITERS = [",", "\t", "|"]
  - IDENTIFIER_PATTERN regex
- [ ] Define exception hierarchy in utils.errors (TOONError, TOONEncodeError, TOONDecodeError)
- [ ] Write unit tests for TOONSpec class

**Deliverables:**

- TOONSpec class with all constants
- Exception hierarchy defined
- 100% test coverage for spec module

### Phase 2: Core Classes (Week 1, Days 4-5)

**Tasks:**

- [ ] Implement `pytoon/core/encoder.py` (Encoder class)
  - **init** with config validation
  - encode() method stub (delegates to encoder module)
- [ ] Implement `pytoon/core/decoder.py` (Decoder class)
  - **init** with config validation
  - decode() method stub (delegates to decoder module)
- [ ] Write unit tests for configuration validation
- [ ] Type hints for all methods (mypy strict)

**Deliverables:**

- Encoder and Decoder class stubs
- Configuration validation working
- mypy strict passing for core module

### Phase 3: Public API (Week 2, Days 1-2)

**Tasks:**

- [ ] Implement `encode()` function in `pytoon/__init__.py`
- [ ] Implement `decode()` function in `pytoon/__init__.py`
- [ ] Add comprehensive docstrings (Google-style)
- [ ] Write unit tests for public API
- [ ] Hypothesis property-based tests for roundtrip fidelity

**Deliverables:**

- Public API functions working
- 85%+ test coverage
- Docstrings complete
- Roundtrip fidelity validated

### Phase 4: Integration (Week 2, Day 3 - Week 3)

**Tasks:**

- [ ] Integrate with encoder module (real encoding)
- [ ] Integrate with decoder module (real decoding)
- [ ] End-to-end integration tests
- [ ] Performance benchmarking (verify <5ms overhead)
- [ ] Documentation finalization

**Deliverables:**

- Full integration with encoder/decoder
- Performance targets met
- API documentation complete
- Ready for CLI-001 integration

---

## Quality Assurance

### Testing Strategy

**Unit Tests (85%+ coverage):**

- TOONSpec constants validation
- Configuration parameter validation
- Error handling for invalid inputs
- Type conversion correctness

**Integration Tests:**

- encode → decode roundtrip
- Configuration options respected
- Error propagation from subsystems

**Property-Based Tests (Hypothesis):**

- Roundtrip fidelity: `decode(encode(data)) == data`
- Random data generation for primitives, dicts, lists

**Performance Tests (pytest-benchmark):**

- Encoder instantiation: <1ms
- Decoder instantiation: <1ms
- Function call overhead: <0.5ms

### Code Quality Gates

- [ ] mypy --strict passes with zero errors
- [ ] ruff check passes (no linting errors)
- [ ] black formatting applied
- [ ] 85%+ test coverage
- [ ] All docstrings complete (Google-style)

### Deployment Verification

- [ ] `from pytoon import encode, decode` works
- [ ] `encode({"key": "value"})` returns valid TOON
- [ ] `decode("key: value")` returns Python dict
- [ ] Configuration options respected
- [ ] Errors raise appropriate exceptions

---

## Risk Management

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Circular imports between core and encoder/decoder | HIGH | MEDIUM | Define clear interfaces, use lazy imports |
| Configuration complexity | MEDIUM | LOW | Sensible defaults, keyword-only args |
| Performance overhead from abstraction | LOW | LOW | Benchmark early, optimize if needed |
| API design mistakes hard to fix post-1.0 | HIGH | LOW | Thorough review, follow JSON stdlib pattern |

---

## Error Handling & Edge Cases

### Error Scenarios

1. **Invalid Configuration**
   - **Cause:** indent <= 0, delimiter not in allowed set
   - **Impact:** Function won't work as expected
   - **Handling:** Raise ValueError with descriptive message
   - **Recovery:** User corrects configuration
   - **UX:** "indent must be positive integer, got: -1"

2. **Unsupported Type**
   - **Cause:** User passes type object, custom class without handler
   - **Impact:** Encoding fails
   - **Handling:** Raise TOONEncodeError with type info
   - **Recovery:** User registers type handler or converts to supported type
   - **UX:** "Cannot encode type: <class 'MyClass'>"

3. **Invalid TOON Syntax**
   - **Cause:** Malformed TOON string
   - **Impact:** Decoding fails
   - **Handling:** Raise TOONDecodeError with position info
   - **Recovery:** User fixes TOON syntax
   - **UX:** "Invalid syntax at line 3, column 5: expected ':' after key"

### Edge Cases

| Edge Case | Detection | Handling | Testing Approach |
|-----------|-----------|----------|------------------|
| Empty input | `if not value` | Return appropriate empty representation | Unit test with empty dict, list |
| Nested None values | Type check | Encode as "null" | Property-based test with optional values |
| Unicode strings | Default Python handling | Preserve encoding | Test with emoji, CJK characters |
| Very long strings | No special detection | Process normally (O(n)) | Benchmark with large datasets |

### Input Validation

**Configuration Validation:**

```python
def _validate_config(indent: int, delimiter: str, key_folding: str) -> None:
    if indent <= 0:
        raise ValueError(f"indent must be positive integer, got: {indent}")
    if delimiter not in [",", "\t", "|"]:
        raise ValueError(f"delimiter must be ',', '\\t', or '|', got: {delimiter!r}")
    if key_folding not in ["off", "safe"]:
        raise ValueError(f"key_folding must be 'off' or 'safe', got: {key_folding!r}")
```

---

## References & Traceability

### Source Documentation

**Specification:**

- docs/specs/core/spec.md - Functional requirements FR-1 through FR-4
- Acceptance criteria: Encoder/Decoder classes, TOONSpec, public API

**Research & Intelligence:**

- docs/research/intel.md
  - Strategic priority: Rapid v1.0 implementation (Week 1-4)
  - Quality differentiation: 85% test coverage, mypy strict
  - API design: Clean API = adoption enabler

**System Context:**

- .sage/agent/system/architecture.md - 4-layer modular architecture
- .sage/agent/system/tech-stack.md - Python 3.8+, zero dependencies
- .sage/agent/system/patterns.md - Facade pattern, error handling pattern

### Related Components

**Dependencies:**

- **UTILS-001:** Exception classes (TOONError hierarchy)
- **ENCODER-001:** Encoding logic implementation
- **DECODER-001:** Decoding logic implementation

**Dependents:**

- **CLI-001:** Uses encode()/decode() for command-line interface
- **DECISION-001:** Uses Core for smart_encode() orchestration

---

**Document Version**: 1.0
**Implementation Status**: Ready for Ticket Generation
**Next Step**: `/sage.tasks` to break down into SMART tickets
