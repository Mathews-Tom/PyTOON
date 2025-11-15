# Decoder Module Specification

**Component ID**: DECODER-001
**Version**: v1.0
**Priority**: P0
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 2.2

## 1. Overview

The Decoder module parses TOON-formatted strings back into Python objects through lexical analysis, syntax parsing, and validation.

**Success Metrics**: <100ms decoding for 1-10KB, 100% roundtrip fidelity, 85%+ test coverage

## 2. Functional Requirements

### FR-1: Lexer - Tokenization

- Tokenizes TOON input into structural elements (IDENTIFIER, STRING, NUMBER, BOOLEAN, NULL, ARRAY_HEADER, etc.)
- Tracks position for error reporting (line, column)
- Handles escape sequences in quoted strings

### FR-2: Parser - Structure Building

- Builds hierarchical Python objects from token stream
- State machine: INITIAL → EXPECT_KEY → EXPECT_VALUE → NESTED/ARRAY
- Handles indentation-based nesting
- Parses array headers: `[N]`, `[N]{fields}`, `[N\t]{fields}`

### FR-3: Validator - Spec Compliance

- **Strict Mode**: Raises errors on array length mismatch, field inconsistency
- **Lenient Mode**: Best-effort parsing with warnings
- Validates delimiter consistency, escape sequences, indentation

### FR-4: PathExpander - Reverse Key Folding

- Reconstructs dotted keys into nested objects
- `data.metadata.items` → `{"data": {"metadata": {"items": ...}}}`
- Enabled when `expand_paths='safe'`

### FR-5: StateMachine - State Transitions

- Manages parser state transitions
- Tracks indentation stack
- Detects dedentation to close nested structures

## 3. Component Structure

```plaintext
pytoon/decoder/
├── lexer.py           # Lexer class
├── parser.py          # Parser class
├── validator.py       # Validator class
├── pathexpander.py    # PathExpander class
└── statemachine.py    # StateMachine class
```

## 4. Acceptance Criteria

- [ ] All 5 decoder components implemented
- [ ] Handles all TOON formats (tabular, inline, list)
- [ ] Strict/lenient validation modes working
- [ ] Decoding performance <100ms for 1-10KB
- [ ] Roundtrip fidelity: `decode(encode(data)) == data`
- [ ] mypy --strict passes

## 5. Dependencies

- **CORE-001**: Decoder class delegates to decoder module
- **UTILS-001**: Exception classes (TOONDecodeError, TOONValidationError)

**Status**: Ready for Planning Phase
