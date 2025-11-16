# PyToon Decoder Refactoring: Executive Summary

## Critical Issue Identified

The PyToon decoder **cannot properly parse nested objects within list-format arrays** due to a fundamental architectural flaw: it strips indentation and relies on pattern matching instead of depth-based parsing.

**Impact**: Data loss and incorrect decoding of valid TOON structures.

---

## Root Cause Analysis

### Current Implementation (BROKEN)

```python
# pytoon/core/decoder.py:361
stripped = line.strip()          # Destroys indentation info
if stripped.startswith("- "):    # Heuristic pattern matching
```

### Reference Implementation (CORRECT)

```typescript
// TOON TypeScript reference
const depth = Math.floor(indent / indentSize)  // Preserve depth
if (line.depth === targetDepth && ...)          // Depth comparison
```

---

## Key Findings

### 1. TOON v2.0 Specification Requirements

From official spec §10 (Objects as List Items):

- First field goes **on the hyphen line**: `- key: value`
- Sibling fields at **depth + 1** (one deeper than hyphen)
- Nested object fields at **depth + 2**
- Structure determined by **depth comparison**, not pattern matching

### 2. Encoder Bug

`pytoon/core/encoder.py:286` incorrectly places entire encoded value after "- ":

```python
lines.append(f"{indent}- {encoded}")  # WRONG: entire dict after hyphen
```

Should be: first field on hyphen line, rest indented below.

### 3. Decoder Bug

`pytoon/core/decoder.py:361` destroys depth information:

```python
stripped = line.strip()  # LOSES ALL DEPTH CONTEXT
```

Should be: compute depth from leading spaces, use depth for parsing decisions.

---

## Solution Architecture

Based on TypeScript reference implementation:

1. **Scanner Phase**: Pre-parse all lines with depth computation
2. **LineCursor**: Navigate through parsed lines with depth awareness
3. **Depth-Based Recursion**: Use depth comparisons to determine structure
4. **followDepth Tracking**: Know where sibling fields should appear

### Key Data Structures

```python
@dataclass
class ParsedLine:
    raw: str           # "  name: Alice"
    indent: int        # 2
    content: str       # "name: Alice"
    depth: int         # 1 (= 2 // 2)
    line_number: int   # 5

class LineCursor:
    def peek() -> ParsedLine
    def next() -> ParsedLine
    def at_end() -> bool
```

---

## Documentation Created

1. **[CODEC_INDENTATION_REFACTORING.md](CODEC_INDENTATION_REFACTORING.md)**
   - Complete technical specification for both encoder and decoder
   - Reference implementation analysis
   - Full code examples for each module
   - Testing strategy
   - 12 comprehensive sections

2. **[INDENTATION_QUICK_REFERENCE.md](INDENTATION_QUICK_REFERENCE.md)**
   - One-page summary of key concepts
   - TOON v2.0 rules at a glance
   - Critical data structures
   - Validation test case

3. **[IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)**
   - Phase-by-phase implementation guide
   - 70+ specific checkboxes
   - Validation gates
   - Sign-off criteria

---

## Estimated Effort

- **Day 1**: Scanner and LineCursor implementation
- **Day 2**: Parser utilities (headers, primitives, escaping)
- **Day 3**: Core decoder with depth tracking
- **Day 4**: Encoder fixes + API integration
- **Day 5**: Comprehensive testing and validation

**Total**: 3-5 days for complete fix

---

## Success Criteria

```python
def test_critical_fix():
    data = [
        {'id': 1, 'meta': {'created': '2025'}},
        {'id': 2, 'meta': {'created': '2024'}},
    ]
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data  # MUST PASS
```

- [ ] All nested object combinations roundtrip correctly
- [ ] Passes TOON v2.0 conformance tests
- [ ] 85%+ test coverage maintained
- [ ] No performance regression
- [ ] mypy --strict compliance

---

## Immediate Next Steps

1. **Create failing test** that demonstrates the bug
2. **Implement Scanner** to parse lines with depth
3. **Implement LineCursor** for navigation
4. **Refactor decoder** to use depth-based parsing
5. **Fix encoder** for proper list-item object formatting

---

## References

- [TOON v2.0 Specification](https://github.com/toon-format/spec/blob/main/SPEC.md) - Sections §10, §12
- [TypeScript Reference](https://github.com/toon-format/toon/tree/main/packages/toon/src/decode) - scanner.ts, decoders.ts
- Current codebase: `pytoon/core/decoder.py:341-410` (list array parsing)
- Current codebase: `pytoon/core/encoder.py:281-287` (list encoding)

---

## Conclusion

The indentation tracking issue is a **critical architectural limitation** that requires **significant but well-defined refactoring**. The solution is clearly documented with reference implementation analysis, comprehensive code examples, and a phased implementation plan. With the provided documentation, the fix can be implemented systematically with high confidence in correctness.
