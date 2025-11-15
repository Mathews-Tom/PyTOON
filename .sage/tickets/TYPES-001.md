# TYPES-001: Type System Implementation (v1.1)

**State:** UNPROCESSED
**Priority:** P1
**Type:** Epic
**Version:** 1.1

## Description

Implement pluggable type system: TypeRegistry, built-in handlers (UUID, datetime, etc.), custom type registration. The type system enables encoding/decoding of custom Python types through a plugin architecture with 15+ built-in handlers.

## Acceptance Criteria

- [ ] TypeRegistry registers and looks up type handlers
- [ ] 15+ built-in type handlers implemented (UUID, datetime, date, time, timedelta, bytes, Enum, Decimal, complex, Path, set, frozenset, etc.)
- [ ] `register_type_handler(python_type, handler)` API functional
- [ ] Type hint-aware decoding: `decode(toon_str, hint=MyClass)`
- [ ] ValueEncoder and Parser integration complete
- [ ] 100% mypy strict mode compliance
- [ ] Roundtrip fidelity for all custom types
- [ ] 85%+ test coverage

## Target Files

- `pytoon/types/__init__.py` (create): Types module exports
- `pytoon/types/registry.py` (create): TypeRegistry class
- `pytoon/types/handlers.py` (create): Built-in type handlers (UUID, datetime, date, time, timedelta, bytes, Enum, Decimal, complex, Path, set, frozenset)
- `pytoon/types/protocol.py` (create): TypeHandler protocol
- `pytoon/encoder/value.py` (modify): Integrate TypeRegistry for custom type encoding
- `pytoon/decoder/parser.py` (modify): Integrate TypeRegistry for type-aware decoding
- `tests/unit/test_types.py` (create): TypeRegistry and handlers tests

## Dependencies

- ENCODER-001 (ValueEncoder for integration)
- DECODER-001 (Parser for type-aware decoding)

## Context

**Specs:** docs/specs/types/spec.md
**Design:** docs/pytoon-system-design.md Section 8 (Phase 2)

## Progress

**Notes:** Generated from /sage.specify command
