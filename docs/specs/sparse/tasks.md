# Tasks: Sparse Array Module

**From:** `spec.md` + `plan.md`
**Timeline:** 3 weeks (v1.2, Weeks 9-11)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 3
- Estimated effort: 16 story points
- Critical path duration: 10 days
- Key risks: Sparsity detection accuracy, polymorphic grouping complexity

## Phase Breakdown

### Phase 1: Sparsity Analysis (Days 1-3, 5 SP)

**Goal:** Detect sparse arrays and calculate presence rates
**Deliverable:** Sparsity analyzer with threshold detection

#### Tasks

**SPARSE-002: Implement Sparsity Analysis**

- **Description:** Create sparsity analyzer that calculates field presence rates across array elements and determines if sparse format (30%+ missing) is optimal
- **Acceptance:**
  - [ ] analyze_sparsity(array) returns dict[str, float] presence rates
  - [ ] Presence rate = count / len(array) * 100
  - [ ] Threshold: 30%+ missing values triggers sparse format
  - [ ] Handles None values and missing keys
  - [ ] O(n*m) where n=rows, m=fields
  - [ ] Unit tests for presence calculation
  - [ ] Threshold tuning with benchmarks
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** ENCODER-004 (TabularAnalyzer)
- **Priority:** P2 (Important for v1.2)

### Phase 2: Sparse Encoding (Days 4-6, 5 SP)

**Goal:** Encode sparse arrays with optional field markers
**Deliverable:** SparseArrayEncoder with ? syntax

#### Tasks

**SPARSE-003: Implement SparseArrayEncoder**

- **Description:** Create SparseArrayEncoder that generates optional field markers (field?) and uses empty-as-null convention for missing values
- **Acceptance:**
  - [ ] encode_sparse(array) generates [N]{field1,field2?}: format
  - [ ] Optional fields marked with ? suffix
  - [ ] Empty string represents null/missing value
  - [ ] Consistent field ordering
  - [ ] Token savings 40%+ on sparse tabular data
  - [ ] Integration with ArrayEncoder dispatch
  - [ ] Roundtrip fidelity with SparseArrayDecoder
  - [ ] Unit tests for sparse encoding
  - [ ] Benchmark token savings
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** SPARSE-002, ENCODER-005
- **Priority:** P2 (Critical for v1.2)

### Phase 3: Polymorphic Arrays (Days 7-10, 6 SP)

**Goal:** Encode arrays with different object types
**Deliverable:** PolymorphicArrayEncoder with discriminator grouping

#### Tasks

**SPARSE-004: Implement PolymorphicArrayEncoder**

- **Description:** Create PolymorphicArrayEncoder that groups array elements by discriminator field (type) and generates sub-tables with per-type optimal schemas (@type: sections)
- **Acceptance:**
  - [ ] encode_polymorphic(array, type_field='type')
  - [ ] Groups elements by discriminator value
  - [ ] @type:{name} section headers
  - [ ] Per-type optimal schema (only fields for that type)
  - [ ] Maintains overall array length
  - [ ] Configurable discriminator field name
  - [ ] Roundtrip fidelity preserves type information
  - [ ] Token savings on heterogeneous collections
  - [ ] Integration tests with mixed types
  - [ ] mypy --strict passes
- **Effort:** 6 story points (3-4 days)
- **Owner:** Backend Developer
- **Dependencies:** SPARSE-003
- **Priority:** P2 (Important for v1.2)

## Critical Path

```plaintext
ENCODER-004 → SPARSE-002 → SPARSE-003 → SPARSE-004
```

**Bottlenecks:**

- SPARSE-002: Sparsity threshold tuning affects format selection
- SPARSE-004: Polymorphic grouping logic is complex

**Parallel Tracks:**

- SPARSE-004 can start after SPARSE-003 basic structure is done

## Quick Wins (Days 1-3)

1. **SPARSE-002**: Sparsity analysis enables format optimization
2. **SPARSE-003**: Optional field markers reduce tokens

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| SPARSE-002 | Wrong sparsity threshold | Benchmark on real datasets | Configurable threshold |
| SPARSE-003 | Empty string ambiguity | Document convention clearly | Use explicit null marker |
| SPARSE-004 | Discriminator field missing | Require field presence | Fallback to "Unknown" type |

## Testing Strategy

### Automated Testing Tasks

- Unit tests for sparsity calculation
- Unit tests for optional field marker generation
- Unit tests for polymorphic grouping
- Token savings benchmarks (40%+ target)
- Roundtrip tests with sparse data
- Integration tests with ArrayEncoder

### Quality Gates

- mypy --strict passes
- 85%+ code coverage
- Token savings 40%+ on sparse data
- Polymorphic arrays preserve type information
- No data loss on sparse encoding

## Team Allocation

**Backend Developer (1.0 FTE)**

- Sparsity analysis (SPARSE-002)
- Sparse encoding (SPARSE-003)
- Polymorphic encoding (SPARSE-004)

## Sprint Planning

**Weeks 9-11: Sparse Arrays (16 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Days 1-3 | Sparsity Analysis | 5 SP | SPARSE-002: analyze_sparsity |
| Days 4-6 | Sparse Encoding | 5 SP | SPARSE-003: SparseArrayEncoder |
| Days 7-10 | Polymorphic Arrays | 6 SP | SPARSE-004: PolymorphicArrayEncoder |

## Format Examples

**Sparse Array (30%+ missing):**

```
events[3]{id,value,optional?}:
  1,100,data
  2,200,
  3,300,
```

The `?` marks optional fields, empty means null.

**Polymorphic Array:**

```
items[3]:
  @type:Product
  [1]{id,name,price}:
    101,Widget,9.99
  @type:Service
  [2]{id,name,hourly_rate}:
    201,Consulting,150
    202,Support,75
```

Each type gets its own optimal schema.

## Token Efficiency Targets

| Data Type | Target Savings | Comparison |
|-----------|----------------|------------|
| Sparse tabular (30% missing) | 40%+ | vs dense tabular |
| Polymorphic collections | 30%+ | vs list format |
| Mixed sparse/polymorphic | 35%+ | vs JSON |

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- mypy --strict passes
- Token savings meet targets (40%+ sparse)
- Polymorphic arrays preserve type info
- Roundtrip fidelity maintained
- Integration with ArrayEncoder complete
- Documentation with format examples
- Benchmark results documented
