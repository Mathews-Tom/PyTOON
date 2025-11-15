# Reference Support Module Specification

**Component ID**: REFS-001
**Version**: v1.1-1.2
**Priority**: P1
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 8 (Phases 2-3)

## 1. Overview

The Reference Support module handles relational data (v1.1) and circular references (v1.2).

**Success Metrics**: Schema-based references working (v1.1), graph encoding/decoding without errors (v1.2)

## 2. Functional Requirements

### FR-1: Schema-Based References (v1.1)

- Detect reference relationships (fields ending in "Id", "Ref")
- Encode schema metadata in `_schema` section
- `encode_refs(data, mode='schema')` API
- `decode_refs(toon_str, resolve=True)` API

### FR-2: Graph Encoding (v1.2)

- Circular reference normalization with object IDs (`$1`, `$2`)
- Graph format: `_graph: true` flag
- Object ID assignment during traversal
- Reference placeholders for circular links

### FR-3: ReferenceEncoder

- Detect relationships during encoding
- Generate schema metadata
- Assign object IDs for graph mode

### FR-4: ReferenceDecoder

- Parse schema metadata
- Resolve reference IDs to objects
- Reconstruct circular references

## 3. Component Structure

```plaintext
pytoon/references/
├── encoder.py    # ReferenceEncoder class
├── decoder.py    # ReferenceDecoder class
└── graph.py      # Graph normalization (v1.2)
```

## 4. Acceptance Criteria

- [ ] Schema-based references encode/decode correctly (v1.1)
- [ ] Circular references handled without errors (v1.2)
- [ ] `encode_refs()` and `decode_refs()` APIs functional
- [ ] `encode_graph()` and `decode_graph()` APIs functional (v1.2)
- [ ] Roundtrip fidelity for relational and graph data

## 5. Dependencies

- **ENCODER-001**: Extends encoding with reference detection
- **DECODER-001**: Extends decoding with reference resolution

**Status**: Ready for Planning Phase (v1.1-1.2)
