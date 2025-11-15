# Utilities Module Specification

**Component ID**: UTILS-001
**Version**: v1.0
**Priority**: P0
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 2.4

## 1. Overview

The Utilities module provides cross-cutting concerns: token counting, validation, and exception hierarchy.

**Success Metrics**: Accurate token counting with tiktoken, comprehensive error messages

## 2. Functional Requirements

### FR-1: TokenCounter

- Estimate tokens using GPT-5 o200k_base encoding (via optional tiktoken dependency)
- Fallback to character-based approximation if tiktoken unavailable
- `count_tokens(text)` → int
- `compare_formats(data)` → dict with JSON/TOON token counts and savings percentage

### FR-2: FormatValidator

- Pre-encode validation: circular reference detection, type compatibility
- Post-decode validation: roundtrip fidelity checks
- Data size limit enforcement (MAX_ARRAY_LENGTH, MAX_STRING_LENGTH, MAX_NESTING_DEPTH)

### FR-3: Exception Hierarchy

```plaintext
TOONError (base)
├── TOONEncodeError
│   ├── UnsupportedTypeError
│   ├── CircularReferenceError
│   └── DataSizeLimitError
├── TOONDecodeError
│   ├── SyntaxError
│   ├── UnexpectedTokenError
│   └── IndentationError
└── TOONValidationError
    ├── ArrayLengthMismatchError
    ├── FieldInconsistencyError
    └── DelimiterMismatchError
```

## 3. Component Structure

```
pytoon/utils/
├── tokens.py        # TokenCounter class
├── validation.py    # FormatValidator class
└── errors.py        # Exception hierarchy
```

## 4. Acceptance Criteria

- [ ] TokenCounter works with and without tiktoken
- [ ] Token estimates within 5% accuracy (with tiktoken)
- [ ] All exception types defined with helpful error messages
- [ ] FormatValidator detects circular references
- [ ] mypy --strict passes

## 5. Dependencies

- **Optional**: tiktoken (for accurate token counting)
- **Required by**: CORE-001, ENCODER-001, DECODER-001

**Status**: Ready for Planning Phase
