# Utils Module Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/utils/spec.md`
**Component ID:** UTILS-001
**Priority:** P0 (Foundation Component)

---

## Context & Documentation

### Traceability Chain

1. **Formal Specification:** docs/specs/utils/spec.md
   - Exception hierarchy (TOONError, TOONEncodeError, TOONDecodeError, TOONValidationError)
   - TokenCounter (GPT-5 o200k_base token estimation)
   - Common utilities (helpers, validators)

2. **Research & Intelligence:** docs/research/intel.md
   - Exception patterns: Fail-fast, descriptive errors
   - Token counting: Core value demonstration (30-60% savings)
   - Optional dependencies: tiktoken for accurate counting

3. **Code Patterns:**
   - `.sage/agent/examples/python/errors/` - Exception hierarchy pattern

---

## Executive Summary

### Business Alignment

- **Purpose:** Shared utilities for error handling and token analysis
- **Value Proposition:** Consistent error experience, provable token savings
- **Target Users:** All PyToon modules (internal dependency)

### Technical Approach

- **Architecture Pattern:** Utility module (shared code)
- **Technology Stack:** Python 3.8+, optional tiktoken for token counting
- **Implementation Strategy:** Foundation-first (exceptions → token counter → helpers)

### Key Success Metrics

**SLOs:**

- Error Messages: Include context (type, position, expected vs actual)
- Token Counting: <5% variance from actual tokenizer (with tiktoken)
- Zero Core Dependencies: Optional dependencies only

---

## Code Examples & Patterns

### Exception Hierarchy Pattern

```python
class TOONError(Exception):
    """Base exception for all TOON errors.

    All TOON-specific exceptions inherit from this class,
    enabling broad exception catching when needed.
    """

class TOONEncodeError(TOONError):
    """Raised when encoding fails.

    Examples:
        - Unsupported type encountered
        - Circular reference detected
        - Data size limit exceeded
    """

class TOONDecodeError(TOONError):
    """Raised when decoding fails.

    Examples:
        - Invalid TOON syntax
        - Unterminated string
        - Unrecognized token
    """

class TOONValidationError(TOONDecodeError):
    """Raised when validation fails in strict mode.

    Examples:
        - Array length mismatch
        - Field count mismatch
        - Delimiter inconsistency
    """
```

### TokenCounter Pattern

```python
class TokenCounter:
    """Estimate token usage for TOON vs JSON comparison.

    Uses tiktoken (optional) for accurate GPT-5 o200k_base counting,
    falls back to character-based estimation if unavailable.
    """

    def __init__(self) -> None:
        try:
            import tiktoken
            self.encoder = tiktoken.get_encoding("o200k_base")
            self.use_tiktoken = True
        except ImportError:
            self.encoder = None
            self.use_tiktoken = False

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.use_tiktoken and self.encoder:
            return len(self.encoder.encode(text))
        # Fallback: estimate 1 token per 4 characters
        return len(text) // 4

    def compare(self, data: Any) -> dict[str, int]:
        """Compare token usage: TOON vs JSON.

        Returns:
            {
                "json_tokens": 150,
                "toon_tokens": 90,
                "savings_percent": 40.0,
                "savings_absolute": 60
            }
        """
        import json
        from pytoon import encode

        json_str = json.dumps(data)
        toon_str = encode(data)

        json_tokens = self.count_tokens(json_str)
        toon_tokens = self.count_tokens(toon_str)

        savings_absolute = json_tokens - toon_tokens
        savings_percent = (savings_absolute / json_tokens * 100) if json_tokens > 0 else 0

        return {
            "json_tokens": json_tokens,
            "toon_tokens": toon_tokens,
            "savings_percent": round(savings_percent, 1),
            "savings_absolute": savings_absolute,
        }
```

---

## Technology Stack

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| Runtime | Python | 3.8+ | Modern exception chaining |
| Token Counting | tiktoken (optional) | Latest | Accurate GPT-5 tokenization |
| Fallback | Character-based | N/A | Zero-dependency fallback |

**Key Decision:** tiktoken is optional dependency (`pip install pytoon[tokenizer]`)

---

## Implementation Roadmap

### Phase 1: Exception Hierarchy (Week 1, Day 1)

**Tasks:**

- [ ] Create `pytoon/utils/__init__.py`
- [ ] Implement `pytoon/utils/errors.py`
  - TOONError (base)
  - TOONEncodeError
  - TOONDecodeError
  - TOONValidationError
- [ ] Write unit tests
- [ ] Documentation with examples

**Deliverables:**

- Complete exception hierarchy
- All exceptions importable
- Tests for exception inheritance

### Phase 2: TokenCounter (Week 3, Day 1)

**Tasks:**

- [ ] Implement `pytoon/utils/token_counter.py`
  - Optional tiktoken import
  - Fallback estimation
  - compare() method for JSON vs TOON
- [ ] Write unit tests (with and without tiktoken)
- [ ] Benchmark token savings on sample data

**Deliverables:**

- TokenCounter working with/without tiktoken
- Token savings comparison functional
- Benchmark results documented

### Phase 3: Common Helpers (Week 3, Day 2)

**Tasks:**

- [ ] Implement `pytoon/utils/helpers.py`
  - validate_indent() - Check indent > 0
  - validate_delimiter() - Check in allowed set
  - is_safe_identifier() - Check for safe key folding
- [ ] Write unit tests
- [ ] Integration with Core configuration

**Deliverables:**

- Helper functions for validation
- Consistent error messages
- Reusable across modules

---

## Quality Assurance

### Testing Strategy

```python
class TestExceptions:
    def test_inheritance(self) -> None:
        assert issubclass(TOONEncodeError, TOONError)
        assert issubclass(TOONDecodeError, TOONError)
        assert issubclass(TOONValidationError, TOONDecodeError)

    def test_can_catch_base(self) -> None:
        try:
            raise TOONEncodeError("test")
        except TOONError:
            pass  # Should catch


class TestTokenCounter:
    def test_compare_shows_savings(self) -> None:
        counter = TokenCounter()
        data = [{"id": i, "name": f"User{i}"} for i in range(10)]
        result = counter.compare(data)
        assert result["savings_percent"] > 0
        assert result["toon_tokens"] < result["json_tokens"]
```

---

## Risk Management

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| tiktoken not installed | LOW | MEDIUM | Graceful fallback to estimation |
| Exception messages unclear | MEDIUM | LOW | Standard format, review all messages |
| Token estimation variance | LOW | LOW | Document accuracy limitations |

---

## References & Traceability

**Specification:** docs/specs/utils/spec.md
**Research:** docs/research/intel.md - Exception patterns, token demonstration
**Patterns:** `.sage/agent/examples/python/errors/`

**Dependents:** CORE-001, ENCODER-001, DECODER-001, CLI-001 all use exceptions

---

**Document Version**: 1.0
**Implementation Status**: Ready for Ticket Generation
