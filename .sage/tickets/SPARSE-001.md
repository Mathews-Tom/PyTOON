# SPARSE-001: Sparse Array Implementation (v1.2)

**State:** UNPROCESSED
**Priority:** P2
**Type:** Epic
**Version:** 1.2

## Description

Implement sparse and polymorphic array support: SparseArrayEncoder, PolymorphicArrayEncoder. The sparse module handles arrays with optional fields (30%+ missing values) and polymorphic data structures with discriminator-based sub-tables, achieving 40%+ token savings on sparse tabular data.

## Acceptance Criteria

- [ ] SparseArrayEncoder detects sparsity (30%+ missing values)
- [ ] Optional field markers (`field?` syntax) implemented
- [ ] Empty-string-as-null convention applied
- [ ] PolymorphicArrayEncoder groups by discriminator field
- [ ] Discriminator-based sub-tables (`@type:` sections) working
- [ ] 40%+ token savings on sparse tabular data
- [ ] 100% mypy strict mode compliance
- [ ] Roundtrip fidelity maintained
- [ ] 85%+ test coverage

## Target Files

- `pytoon/sparse/__init__.py` (create): Sparse module exports
- `pytoon/sparse/sparse.py` (create): SparseArrayEncoder class
- `pytoon/sparse/polymorphic.py` (create): PolymorphicArrayEncoder class
- `pytoon/encoder/array.py` (modify): Integrate sparse/polymorphic array detection
- `tests/unit/test_sparse.py` (create): Sparse array tests
- `tests/unit/test_polymorphic.py` (create): Polymorphic array tests

## Dependencies

- ENCODER-001 (ArrayEncoder for integration)

## Context

**Specs:** docs/specs/sparse/spec.md
**Design:** docs/pytoon-system-design.md Section 8 (Phase 3)

## Progress

**Notes:** Generated from /sage.specify command
