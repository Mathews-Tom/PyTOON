# PyToon Decoder Refactoring Implementation Checklist

## Pre-Implementation Validation

- [ ] Confirm understanding of TOON v2.0 spec §10 (Objects as List Items)
- [ ] Review TypeScript reference implementation structure
- [ ] Create failing test case that demonstrates the bug
- [ ] Document expected behavior for nested objects in list arrays

---

## Phase 1: Data Structures (Day 1)

### 1.1 Create Type Definitions

```bash
# Create new file
touch pytoon/decoder/types.py
```

- [ ] Define `ParsedLine` dataclass with:
  - `raw: str` - Original line
  - `indent: int` - Leading space count
  - `content: str` - Content after indentation
  - `depth: int` - Computed depth
  - `line_number: int` - 1-based line number

- [ ] Define `BlankLineInfo` for strict mode validation

- [ ] Define `ArrayHeaderInfo` dataclass:
  - `key: str | None`
  - `length: int`
  - `delimiter: str`
  - `fields: list[str] | None`

- [ ] Add type exports to `pytoon/decoder/__init__.py`

### 1.2 Implement LineCursor

- [ ] Create `LineCursor` class with:
  - `__init__(lines, blank_lines)`
  - `peek() -> ParsedLine | None`
  - `next() -> ParsedLine | None`
  - `current() -> ParsedLine | None`
  - `advance() -> None`
  - `at_end() -> bool`
  - `peek_at_depth(depth) -> ParsedLine | None`

- [ ] Add blank line tracking for validation

### 1.3 Unit Tests for Data Structures

- [ ] Test `ParsedLine` immutability
- [ ] Test `LineCursor.peek()` doesn't advance
- [ ] Test `LineCursor.next()` advances
- [ ] Test `LineCursor.at_end()` detection
- [ ] Test `LineCursor.peek_at_depth()` filtering

---

## Phase 2: Scanner Implementation (Day 1)

### 2.1 Create Scanner Module

```bash
touch pytoon/decoder/scanner.py
```

- [ ] Implement `scan_lines(source, indent_size, strict)`:
  - Split source on newlines
  - Count leading spaces for each line
  - Compute depth: `indent // indent_size`
  - Track blank lines separately
  - Return `ScanResult` with lines and blank_lines

- [ ] Strict mode validation:
  - [ ] Reject tabs in indentation
  - [ ] Enforce exact multiples of indent_size
  - [ ] Track line numbers for error messages

### 2.2 Scanner Tests

- [ ] Test depth computation for various indentations
- [ ] Test blank line tracking
- [ ] Test strict mode tab rejection
- [ ] Test strict mode indent validation
- [ ] Test edge cases: empty input, single line, trailing newlines

---

## Phase 3: Parser Utilities (Day 2)

### 3.1 Create Parser Utils Module

```bash
touch pytoon/decoder/parser_utils.py
```

- [ ] Implement `parse_array_header()`:
  - Extract key (if any)
  - Parse bracket segment for length and delimiter
  - Parse optional fields segment
  - Extract inline values after colon

- [ ] Implement `parse_bracket_segment()`:
  - Handle length parsing
  - Detect delimiter suffix (tab, pipe)

- [ ] Implement `parse_delimited_values()`:
  - Split on delimiter
  - Handle quoted strings with escapes
  - Preserve empty tokens

- [ ] Implement `parse_primitive_token()`:
  - Handle quoted strings
  - Parse null/true/false literals
  - Parse integers and floats
  - Return unquoted strings

- [ ] Implement `parse_key_token()`:
  - Handle quoted keys
  - Handle unquoted keys
  - Validate colon after key
  - Return key, end position, and quoted flag

- [ ] Implement `unescape_string()`:
  - Handle `\\`, `\"`, `\n`, `\r`, `\t`
  - Reject invalid escape sequences

- [ ] Implement `find_closing_quote()`:
  - Handle escape sequences
  - Return position or -1

### 3.2 Parser Utils Tests

- [ ] Test array header parsing (all variations)
- [ ] Test delimited value parsing with quotes
- [ ] Test primitive token parsing (all types)
- [ ] Test key parsing (quoted and unquoted)
- [ ] Test escape sequence handling
- [ ] Test invalid escape rejection in strict mode

---

## Phase 4: Core Decoder (Day 3)

### 4.1 Main Decoder Entry Point

```bash
touch pytoon/decoder/core.py
```

- [ ] Implement `decode_toon()`:
  - Call scanner to get parsed lines
  - Handle empty document (return {})
  - Create LineCursor
  - Call `decode_value_from_cursor()`

- [ ] Implement `decode_value_from_cursor()`:
  - Check for root array header
  - Check for single primitive
  - Default to object

### 4.2 Object Decoding

- [ ] Implement `decode_object()`:
  - Track computed depth from first field
  - Loop through lines at computed depth
  - Parse key-value pairs
  - Stop when depth changes

- [ ] Implement `decode_key_value()`:
  - Check for array header first
  - Parse key and rest of line
  - Handle nested object (no value after colon)
  - Handle inline primitive value
  - Return (key, value) tuple

### 4.3 Array Decoding

- [ ] Implement `decode_array_from_header()`:
  - Dispatch to inline/tabular/list decoders

- [ ] Implement `decode_inline_array()`:
  - Parse delimited values
  - Convert to primitives
  - Validate count in strict mode

- [ ] Implement `decode_tabular_array()`:
  - Read rows at base_depth + 1
  - Parse delimited values
  - Map to field names
  - Validate counts in strict mode

- [ ] Implement `decode_list_array()`:
  - Read list items at base_depth + 1
  - Check for "- " prefix
  - Dispatch to `decode_list_item()`
  - Validate count in strict mode

### 4.4 Critical: List Item Object Decoding

- [ ] Implement `decode_list_item()`:
  - Extract content after "- "
  - Check for nested array header
  - Check for object (has colon)
  - Handle primitive

- [ ] **CRITICAL** Implement `decode_object_from_list_item()`:
  - Parse first field from hyphen line
  - Set follow_depth = base_depth + 1
  - Loop: read sibling fields at follow_depth
  - Stop when: depth < follow_depth OR new list item
  - This is the KEY fix for nested object indentation

### 4.5 Core Decoder Tests

- [ ] Test object decoding (flat)
- [ ] Test object decoding (nested)
- [ ] Test inline array decoding
- [ ] Test tabular array decoding
- [ ] Test list array with primitives
- [ ] **CRITICAL** Test list array with nested objects
- [ ] Test deeply nested structures
- [ ] Test empty arrays/objects
- [ ] Test strict mode validation errors

---

## Phase 5: Encoder Fixes (Day 4)

### 5.1 Fix List Array Encoding

File: `pytoon/core/encoder.py`

- [ ] Refactor `_encode_list()` for non-tabular cases:
  - Don't put entire encoded value after "- "
  - For dict items, use `encode_list_item_object()`

- [ ] Implement `encode_list_item_object()`:
  - First field on hyphen line: `- key: value`
  - Subsequent fields at depth + 1
  - Handle nested objects (depth + 2)
  - Handle arrays as first field

- [ ] Verify indentation is consistent

### 5.2 Encoder Tests

- [ ] Test single-field object in list
- [ ] Test multi-field object in list
- [ ] Test nested object in list
- [ ] Test array value in list object
- [ ] Verify output matches TOON v2.0 spec examples

---

## Phase 6: Integration & API (Day 4)

### 6.1 Wire Up New Decoder

File: `pytoon/__init__.py`

- [ ] Import from new decoder module
- [ ] Maintain backward-compatible API signature
- [ ] Handle options: strict, expand_paths, indent

### 6.2 Update Decoder Class

File: `pytoon/core/decoder.py`

- [ ] Modify `Decoder.decode()` to use new implementation
- [ ] Ensure all options are passed through

### 6.3 Deprecate Old Implementation

- [ ] Keep old code as `_decode_legacy()` for comparison
- [ ] Add deprecation warning if accessed directly

---

## Phase 7: Comprehensive Testing (Day 5)

### 7.1 Integration Tests

- [ ] Roundtrip test: nested objects in list arrays
- [ ] Roundtrip test: arrays in list item objects
- [ ] Roundtrip test: deeply nested (3+ levels)
- [ ] Roundtrip test: mixed arrays (primitives + objects)

### 7.2 Property-Based Tests

- [ ] Generate random nested structures with Hypothesis
- [ ] Test encode→decode roundtrip for all structures
- [ ] Test decode→encode produces valid TOON

### 7.3 Conformance Tests

- [ ] Implement TOON v2.0 spec §10 examples
- [ ] Implement Appendix A examples
- [ ] Verify against TypeScript reference implementation outputs

### 7.4 Edge Cases

- [ ] Empty list item: `- ` → `{}`
- [ ] Single dash: `-` → `{}`
- [ ] Quoted keys in objects
- [ ] Special characters in values
- [ ] Unicode strings

### 7.5 Error Handling

- [ ] Invalid indentation (strict mode)
- [ ] Array count mismatches
- [ ] Unterminated strings
- [ ] Invalid escape sequences
- [ ] Missing colons after keys

---

## Phase 8: Documentation & Cleanup (Day 5)

### 8.1 Code Documentation

- [ ] Add comprehensive docstrings to all new functions
- [ ] Document depth tracking strategy
- [ ] Add inline comments for complex logic

### 8.2 User Documentation

- [ ] Update README with any API changes
- [ ] Add examples of nested object encoding/decoding
- [ ] Document strict vs lenient mode behavior

### 8.3 Performance Validation

- [ ] Benchmark decoder performance
- [ ] Ensure <100ms for 1-10KB datasets
- [ ] Profile memory usage with large documents

### 8.4 Final Cleanup

- [ ] Remove deprecated code (after validation period)
- [ ] Update CHANGELOG.md
- [ ] Run full test suite
- [ ] Run mypy --strict
- [ ] Run ruff check
- [ ] Ensure 85%+ code coverage

---

## Validation Gates

### Gate 1: Scanner Works
```python
scan_lines("  name: Alice", 2, True)
# Returns ParsedLine with depth=1
```

### Gate 2: Object Decoding Works
```python
decode_toon("name: Alice\nage: 30", 2, True)
# Returns {'name': 'Alice', 'age': 30}
```

### Gate 3: List Array Works
```python
decode_toon("[2]:\n  - 1\n  - 2", 2, True)
# Returns [1, 2]
```

### Gate 4: CRITICAL - Nested Objects in List Work
```python
data = [{'id': 1, 'meta': {'created': '2025'}}]
encoded = encode(data)
decoded = decode(encoded)
assert decoded == data  # MUST PASS
```

---

## Risk Mitigation

- [ ] Run old and new decoder in parallel during testing
- [ ] Compare outputs for discrepancies
- [ ] Keep old decoder accessible until fully validated
- [ ] Monitor for performance regressions

---

## Sign-Off Criteria

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Property-based tests pass
- [ ] Conformance tests pass
- [ ] mypy --strict passes
- [ ] ruff check passes
- [ ] Code coverage ≥ 85%
- [ ] Performance benchmarks within targets
- [ ] No known regressions
- [ ] Documentation complete
