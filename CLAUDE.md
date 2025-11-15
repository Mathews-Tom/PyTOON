# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyToon is a production-ready Python library implementing Token-Oriented Object Notation (TOON) v1.5+ specification, providing 30-60% token savings over JSON for LLM applications through bidirectional JSON↔TOON conversion.

## Version Roadmap

- **v1.0** (Weeks 1-5): Core TOON v1.5+ encoder/decoder, CLI, PyPI package
- **v1.1** (Weeks 6-8): DecisionEngine (smart format selection), TypeRegistry (enhanced types), Reference support (relational data)
- **v1.2** (Weeks 9-11): Sparse/polymorphic arrays, Graph encoding (circular refs)
- **v1.3** (Weeks 12-13): Enhanced error reporting, debug mode, visual diff tools
- **v2.0+** (Future): Streaming API, hybrid format, Cython acceleration

See `docs/pytoon-system-design.md` Section 8 for detailed roadmap and `docs/pytoon-enhancements.md` for enhancement specifications.

## Architecture

### Modular Component Structure

The system follows strict separation of concerns with four layers:

1. **Core Encoder/Decoder** (`pytoon/core/`, `pytoon/encoder/`, `pytoon/decoder/`)

   **Encoder Components**:
   - TabularAnalyzer: Detects uniform arrays qualifying for TOON's tabular format
   - ValueEncoder: Normalizes primitives (null, bool, numbers, strings) to TOON types
   - ArrayEncoder: Dispatches to tabular/inline/list formats based on data uniformity
   - ObjectEncoder: Handles nested dictionaries with proper indentation
   - QuotingEngine: Context-aware string quoting to minimize tokens while preserving parseability
   - KeyFoldingEngine: Collapses single-key wrapper chains into dotted paths (e.g., `data.metadata.items` vs nested structure)

   **Decoder Components**:
   - Lexer: Tokenizes TOON input into structural elements (identifiers, strings, numbers, array headers, etc.)
   - Parser: Builds hierarchical Python objects using state machine (INITIAL → EXPECT_KEY → EXPECT_VALUE → nested states)
   - Validator: Enforces TOON v1.5 spec rules in strict mode (array length matching, field consistency)
   - PathExpander: Reconstructs dotted keys into nested objects (reverses key folding)
   - StateMachine: Manages parser state transitions and indentation tracking

2. **Intelligence Layer** (`pytoon/decision/`) - **v1.1+**
   - DecisionEngine: Analyzes data and recommends optimal format (TOON, JSON, graph, hybrid)
   - DataMetrics: Computes nesting depth, uniformity score, reference density, tabular eligibility
   - StructuralAnalyzer: Data shape analysis with confidence scores and reasoning
   - `smart_encode()`: Automatic format selection based on data characteristics

3. **Enhanced Modules** (`pytoon/references/`, `pytoon/types/`, `pytoon/sparse/`) - **v1.1-1.2**

   **Reference Support** (v1.1-1.2):
   - ReferenceEncoder: Schema-based reference encoding (`_schema` section)
   - ReferenceDecoder: Reference resolution with `resolve_refs=True`
   - GraphEncoder: Circular reference normalization with object IDs (`$1`, `$2`)
   - `encode_refs()`, `decode_refs()`, `encode_graph()`, `decode_graph()` APIs

   **Type System** (v1.1):
   - TypeRegistry: Pluggable type handler system
   - Built-in handlers: UUID, date, time, timedelta, bytes, Enum, complex
   - `register_type_handler()`: API for custom type extensions
   - Type hint-aware decoding

   **Sparse/Polymorphic Arrays** (v1.2):
   - SparseArrayEncoder: Optional field markers (`field?`), empty-as-null convention
   - PolymorphicArrayEncoder: Discriminator-based sub-tables (`@type:` sections)
   - Automatic sparsity detection (30%+ missing values)

4. **Public API** (`pytoon/__init__.py`)
   - `encode(value, ...) -> str` - Core TOON encoding
   - `decode(toon_string, ...) -> Any` - Core TOON decoding
   - `smart_encode(value, auto=True, ...) -> tuple[str, FormatDecision]` - v1.1+ intelligent format selection
   - `encode_refs(value, mode='schema', ...) -> str` - v1.1+ relational data encoding
   - `decode_refs(toon_string, resolve=True, ...) -> Any` - v1.1+ reference resolution
   - `encode_graph(value, ...) -> str` - v1.2+ circular reference handling
   - `decode_graph(toon_string, ...) -> Any` - v1.2+ graph reconstruction
   - TokenCounter: GPT-5 o200k_base token estimation and JSON vs TOON comparison
   - CLI: `pytoon` command with `--auto-decide`, `--explain`, `--debug` flags (v1.1-1.3)

Encoder and Decoder are fully independent, sharing only type definitions and specification references from the Specification Module (`pytoon/spec/`).

## Project Structure

```
pytoon/
├── pytoon/                    # Main package
│   ├── __init__.py           # Public API: encode, decode, smart_encode
│   ├── core/                 # Core encoder/decoder (v1.0)
│   ├── encoder/              # Encoder components
│   ├── decoder/              # Decoder components
│   ├── decision/             # Intelligence layer (v1.1)
│   ├── references/           # Reference/graph support (v1.1-1.2)
│   ├── types/                # Type system (v1.1)
│   ├── sparse/               # Sparse/polymorphic arrays (v1.2)
│   ├── utils/                # Utilities, TokenCounter
│   └── cli/                  # CLI interface
├── tests/
│   ├── unit/                 # Unit tests per module
│   ├── integration/          # End-to-end tests
│   ├── property/             # Hypothesis property-based tests
│   └── benchmarks/           # Performance benchmarks
├── docs/
│   ├── pytoon-system-design.md     # System architecture (this is the source of truth)
│   └── pytoon-enhancements.md      # v1.1-2.0 enhancement proposals
├── examples/                 # Usage examples
├── pyproject.toml           # Package metadata, dependencies, tool configs
└── CLAUDE.md                # This file
```

## Development Commands

```bash
# Install package in editable mode with dev dependencies
uv pip install -e ".[dev]" --system

# Run tests
uv run pytest

# Run tests with coverage (85% minimum required)
uv run pytest --cov=pytoon --cov-report=term-missing --cov-report=html

# Type checking (mypy strict mode required)
uv run mypy --strict pytoon/

# Linting
uv run ruff check pytoon/
uv run black --check pytoon/

# Format code
uv run black pytoon/
uv run isort pytoon/

# Run single test file
uv run pytest tests/unit/test_encoder.py

# Run specific test
uv run pytest tests/unit/test_encoder.py::test_tabular_array_encoding

# Run property-based tests (Hypothesis)
uv run pytest tests/property/

# Run benchmarks
uv run pytest tests/benchmarks/ --benchmark-only

# Build package for PyPI
python -m build

# Check package before publishing
twine check dist/*

# Publish to PyPI (requires PYPI_API_TOKEN)
twine upload dist/*
```

## Critical Implementation Rules

### TOON Specification Compliance

- **100% TOON v1.5+ spec adherence required** - no partial implementations
- Tabular arrays require: uniform field sets, no nested objects/arrays in values, identical keys across all objects
- Array header format: `[N]` for length, `[N]{fields}` or `[N\t]{fields}` for tabular with field list
- String quoting required when: empty, contains delimiter/structural chars, looks like boolean/number/null, has leading/trailing whitespace, starts with `- `, matches structural tokens like `[5]` or `{key}`

### Type Conversions

- `None` → `null`
- Booleans → lowercase `true`/`false`
- Numbers → decimal notation (no scientific notation: 1e6 becomes 1000000)
- `float('nan')`, `float('inf')` → `null`
- `-0.0` → `0` (normalized to positive zero)

### Error Handling

- Encoder must detect: circular references, unsupported types, data size limits
- Decoder strict mode: raise TOONValidationError on array length mismatch, field inconsistency, delimiter errors
- Decoder lenient mode: best-effort parsing with warnings, auto-detect delimiters, skip malformed rows

### Testing Requirements

- Roundtrip fidelity: `decode(encode(data)) == data` must hold for all valid inputs
- Property-based testing with Hypothesis for random data generation
- Test coverage target: 85%+ code coverage enforced
- Test against official TOON specification test suite

## Key Technical Decisions

- **Time Complexity**: O(n) for both encoding and decoding
- **Space Complexity**: O(n) for output strings and reconstructed data
- **Performance Target**: <100ms for 1-10KB datasets
- **Validation Overhead**: <5% in strict mode
- **Python Version**: 3.8+ minimum (use modern type hints: `list[int]`, `dict[str, Any]`, `int | None`)
- **Core Dependencies**: Zero external dependencies for core functionality; tiktoken is optional for accurate token counting

## Important Patterns

### Encoder Dispatch Flow
```
Python Object → Determine Type → [Primitive: ValueEncoder | Dict: ObjectEncoder | List: ArrayEncoder]
ArrayEncoder → TabularAnalyzer → [Uniform: Tabular Format | All Primitives: Inline | Mixed: List Format]
```

### Decoder State Machine Flow
```
INITIAL → EXPECT_KEY (read key) → EXPECT_COLON → EXPECT_VALUE (read value or header) →
  [NESTED_OBJECT | ARRAY_TABULAR | ARRAY_INLINE] → back to EXPECT_KEY
```

### Indentation Rules
- Default: 2 spaces per level (configurable)
- Decoder must track indentation stack to detect dedentation closing nested structures
- Validate indentation consistency (multiples of indent size)

## Architecture Priorities

1. **Modularity**: Each component has single responsibility
2. **Type Safety**: Full type hints with mypy strict mode compliance
3. **Performance**: Minimize token usage while maintaining O(n) complexity
4. **Extensibility**: Plugin architecture for custom type handlers and validators
5. **Spec Compliance**: Automated conformance testing against TOON v1.5+

## PyPI Publishing

This project is designed for PyPI publication as the `pytoon` package.

**Package Name**: `pytoon`
**Installation**: `pip install pytoon` (after v1.0 release)
**Optional Dependencies**: `pip install pytoon[tokenizer]` (includes tiktoken for accurate token counting)

**Publishing Checklist**:
1. Update version in `pytoon/__version__.py` and `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Run full test suite: `uv run pytest --cov=pytoon --cov-fail-under=85`
4. Type check: `uv run mypy --strict pytoon/`
5. Build package: `python -m build`
6. Check package: `twine check dist/*`
7. Create GitHub release tag (triggers automated PyPI publication via `.github/workflows/publish.yml`)
8. Verify on PyPI: `pip install pytoon=={version}` in clean environment

**Semantic Versioning**:
- MAJOR (X.0.0): Breaking API changes
- MINOR (1.X.0): Backward-compatible features (v1.1, v1.2, v1.3)
- PATCH (1.0.X): Backward-compatible bug fixes

## Common Pitfalls

- Do not use eval-based parsing (security risk)
- Avoid scientific notation in number encoding
- Never fold keys containing dots or special characters (ambiguity)
- Handle empty arrays and objects correctly: `array[0]:` and empty output respectively
- Tabular arrays must validate field uniformity before encoding
- Always use `uv` package manager (not pip directly) for development
- Maintain 85%+ test coverage for all new code
- DecisionEngine thresholds: depth > 6 levels favors JSON over TOON
- Reference support requires opt-in (`encode_refs()`, not `encode()`) for backward compatibility
