# Tasks: Core Module

**From:** `spec.md` + `plan.md`
**Timeline:** 1 week (Sprint 1)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 5
- Estimated effort: 14 story points
- Critical path duration: 5 days
- Key risks: API design decisions, circular import prevention

## Phase Breakdown

### Phase 1: Foundation (Days 1-2, 5 SP)

**Goal:** Establish TOON v1.5+ specification constants and exception hierarchy
**Deliverable:** TOONSpec class and error types importable

#### Tasks

**CORE-002: Implement TOONSpec Class**

- **Description:** Create TOONSpec class with TOON v1.5+ specification constants including VERSION, DEFAULT_INDENT, SUPPORTED_DELIMITERS, and IDENTIFIER_PATTERN regex
- **Acceptance:**
  - [ ] TOONSpec.VERSION == "1.5"
  - [ ] TOONSpec.DEFAULT_INDENT == 2
  - [ ] TOONSpec.SUPPORTED_DELIMITERS == [",", "\t", "|"]
  - [ ] TOONSpec.IDENTIFIER_PATTERN validates safe identifiers
  - [ ] All constants have type hints
  - [ ] Unit tests cover all constants
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** UTILS-001 (exception hierarchy)
- **Priority:** P0 (Blocker - foundation for all encoding/decoding)

**CORE-003: Create Package Structure**

- **Description:** Set up pytoon package structure with **init**.py, **version**.py, py.typed marker, and core module exports
- **Acceptance:**
  - [ ] pytoon/**init**.py created with public API stubs
  - [ ] pytoon/**version**.py with **version** = "1.0.0"
  - [ ] pytoon/py.typed marker for PEP 561
  - [ ] pytoon/core/**init**.py exports Encoder, Decoder, TOONSpec
  - [ ] All imports work: `from pytoon import encode, decode`
- **Effort:** 2 story points (3-4 hours)
- **Owner:** Backend Developer
- **Dependencies:** None
- **Priority:** P0 (Blocker - package foundation)

### Phase 2: Core Classes (Days 3-4, 6 SP)

**Goal:** Implement Encoder and Decoder class stubs with configuration validation
**Deliverable:** Classes instantiable with validated configuration

#### Tasks

**CORE-004: Implement Encoder Class**

- **Description:** Create Encoder class with **init** accepting configuration parameters (indent, delimiter, key_folding) and encode() method stub that will delegate to encoder module
- **Acceptance:**
  - [ ] Encoder.**init** validates indent > 0
  - [ ] Encoder.**init** validates delimiter in [",", "\t", "|"]
  - [ ] Encoder.**init** validates key_folding in ["off", "safe"]
  - [ ] Encoder.encode(value) returns placeholder string
  - [ ] ValueError raised for invalid config with descriptive message
  - [ ] Full type hints with Literal types
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** CORE-002 (TOONSpec), UTILS-001 (TOONEncodeError)
- **Priority:** P0 (Critical - core functionality)

**CORE-005: Implement Decoder Class**

- **Description:** Create Decoder class with **init** accepting configuration parameters (strict, expand_paths) and decode() method stub that will delegate to decoder module
- **Acceptance:**
  - [ ] Decoder.**init** validates strict is bool
  - [ ] Decoder.**init** validates expand_paths in ["off", "safe"]
  - [ ] Decoder.decode(toon_string) returns placeholder dict
  - [ ] ValueError raised for invalid config
  - [ ] Full type hints with Literal types
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** CORE-002 (TOONSpec), UTILS-001 (TOONDecodeError)
- **Priority:** P0 (Critical - core functionality)

### Phase 3: Public API (Day 5, 3 SP)

**Goal:** Expose top-level encode() and decode() functions
**Deliverable:** Public API functional with comprehensive docstrings

#### Tasks

**CORE-006: Implement Public API Functions**

- **Description:** Create encode() and decode() top-level functions that instantiate Encoder/Decoder with defaults and delegate to their methods, including Google-style docstrings with examples
- **Acceptance:**
  - [ ] encode(value, **kwargs) function with full signature
  - [ ] decode(toon_string, **kwargs) function with full signature
  - [ ] Keyword-only arguments (indent=2, delimiter=",", etc.)
  - [ ] Google-style docstrings with Args, Returns, Raises, Examples
  - [ ] Functions delegate to Encoder/Decoder classes
  - [ ] Basic unit tests for API surface
  - [ ] Roundtrip test stub: decode(encode(data)) works
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** CORE-004 (Encoder), CORE-005 (Decoder)
- **Priority:** P0 (Critical - user-facing API)

## Critical Path

```plaintext
UTILS-001 → CORE-003 → CORE-002 → CORE-004 → CORE-006
                              ↓
                        CORE-005
```

**Bottlenecks:**

- CORE-002: Specification constants must be correct (spec compliance)
- CORE-006: API design locked after v1.0 release

**Parallel Tracks:**

- CORE-004 and CORE-005 can be developed in parallel after CORE-002

## Quick Wins (Day 1)

1. **CORE-003**: Package structure unblocks everything
2. **CORE-002**: TOONSpec constants enable spec compliance

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| CORE-002 | Spec interpretation errors | Cross-reference TOON v1.5 spec | Consult original TOON documentation |
| CORE-004/005 | Circular imports with encoder/decoder | Use lazy imports, type: TYPE_CHECKING | Define interfaces as protocols |
| CORE-006 | API design regret post-1.0 | Follow JSON stdlib pattern | Deprecation plan documented |

## Testing Strategy

### Automated Testing Tasks

- Unit tests for TOONSpec constants (100% coverage)
- Unit tests for config validation (all error paths)
- Integration test stubs for encode/decode flow
- Property-based tests prepared for roundtrip fidelity

### Quality Gates

- mypy --strict passes
- 85%+ code coverage for core module
- All docstrings complete
- No TODO comments in production code

## Team Allocation

**Backend Developer (1.0 FTE)**

- Core API design (CORE-002, CORE-006)
- Class implementation (CORE-004, CORE-005)
- Configuration validation (all tasks)

## Sprint Planning

**Week 1: Core Foundation (14 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Day 1 | Package Structure | 2 SP | CORE-003: Package scaffold |
| Day 2 | Specification | 3 SP | CORE-002: TOONSpec class |
| Day 3 | Encoder Class | 3 SP | CORE-004: Encoder stub |
| Day 4 | Decoder Class | 3 SP | CORE-005: Decoder stub |
| Day 5 | Public API | 3 SP | CORE-006: encode/decode functions |

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- mypy --strict passes with zero errors
- Documentation updated (docstrings complete)
- No security vulnerabilities (no eval/exec)
- API matches specification exactly
