# Decision Engine Module Specification

**Component ID**: DECISION-001
**Version**: v1.1
**Priority**: P1
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 8 (Phase 2)

## 1. Overview

The Decision Engine provides intelligent format selection analyzing data structure to recommend optimal serialization format.

**Success Metrics**: 90%+ accuracy on format recommendations, clear reasoning for decisions

## 2. Functional Requirements

### FR-1: DataMetrics Computation

- Nesting depth calculation (max depth in object tree)
- Uniformity score (percentage of arrays eligible for tabular format)
- Reference density (percentage of potential reference relationships)
- Array size distribution

### FR-2: StructuralAnalyzer

- Tabular eligibility scoring (0-100%)
- Complexity analysis (nesting patterns, field counts)
- Data shape classification (flat, nested, mixed, graph)

### FR-3: DecisionEngine

- Recommends format: TOON, JSON, graph, hybrid
- Confidence score (0-100%)
- Reasoning array explaining decision
- **Thresholds**:
  - Depth > 6 levels → favor JSON over TOON
  - Uniformity < 30% → favor JSON
  - Uniformity > 70% → favor TOON
  - Reference density > 20% → recommend graph format

### FR-4: smart_encode() API

```python
def smart_encode(value, auto=True, explain=False) -> tuple[str, FormatDecision]:
    """
    Automatically select optimal format and encode.
    
    Returns:
        (encoded_string, decision) where decision contains:
        - format: 'toon' | 'json' | 'graph' | 'hybrid'
        - confidence: 0-100
        - reasoning: list[str]
        - metrics: DataMetrics
    """
```

## 3. Component Structure

```plaintext
pytoon/decision/
├── engine.py      # DecisionEngine class
├── analyzer.py    # StructuralAnalyzer class
└── metrics.py     # DataMetrics class
```

## 4. Acceptance Criteria

- [ ] DecisionEngine 90%+ accuracy on format selection
- [ ] `smart_encode()` API functional
- [ ] Reasoning explanations clear and actionable
- [ ] CLI supports `--auto-decide` and `--explain` flags
- [ ] mypy --strict passes

## 5. Dependencies

- **ENCODER-001**: Uses encoder for TOON format
- **CORE-001**: Integrates with core API

**Status**: Ready for Planning Phase (v1.1)
