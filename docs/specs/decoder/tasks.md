# Tasks: Decoder Module

**From:** `spec.md` + `plan.md`
**Timeline:** 2 weeks (Sprint 2-3)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 5
- Estimated effort: 34 story points
- Critical path duration: 10 days
- Key risks: State machine complexity, escape sequence handling, indentation parsing

## Phase Breakdown

### Phase 1: Lexer (Days 1-2, 8 SP)

**Goal:** Tokenize TOON input into structural elements
**Deliverable:** Lexer class with position tracking and all token types

#### Tasks

**DECODER-002: Implement Lexer Class**

- **Description:** Create Lexer that tokenizes TOON input into token stream with types (IDENTIFIER, STRING, NUMBER, BOOLEAN, NULL, ARRAY_HEADER, COLON, NEWLINE, INDENT, DEDENT) and position tracking (line, column)
- **Acceptance:**
  - [ ] TokenType enum with all token types
  - [ ] Token dataclass with type, value, line, column
  - [ ] tokenize() returns list[Token] ending with EOF
  - [ ] Handles identifiers: key → IDENTIFIER("key")
  - [ ] Handles quoted strings with escape sequences: "value" → STRING("value")
  - [ ] Handles numbers: 42, 3.14, -1 → NUMBER
  - [ ] Handles booleans: true, false → BOOLEAN
  - [ ] Handles null → NULL
  - [ ] Handles array headers: [3], [2]{id,name} → ARRAY_HEADER
  - [ ] Tracks line and column for error reporting
  - [ ] Handles INDENT/DEDENT based on indentation
  - [ ] Unit tests for all token types
  - [ ] Error reporting includes position
  - [ ] mypy --strict passes
- **Effort:** 8 story points (4-5 days)
- **Owner:** Backend Developer
- **Dependencies:** UTILS-002 (TOONDecodeError)
- **Priority:** P0 (Blocker - foundation for parsing)

### Phase 2: Parser Core (Days 3-5, 18 SP)

**Goal:** Build hierarchical Python objects from token stream
**Deliverable:** Parser with state machine and full TOON format support

#### Tasks

**DECODER-003: Implement StateMachine Class**

- **Description:** Create StateMachine that manages parser state transitions (INITIAL, EXPECT_KEY, EXPECT_COLON, EXPECT_VALUE, IN_ARRAY_TABULAR, IN_ARRAY_INLINE, IN_NESTED_OBJECT) and indentation stack
- **Acceptance:**
  - [ ] ParserState enum with all states
  - [ ] Indentation stack tracking (list[int])
  - [ ] State transition methods (enter_state, exit_state)
  - [ ] Tracks current indentation level
  - [ ] Detects dedentation to close nested structures
  - [ ] Validates indentation consistency (multiples of indent size)
  - [ ] Unit tests for state transitions
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** None (internal state management)
- **Priority:** P0 (Critical - parser coordination)

**DECODER-004: Implement Parser Class**

- **Description:** Create Parser that builds hierarchical Python objects from token stream using StateMachine, handling all TOON formats (tabular arrays, inline arrays, list arrays, nested objects)
- **Acceptance:**
  - [ ] parse() returns Python object (dict, list, or primitive)
  - [ ] Parses flat objects: "key: value" → {"key": "value"}
  - [ ] Parses nested objects with indentation
  - [ ] Parses tabular arrays: "[2]{id,name}:\n  1,Alice\n  2,Bob"
  - [ ] Parses inline arrays: "[3]: a,b,c"
  - [ ] Parses list arrays: "[2]:\n  - val1\n  - val2"
  - [ ] Handles array header parsing (length, fields)
  - [ ] Reconstructs proper Python types from TOON values
  - [ ] Uses StateMachine for state management
  - [ ] O(n) time complexity where n=token count
  - [ ] Comprehensive test suite for all formats
  - [ ] mypy --strict passes
- **Effort:** 13 story points (1 week)
- **Owner:** Backend Developer
- **Dependencies:** DECODER-002 (Lexer), DECODER-003 (StateMachine)
- **Priority:** P0 (Critical - core decoding logic)

### Phase 3: Validation (Day 6, 5 SP)

**Goal:** Enforce TOON v1.5 spec compliance
**Deliverable:** Validator with strict and lenient modes

#### Tasks

**DECODER-005: Implement Validator Class**

- **Description:** Create Validator that enforces TOON v1.5 spec rules in strict mode (raises errors) or lenient mode (collects warnings) for array length mismatch, field inconsistency, and delimiter errors
- **Acceptance:**
  - [ ] Validator.__init__(strict=True) for strict mode
  - [ ] Validator.__init__(strict=False) for lenient mode
  - [ ] validate_array_length(declared, actual, line) raises/warns on mismatch
  - [ ] validate_field_consistency(fields, row_values, line) checks count
  - [ ] validate_delimiter_consistency() checks uniform delimiter
  - [ ] Strict mode raises TOONValidationError with line info
  - [ ] Lenient mode collects warnings list
  - [ ] Error messages include line and column numbers
  - [ ] Unit tests for both modes
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** UTILS-002 (TOONValidationError)
- **Priority:** P0 (Critical - spec compliance)

### Phase 4: Path Expansion (Days 7-8, 3 SP)

**Goal:** Reverse key folding for dotted paths
**Deliverable:** PathExpander that reconstructs nested structures

#### Tasks

**DECODER-006: Implement PathExpander Class**

- **Description:** Create PathExpander that reverses key folding by expanding dotted keys into nested dictionaries (data.metadata.items → {"data": {"metadata": {"items": ...}}})
- **Acceptance:**
  - [ ] expand({"a.b.c": 1}) returns {"a": {"b": {"c": 1}}}
  - [ ] Handles multiple dotted keys in same object
  - [ ] Handles mixed dotted and regular keys
  - [ ] Preserves non-dotted keys as-is
  - [ ] Raises error on key conflict (a.b and a.b.c)
  - [ ] Only expands when expand_paths='safe' enabled
  - [ ] Unit tests for expansion logic
  - [ ] Integration with Decoder.decode()
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** None (post-processing)
- **Priority:** P0 (Important - reverse key folding)

## Critical Path

```plaintext
UTILS-002 → DECODER-002 → DECODER-004 → Integration with Core
                              ↓
                        DECODER-003
                              ↓
                        DECODER-005
```

**Bottlenecks:**

- DECODER-004: Parser state machine is most complex (highest risk)
- DECODER-002: Lexer must handle all TOON syntax correctly

**Parallel Tracks:**

- DECODER-003 can be started while DECODER-002 is in progress
- DECODER-005 and DECODER-006 can be developed after Parser stub exists

## Quick Wins (Days 1-2)

1. **DECODER-002**: Lexer enables all parsing work
2. **DECODER-003**: StateMachine provides parser foundation

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| DECODER-002 | Escape sequence edge cases | Comprehensive escape tests, follow JSON patterns | Conservative parsing rules |
| DECODER-004 | State machine complexity | Clear state diagrams, extensive unit tests | Simplify state transitions |
| DECODER-004 | Performance with large inputs | O(n) algorithm, early benchmarking | Stream processing in v2.0 |
| DECODER-005 | Error messages unclear | Include line/column in all errors | Standardize error format |

## Testing Strategy

### Automated Testing Tasks

- Unit tests: All token types for Lexer
- Unit tests: State transitions for StateMachine
- Unit tests: All TOON formats for Parser (tabular, inline, list)
- Unit tests: Strict/lenient modes for Validator
- Integration tests: Roundtrip fidelity with Encoder
- Property-based tests: Random TOON string generation
- Security tests: No eval() or exec() usage

### Quality Gates

- mypy --strict passes for all decoder components
- 85%+ code coverage per component
- Roundtrip fidelity: decode(encode(data)) == data
- Performance <100ms for 1-10KB datasets
- No security vulnerabilities (no eval/exec)
- Error messages include position information

## Team Allocation

**Backend Developer (1.0 FTE)**

- Lexer implementation (DECODER-002)
- State machine design (DECODER-003)
- Parser logic (DECODER-004)
- Validation rules (DECODER-005)
- Path expansion (DECODER-006)

## Sprint Planning

**Week 3: Decoder Module (34 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Days 1-2 | Lexer | 8 SP | DECODER-002: Tokenization |
| Day 3 | State Machine | 5 SP | DECODER-003: State management |
| Days 4-6 | Parser | 13 SP | DECODER-004: Structure building |
| Day 7 | Validator | 5 SP | DECODER-005: Spec enforcement |
| Day 8 | Path Expander | 3 SP | DECODER-006: Reverse folding |

## Security Requirements

**CRITICAL - No eval-based parsing:**

- [ ] No eval() usage anywhere in decoder
- [ ] No exec() usage anywhere in decoder
- [ ] Bandit security scan passes
- [ ] All input validated before processing
- [ ] Resource limits enforced (max string length, max nesting)

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- mypy --strict passes with zero errors
- No security vulnerabilities (no eval/exec)
- Roundtrip fidelity validated with Encoder
- Performance targets met (<100ms for 1-10KB)
- Error messages include line/column information
- Integration with Core.Decoder works
- Documentation complete with parsing examples
