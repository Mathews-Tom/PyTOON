# DECISION-001: Decision Engine Implementation (v1.1)

**State:** UNPROCESSED
**Priority:** P1
**Type:** Epic
**Version:** 1.1

## Description

Implement intelligent format selection: DecisionEngine, StructuralAnalyzer, DataMetrics, smart_encode() API. The decision module analyzes data characteristics and recommends optimal format (TOON, JSON, graph, hybrid) based on nesting depth, uniformity, reference density, and tabular eligibility.

## Acceptance Criteria

- [ ] DecisionEngine analyzes data and selects optimal format
- [ ] StructuralAnalyzer computes nesting depth, uniformity score
- [ ] DataMetrics calculates reference density, tabular eligibility
- [ ] `smart_encode(value, auto=True, explain=False)` API functional
- [ ] CLI `--auto-decide` and `--explain` flags implemented
- [ ] 100% mypy strict mode compliance
- [ ] 85%+ test coverage

## Target Files

- `pytoon/decision/__init__.py` (create): Decision module exports
- `pytoon/decision/engine.py` (create): DecisionEngine class
- `pytoon/decision/analyzer.py` (create): StructuralAnalyzer class
- `pytoon/decision/metrics.py` (create): DataMetrics class
- `pytoon/__init__.py` (modify): Add smart_encode export
- `pytoon/cli/main.py` (modify): Add --auto-decide and --explain flags
- `tests/unit/test_decision_engine.py` (create): DecisionEngine tests
- `tests/unit/test_structural_analyzer.py` (create): StructuralAnalyzer tests
- `tests/unit/test_data_metrics.py` (create): DataMetrics tests

## Dependencies

- CORE-001 (encode function)
- ENCODER-001 (TabularAnalyzer for eligibility checks)

## Context

**Specs:** docs/specs/decision/spec.md
**Design:** docs/pytoon-system-design.md Section 8 (Phase 2)

## Progress

**Notes:** Generated from /sage.specify command
