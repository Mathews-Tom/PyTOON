# CLI Module Implementation Blueprint (PRP)

**Format:** Product Requirements Prompt (Context Engineering)
**Generated:** 2025-11-15
**Specification:** `docs/specs/cli/spec.md`
**Component ID:** CLI-001
**Priority:** P0 (Core v1.0 Component)

---

## Context & Documentation

### Traceability Chain

1. **Formal Specification:** docs/specs/cli/spec.md
   - Command-line interface for TOON encoding/decoding
   - Input from stdin, file, or argument
   - Output to stdout or file
   - Configuration flags (--indent, --delimiter, --strict)

2. **Research & Intelligence:** docs/research/intel.md
   - Developer experience critical for adoption
   - Pipeline-friendly tool design
   - Future flags: --auto-decide (v1.1), --explain, --debug (v1.3)

3. **Code Patterns:**
   - Standard argparse CLI pattern
   - Unix philosophy: small tools that do one thing well

---

## Executive Summary

### Business Alignment

- **Purpose:** Command-line tool for TOON operations
- **Value Proposition:** Quick adoption, pipeline integration, demo capability
- **Target Users:** Developers, data engineers, CLI power users

### Technical Approach

- **Architecture Pattern:** CLI wrapper over Core API
- **Technology Stack:** Python 3.8+, argparse (stdlib)
- **Implementation Strategy:** Wrapper over encode()/decode() with argument parsing

---

## Code Examples & Patterns

### CLI Entry Point Pattern

```python
#!/usr/bin/env python3
"""PyToon CLI - Token-Oriented Object Notation tool."""

import argparse
import json
import sys
from typing import Literal

from pytoon import encode, decode, __version__


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.version:
        print(f"pytoon {__version__}")
        return 0

    if args.command == "encode":
        return encode_command(args)
    elif args.command == "decode":
        return decode_command(args)

    parser.print_help()
    return 1


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="pytoon",
        description="Convert between JSON and TOON formats",
    )
    parser.add_argument("--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command")

    # encode subcommand
    encode_parser = subparsers.add_parser("encode", help="Encode JSON to TOON")
    encode_parser.add_argument("input", nargs="?", help="Input JSON file (default: stdin)")
    encode_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    encode_parser.add_argument("--indent", type=int, default=2, help="Indentation spaces")
    encode_parser.add_argument("--delimiter", choices=[",", "\\t", "|"], default=",")
    encode_parser.add_argument("--key-folding", choices=["off", "safe"], default="off")

    # decode subcommand
    decode_parser = subparsers.add_parser("decode", help="Decode TOON to JSON")
    decode_parser.add_argument("input", nargs="?", help="Input TOON file (default: stdin)")
    decode_parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    decode_parser.add_argument("--strict", action="store_true", default=True)
    decode_parser.add_argument("--lenient", action="store_false", dest="strict")

    return parser


def encode_command(args: argparse.Namespace) -> int:
    """Handle encode subcommand."""
    try:
        # Read input
        if args.input:
            with open(args.input, "r") as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)

        # Encode to TOON
        toon = encode(
            data,
            indent=args.indent,
            delimiter=args.delimiter.replace("\\t", "\t"),
            key_folding=args.key_folding,
        )

        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(toon)
        else:
            print(toon)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def decode_command(args: argparse.Namespace) -> int:
    """Handle decode subcommand."""
    try:
        # Read input
        if args.input:
            with open(args.input, "r") as f:
                toon = f.read()
        else:
            toon = sys.stdin.read()

        # Decode to Python
        data = decode(toon, strict=args.strict)

        # Write JSON output
        if args.output:
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
        else:
            print(json.dumps(data, indent=2))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

---

## Technology Stack

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| Argument Parsing | argparse (stdlib) | 3.8+ | Zero dependencies, standard pattern |
| I/O | stdin/stdout | N/A | Unix pipeline compatibility |
| JSON parsing | json (stdlib) | 3.8+ | Standard for input/output |

---

## Implementation Roadmap

### Phase 1: Basic CLI (Week 3, Days 3-4)

**Tasks:**

- [ ] Create `pytoon/cli/__init__.py`
- [ ] Implement `pytoon/cli/__main__.py`
  - Argument parsing with argparse
  - encode subcommand
  - decode subcommand
- [ ] Add entry point in pyproject.toml

  ```toml
  [project.scripts]
  pytoon = "pytoon.cli:main"
  ```

- [ ] Write integration tests

**Deliverables:**

- `pytoon encode` and `pytoon decode` commands working
- File and stdin/stdout support
- All configuration flags respected

### Phase 2: Polish & Documentation (Week 3, Day 5)

**Tasks:**

- [ ] Add `--version` flag
- [ ] Add `--help` with examples
- [ ] Error handling with descriptive messages
- [ ] Test pipeline usage (`cat file.json | pytoon encode`)
- [ ] README examples for CLI usage

**Deliverables:**

- Production-ready CLI
- Comprehensive help text
- Pipeline compatibility validated

---

## Quality Assurance

### Testing Strategy

```python
class TestCLI:
    def test_encode_stdin(self, tmp_path: Path) -> None:
        """Test encoding from stdin."""
        input_json = '{"key": "value"}'
        result = subprocess.run(
            ["python", "-m", "pytoon", "encode"],
            input=input_json,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "key: value" in result.stdout

    def test_decode_file(self, tmp_path: Path) -> None:
        """Test decoding from file."""
        toon_file = tmp_path / "input.toon"
        toon_file.write_text("key: value")

        result = subprocess.run(
            ["python", "-m", "pytoon", "decode", str(toon_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert '"key": "value"' in result.stdout
```

---

## Risk Management

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Platform-specific issues | MEDIUM | LOW | Test on macOS, Linux, Windows |
| Large file memory issues | LOW | LOW | Stream processing in v2.0+ |
| Error message clarity | MEDIUM | LOW | Review all error paths |

---

## References & Traceability

**Specification:** docs/specs/cli/spec.md
**Research:** docs/research/intel.md - Developer experience, pipeline tools
**Dependencies:** CORE-001 (encode/decode functions)

---

**Document Version**: 1.0
**Implementation Status**: Ready for Ticket Generation
