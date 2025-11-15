# Type System Module Specification

**Component ID**: TYPES-001
**Version**: v1.1
**Priority**: P1
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 8 (Phase 2)

## 1. Overview

The Type System provides pluggable type handler architecture for encoding/decoding custom Python types.

**Success Metrics**: 15+ built-in type handlers, extensible plugin API

## 2. Functional Requirements

### FR-1: TypeRegistry

- Register custom type handlers: `register_type_handler(python_type, handler)`
- Lookup handlers by type: `get_handler(value)`
- Priority-based resolution (user handlers > built-in handlers)

### FR-2: Built-in Type Handlers

- UUID → string representation
- datetime → ISO 8601 string
- date → ISO 8601 date string
- time → ISO 8601 time string
- timedelta → duration string
- bytes → base64 string
- Enum → value serialization
- Decimal → float conversion
- complex → [real, imag] array
- Path → string path
- set/frozenset → sorted array

### FR-3: TypeHandler Protocol

```python
class TypeHandler(Protocol):
    def encode(self, value: Any) -> str:
        """Encode custom type to TOON-compatible string."""
        
    def decode(self, value: str, hint: type | None) -> Any:
        """Decode string back to custom type."""
```

### FR-4: Type Hint-Aware Decoding

- Use type hints to guide decoding: `decode(toon_str, hint=MyClass)`
- Automatic type inference from value patterns

## 3. Component Structure

```plaintext
pytoon/types/
├── registry.py     # TypeRegistry class
├── handlers.py     # Built-in type handlers
└── protocol.py     # TypeHandler protocol
```

## 4. Acceptance Criteria

- [ ] 15+ built-in type handlers implemented
- [ ] `register_type_handler()` API functional
- [ ] Type hint-aware decoding works
- [ ] Roundtrip fidelity for all custom types
- [ ] mypy --strict passes

## 5. Dependencies

- **ENCODER-001**: Extends ValueEncoder
- **DECODER-001**: Extends Parser with type-aware decoding

**Status**: Ready for Planning Phase (v1.1)
