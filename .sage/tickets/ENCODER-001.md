# ENCODER-001: Encoder Module Implementation

**State:** UNPROCESSED
**Priority:** P0
**Type:** Epic
**Version:** 1.0

## Description

Implement encoder components: TabularAnalyzer, ValueEncoder, ArrayEncoder, ObjectEncoder, QuotingEngine, KeyFoldingEngine. The encoder module is responsible for achieving 30-60% token savings over JSON through intelligent format dispatch, context-aware quoting, and key folding optimizations.

## Acceptance Criteria

- [ ] TabularAnalyzer detects uniform arrays qualifying for tabular format
- [ ] ValueEncoder normalizes primitives (null, bool, numbers, strings) to TOON types
- [ ] ArrayEncoder dispatches to tabular/inline/list formats based on uniformity
- [ ] ObjectEncoder handles nested dictionaries with proper indentation
- [ ] QuotingEngine applies context-aware string quoting to minimize tokens
- [ ] KeyFoldingEngine collapses single-key wrapper chains into dotted paths
- [ ] 100% mypy strict mode compliance
- [ ] 30-60% token savings on typical LLM datasets
- [ ] 85%+ test coverage

## Target Files

- `pytoon/encoder/__init__.py` (create): Encoder module exports
- `pytoon/encoder/tabular.py` (create): TabularAnalyzer class
- `pytoon/encoder/value.py` (create): ValueEncoder class
- `pytoon/encoder/array.py` (create): ArrayEncoder class
- `pytoon/encoder/object.py` (create): ObjectEncoder class
- `pytoon/encoder/quoting.py` (create): QuotingEngine class
- `pytoon/encoder/keyfolding.py` (create): KeyFoldingEngine class
- `tests/unit/test_tabular.py` (create): TabularAnalyzer tests
- `tests/unit/test_value_encoder.py` (create): ValueEncoder tests
- `tests/unit/test_array_encoder.py` (create): ArrayEncoder tests
- `tests/unit/test_object_encoder.py` (create): ObjectEncoder tests
- `tests/unit/test_quoting.py` (create): QuotingEngine tests
- `tests/unit/test_keyfolding.py` (create): KeyFoldingEngine tests

## Dependencies

- CORE-001 (foundation component with Encoder class)
- UTILS-001 (exception hierarchy, validation)

## Context

**Specs:** docs/specs/encoder/spec.md
**Design:** docs/pytoon-system-design.md Section 2

## Progress

**Notes:** Generated from /sage.specify command
