# Sparse Array Module Specification

**Component ID**: SPARSE-001
**Version**: v1.2
**Priority**: P2
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 8 (Phase 3)

## 1. Overview

The Sparse Array module handles arrays with optional fields and polymorphic data structures.

**Success Metrics**: 40%+ token savings on sparse tabular data, polymorphic arrays group by discriminator

## 2. Functional Requirements

### FR-1: Sparse Array Encoding

- Detect sparsity: 30%+ missing values → sparse mode
- Optional field markers: `field?` syntax
- Empty-string-as-null convention
- Automatic sparsity analysis

### FR-2: Polymorphic Array Encoding

- Discriminator-based sub-tables (`@type:` sections)
- Per-type optimal schema
- Configurable discriminator field (default: `type`)

### FR-3: SparseArrayEncoder

- Analyze field presence across rows
- Generate optional field markers
- Encode sparse values efficiently

### FR-4: PolymorphicArrayEncoder

- Group array elements by discriminator value
- Create sub-tables for each type
- Optimize schema per type

## 3. Component Structure

```plaintext
pytoon/sparse/
├── sparse.py         # SparseArrayEncoder class
└── polymorphic.py    # PolymorphicArrayEncoder class
```

## 4. Usage Examples

```python
# Sparse array (30% missing values)
events = [
    {"id": 1, "value": 100, "optional": "data"},
    {"id": 2, "value": 200},  # missing optional
    {"id": 3, "value": 300},  # missing optional
]

# Encoded with optional field marker:
events[3]{id,value,optional?}:
  1,100,data
  2,200,
  3,300,

# Polymorphic array
mixed_events = [
    {"type": "click", "id": 1, "x": 100, "y": 200},
    {"type": "pageview", "id": 2, "url": "/home"},
    {"type": "error", "id": 3, "message": "Failed"}
]

# Encoded with discriminator sub-tables:
events[3]:
  @type:click{id,x,y}:
    1,100,200
  @type:pageview{id,url}:
    2,/home
  @type:error{id,message}:
    3,Failed
```

## 5. Acceptance Criteria

- [ ] Sparse arrays (30%+ sparsity) encode efficiently
- [ ] Polymorphic arrays group by discriminator
- [ ] 40%+ token savings on sparse tabular data
- [ ] Roundtrip fidelity maintained
- [ ] mypy --strict passes

## 6. Dependencies

- **ENCODER-001**: Extends ArrayEncoder with sparse/polymorphic support

**Status**: Ready for Planning Phase (v1.2)
