# CLI Module Specification

**Component ID**: CLI-001
**Version**: v1.0
**Priority**: P0
**Status**: Specification
**Source**: `docs/pytoon-system-design.md` Section 4.3

## 1. Overview

The CLI module provides command-line interface for TOON encoding/decoding with auto-detection and token statistics.

**Success Metrics**: Auto-detection accuracy 100%, user-friendly error messages

## 2. Functional Requirements

### FR-1: Auto-Detection

- Detect encode mode for `.json` input → `.toon` output
- Detect decode mode for `.toon` input → `.json` output
- Support stdin/stdout with `-` argument

### FR-2: Command Options

| Flag | Description | Default |
|------|-------------|---------|
| `-e, --encode` | Force encode mode | Auto-detect |
| `-d, --decode` | Force decode mode | Auto-detect |
| `-o, --output FILE` | Output file | stdout |
| `--delimiter {comma,tab,pipe}` | Delimiter | comma |
| `--indent N` | Indentation spaces | 2 |
| `--key-folding {off,safe}` | Key folding mode | off |
| `--no-strict` | Disable strict validation | Strict enabled |
| `--stats` | Show token count and savings | Disabled |

### FR-3: Token Statistics

When `--stats` flag enabled:

```
TOON: 1,234 tokens | JSON: 2,456 tokens | Savings: 49.8%
```

## 3. Usage Examples

```bash
# Encode JSON to TOON
pytoon data.json -o output.toon

# Decode TOON to JSON  
pytoon data.toon -o output.json

# Tab-delimited with stats
pytoon data.json --delimiter tab --stats

# Stdin/stdout
echo '{"x": 1}' | pytoon
```

## 4. Component Structure

```plaintext
pytoon/cli/
├── __init__.py
└── main.py    # CLI entry point with argparse
```

## 5. Acceptance Criteria

- [ ] Auto-detection works for .json/.toon files
- [ ] All command options functional
- [ ] Error messages user-friendly
- [ ] Exit codes: 0 (success), 1 (error)
- [ ] `--stats` shows accurate token counts

**Status**: Ready for Planning Phase
