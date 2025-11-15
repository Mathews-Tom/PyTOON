# Decoder Module Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/decoder/spec.md`
**Component ID:** DECODER-001
**Priority:** P0 (Core v1.0 Component)

---

## Context & Documentation

### Traceability Chain

1. **Formal Specification:** docs/specs/decoder/spec.md
   - FR-1: Lexer (tokenization)
   - FR-2: Parser (structure building)
   - FR-3: Validator (spec compliance)
   - FR-4: PathExpander (reverse key folding)
   - FR-5: StateMachine (state transitions)

2. **Research & Intelligence:** docs/research/intel.md
   - Security critical: No eval-based parsing
   - Performance target: <100ms for 1-10KB
   - Strict/lenient modes for production flexibility

3. **System Context:**
   - Architecture: `.sage/agent/system/architecture.md` - 5 decoder components
   - Patterns: `.sage/agent/examples/python/decoder/` - State machine pattern

### Related Documentation

**Dependencies:**

- **CORE-001:** Decoder class delegates to these components
- **UTILS-001:** Exception classes (TOONDecodeError, TOONValidationError)

**Dependents:**

- **CORE-001:** Core.Decoder orchestrates these components

---

## Executive Summary

### Business Alignment

- **Purpose:** Parse TOON strings back into Python objects with validation
- **Value Proposition:** Reliable, secure deserialization with strict/lenient modes
- **Target Users:** Developers consuming TOON-encoded LLM responses

### Technical Approach

- **Architecture Pattern:** Pipeline Pattern (Lexer → Parser → Validator → PathExpander)
- **Technology Stack:** Python 3.8+, state machine parser, regex tokenizer
- **Implementation Strategy:** Sequential pipeline (tokenize → parse → validate → expand)

### Key Success Metrics

**SLOs:**

- Performance: <100ms decoding for 1-10KB datasets
- Accuracy: 100% roundtrip fidelity
- Security: No eval() or exec() usage

**KPIs:**

- Test Coverage: 85%+ per component
- Error Quality: Descriptive errors with line/column info
- Validation: Strict mode catches spec violations

---

## Code Examples & Patterns

### Repository Patterns

**1. Lexer Pattern:** `.sage/agent/examples/python/decoder/`

```python
from dataclasses import dataclass
from enum import Enum, auto

class TokenType(Enum):
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    NULL = auto()
    ARRAY_HEADER = auto()
    COLON = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class Lexer:
    """Tokenize TOON input into structural elements."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """Generate token stream from TOON source."""
        while self.pos < len(self.source):
            token = self._next_token()
            if token:
                self.tokens.append(token)
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def _next_token(self) -> Token | None:
        # Tokenization logic
        ...
```

**2. Parser State Machine Pattern:**

```python
from enum import Enum, auto

class ParserState(Enum):
    INITIAL = auto()
    EXPECT_KEY = auto()
    EXPECT_COLON = auto()
    EXPECT_VALUE = auto()
    IN_ARRAY_TABULAR = auto()
    IN_ARRAY_INLINE = auto()
    IN_NESTED_OBJECT = auto()

class Parser:
    """Build hierarchical Python objects from token stream."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.state = ParserState.INITIAL
        self.indent_stack: list[int] = [0]
        self.result: dict[str, Any] = {}

    def parse(self) -> Any:
        """Parse tokens into Python object."""
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self._handle_token(token)
        return self.result

    def _handle_token(self, token: Token) -> None:
        if self.state == ParserState.EXPECT_KEY:
            self._handle_expect_key(token)
        elif self.state == ParserState.EXPECT_VALUE:
            self._handle_expect_value(token)
        # ... more state handlers
```

**3. Validator Pattern:**

```python
class Validator:
    """Enforce TOON v1.5 spec rules."""

    def __init__(self, strict: bool = True) -> None:
        self.strict = strict
        self.warnings: list[str] = []

    def validate_array_length(
        self, declared: int, actual: int, line: int
    ) -> None:
        """Validate array length matches declaration."""
        if declared != actual:
            msg = f"Array length mismatch at line {line}: declared {declared}, actual {actual}"
            if self.strict:
                raise TOONValidationError(msg)
            else:
                self.warnings.append(msg)

    def validate_field_consistency(
        self, fields: list[str], row_values: list[Any], line: int
    ) -> None:
        """Validate row has correct number of fields."""
        if len(fields) != len(row_values):
            msg = f"Field count mismatch at line {line}: expected {len(fields)}, got {len(row_values)}"
            if self.strict:
                raise TOONValidationError(msg)
            else:
                self.warnings.append(msg)
```

### Key Takeaways

- State machine pattern for parser (clear state transitions)
- Token with position info for error reporting
- Strict/lenient modes for production flexibility
- No eval() or exec() (security critical)

---

## Technology Stack

### Recommended Stack

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| Runtime | Python | 3.8+ | Modern type hints, dataclasses |
| Parsing | Custom state machine | N/A | Security (no eval), control |
| Regex | stdlib re | 3.8+ | Token pattern matching |
| Data Classes | dataclasses | 3.8+ | Token representation |
| Enums | enum | 3.8+ | State and token types |

**Key Technology Decisions:**

1. **Custom Parser:** No eval() or exec() for security
2. **State Machine:** Clear state transitions, easy debugging
3. **Position Tracking:** Line/column for descriptive errors

---

## Architecture Design

### Component Breakdown

**5 Decoder Components:**

1. **Lexer**
   - **Purpose:** Tokenize TOON string into token stream
   - **Input:** TOON string
   - **Output:** `list[Token]`
   - **Token Types:** IDENTIFIER, STRING, NUMBER, BOOLEAN, NULL, ARRAY_HEADER, etc.

2. **Parser**
   - **Purpose:** Build hierarchical structure from tokens
   - **Input:** `list[Token]`
   - **Output:** Python object (dict, list, primitive)
   - **Pattern:** State machine with indent tracking

3. **Validator**
   - **Purpose:** Enforce TOON v1.5 spec rules
   - **Modes:** Strict (raise errors) / Lenient (warnings)
   - **Checks:** Array length, field consistency, delimiter consistency

4. **PathExpander**
   - **Purpose:** Reverse key folding (dotted paths to nested dicts)
   - **Input:** `dict[str, Any]` with dotted keys
   - **Output:** `dict[str, Any]` with nested structure
   - **Example:** `{"a.b.c": 1}` → `{"a": {"b": {"c": 1}}}`

5. **StateMachine**
   - **Purpose:** Manage parser state transitions
   - **States:** INITIAL, EXPECT_KEY, EXPECT_VALUE, IN_ARRAY, etc.
   - **Indentation:** Track indent stack for nesting depth

### Data Flow

```plaintext
TOON String
    │
    ▼
Lexer.tokenize()
    │
    ▼
Token Stream: [IDENTIFIER, COLON, STRING, NEWLINE, ...]
    │
    ▼
Parser.parse()
    │
    ├─→ StateMachine (state transitions)
    │
    ├─→ Validator (strict mode checks)
    │
    ▼
Raw Python Object (with dotted keys)
    │
    ▼
PathExpander.expand() (if expand_paths='safe')
    │
    ▼
Final Python Object
```

---

## Implementation Roadmap

### Phase 1: Lexer (Week 2, Days 1-2)

**Tasks:**

- [ ] Create `pytoon/decoder/__init__.py`
- [ ] Implement `pytoon/decoder/lexer.py`
  - Token dataclass with line/column
  - TokenType enum
  - tokenize() method
  - Handle: identifiers, strings, numbers, booleans, null, array headers
- [ ] Write unit tests (85%+ coverage)
- [ ] Test escape sequence handling

**Deliverables:**

- Lexer tokenizes all TOON constructs
- Position tracking for errors
- Escape sequences handled correctly

### Phase 2: Parser Core (Week 2, Days 3-4)

**Tasks:**

- [ ] Implement `pytoon/decoder/statemachine.py`
  - ParserState enum
  - State transition logic
  - Indent stack management
- [ ] Implement `pytoon/decoder/parser.py`
  - parse() method
  - Handle array formats (tabular, inline, list)
  - Handle nested objects
- [ ] Write integration tests
- [ ] Test indentation-based nesting

**Deliverables:**

- Parser builds correct Python objects
- All array formats supported
- Nested structures handled

### Phase 3: Validation (Week 2, Day 5)

**Tasks:**

- [ ] Implement `pytoon/decoder/validator.py`
  - Strict/lenient modes
  - Array length validation
  - Field consistency validation
  - Delimiter consistency
- [ ] Write validation test suite
- [ ] Test error messages (line/column info)

**Deliverables:**

- Validator catches spec violations
- Descriptive error messages
- Lenient mode collects warnings

### Phase 4: Path Expansion & Integration (Week 3, Days 1-2)

**Tasks:**

- [ ] Implement `pytoon/decoder/pathexpander.py`
  - expand() method
  - Reverse key folding
  - Handle edge cases (special chars in keys)
- [ ] End-to-end integration tests
- [ ] Performance benchmarking (<100ms for 1-10KB)
- [ ] Roundtrip fidelity tests with Encoder

**Deliverables:**

- PathExpander reverses key folding
- Performance targets met
- Roundtrip fidelity validated

---

## Quality Assurance

### Testing Strategy

**Unit Tests (85%+ coverage per component):**

```python
class TestLexer:
    def test_tokenize_identifier(self) -> None:
        lexer = Lexer("key: value")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "key"

    def test_tokenize_array_header(self) -> None:
        lexer = Lexer("[3]{id,name}:")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.ARRAY_HEADER
        assert tokens[0].value == "[3]{id,name}"

    def test_track_position(self) -> None:
        lexer = Lexer("key: value\nother: data")
        tokens = lexer.tokenize()
        # "other" is on line 2
        other_token = [t for t in tokens if t.value == "other"][0]
        assert other_token.line == 2


class TestValidator:
    def test_strict_array_length_mismatch(self) -> None:
        validator = Validator(strict=True)
        with pytest.raises(TOONValidationError):
            validator.validate_array_length(3, 2, line=5)

    def test_lenient_array_length_mismatch(self) -> None:
        validator = Validator(strict=False)
        validator.validate_array_length(3, 2, line=5)
        assert len(validator.warnings) == 1
```

**Property-Based Tests:**

```python
@given(st.dictionaries(st.text(), st.integers()))
def test_roundtrip_fidelity(data: dict[str, int]) -> None:
    toon = encode(data)
    recovered = decode(toon)
    assert recovered == data
```

### Code Quality Gates

- [ ] mypy --strict passes
- [ ] No eval() or exec() usage
- [ ] All errors include line/column info
- [ ] 85%+ test coverage
- [ ] Security scan passes (Bandit)

---

## Risk Management

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Parser state machine complexity | HIGH | MEDIUM | Clear state diagrams, extensive testing |
| Escape sequence edge cases | MEDIUM | MEDIUM | Comprehensive escape tests, follow JSON patterns |
| Performance with large inputs | MEDIUM | LOW | O(n) algorithm, early benchmarking |
| Security vulnerabilities | HIGH | LOW | No eval(), input validation, Bandit scans |

---

## Error Handling & Edge Cases

### Error Scenarios

1. **Invalid Syntax**
   - **Cause:** Malformed TOON (missing colon, unbalanced brackets)
   - **Handling:** Raise TOONDecodeError with position
   - **UX:** "Syntax error at line 3, column 5: expected ':' after 'key'"

2. **Array Length Mismatch**
   - **Cause:** Declared length doesn't match actual rows
   - **Handling:** Raise TOONValidationError (strict) or warn (lenient)
   - **UX:** "Array length mismatch at line 10: declared 5, actual 4"

3. **Unterminated String**
   - **Cause:** Missing closing quote
   - **Handling:** Raise TOONDecodeError
   - **UX:** "Unterminated string starting at line 7, column 12"

### Edge Cases

| Edge Case | Detection | Handling | Testing |
|-----------|-----------|----------|---------|
| Empty input | `if not source` | Return empty dict | Unit test |
| Single value | No key | Return primitive | Unit test |
| Deeply nested | Indent stack depth | Support Python recursion limit | Stress test |
| Mixed delimiters | Lexer detection | Lenient: auto-detect, Strict: error | Validation test |
| Unicode identifiers | Regex pattern | Support Unicode | Unicode test suite |

---

## References & Traceability

### Source Documentation

**Specification:** docs/specs/decoder/spec.md

- Functional requirements FR-1 through FR-5
- State machine transitions
- Validation rules

**Research:** docs/research/intel.md

- Security: No eval-based parsing
- Performance: <100ms for 1-10KB
- Production readiness: Strict/lenient modes

**Code Patterns:**

- `.sage/agent/examples/python/decoder/` - Lexer and parser patterns
- `.sage/agent/examples/python/errors/` - Exception patterns

### Related Components

**Dependencies:**

- **UTILS-001:** TOONDecodeError, TOONValidationError

**Dependents:**

- **CORE-001:** Core.Decoder orchestrates these components

---

**Document Version**: 1.0
**Implementation Status**: Ready for Ticket Generation
**Next Step**: `/sage.tasks` to break down into SMART tickets
