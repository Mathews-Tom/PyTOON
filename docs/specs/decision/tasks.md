# Tasks: Decision Engine Module

**From:** `spec.md` + `plan.md`
**Timeline:** 2 weeks (v1.1, Weeks 5-6)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 4
- Estimated effort: 21 story points
- Critical path duration: 8 days
- Key risks: Heuristic accuracy, false recommendations

## Phase Breakdown

### Phase 1: Metrics Computation (Days 1-3, 8 SP)

**Goal:** Compute structural metrics for format decision
**Deliverable:** DataMetrics class with comprehensive analysis

#### Tasks

**DECISION-002: Implement DataMetrics Class**

- **Description:** Create DataMetrics that computes structural metrics including nesting depth, uniformity score, tabular eligibility percentage, reference density, and total size
- **Acceptance:**
  - [ ] DataMetrics dataclass with all fields
  - [ ] _max_depth() computes maximum nesting depth
  - [ ] _uniformity_score() calculates array uniformity (0-100%)
  - [ ] _tabular_eligibility() uses TabularAnalyzer
  - [ ] _reference_density() tracks shared object references via id()
  - [ ] total_size_bytes field for data size
  - [ ] O(n) traversal algorithm
  - [ ] Unit tests for all metrics
  - [ ] Benchmark on diverse datasets
  - [ ] mypy --strict passes
- **Effort:** 8 story points (4-5 days)
- **Owner:** Backend Developer
- **Dependencies:** ENCODER-004 (TabularAnalyzer)
- **Priority:** P1 (Critical for v1.1 - foundation for decisions)

### Phase 2: Decision Logic (Days 4-6, 8 SP)

**Goal:** Implement format recommendation heuristics
**Deliverable:** DecisionEngine with reasoning and confidence scoring

#### Tasks

**DECISION-003: Implement DecisionEngine Class**

- **Description:** Create DecisionEngine that analyzes DataMetrics and recommends optimal format (TOON vs JSON) with confidence score and reasoning array explaining the decision
- **Acceptance:**
  - [ ] FormatDecision dataclass with recommended_format, confidence, reasoning, metrics
  - [ ] analyze(data) returns FormatDecision
  - [ ] Depth > 6 levels: score -= 0.3, reasoning "High nesting favors JSON"
  - [ ] Uniformity > 80%: score += 0.4, reasoning "High uniformity favors TOON"
  - [ ] Uniformity < 30%: score -= 0.2, reasoning "Low uniformity favors JSON"
  - [ ] Tabular eligibility > 50%: score += 0.2
  - [ ] Confidence score 0.0 - 1.0 range
  - [ ] Reasoning array with clear explanations
  - [ ] Unit tests for all heuristics
  - [ ] >90% accuracy on benchmark datasets
  - [ ] mypy --strict passes
- **Effort:** 8 story points (4-5 days)
- **Owner:** Backend Developer
- **Dependencies:** DECISION-002 (DataMetrics)
- **Priority:** P1 (Critical for v1.1 - core intelligence)

### Phase 3: Public API (Days 7-8, 5 SP)

**Goal:** Expose smart_encode() as public API
**Deliverable:** smart_encode() function with auto mode and CLI integration

#### Tasks

**DECISION-004: Implement smart_encode API**

- **Description:** Create smart_encode() function that automatically selects optimal format using DecisionEngine and returns both encoded string and FormatDecision
- **Acceptance:**
  - [ ] smart_encode(data, auto=True) signature
  - [ ] Returns tuple[str, FormatDecision]
  - [ ] When auto=True and decision is "json", uses json.dumps()
  - [ ] When auto=True and decision is "toon", uses pytoon.encode()
  - [ ] When auto=False, always uses TOON
  - [ ] Accepts **kwargs for encoding options
  - [ ] Added to pytoon.**init**.py exports
  - [ ] Google-style docstrings with examples
  - [ ] Integration tests
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** DECISION-003 (DecisionEngine), CORE-006 (encode)
- **Priority:** P1 (Important - user-facing API)

**DECISION-005: Add CLI --auto-decide Flag**

- **Description:** Add --auto-decide flag to CLI encode command that uses smart_encode() and --explain flag that prints FormatDecision reasoning
- **Acceptance:**
  - [ ] --auto-decide flag on encode command
  - [ ] Uses smart_encode() when flag enabled
  - [ ] --explain flag prints reasoning to stderr
  - [ ] Format: "Recommended: TOON (confidence: 85%)\nReasons:\n- High uniformity (92%) favors TOON\n- Shallow nesting suitable for TOON"
  - [ ] Works with other encode flags
  - [ ] Unit tests for new flags
  - [ ] mypy --strict passes
- **Effort:** 2 story points (3-4 hours)
- **Owner:** Backend Developer
- **Dependencies:** DECISION-004 (smart_encode), CLI-003 (encode command)
- **Priority:** P1 (Important - usability feature)

## Critical Path

```plaintext
ENCODER-004 → DECISION-002 → DECISION-003 → DECISION-004
                                                  ↓
                                             DECISION-005
```

**Bottlenecks:**

- DECISION-003: Heuristic accuracy critical (>90% target)
- DECISION-002: Metrics computation must be comprehensive

**Parallel Tracks:**

- DECISION-005 can be developed after DECISION-004 API stable

## Quick Wins (Days 1-2)

1. **DECISION-002**: Metrics provide immediate insight into data
2. **DECISION-003**: Core intelligence differentiator

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| DECISION-002 | Metrics too slow on large data | O(n) algorithm, single traversal | Cache metrics for repeated calls |
| DECISION-003 | Heuristics too simplistic | Extensive benchmarking, tune thresholds | Conservative defaults, explain reasoning |
| DECISION-003 | False recommendations | Clear confidence scoring | User can override with auto=False |

## Testing Strategy

### Automated Testing Tasks

- Unit tests for all metric computations
- Unit tests for decision heuristics (all thresholds)
- Benchmark tests: >90% accuracy on diverse datasets
- Integration tests for smart_encode()
- CLI tests for --auto-decide and --explain flags
- Performance tests: <10ms for decision

### Benchmark Datasets

1. **High Uniformity** (TOON recommended): Employee records, time-series
2. **Low Uniformity** (JSON recommended): Heterogeneous configs
3. **Deep Nesting** (JSON recommended): Complex nested structures
4. **Mixed Data** (Decision varies): Real-world API responses

### Quality Gates

- mypy --strict passes
- >90% accuracy on benchmark datasets
- Reasoning explanations clear and actionable
- Performance <10ms for format decision
- Confidence scores meaningful (0.0 - 1.0)

## Team Allocation

**Backend Developer (1.0 FTE)**

- Metrics computation (DECISION-002)
- Decision heuristics (DECISION-003)
- Public API (DECISION-004)
- CLI integration (DECISION-005)

## Sprint Planning

**Weeks 5-6: Decision Engine (21 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Days 1-3 | Data Metrics | 8 SP | DECISION-002: Metrics |
| Days 4-6 | Decision Logic | 8 SP | DECISION-003: Engine |
| Day 7 | Public API | 3 SP | DECISION-004: smart_encode |
| Day 8 | CLI Integration | 2 SP | DECISION-005: --auto-decide |

## Strategic Value

**UNIQUE DIFFERENTIATOR**: No competitors have automatic format selection.

This feature solves the "when to use TOON vs JSON" decision paralysis and provides:

1. Automatic optimization for token savings
2. Clear reasoning for format recommendations
3. Confidence scoring for transparency
4. CLI integration for immediate usability

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- >90% accuracy on benchmark datasets
- mypy --strict passes
- Reasoning explanations clear and actionable
- CLI flags working (--auto-decide, --explain)
- Documentation complete with decision examples
- Blog post drafted: "PyToon v1.1: Smart Format Selection"
