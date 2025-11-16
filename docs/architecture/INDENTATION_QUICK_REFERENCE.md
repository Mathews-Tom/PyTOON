# PyToon Indentation Tracking: Quick Reference

## The Core Problem

**Current Implementation (BROKEN)**:
```python
# pytoon/core/decoder.py:361
stripped = line.strip()  # ← DESTROYS INDENTATION INFO
if stripped.startswith("- "):  # ← PATTERN MATCHING (fragile)
```

**Why it fails**: Cannot determine when a nested object ends vs. when a sibling field continues.

---

## The Fix: Depth-Based Parsing

### Key Principle

```
Depth = leading_spaces // indent_size
```

Track depth for every line. Use depth comparisons, NOT pattern matching.

---

## TOON v2.0 Rules for Objects in List Items

```toon
items[2]:              # depth=0, array header
  - id: 1              # depth=1, list item with first field
    meta:              # depth=1, sibling field (nested object)
      created: 2025    # depth=2, nested object field
    status: active     # depth=1, sibling field
  - id: 2              # depth=1, new list item
    name: Second       # depth=1, sibling field
```

### Parsing Rules:

1. **List items** start with `"- "` at `item_depth = array_depth + 1`
2. **First field** is on the hyphen line (after `"- "`)
3. **Sibling fields** are at `item_depth` (NOT starting with `"- "`)
4. **Nested objects** have fields at `item_depth + 1`
5. **New list item** detected when depth = item_depth AND starts with `"- "`

---

## Reference Implementation Pattern

```python
def decode_object_from_list_item(first_field_content, cursor, base_depth):
    # Parse first field (on hyphen line)
    key, value = decode_key_value(first_field_content, cursor, base_depth)
    obj = {key: value}

    # Read siblings at base_depth + 1
    follow_depth = base_depth + 1

    while not cursor.at_end():
        line = cursor.peek()

        # Stop conditions:
        # 1. Line is shallower than expected
        # 2. Line is a new list item (starts with "- ")
        if line.depth < follow_depth:
            break
        if line.depth == follow_depth and line.content.startswith("- "):
            break

        # This is a sibling field
        if line.depth == follow_depth:
            cursor.advance()
            k, v = decode_key_value(line.content, cursor, follow_depth)
            obj[k] = v
        else:
            break

    return obj
```

---

## Critical Data Structures

```python
@dataclass
class ParsedLine:
    raw: str           # Original line
    indent: int        # Leading spaces
    content: str       # Content after spaces
    depth: int         # indent // indent_size
    line_number: int   # For error messages

class LineCursor:
    def peek(self) -> ParsedLine | None
    def next(self) -> ParsedLine | None
    def at_end(self) -> bool
```

---

## Encoder Fix

**Current (BROKEN)**:
```python
lines.append(f"{indent}- {encoded}")  # Multi-line encoded goes AFTER "-"
```

**Correct**:
```python
# First field ON the hyphen line
lines.append(f"{indent}- {first_key}: {first_value}")
# Subsequent fields at indent + indent_size
for key in remaining_keys:
    lines.append(f"{indent + spaces}{key}: {value}")
```

---

## Test Case to Validate Fix

```python
def test_nested_objects_in_list():
    data = [
        {'id': 1, 'meta': {'created': '2025'}},
        {'id': 2, 'meta': {'created': '2024'}},
    ]

    encoded = encode(data)
    # Expected:
    # [2]:
    #   - id: 1
    #     meta:
    #       created: "2025"
    #   - id: 2
    #     meta:
    #       created: "2024"

    decoded = decode(encoded)
    assert decoded == data  # MUST PASS after fix
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `pytoon/decoder/types.py` | Add `ParsedLine`, `LineCursor` |
| `pytoon/decoder/scanner.py` | Add `scan_lines()` function |
| `pytoon/decoder/parser_utils.py` | Add header/key/value parsing |
| `pytoon/decoder/core.py` | Implement depth-based decoder |
| `pytoon/core/encoder.py:286` | Fix list item object formatting |
| `pytoon/__init__.py` | Wire up new decoder |

---

## Success Metrics

- [ ] `decode(encode(data)) == data` for all nested object combinations
- [ ] Passes TOON v2.0 conformance tests
- [ ] No regression in existing functionality
- [ ] 85%+ test coverage maintained
- [ ] mypy --strict passes
