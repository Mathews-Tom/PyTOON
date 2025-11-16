# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-11-17

### Changed
- Renamed PyPI package from `pytoon` to `toon-codec` (module import remains `pytoon`)
- Updated license format in pyproject.toml to comply with PEP 639 (SPDX expression)
- Removed deprecated license classifier

### Documentation
- Comprehensive README rewrite with:
  - Installation instructions and badges
  - Quick start guide with code examples
  - JSON vs TOON comparison showing 59% token savings
  - Performance metrics table
  - 8 detailed usage examples (tabular data, nested objects, smart encoding, custom types, references, graphs, validation)
  - Complete API reference
  - Configuration options table
  - Architecture overview
  - Roadmap for v1.1-v2.0+
  - Use cases and contributing guidelines

## [1.0.0] - 2025-11-17

### Added

#### Core TOON v1.5+ Implementation
- **Bidirectional JSON-TOON conversion** with full specification compliance
- **30-60% token savings** over JSON for structured LLM input/output
- **`encode()` function** - Convert Python objects to TOON format
  - Configurable indentation (default: 2 spaces)
  - Multiple delimiter support: comma, tab, or pipe
  - Key folding modes: off or safe
  - ASCII enforcement option
  - Sorted keys support
- **`decode()` function** - Parse TOON strings back to Python objects
  - Strict and lenient validation modes
  - Path expansion support
  - Roundtrip fidelity guarantee: `decode(encode(data)) == data`

#### Encoder Components
- **TabularAnalyzer** - Detects uniform arrays qualifying for TOON's tabular format
- **ValueEncoder** - Normalizes primitives (null, bool, numbers, strings) to TOON types
- **ArrayEncoder** - Dispatches to tabular/inline/list formats based on data uniformity
- **ObjectEncoder** - Handles nested dictionaries with proper indentation
- **QuotingEngine** - Context-aware string quoting to minimize tokens
- **KeyFoldingEngine** - Collapses single-key wrapper chains into dotted paths

#### Decoder Components
- **Lexer** - Tokenizes TOON input into structural elements
- **Parser** - Builds hierarchical Python objects using state machine
- **Validator** - Enforces TOON v1.5 spec rules in strict mode
- **PathExpander** - Reconstructs dotted keys into nested objects
- **StateMachine** - Manages parser state transitions and indentation tracking
- **Depth-based decoder** - Advanced parsing with line scanning and depth computation

#### Decision Engine (v1.1 Feature)
- **`smart_encode()` function** - Automatic format selection based on data characteristics
- **DecisionEngine** - Analyzes data and recommends optimal format (TOON, JSON, graph, hybrid)
- **DataMetrics** - Computes nesting depth, uniformity score, reference density
- **StructuralAnalyzer** - Data shape analysis with confidence scores and reasoning
- **FormatDecision** - Contains recommended format, confidence level, and reasoning

#### Type System (v1.1 Feature)
- **TypeRegistry** - Pluggable type handler system with protocol-based design
- **12 built-in type handlers** with roundtrip fidelity:
  - UUID - Universally unique identifiers
  - date - Calendar dates
  - time - Time of day
  - datetime - Combined date and time
  - timedelta - Time duration
  - bytes - Binary data (base64 encoded)
  - Enum - Enumeration values
  - complex - Complex numbers
  - Decimal - Arbitrary precision decimals
  - Path - File system paths
  - IPv4Address/IPv6Address - Network addresses
  - URL - Uniform resource locators
- **`register_type_handler()` API** - Custom type extensions
- **`get_type_registry()` API** - Access to global type registry
- Automatic custom type support integrated with encoder

#### Reference Support (v1.1-1.2 Feature)
- **`encode_refs()` function** - Schema-based reference encoding
  - Detects shared object references
  - Uses placeholders ($1, $2, etc.) with _schema section
  - Efficient encoding of relational data
- **`decode_refs()` function** - Reference resolution with resolve option
  - Reconstructs shared objects with Python object identity
  - Supports both resolved and placeholder modes

#### Graph Support (v1.2 Feature)
- **`encode_graph()` function** - Circular reference handling
  - Detects circular references in data
  - Uses $ref:N placeholders with _graph flag
  - Normalizes object IDs for graph structures
- **`decode_graph()` function** - Graph reconstruction
  - Parses _graph: true flag and $ref:N placeholders
  - Reconstructs circular references properly

#### Sparse/Polymorphic Arrays (v1.2 Feature)
- **SparseArrayEncoder** - Optional field markers (`field?`)
- **PolymorphicArrayEncoder** - Discriminator-based sub-tables (`@type:` sections)
- Automatic sparsity detection (30%+ missing values)
- Empty-as-null convention support

#### CLI Interface
- **`pytoon` command** - Command-line tool for TOON operations
- Conversion between JSON and TOON formats
- Batch processing support
- Planned: `--auto-decide`, `--explain`, `--debug` flags (v1.1-1.3)

#### Error Handling
- **TOONError** - Base exception for all TOON-related errors
- **TOONEncodeError** - Encoding failures (unsupported types, circular references)
- **TOONDecodeError** - Decoding failures (invalid syntax, parse errors)
- **TOONValidationError** - Validation failures (array length mismatch, field inconsistency)

#### Package Infrastructure
- **Zero external dependencies** for core functionality
- **Optional tiktoken dependency** for accurate GPT token counting
- **py.typed marker** - Full PEP 561 type hint support
- **Python 3.8+ compatibility** with modern type hints
- **MIT License** - Permissive open source licensing

### Technical Details

#### Performance Characteristics
- **Time Complexity**: O(n) for both encoding and decoding
- **Space Complexity**: O(n) for output strings and reconstructed data
- **Performance Target**: <100ms for 1-10KB datasets
- **Validation Overhead**: <5% in strict mode

#### Type Conversion Rules
- `None` → `null`
- Booleans → lowercase `true`/`false`
- Numbers → decimal notation (no scientific notation)
- `float('nan')`, `float('inf')` → `null`
- `-0.0` → `0` (normalized to positive zero)

#### Quality Assurance
- **Property-based testing** with Hypothesis for random data generation
- **85%+ test coverage** enforced
- **mypy strict mode** compliance
- **Ruff linting** with comprehensive rule set
- **Black formatting** for consistent code style

### Notes

This is the initial production release of PyToon, implementing the complete TOON v1.5+ specification with advanced features including intelligent format selection, pluggable type system, reference tracking, graph encoding, and sparse array support.

[1.0.0]: https://github.com/AetherForge/PyToon/releases/tag/v1.0.0
