# Type Registry Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/types/spec.md`
**Component ID:** TYPES-001
**Priority:** P1 (v1.1 Feature - Extensibility)

---

## Context & Documentation

### Traceability Chain

1. **Formal Specification:** docs/specs/types/spec.md
   - TypeRegistry: Pluggable type handler system
   - Built-in handlers: UUID, date, time, timedelta, bytes, Enum, complex
   - register_type_handler() API for custom extensions

2. **Research & Intelligence:** docs/research/intel.md
   - Extensibility enables enterprise adoption (custom domain types)
   - Type hint-aware decoding
   - Strategic value: Differentiation through plugin architecture

---

## Executive Summary

### Business Alignment

- **Purpose:** Support custom type serialization beyond primitives
- **Value Proposition:** Handle domain-specific types (UUID, datetime, etc.)
- **Target Users:** Enterprise developers with custom data models

### Technical Approach

- **Architecture Pattern:** Registry Pattern with Protocol-based handlers
- **Technology Stack:** Python 3.8+, typing.Protocol
- **Implementation Timeline:** Weeks 6-7 (v1.1 release)

---

## Core Implementation

### TypeRegistry

```python
from typing import Any, Protocol, Type, TypeVar
from datetime import datetime, date, time, timedelta
from uuid import UUID

T = TypeVar("T")

class TypeHandler(Protocol[T]):
    """Protocol for custom type handlers."""

    @staticmethod
    def can_handle(obj: Any) -> bool:
        """Check if handler can process this object."""
        ...

    @staticmethod
    def encode(obj: T) -> str:
        """Encode object to TOON string."""
        ...

    @staticmethod
    def decode(s: str, type_hint: Type[T] | None = None) -> T:
        """Decode string back to object."""
        ...

class TypeRegistry:
    """Registry for custom type handlers."""

    def __init__(self) -> None:
        self._handlers: list[Type[TypeHandler[Any]]] = []
        self._register_builtin_handlers()

    def _register_builtin_handlers(self) -> None:
        """Register built-in type handlers."""
        self.register(UUIDHandler)
        self.register(DatetimeHandler)
        self.register(DateHandler)
        self.register(TimeHandler)
        self.register(TimedeltaHandler)
        self.register(BytesHandler)
        self.register(ComplexHandler)

    def register(self, handler: Type[TypeHandler[Any]]) -> None:
        """Register a custom type handler."""
        self._handlers.append(handler)

    def encode_value(self, obj: Any) -> str | None:
        """Try to encode with registered handlers."""
        for handler in self._handlers:
            if handler.can_handle(obj):
                return handler.encode(obj)
        return None


class UUIDHandler:
    """Handler for UUID type."""

    @staticmethod
    def can_handle(obj: Any) -> bool:
        return isinstance(obj, UUID)

    @staticmethod
    def encode(obj: UUID) -> str:
        return f"uuid:{obj}"

    @staticmethod
    def decode(s: str, type_hint: Type[UUID] | None = None) -> UUID:
        if s.startswith("uuid:"):
            return UUID(s[5:])
        return UUID(s)


class DatetimeHandler:
    """Handler for datetime type."""

    @staticmethod
    def can_handle(obj: Any) -> bool:
        return isinstance(obj, datetime)

    @staticmethod
    def encode(obj: datetime) -> str:
        return f"datetime:{obj.isoformat()}"

    @staticmethod
    def decode(s: str, type_hint: Type[datetime] | None = None) -> datetime:
        if s.startswith("datetime:"):
            return datetime.fromisoformat(s[9:])
        return datetime.fromisoformat(s)
```

---

## Implementation Roadmap

### Phase 1: Registry Core (Week 6, Days 3-4)

**Tasks:**

- [ ] Create `pytoon/types/__init__.py`
- [ ] Implement TypeRegistry class
- [ ] TypeHandler Protocol definition
- [ ] register_type_handler() API
- [ ] Unit tests for registry operations

### Phase 2: Built-in Handlers (Week 6, Day 5 - Week 7, Day 1)

**Tasks:**

- [ ] UUIDHandler
- [ ] DatetimeHandler, DateHandler, TimeHandler
- [ ] TimedeltaHandler
- [ ] BytesHandler (base64 encoding)
- [ ] ComplexHandler
- [ ] EnumHandler
- [ ] Integration with Encoder

### Phase 3: Integration (Week 7, Days 2-3)

**Tasks:**

- [ ] Integrate with encode() function
- [ ] Integrate with decode() (type hint awareness)
- [ ] Documentation with custom handler examples
- [ ] Publish as v1.1 feature

---

## Quality Assurance

```python
class TestTypeRegistry:
    def test_uuid_roundtrip(self) -> None:
        """Test UUID encoding and decoding."""
        registry = TypeRegistry()
        uid = UUID("12345678-1234-5678-1234-567812345678")
        encoded = registry.encode_value(uid)
        assert encoded == f"uuid:{uid}"

    def test_datetime_roundtrip(self) -> None:
        """Test datetime handling."""
        dt = datetime(2025, 11, 15, 12, 30, 45)
        encoded = DatetimeHandler.encode(dt)
        decoded = DatetimeHandler.decode(encoded)
        assert decoded == dt

    def test_custom_handler(self) -> None:
        """Test registering custom handler."""
        registry = TypeRegistry()
        registry.register(CustomHandler)
        # Custom type should now be handleable
```

---

## References & Traceability

**Specification:** docs/specs/types/spec.md
**Research:** docs/research/intel.md - Extensibility for enterprise adoption
**Dependencies:** ENCODER-001, DECODER-001

---

**Document Version**: 1.0
**Implementation Status**: Ready for v1.1 Ticket Generation
