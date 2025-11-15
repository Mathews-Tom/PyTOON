# Tasks: Encoder Module

**From:** `spec.md` + `plan.md`
**Timeline:** 2 weeks (Sprint 1-2)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 6
- Estimated effort: 31 story points
- Critical path duration: 10 days
- Key risks: Quoting edge cases, scientific notation handling, token efficiency validation

## Phase Breakdown

### Phase 1: Foundation (Days 1-2, 10 SP)

**Goal:** Implement primitive value encoding and string quoting
**Deliverable:** ValueEncoder and QuotingEngine classes with 100% spec compliance

#### Tasks

**ENCODER-002: Implement ValueEncoder Class**

- **Description:** Create ValueEncoder that normalizes Python primitives to TOON representation including None→null, bool→true/false, numbers without scientific notation, NaN/Inf→null, -0.0→0
- **Acceptance:**
  - [ ] encode_value(None) returns "null"
  - [ ] encode_value(True) returns "true" (lowercase)
  - [ ] encode_value(False) returns "false" (lowercase)
  - [ ] encode_value(42) returns "42"
  - [ ] encode_value(3.14) returns "3.14"
  - [ ] encode_value(1e6) returns "1000000" (no scientific notation)
  - [ ] encode_value(float('nan')) returns "null"
  - [ ] encode_value(float('inf')) returns "null"
  - [ ] encode_value(-0.0) returns "0"
  - [ ] Raises TOONEncodeError for unsupported types
  - [ ] 100+ unit tests for edge cases
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** UTILS-002 (TOONEncodeError)
- **Priority:** P0 (Blocker - foundation for all encoding)

**ENCODER-003: Implement QuotingEngine Class**

- **Description:** Create context-aware QuotingEngine that determines when strings need quoting (empty, contains delimiter, looks like keyword, has whitespace, etc.) and applies escape sequences
- **Acceptance:**
  - [ ] needs_quoting("") returns True (empty string)
  - [ ] needs_quoting("true") returns True (keyword)
  - [ ] needs_quoting("42") returns True (looks like number)
  - [ ] needs_quoting("a,b", ",") returns True (contains delimiter)
  - [ ] needs_quoting(" padded ") returns True (whitespace)
  - [ ] needs_quoting("- item") returns True (list marker)
  - [ ] needs_quoting("[5]") returns True (structural token)
  - [ ] needs_quoting("hello") returns False (safe identifier)
  - [ ] quote_string() applies escapes: \", \\, \n, \r, \t
  - [ ] Unit tests for all quoting rules
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** CORE-002 (TOONSpec for delimiter list)
- **Priority:** P0 (Blocker - string safety critical)

### Phase 2: Array Encoding (Days 3-4, 13 SP)

**Goal:** Implement array format detection and encoding
**Deliverable:** TabularAnalyzer and ArrayEncoder with 3 format support

#### Tasks

**ENCODER-004: Implement TabularAnalyzer Class**

- **Description:** Create TabularAnalyzer that analyzes arrays to determine tabular format eligibility by checking uniform keys, no nested structures, and calculating uniformity score
- **Acceptance:**
  - [ ] analyze([]) returns (True, [], 0.0) for empty array
  - [ ] analyze([{"id": 1}]) returns (True, ["id"], 100.0)
  - [ ] analyze([{"id": 1}, {"id": 2, "name": "X"}]) returns (False, [], 0.0) - non-uniform
  - [ ] analyze([{"id": 1, "meta": {}}]) returns (False, ["id", "meta"], 0.0) - nested object
  - [ ] analyze([{"id": 1, "tags": []}]) returns (False, [], 0.0) - nested array
  - [ ] Returns field list in consistent order
  - [ ] O(n*m) time complexity where n=rows, m=fields
  - [ ] Unit tests for all edge cases
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** None (pure analysis)
- **Priority:** P0 (Critical - enables tabular format)

**ENCODER-005: Implement ArrayEncoder Class**

- **Description:** Create ArrayEncoder that dispatches to tabular, inline, or list format based on TabularAnalyzer results, generating correct array headers ([N], [N]{fields}, [N\t]{fields})
- **Acceptance:**
  - [ ] Tabular format: [{"id": 1, "name": "Alice"}] → "array[1]{id,name}:\n  1,Alice"
  - [ ] Inline format: ["a", "b", "c"] → "array[3]: a,b,c"
  - [ ] List format: [{"k": "v"}, "s", 42] → "array[3]:\n  - k: v\n  - s\n  - 42"
  - [ ] Header includes delimiter hint for tab: [N\t]{fields}
  - [ ] Indentation correct for nested arrays
  - [ ] Calls ValueEncoder for primitive elements
  - [ ] Token efficiency validated (30-60% savings on tabular)
  - [ ] Comprehensive test suite for all 3 formats
  - [ ] mypy --strict passes
- **Effort:** 8 story points (4-5 days)
- **Owner:** Backend Developer
- **Dependencies:** ENCODER-002, ENCODER-003, ENCODER-004
- **Priority:** P0 (Critical - core token savings)

### Phase 3: Object Encoding (Day 5, 5 SP)

**Goal:** Implement nested dictionary encoding with indentation
**Deliverable:** ObjectEncoder with proper nesting and key iteration

#### Tasks

**ENCODER-006: Implement ObjectEncoder Class**

- **Description:** Create ObjectEncoder that encodes Python dicts with proper indentation, key: value syntax, recursive nesting, and array delegation
- **Acceptance:**
  - [ ] Flat dict: {"key": "value"} → "key: value"
  - [ ] Nested dict proper indentation (2 spaces per level)
  - [ ] Preserves key order (Python 3.7+ dict order)
  - [ ] Detects arrays and delegates to ArrayEncoder
  - [ ] Handles empty dict correctly (no output)
  - [ ] Recursive encoding for deeply nested structures
  - [ ] sort_keys option when enabled
  - [ ] Unit tests for nested structures
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** ENCODER-002, ENCODER-005
- **Priority:** P0 (Critical - main encoding logic)

### Phase 4: Optimization (Days 6-7, 3 SP)

**Goal:** Implement key folding for additional token savings
**Deliverable:** KeyFoldingEngine for dotted path optimization

#### Tasks

**ENCODER-007: Implement KeyFoldingEngine Class**

- **Description:** Create KeyFoldingEngine that collapses single-key wrapper chains into dotted paths (data.metadata.items) when key_folding='safe' is enabled
- **Acceptance:**
  - [ ] {"a": {"b": {"c": 1}}} → "a.b.c: 1" when folding enabled
  - [ ] Stops at multi-key objects
  - [ ] Stops at non-dict values (arrays, primitives)
  - [ ] Only folds keys matching safe identifier pattern
  - [ ] Respects max_depth parameter if provided
  - [ ] Does NOT fold keys containing dots or special chars
  - [ ] Unit tests for folding logic and edge cases
  - [ ] Integration with ObjectEncoder
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** ENCODER-006, UTILS-004 (is_safe_identifier)
- **Priority:** P0 (Important - optimization feature)

## Critical Path

```plaintext
UTILS-002 → ENCODER-002 → ENCODER-005 → ENCODER-006 → Integration
                   ↓
             ENCODER-003
                   ↓
             ENCODER-004
```

**Bottlenecks:**

- ENCODER-005: Complex format dispatch logic (highest risk)
- ENCODER-003: Quoting edge cases (many rules to get right)

**Parallel Tracks:**

- ENCODER-002 and ENCODER-003 can be developed in parallel
- ENCODER-004 can be developed in parallel with primitive encoders

## Quick Wins (Days 1-2)

1. **ENCODER-002**: ValueEncoder enables primitive encoding
2. **ENCODER-004**: TabularAnalyzer enables format selection

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| ENCODER-002 | Scientific notation edge cases | Extensive numeric tests, avoid f-strings | Use decimal module for precision |
| ENCODER-003 | Missing quoting rule causes parse error | Comprehensive test suite, fuzz testing | Conservative quoting by default |
| ENCODER-005 | Token savings underperformance | Early benchmarking with real data | Optimize tabular format |
| ENCODER-007 | Key folding ambiguity | Only fold safe identifiers | Conservative folding rules |

## Testing Strategy

### Automated Testing Tasks

- Unit tests: 100+ cases for ValueEncoder edge cases
- Unit tests: All quoting rules with examples
- Unit tests: Tabular analyzer uniformity detection
- Integration tests: End-to-end encoding flows
- Property-based tests: Random data generation (Hypothesis)
- Performance tests: Token savings validation (30-60% target)

### Quality Gates

- mypy --strict passes for all encoder components
- 85%+ code coverage per component
- Token efficiency benchmarks meet targets
- No scientific notation in number encoding
- Roundtrip fidelity validated with Decoder

## Team Allocation

**Backend Developer (1.0 FTE)**

- Primitive encoding (ENCODER-002, ENCODER-003)
- Array analysis and encoding (ENCODER-004, ENCODER-005)
- Object encoding (ENCODER-006)
- Key folding optimization (ENCODER-007)

## Sprint Planning

**Week 2: Encoder Module (31 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Days 1-2 | Primitives | 10 SP | ENCODER-002 + ENCODER-003 |
| Day 3 | Array Analysis | 5 SP | ENCODER-004 |
| Days 4-5 | Array Encoding | 8 SP | ENCODER-005 |
| Day 6 | Object Encoding | 5 SP | ENCODER-006 |
| Day 7 | Key Folding | 3 SP | ENCODER-007 |

## Token Efficiency Validation

**Benchmark Tests Required:**

1. Uniform employee records: Target 36% reduction
2. Time-series analytics: Target 34% reduction
3. API response data: Target 30% reduction
4. E-commerce orders: May be negative (nested data warning)

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- mypy --strict passes with zero errors
- Token efficiency validated against benchmarks
- No scientific notation in number output
- Integration with Core.Encoder works
- Documentation complete with encoding examples
