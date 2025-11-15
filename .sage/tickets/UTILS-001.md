# UTILS-001: Utilities Module Implementation

**State:** UNPROCESSED
**Priority:** P0
**Type:** Epic
**Version:** 1.0

## Description

Implement utilities: TokenCounter, FormatValidator, exception hierarchy. The utilities module provides cross-cutting functionality including GPT-5 token counting, format validation, and comprehensive exception types.

## Acceptance Criteria

- [ ] TokenCounter estimates GPT-5 o200k_base token counts
- [ ] TokenCounter compares JSON vs TOON token efficiency
- [ ] FormatValidator validates TOON format correctness
- [ ] Exception hierarchy covers all error cases (encode, decode, validation)
- [ ] 100% mypy strict mode compliance
- [ ] 85%+ test coverage

## Target Files

- `pytoon/utils/__init__.py` (create): Utils module exports
- `pytoon/utils/tokens.py` (create): TokenCounter class
- `pytoon/utils/validation.py` (create): FormatValidator class
- `pytoon/utils/errors.py` (create): Exception hierarchy (TOONError, TOONEncodeError, TOONDecodeError, TOONValidationError)
- `tests/unit/test_tokens.py` (create): TokenCounter tests
- `tests/unit/test_validation.py` (create): FormatValidator tests
- `tests/unit/test_errors.py` (create): Exception hierarchy tests

## Dependencies

None (foundation component)

## Context

**Specs:** docs/specs/utils/spec.md
**Design:** docs/pytoon-system-design.md Section 2

## Progress

**Notes:** Generated from /sage.specify command
