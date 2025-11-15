# References Module Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/references/spec.md`
**Component ID:** REFERENCES-001
**Priority:** P2 (v1.1-1.2 Feature - Advanced Use Cases)

---

## Context & Documentation

### Traceability Chain

1. **Formal Specification:** docs/specs/references/spec.md
   - ReferenceEncoder: Schema-based reference encoding (`_schema` section)
   - ReferenceDecoder: Reference resolution with `resolve_refs=True`
   - GraphEncoder: Circular reference normalization (object IDs: $1, $2)

2. **Research & Intelligence:** docs/research/intel.md
   - Enables complex enterprise data structures
   - Handles relational data efficiently
   - Circular reference support critical for graph data

---

## Executive Summary

### Business Alignment

- **Purpose:** Handle relational data with references and circular structures
- **Value Proposition:** Support complex enterprise data models
- **Target Users:** Enterprise developers with graph/relational data

### Technical Approach

- **Architecture Pattern:** Reference tracking with object ID mapping
- **Technology Stack:** Python 3.8+, id() tracking, schema generation
- **Implementation Timeline:** Weeks 7-8 (v1.1) and Weeks 9-11 (v1.2)

---

## Core Implementation

### ReferenceEncoder

```python
class ReferenceEncoder:
    """Encode data with reference support.

    Creates _schema section for shared references:

    _schema:
      User: {id: int, name: str}
    users[2]{$User}:
      $1,Alice
      $2,Bob
    """

    def encode_refs(self, data: Any, mode: str = "schema") -> str:
        """Encode with reference tracking."""
        if mode == "schema":
            return self._schema_mode(data)
        elif mode == "inline":
            return self._inline_mode(data)
        raise ValueError(f"Unknown mode: {mode}")

    def _schema_mode(self, data: Any) -> str:
        """Generate schema-based encoding with shared references."""
        # Track seen objects by id()
        seen: dict[int, str] = {}
        schema: dict[str, Any] = {}

        # First pass: detect shared references
        self._detect_references(data, seen, schema)

        # Second pass: encode with references
        return self._encode_with_schema(data, schema)


class GraphEncoder:
    """Encode graphs with circular references.

    Uses object IDs ($1, $2) to break cycles:

    users[2]{id,friend}:
      1,$2
      2,$1
    """

    def encode_graph(self, data: Any) -> str:
        """Encode graph structure with cycle handling."""
        object_ids: dict[int, str] = {}
        id_counter = 0

        def assign_id(obj: Any) -> str:
            nonlocal id_counter
            obj_id = id(obj)
            if obj_id not in object_ids:
                id_counter += 1
                object_ids[obj_id] = f"${id_counter}"
            return object_ids[obj_id]

        # Traverse and assign IDs
        self._assign_ids(data, assign_id)

        # Encode with ID references
        return self._encode_with_ids(data, object_ids)
```

---

## Implementation Roadmap

### Phase 1: Reference Detection (Week 7, Day 4)

**Tasks:**
- [ ] Create `pytoon/references/__init__.py`
- [ ] Implement reference detection (id() tracking)
- [ ] Schema generation for shared types
- [ ] Unit tests for detection

### Phase 2: Schema-Based Encoding (Week 8, Days 1-2)

**Tasks:**
- [ ] ReferenceEncoder._schema_mode()
- [ ] encode_refs() API
- [ ] decode_refs() with resolve_refs option
- [ ] Integration tests

### Phase 3: Graph Encoding (Weeks 9-10 - v1.2)

**Tasks:**
- [ ] GraphEncoder for circular references
- [ ] Object ID assignment ($1, $2)
- [ ] encode_graph() and decode_graph() APIs
- [ ] Test with circular structures

---

## API Surface

```python
from pytoon import encode_refs, decode_refs, encode_graph, decode_graph

# Schema-based references (v1.1)
data = {"users": [user1, user2], "admins": [user1]}  # user1 shared
toon = encode_refs(data, mode="schema")
recovered = decode_refs(toon, resolve_refs=True)

# Graph with cycles (v1.2)
user1 = {"id": 1, "friend": None}
user2 = {"id": 2, "friend": user1}
user1["friend"] = user2  # Circular reference
toon = encode_graph({"users": [user1, user2]})
recovered = decode_graph(toon)
```

---

## References & Traceability

**Specification:** docs/specs/references/spec.md
**Dependencies:** ENCODER-001, DECODER-001
**Version:** v1.1 (schema refs) and v1.2 (graph encoding)

---

**Document Version**: 1.0
**Implementation Status**: Ready for v1.1-1.2 Ticket Generation
