# DECODER-001: Decoder Module Implementation

**State:** UNPROCESSED
**Priority:** P0
**Type:** Epic
**Version:** 1.0

## Description

Implement decoder components: Lexer, Parser, Validator, PathExpander, StateMachine. The decoder module reconstructs Python objects from TOON strings using a state-machine-based parser with strict/lenient validation modes.

## Acceptance Criteria

- [ ] Lexer tokenizes TOON input into structural elements
- [ ] Parser builds hierarchical Python objects using state machine
- [ ] Validator enforces TOON v1.5 spec rules in strict mode
- [ ] PathExpander reconstructs dotted keys into nested objects
- [ ] StateMachine manages parser state transitions and indentation tracking
- [ ] 100% mypy strict mode compliance
- [ ] Roundtrip fidelity: `decode(encode(data)) == data`
- [ ] Strict mode validation with detailed error messages
- [ ] 85%+ test coverage

## Target Files

- `pytoon/decoder/__init__.py` (create): Decoder module exports
- `pytoon/decoder/lexer.py` (create): Lexer class (tokenization)
- `pytoon/decoder/parser.py` (create): Parser class (structure building)
- `pytoon/decoder/validator.py` (create): Validator class (strict/lenient modes)
- `pytoon/decoder/pathexpander.py` (create): PathExpander class (reverse key folding)
- `pytoon/decoder/statemachine.py` (create): StateMachine class (state transitions)
- `tests/unit/test_lexer.py` (create): Lexer tests
- `tests/unit/test_parser.py` (create): Parser tests
- `tests/unit/test_validator.py` (create): Validator tests
- `tests/unit/test_pathexpander.py` (create): PathExpander tests
- `tests/unit/test_statemachine.py` (create): StateMachine tests

## Dependencies

- CORE-001 (foundation component with Decoder class)
- UTILS-001 (exception hierarchy, validation)

## Context

**Specs:** docs/specs/decoder/spec.md
**Design:** docs/pytoon-system-design.md Section 2

## Progress

**Notes:** Generated from /sage.specify command
