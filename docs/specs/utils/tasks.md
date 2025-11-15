# Tasks: Utils Module

**From:** `spec.md` + `plan.md`
**Timeline:** 3 days (Sprint 1, Week 1)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 3
- Estimated effort: 10 story points
- Critical path duration: 3 days
- Key risks: tiktoken optional dependency handling

## Phase Breakdown

### Phase 1: Exception Hierarchy (Day 1, 3 SP)

**Goal:** Establish complete TOON exception hierarchy
**Deliverable:** All exception classes importable and properly inherited

#### Tasks

**UTILS-002: Implement Exception Hierarchy**

- **Description:** Create complete TOON exception hierarchy with TOONError as base, TOONEncodeError, TOONDecodeError, and TOONValidationError with descriptive docstrings
- **Acceptance:**
  - [ ] TOONError base class with docstring
  - [ ] TOONEncodeError inherits from TOONError
  - [ ] TOONDecodeError inherits from TOONError
  - [ ] TOONValidationError inherits from TOONDecodeError
  - [ ] All exceptions have descriptive docstrings with examples
  - [ ] Can catch broad (TOONError) or specific exceptions
  - [ ] Unit tests verify inheritance chain
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** None (foundation component)
- **Priority:** P0 (Blocker - all modules depend on error classes)

### Phase 2: Token Counting (Days 2-3, 5 SP)

**Goal:** Implement token counting with optional tiktoken dependency
**Deliverable:** TokenCounter class demonstrating TOON token savings

#### Tasks

**UTILS-003: Implement TokenCounter Class**

- **Description:** Create TokenCounter class that uses tiktoken (optional) for GPT-5 o200k_base token counting with fallback to character estimation, including compare() method for JSON vs TOON savings
- **Acceptance:**
  - [ ] TokenCounter.__init__ gracefully handles missing tiktoken
  - [ ] count_tokens(text) returns int token count
  - [ ] Uses tiktoken o200k_base encoding when available
  - [ ] Falls back to len(text) // 4 estimation without tiktoken
  - [ ] compare(data) returns dict with json_tokens, toon_tokens, savings_percent, savings_absolute
  - [ ] Savings percentage calculated correctly
  - [ ] Unit tests work with and without tiktoken installed
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** CORE-006 (encode function for comparison)
- **Priority:** P0 (Critical - demonstrates core value proposition)

### Phase 3: Common Helpers (Day 3, 2 SP)

**Goal:** Provide reusable validation utilities
**Deliverable:** Helper functions for configuration validation

#### Tasks

**UTILS-004: Implement Common Helper Functions**

- **Description:** Create helper functions for configuration validation including validate_indent(), validate_delimiter(), and is_safe_identifier() regex check
- **Acceptance:**
  - [ ] validate_indent(n) raises ValueError if n <= 0
  - [ ] validate_delimiter(d) raises ValueError if d not in [",", "\t", "|"]
  - [ ] is_safe_identifier(key) returns bool for safe key folding
  - [ ] Consistent error message format across all validators
  - [ ] Used by Core Encoder/Decoder config validation
  - [ ] Unit tests cover all validation paths
  - [ ] mypy --strict passes
- **Effort:** 2 story points (3-4 hours)
- **Owner:** Backend Developer
- **Dependencies:** None
- **Priority:** P0 (Blocker - used by CORE-004, CORE-005)

## Critical Path

```plaintext
UTILS-002 → [CORE-001 depends on this]
UTILS-004 → [CORE-004, CORE-005 use validators]
UTILS-003 → [CLI --stats flag depends on this]
```

**Bottlenecks:**

- UTILS-002: Must be first as all modules need exceptions
- UTILS-003: Requires CORE-006 to be functional for comparison

## Quick Wins (Day 1)

1. **UTILS-002**: Exception hierarchy unblocks CORE-001
2. **UTILS-004**: Helper functions enable consistent validation

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| UTILS-002 | Exception messages unclear | Standard format: "{what} at {where}: {detail}" | Review all error paths with examples |
| UTILS-003 | tiktoken not installed | Graceful fallback with clear documentation | Character estimation is acceptable |
| UTILS-003 | Token estimate variance | Document accuracy limitations | Accept ±5% variance vs tiktoken |

## Testing Strategy

### Automated Testing Tasks

- Unit tests for exception inheritance (100% coverage)
- Unit tests for TokenCounter with/without tiktoken
- Unit tests for helper validation functions
- Integration tests with Core module

### Quality Gates

- mypy --strict passes
- 85%+ code coverage
- All functions have docstrings
- Optional dependency (tiktoken) handled gracefully

## Team Allocation

**Backend Developer (0.5 FTE)**

- Exception design (UTILS-002)
- Token counting implementation (UTILS-003)
- Validation helpers (UTILS-004)

## Sprint Planning

**Week 1, Days 1-3: Utils Foundation (10 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Day 1 | Exceptions | 3 SP | UTILS-002: Error hierarchy |
| Day 2 | Token Counter Start | 3 SP | UTILS-003: TokenCounter core |
| Day 3 | Token Counter Complete + Helpers | 4 SP | UTILS-003 finish + UTILS-004 |

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- mypy --strict passes
- Optional dependency (tiktoken) documented
- Exception messages are descriptive and actionable
