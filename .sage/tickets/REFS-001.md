# REFS-001: Reference Support Implementation (v1.1-1.2)

**State:** UNPROCESSED
**Priority:** P1
**Type:** Epic
**Version:** 1.1

## Description

Implement reference/graph support: schema-based references (v1.1), circular reference handling (v1.2). The reference module enables encoding/decoding of relational data with schema metadata and circular references using object ID normalization.

## Acceptance Criteria

- [ ] ReferenceEncoder detects relationships and generates schema metadata (v1.1)
- [ ] ReferenceDecoder resolves reference IDs to objects (v1.1)
- [ ] Graph normalization with object IDs (`$1`, `$2`) for circular refs (v1.2)
- [ ] `encode_refs(data, mode='schema')` and `decode_refs(toon_str, resolve=True)` APIs functional
- [ ] `encode_graph(data)` and `decode_graph(toon_str)` APIs functional (v1.2)
- [ ] 100% mypy strict mode compliance
- [ ] Roundtrip fidelity for relational and graph data
- [ ] 85%+ test coverage

## Target Files

- `pytoon/references/__init__.py` (create): References module exports
- `pytoon/references/encoder.py` (create): ReferenceEncoder class
- `pytoon/references/decoder.py` (create): ReferenceDecoder class
- `pytoon/references/graph.py` (create): Graph normalization (circular references, object IDs)
- `pytoon/__init__.py` (modify): Add encode_refs, decode_refs, encode_graph, decode_graph exports
- `tests/unit/test_references.py` (create): Reference encoding/decoding tests
- `tests/unit/test_graph.py` (create): Graph encoding/decoding tests

## Dependencies

- ENCODER-001 (extends encoding with reference detection)
- DECODER-001 (extends decoding with reference resolution)

## Context

**Specs:** docs/specs/references/spec.md
**Design:** docs/pytoon-system-design.md Section 8 (Phases 2-3)

## Progress

**Notes:** Generated from /sage.specify command
