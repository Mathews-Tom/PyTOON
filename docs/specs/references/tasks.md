# Tasks: Reference Support Module

**From:** `spec.md` + `plan.md`
**Timeline:** 2 weeks (v1.1-1.2, Weeks 7-8)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 3
- Estimated effort: 16 story points
- Critical path duration: 8 days
- Key risks: Object identity tracking, circular reference handling

## Phase Breakdown

### Phase 1: Reference Detection (Days 1-2, 5 SP)

**Goal:** Detect shared object references in data
**Deliverable:** Reference detection and schema generation

#### Tasks

**REFS-002: Implement Reference Detection**

- **Description:** Create reference detection system that tracks shared objects via id(), detects reference patterns (fields ending in "Id", "Ref"), and generates schema metadata for encode_refs()
- **Acceptance:**
  - [ ] Track objects by id() during traversal
  - [ ] Detect shared references (same object multiple times)
  - [ ] Identify reference fields by naming pattern (*Id, *Ref)
  - [ ] Generate _schema section with type definitions
  - [ ] O(n) traversal with hash map for id tracking
  - [ ] Unit tests for reference detection
  - [ ] mypy --strict passes
- **Effort:** 5 story points (2-3 days)
- **Owner:** Backend Developer
- **Dependencies:** None (traversal logic)
- **Priority:** P1 (Blocker for reference support)

### Phase 2: Schema-Based Encoding (Days 3-5, 8 SP)

**Goal:** Implement encode_refs() and decode_refs() APIs
**Deliverable:** Relational data encoding with reference resolution

#### Tasks

**REFS-003: Implement ReferenceEncoder/Decoder**

- **Description:** Create ReferenceEncoder that generates schema-based TOON with object IDs and ReferenceDecoder that resolves references back to shared objects
- **Acceptance:**
  - [ ] ReferenceEncoder.encode_refs(data, mode='schema')
  - [ ] Schema section format: _schema: {type_name: {fields}}
  - [ ] Reference placeholders: $1, $2, etc.
  - [ ] ReferenceDecoder.decode_refs(toon_str, resolve=True)
  - [ ] Resolves $1, $2 back to actual objects
  - [ ] When resolve=False, returns with placeholder IDs
  - [ ] Roundtrip fidelity for relational data
  - [ ] Integration tests with shared objects
  - [ ] Added to pytoon.__init__.py exports
  - [ ] mypy --strict passes
- **Effort:** 8 story points (4-5 days)
- **Owner:** Backend Developer
- **Dependencies:** REFS-002, ENCODER-006, DECODER-004
- **Priority:** P1 (Critical - relational data support)

### Phase 3: Graph Encoding (Days 6-8, 3 SP) - v1.2

**Goal:** Handle circular references with graph normalization
**Deliverable:** encode_graph() and decode_graph() for cyclic data

#### Tasks

**REFS-004: Implement GraphEncoder/Decoder**

- **Description:** Create GraphEncoder that normalizes circular references with object IDs and GraphDecoder that reconstructs the object graph
- **Acceptance:**
  - [ ] encode_graph(data) detects circular references
  - [ ] Object ID assignment during traversal
  - [ ] Reference placeholder for cycles: $ref:1
  - [ ] _graph: true flag in output
  - [ ] decode_graph(toon_str) reconstructs cycles
  - [ ] No infinite recursion on circular data
  - [ ] Roundtrip fidelity for graph structures
  - [ ] Unit tests with circular references
  - [ ] Added to pytoon.__init__.py exports
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1-2 days)
- **Owner:** Backend Developer
- **Dependencies:** REFS-003
- **Priority:** P2 (v1.2 feature)

## Critical Path

```plaintext
REFS-002 → REFS-003 → REFS-004 (v1.2)
```

**Bottlenecks:**

- REFS-002: Object identity tracking must be correct
- REFS-003: Schema generation complexity

**Parallel Tracks:**

- REFS-004 (v1.2) follows after REFS-003 (v1.1) is stable

## Quick Wins (Days 1-2)

1. **REFS-002**: Reference detection enables schema generation
2. **REFS-003**: Relational data support is immediately useful

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| REFS-002 | id() not stable across runs | Document behavior, use content-based hashing | Content hash for determinism |
| REFS-003 | Schema generation too complex | Simple field list approach | Minimize schema metadata |
| REFS-004 | Infinite recursion on cycles | id() tracking during traversal | Depth limit as safety |

## Testing Strategy

### Automated Testing Tasks

- Unit tests for reference detection
- Unit tests for schema generation
- Roundtrip tests with shared objects
- Circular reference tests (no infinite loop)
- Performance tests with large object graphs
- Integration tests with mixed data

### Quality Gates

- mypy --strict passes
- 85%+ code coverage
- No infinite recursion on circular data
- Roundtrip fidelity for relational data
- Schema format documented

## Team Allocation

**Backend Developer (1.0 FTE)**

- Reference detection (REFS-002)
- Schema-based encoding (REFS-003)
- Graph normalization (REFS-004)

## Sprint Planning

**Weeks 7-8: Reference Support (16 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Days 1-2 | Reference Detection | 5 SP | REFS-002: Detection |
| Days 3-5 | Schema Encoding | 8 SP | REFS-003: encode_refs/decode_refs |
| Days 6-8 | Graph Encoding | 3 SP | REFS-004: encode_graph/decode_graph |

## API Surface

```python
from pytoon import encode_refs, decode_refs, encode_graph, decode_graph

# Schema-based references (v1.1)
user = {"id": 1, "name": "Alice"}
data = {"users": [user], "admins": [user]}  # user shared
toon = encode_refs(data, mode="schema")
# Output includes _schema section and $1 references

recovered = decode_refs(toon, resolve_refs=True)
# recovered["users"][0] is recovered["admins"][0]

# Graph with cycles (v1.2)
user1 = {"id": 1, "friend": None}
user2 = {"id": 2, "friend": user1}
user1["friend"] = user2  # Circular!

toon = encode_graph({"users": [user1, user2]})
recovered = decode_graph(toon)
# Circular reference reconstructed
```

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- mypy --strict passes
- No infinite recursion on circular data
- Roundtrip fidelity for relational and graph data
- APIs added to public exports
- Documentation with examples
- Schema format specification documented
