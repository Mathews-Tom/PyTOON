# Tasks: Type System Module

**From:** `spec.md` + `plan.md`
**Timeline:** 2 weeks (v1.1, Weeks 6-7)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 3
- Estimated effort: 18 story points
- Critical path duration: 7 days
- Key risks: Protocol compatibility, type hint inference

## Phase Breakdown

### Phase 1: Registry Core (Days 1-2, 5 SP)

**Goal:** Implement pluggable type handler registry
**Deliverable:** TypeRegistry class with registration and lookup

#### Tasks

**TYPES-002: Implement TypeRegistry Class**

- **Description:** Create TypeRegistry that manages type handlers with register(), get_handler(), and priority-based resolution (user handlers take precedence over built-in)
- **Acceptance:**
  - [ ] TypeRegistry class with private _handlers list
  - [ ] register(handler) adds handler to registry
  - [ ] encode_value(obj) finds matching handler and encodes
  - [ ] decode_value(s, hint) finds matching handler and decodes
  - [ ] Priority: user handlers checked before built-in
  - [ ] Returns None if no handler matches
  - [ ] Thread-safe registration (optional for v1.1)
  - [ ] Unit tests for registry operations
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** None (core registry pattern)
- **Priority:** P1 (Blocker for type support)

### Phase 2: Built-in Handlers (Days 3-5, 8 SP)

**Goal:** Implement 15+ built-in type handlers
**Deliverable:** Complete handler suite for common Python types

#### Tasks

**TYPES-003: Implement Built-in Type Handlers**

- **Description:** Create TypeHandler implementations for UUID, datetime, date, time, timedelta, bytes (base64), Enum, Decimal, complex, Path, set, and frozenset with encode/decode methods
- **Acceptance:**
  - [ ] TypeHandler Protocol with can_handle(), encode(), decode()
  - [ ] UUIDHandler: UUID → "uuid:..." string
  - [ ] DatetimeHandler: datetime → "datetime:ISO8601"
  - [ ] DateHandler: date → "date:YYYY-MM-DD"
  - [ ] TimeHandler: time → "time:HH:MM:SS"
  - [ ] TimedeltaHandler: timedelta → "timedelta:seconds"
  - [ ] BytesHandler: bytes → "bytes:base64..."
  - [ ] EnumHandler: Enum → "enum:Class.value"
  - [ ] DecimalHandler: Decimal → "decimal:..."
  - [ ] ComplexHandler: complex → "complex:real,imag"
  - [ ] PathHandler: Path → "path:/..."
  - [ ] SetHandler: set → sorted list representation
  - [ ] FrozensetHandler: frozenset → sorted list representation
  - [ ] 15+ handlers total
  - [ ] Roundtrip fidelity for all types
  - [ ] Unit tests for each handler
  - [ ] mypy --strict passes
- **Effort:** 8 story points (4-5 days)
- **Owner:** Backend Developer
- **Dependencies:** TYPES-002 (TypeRegistry)
- **Priority:** P1 (Critical - core type support)

### Phase 3: Integration (Days 6-7, 5 SP)

**Goal:** Integrate TypeRegistry with Encoder and Decoder
**Deliverable:** Seamless custom type encoding/decoding

#### Tasks

**TYPES-004: Integrate TypeRegistry with Encoder/Decoder**

- **Description:** Modify ValueEncoder to use TypeRegistry for custom types and Parser to use type hints for decoding, with register_type_handler() public API
- **Acceptance:**
  - [ ] ValueEncoder checks TypeRegistry before raising error
  - [ ] encode({"uuid": uuid_obj}) works automatically
  - [ ] decode() with type hints reconstructs custom types
  - [ ] register_type_handler(handler) public API
  - [ ] Added to pytoon.__init__.py exports
  - [ ] User can register custom handlers
  - [ ] Global registry accessible
  - [ ] Integration tests with mixed types
  - [ ] Documentation with custom handler examples
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** TYPES-002, TYPES-003, ENCODER-002, DECODER-004
- **Priority:** P1 (Important - usability)

## Critical Path

```plaintext
TYPES-002 → TYPES-003 → TYPES-004 → Integration
```

**Bottlenecks:**

- TYPES-003: Many handlers to implement correctly
- TYPES-004: Integration must be seamless

**Parallel Tracks:**

- Individual handlers in TYPES-003 can be developed in parallel

## Quick Wins (Days 1-2)

1. **TYPES-002**: Registry enables all custom type work
2. **UUIDHandler**: Most requested type support

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| TYPES-002 | Protocol compatibility issues | Use typing.Protocol properly | Fallback to ABC |
| TYPES-003 | Type hint inference fails | Prefix-based decoding (uuid:...) | Require explicit hints |
| TYPES-004 | Breaking existing encode/decode | Backward compatible (optional registry) | Opt-in via parameter |

## Testing Strategy

### Automated Testing Tasks

- Unit tests for TypeRegistry operations
- Unit tests for each of 15+ handlers
- Roundtrip tests: encode → decode for all types
- Integration tests with mixed data
- Type hint inference tests
- Custom handler registration tests

### Quality Gates

- mypy --strict passes
- 85%+ code coverage
- All 15+ handlers working
- Roundtrip fidelity for all custom types
- Type hint-aware decoding functional

## Team Allocation

**Backend Developer (1.0 FTE)**

- Registry implementation (TYPES-002)
- Handler implementations (TYPES-003)
- Encoder/Decoder integration (TYPES-004)

## Sprint Planning

**Weeks 6-7: Type System (18 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Days 1-2 | Registry Core | 5 SP | TYPES-002: TypeRegistry |
| Days 3-5 | Built-in Handlers | 8 SP | TYPES-003: 15+ handlers |
| Days 6-7 | Integration | 5 SP | TYPES-004: Encoder/Decoder |

## Handler Implementation Guide

**TypeHandler Protocol:**

```python
class TypeHandler(Protocol[T]):
    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Return True if handler can process this object."""
        ...

    @staticmethod
    def encode(obj: T) -> str:
        """Encode object to prefixed string."""
        ...

    @staticmethod
    def decode(s: str, type_hint: Type[T] | None = None) -> T:
        """Decode string back to object."""
        ...
```

**Encoding Format Convention:**

- `uuid:12345678-1234-5678-1234-567812345678`
- `datetime:2025-11-15T12:30:45`
- `bytes:SGVsbG8gV29ybGQ=`
- `complex:3.0,4.0`

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- 15+ built-in handlers implemented
- mypy --strict passes
- Roundtrip fidelity for all custom types
- register_type_handler() API documented
- Integration with Encoder/Decoder seamless
- Examples for custom handler creation
