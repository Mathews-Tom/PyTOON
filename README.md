# toon-codec

> Token-Oriented Object Notation (TOON) codec for Python — 30-60% token savings over JSON for LLM applications

[![PyPI version](https://badge.fury.io/py/toon-codec.svg)](https://badge.fury.io/py/toon-codec)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](https://github.com/AetherForge/PyToon)

**toon-codec** is a production-ready Python library implementing the TOON v1.5+ specification, providing significant token savings for structured LLM input/output through bidirectional JSON-TOON conversion.

## Key Features

- **30-60% Token Savings** - Reduce LLM API costs with compact data representation
- **Full TOON v1.5+ Compliance** - Complete specification implementation with strict validation
- **Roundtrip Fidelity** - Guaranteed `decode(encode(data)) == data` for all valid inputs
- **Zero Dependencies** - Core functionality requires no external packages
- **Type Safe** - Full type hints with mypy strict mode compliance
- **Intelligent Format Selection** - Auto-detect optimal serialization format
- **Advanced Features** - Reference tracking, graph encoding, sparse arrays

## Installation

```bash
pip install toon-codec
```

With optional token counting support (requires tiktoken):

```bash
pip install toon-codec[tokenizer]
```

## Quick Start

```python
from pytoon import encode, decode

# Basic encoding
data = {"name": "Alice", "age": 30, "active": True}
toon = encode(data)
print(toon)
# name: Alice
# age: 30
# active: true

# Decoding back to Python
recovered = decode(toon)
assert recovered == data  # Roundtrip guaranteed
```

## Why TOON?

TOON (Token-Oriented Object Notation) is designed specifically for LLM applications where every token counts. Compare JSON vs TOON:

### JSON (56 tokens)

```json
[
  {"id": 1, "name": "Alice", "email": "alice@example.com"},
  {"id": 2, "name": "Bob", "email": "bob@example.com"},
  {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
]
```

### TOON (23 tokens) - 59% savings

```
[3]{id,name,email}
1,Alice,alice@example.com
2,Bob,bob@example.com
3,Charlie,charlie@example.com
```

## Performance Metrics

| Data Type | JSON Tokens | TOON Tokens | Savings |
|-----------|-------------|-------------|---------|
| Tabular data (uniform arrays) | 100 | 35-45 | 55-65% |
| Nested objects | 100 | 60-70 | 30-40% |
| Simple key-value | 100 | 70-80 | 20-30% |
| Mixed structures | 100 | 50-65 | 35-50% |

**Performance Characteristics:**

- **Time Complexity**: O(n) for encoding and decoding
- **Space Complexity**: O(n) for output
- **Speed**: <100ms for 1-10KB datasets
- **Validation Overhead**: <5% in strict mode

## Usage Examples

### Tabular Data (Maximum Savings)

```python
from pytoon import encode, decode

# List of uniform objects - ideal for TOON
users = [
    {"id": 1, "name": "Alice", "role": "admin"},
    {"id": 2, "name": "Bob", "role": "user"},
    {"id": 3, "name": "Charlie", "role": "user"},
]

toon = encode(users)
print(toon)
# [3]{id,name,role}
# 1,Alice,admin
# 2,Bob,user
# 3,Charlie,user

# Decode back
assert decode(toon) == users
```

### Nested Objects

```python
config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "credentials": {
            "user": "admin",
            "password": "secret"
        }
    },
    "cache": {
        "enabled": True,
        "ttl": 3600
    }
}

toon = encode(config)
print(toon)
# database:
#   host: localhost
#   port: 5432
#   credentials:
#     user: admin
#     password: secret
# cache:
#   enabled: true
#   ttl: 3600
```

### Intelligent Format Selection

```python
from pytoon import smart_encode

data = [{"id": 1}, {"id": 2}, {"id": 3}]
encoded, decision = smart_encode(data)

print(f"Recommended: {decision.recommended_format}")
print(f"Confidence: {decision.confidence:.2f}")
print(f"Reasoning: {decision.reasoning}")
# Recommended: toon
# Confidence: 0.95
# Reasoning: ['High uniformity (100.0%) strongly favors TOON', ...]
```

### Custom Type Support

```python
from pytoon import encode, decode, register_type_handler
from datetime import datetime
import uuid

# Built-in support for common types
data = {
    "id": uuid.uuid4(),
    "created": datetime.now(),
    "tags": ["python", "llm", "efficiency"]
}

toon = encode(data)
recovered = decode(toon)
# Types are preserved through encoding/decoding
```

### Reference Tracking (Relational Data)

```python
from pytoon import encode_refs, decode_refs

# Shared object references
user = {"id": 1, "name": "Alice"}
data = {
    "author": user,
    "reviewer": user,  # Same object referenced twice
}

toon = encode_refs(data)
# Efficiently encodes shared references with $1, $2 placeholders

recovered = decode_refs(toon, resolve=True)
assert recovered["author"] is recovered["reviewer"]  # Same Python object
```

### Graph Encoding (Circular References)

```python
from pytoon import encode_graph, decode_graph

# Handle circular references
node1 = {"id": 1, "value": "A"}
node2 = {"id": 2, "value": "B"}
node1["next"] = node2
node2["next"] = node1  # Circular!

toon = encode_graph({"nodes": [node1, node2]})
recovered = decode_graph(toon)
# Circular structure preserved
```

### Validation Modes

```python
from pytoon import decode

# Strict mode (default) - raises on validation errors
try:
    decode("[5]: 1,2,3", strict=True)  # Declared 5, got 3
except Exception as e:
    print(f"Validation error: {e}")

# Lenient mode - best-effort parsing
result = decode("[5]: 1,2,3", strict=False)
# Returns [1, 2, 3] with warning
```

## API Reference

### Core Functions

```python
# Encoding
encode(value, *, indent=2, delimiter=",", key_folding="off",
       ensure_ascii=False, sort_keys=False) -> str

# Decoding
decode(toon_string, *, strict=True, expand_paths="off") -> Any

# Intelligent encoding
smart_encode(value, *, auto=True, ...) -> tuple[str, FormatDecision]
```

### Advanced Functions

```python
# Reference support (v1.1)
encode_refs(data, mode="schema", ...) -> str
decode_refs(toon_string, resolve=True) -> Any

# Graph support (v1.2)
encode_graph(data, ...) -> str
decode_graph(toon_string) -> Any

# Type system
register_type_handler(type_class, handler)
get_type_registry() -> TypeRegistry
```

### Exceptions

```python
from pytoon import TOONError, TOONEncodeError, TOONDecodeError, TOONValidationError

# TOONError - Base exception
# TOONEncodeError - Encoding failures
# TOONDecodeError - Parsing failures
# TOONValidationError - Validation failures
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `indent` | int | 2 | Spaces per indentation level |
| `delimiter` | str | "," | Field delimiter: ",", "\t", or "\|" |
| `key_folding` | str | "off" | Key folding: "off" or "safe" |
| `ensure_ascii` | bool | False | Escape non-ASCII characters |
| `sort_keys` | bool | False | Sort dictionary keys |
| `strict` | bool | True | Enable strict validation |

## Architecture

```plaintext
toon-codec/
├── pytoon/                    # Main package (import as pytoon)
│   ├── core/                 # Core encoder/decoder
│   ├── encoder/              # Encoding components
│   ├── decoder/              # Decoding components
│   ├── decision/             # Intelligent format selection
│   ├── references/           # Reference & graph support
│   ├── types/                # Type system & handlers
│   ├── sparse/               # Sparse/polymorphic arrays
│   └── utils/                # Utilities & error handling
└── tests/                    # Comprehensive test suite
```

## Roadmap

### Current (v1.0.0)

- Full TOON v1.5+ specification compliance
- Bidirectional JSON-TOON conversion
- Intelligent format selection (DecisionEngine)
- Pluggable type system with 12 built-in handlers
- Reference tracking and graph encoding
- Sparse and polymorphic array support
- CLI interface

### Planned (v1.1 - v1.3)

- **v1.1**: Enhanced CLI with `--auto-decide`, `--explain`, `--debug` flags
- **v1.2**: Performance optimizations and streaming support
- **v1.3**: Visual diff tools and enhanced error reporting

### Future (v2.0+)

- **Streaming API** - Process large datasets without full memory load
- **Hybrid Format** - Automatically mix TOON and JSON for optimal results
- **Cython Acceleration** - Optional C extensions for 10x speedup
- **Schema Validation** - JSON Schema-like validation for TOON
- **Language Bindings** - JavaScript, Rust, Go implementations

## Use Cases

- **LLM API Cost Reduction** - Save 30-60% on token costs
- **Structured Output Parsing** - Efficiently parse LLM responses
- **Data Pipeline Optimization** - Compact intermediate representations
- **Configuration Files** - Human-readable, token-efficient configs
- **API Response Compression** - Reduce bandwidth for structured data
- **Prompt Engineering** - Fit more context in limited token windows

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md).

```bash
# Development setup
git clone https://github.com/AetherForge/PyToon.git
cd PyToon
pip install -e ".[dev]"

# Run tests
pytest --cov=pytoon --cov-fail-under=85

# Type checking
mypy --strict pytoon/

# Linting
ruff check pytoon/
black pytoon/
```

## Testing

The project includes comprehensive testing:

- **1887+ tests** with property-based testing (Hypothesis)
- **85%+ code coverage** enforced
- **Roundtrip fidelity** verification
- **Specification compliance** testing
- **Performance benchmarking**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pytoon --cov-report=html

# Run specific test file
pytest tests/unit/test_encoder.py
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **PyPI**: <https://pypi.org/project/toon-codec/>
- **Repository**: <https://github.com/AetherForge/PyToon>
- **Documentation**: <https://github.com/AetherForge/PyToon#readme>
- **Issues**: <https://github.com/AetherForge/PyToon/issues>
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

**Note**: Install as `pip install toon-codec`, import as `from pytoon import encode, decode`
