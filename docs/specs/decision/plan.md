# Decision Engine Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/decision/spec.md`
**Component ID:** DECISION-001
**Priority:** P1 (v1.1 Feature - Key Differentiator)

---

## Context & Documentation

### Traceability Chain

1. **Formal Specification:** docs/specs/decision/spec.md
   - DecisionEngine: Recommends optimal format (TOON vs JSON)
   - DataMetrics: Computes nesting depth, uniformity score, reference density
   - StructuralAnalyzer: Data shape analysis with confidence scores

2. **Research & Intelligence:** docs/research/intel.md
   - **UNIQUE DIFFERENTIATOR** - No competitors have smart format selection
   - Addresses "when to use TOON vs JSON" decision paralysis
   - High strategic value (Strategic Priority #5 in intel)

3. **System Context:**
   - Architecture: Intelligence Layer (Layer 3)
   - API: `smart_encode(value, auto=True) -> tuple[str, FormatDecision]`

---

## Executive Summary

### Business Alignment

- **Purpose:** Automatically recommend optimal serialization format
- **Value Proposition:** Solves decision paralysis, maximizes token savings intelligently
- **Strategic Importance:** UNIQUE competitive advantage (v1.1 differentiator)

### Technical Approach

- **Architecture Pattern:** Strategy Pattern with heuristic scoring
- **Technology Stack:** Python 3.8+, statistical analysis of data structure
- **Implementation Timeline:** Weeks 5-6 (post v1.0 release)

### Key Success Metrics

**SLOs:**

- Decision Accuracy: >90% optimal format selection on benchmarks
- Performance: <10ms for format decision
- Confidence Scoring: Clear reasoning for recommendations

---

## Core Implementation

### DecisionEngine

```python
from dataclasses import dataclass
from typing import Any, Literal

@dataclass
class FormatDecision:
    """Format recommendation with reasoning."""
    recommended_format: Literal["toon", "json", "hybrid"]
    confidence: float  # 0.0 - 1.0
    reasoning: list[str]
    metrics: "DataMetrics"

@dataclass
class DataMetrics:
    """Computed metrics for format decision."""
    nesting_depth: int
    uniformity_score: float  # 0.0 - 100.0
    tabular_eligibility: float  # % of arrays that are tabular
    reference_density: float  # % of repeated references
    total_size_bytes: int

class DecisionEngine:
    """Recommend optimal serialization format."""

    def analyze(self, data: Any) -> FormatDecision:
        """Analyze data and recommend format.

        Decision Logic:
        - depth > 6: Favor JSON (TOON indentation overhead)
        - uniformity > 80%: Strongly favor TOON (tabular savings)
        - uniformity < 30%: Favor JSON (little benefit)
        - reference_density > 50%: Consider graph format (v1.2)
        """
        metrics = self._compute_metrics(data)
        return self._make_decision(metrics)

    def _compute_metrics(self, data: Any) -> DataMetrics:
        """Compute data structure metrics."""
        depth = self._max_depth(data)
        uniformity = self._uniformity_score(data)
        tabular = self._tabular_eligibility(data)
        refs = self._reference_density(data)
        size = len(str(data))

        return DataMetrics(depth, uniformity, tabular, refs, size)

    def _make_decision(self, metrics: DataMetrics) -> FormatDecision:
        """Make format recommendation based on metrics."""
        reasoning = []
        score = 0.5  # Start neutral

        # Depth heuristic
        if metrics.nesting_depth > 6:
            score -= 0.3
            reasoning.append(f"High nesting depth ({metrics.nesting_depth}) favors JSON")
        elif metrics.nesting_depth <= 3:
            score += 0.1
            reasoning.append("Shallow nesting suitable for TOON")

        # Uniformity heuristic
        if metrics.uniformity_score > 80:
            score += 0.4
            reasoning.append(f"High uniformity ({metrics.uniformity_score:.1f}%) strongly favors TOON")
        elif metrics.uniformity_score < 30:
            score -= 0.2
            reasoning.append(f"Low uniformity ({metrics.uniformity_score:.1f}%) favors JSON")

        # Tabular eligibility
        if metrics.tabular_eligibility > 50:
            score += 0.2
            reasoning.append(f"High tabular eligibility ({metrics.tabular_eligibility:.1f}%)")

        # Make decision
        if score > 0.6:
            return FormatDecision("toon", score, reasoning, metrics)
        elif score < 0.4:
            return FormatDecision("json", 1.0 - score, reasoning, metrics)
        else:
            reasoning.append("Marginal case, defaulting to TOON for token savings")
            return FormatDecision("toon", score, reasoning, metrics)


def smart_encode(
    data: Any,
    auto: bool = True,
    **kwargs: Any,
) -> tuple[str, FormatDecision]:
    """Encode with intelligent format selection.

    Args:
        data: Python object to encode
        auto: If True, use DecisionEngine recommendation
        **kwargs: Additional encoding options

    Returns:
        (encoded_string, FormatDecision)
    """
    engine = DecisionEngine()
    decision = engine.analyze(data)

    if auto and decision.recommended_format == "json":
        import json
        return (json.dumps(data, **kwargs), decision)

    from pytoon import encode
    return (encode(data, **kwargs), decision)
```

---

## Implementation Roadmap

### Phase 1: DataMetrics (Week 5, Days 1-2)

**Tasks:**

- [ ] Create `pytoon/decision/__init__.py`
- [ ] Implement metrics computation
  - _max_depth() - Tree traversal
  - _uniformity_score() - Array uniformity analysis
  - _tabular_eligibility() - Use TabularAnalyzer
  - _reference_density() - Object identity tracking
- [ ] Unit tests for all metrics
- [ ] Benchmark on diverse datasets

### Phase 2: DecisionEngine (Week 5, Days 3-4)

**Tasks:**

- [ ] Implement decision logic heuristics
- [ ] FormatDecision dataclass with reasoning
- [ ] Confidence scoring algorithm
- [ ] Integration tests with real-world data
- [ ] Validate >90% accuracy on benchmarks

### Phase 3: Public API (Week 6, Days 1-2)

**Tasks:**

- [ ] Implement smart_encode() function
- [ ] Add to public API (`from pytoon import smart_encode`)
- [ ] CLI flag: `--auto-decide`
- [ ] Documentation with decision examples
- [ ] Blog post: "PyToon v1.1: Smart Format Selection"

---

## Quality Assurance

### Testing Strategy

```python
class TestDecisionEngine:
    def test_high_uniformity_favors_toon(self) -> None:
        """Uniform tabular data should favor TOON."""
        data = [{"id": i, "name": f"User{i}"} for i in range(100)]
        engine = DecisionEngine()
        decision = engine.analyze(data)
        assert decision.recommended_format == "toon"
        assert decision.confidence > 0.7

    def test_deep_nesting_favors_json(self) -> None:
        """Deeply nested data should favor JSON."""
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": 1}}}}}}}
        engine = DecisionEngine()
        decision = engine.analyze(data)
        assert decision.recommended_format == "json"

    def test_reasoning_provided(self) -> None:
        """Decision should include reasoning."""
        data = [{"id": 1}]
        engine = DecisionEngine()
        decision = engine.analyze(data)
        assert len(decision.reasoning) > 0
```

---

## Risk Management

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Heuristics too simplistic | HIGH | MEDIUM | Extensive benchmarking, tune thresholds |
| Performance overhead | MEDIUM | LOW | Cache metrics, optimize traversal |
| False recommendations | HIGH | LOW | Conservative defaults, explain reasoning |

---

## References & Traceability

**Specification:** docs/specs/decision/spec.md
**Research:** docs/research/intel.md - Strategic Priority #5, Unique Differentiator
**Dependencies:** CORE-001, ENCODER-001 (TabularAnalyzer for uniformity)

---

**Document Version**: 1.0
**Implementation Status**: Ready for v1.1 Ticket Generation
**Strategic Value**: HIGH - Primary v1.1 differentiator from competitors
