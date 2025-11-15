# CORE-001: Core Module Implementation

**State:** UNPROCESSED
**Priority:** P0
**Type:** Epic
**Version:** 1.0

## Description

Implement core module providing Encoder/Decoder classes and public API (encode/decode functions). The core module serves as the foundation for PyToon, providing the central entry points for TOON encoding/decoding operations with zero external runtime dependencies.

## Acceptance Criteria

- [ ] Encoder class instantiates with configuration parameters
- [ ] Encoder.encode(value) returns valid TOON string
- [ ] Decoder class instantiates with configuration parameters
- [ ] Decoder.decode(toon_string) returns Python objects
- [ ] `encode(value, ...)` and `decode(toon_string, ...)` top-level functions exist
- [ ] TOONSpec class defines TOON v1.5+ constants and patterns
- [ ] 100% mypy strict mode compliance
- [ ] Roundtrip fidelity: `decode(encode(data)) == data`
- [ ] Performance: Core overhead <5ms for 1-10KB datasets
- [ ] 85%+ test coverage

## Target Files

- `pytoon/__init__.py` (create): Public API exports (encode, decode)
- `pytoon/__version__.py` (create): Version information
- `pytoon/core/__init__.py` (create): Core module exports
- `pytoon/core/encoder.py` (create): Main Encoder class
- `pytoon/core/decoder.py` (create): Main Decoder class
- `pytoon/core/spec.py` (create): TOON v1.5+ specification constants
- `pytoon/py.typed` (create): PEP 561 marker for type stubs
- `tests/unit/test_core_encoder.py` (create): Encoder class unit tests
- `tests/unit/test_core_decoder.py` (create): Decoder class unit tests
- `tests/unit/test_spec.py` (create): TOONSpec class tests
- `tests/integration/test_roundtrip.py` (create): Roundtrip fidelity tests

## Dependencies

None (foundation component)

## Context

**Specs:** docs/specs/core/spec.md
**Design:** docs/pytoon-system-design.md Section 2

## Progress

**Notes:** Generated from /sage.specify command
