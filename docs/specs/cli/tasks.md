# Tasks: CLI Module

**From:** `spec.md` + `plan.md`
**Timeline:** 1 week (Sprint 3)
**Team:** 1 Senior Backend Developer
**Created:** 2025-11-15

## Summary

- Total tasks: 5
- Estimated effort: 13 story points
- Critical path duration: 5 days
- Key risks: Platform compatibility, error message clarity

## Phase Breakdown

### Phase 1: Basic CLI (Days 1-3, 9 SP)

**Goal:** Implement core encode/decode commands with file I/O
**Deliverable:** Functional pytoon CLI with stdin/stdout support

#### Tasks

**CLI-002: Implement Argument Parser**

- **Description:** Create argument parser using argparse with subcommands (encode, decode), configuration flags (--indent, --delimiter, --key-folding, --strict), and help text
- **Acceptance:**
  - [ ] argparse-based CLI with subcommands
  - [ ] encode subcommand with input file argument
  - [ ] decode subcommand with input file argument
  - [ ] -o/--output flag for output file
  - [ ] --indent N flag (default: 2)
  - [ ] --delimiter {comma,tab,pipe} flag (default: comma)
  - [ ] --key-folding {off,safe} flag (default: off)
  - [ ] --strict/--lenient flags for decode
  - [ ] --version flag shows pytoon version
  - [ ] --help with clear usage examples
  - [ ] Unit tests for argument parsing
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** CORE-003 (**version**)
- **Priority:** P0 (Blocker - CLI foundation)

**CLI-003: Implement Encode Command**

- **Description:** Create encode command handler that reads JSON from file or stdin, calls pytoon.encode() with configuration, and writes TOON to file or stdout
- **Acceptance:**
  - [ ] Reads JSON from file when path provided
  - [ ] Reads JSON from stdin when no file (or - argument)
  - [ ] Writes TOON to file when -o/--output specified
  - [ ] Writes TOON to stdout when no output file
  - [ ] Respects --indent, --delimiter, --key-folding flags
  - [ ] Exit code 0 on success
  - [ ] Exit code 1 on error with descriptive message to stderr
  - [ ] Handles file not found gracefully
  - [ ] Handles invalid JSON gracefully
  - [ ] Integration tests with real files
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** CORE-006 (encode function)
- **Priority:** P0 (Critical - core CLI feature)

**CLI-004: Implement Decode Command**

- **Description:** Create decode command handler that reads TOON from file or stdin, calls pytoon.decode() with configuration, and writes JSON to file or stdout
- **Acceptance:**
  - [ ] Reads TOON from file when path provided
  - [ ] Reads TOON from stdin when no file (or - argument)
  - [ ] Writes JSON (pretty-printed, indent=2) to file when -o/--output specified
  - [ ] Writes JSON to stdout when no output file
  - [ ] Respects --strict/--lenient flag
  - [ ] Exit code 0 on success
  - [ ] Exit code 1 on error with descriptive message to stderr
  - [ ] Handles file not found gracefully
  - [ ] Handles invalid TOON syntax gracefully
  - [ ] Integration tests with real files
  - [ ] mypy --strict passes
- **Effort:** 3 story points (1 day)
- **Owner:** Backend Developer
- **Dependencies:** CORE-006 (decode function)
- **Priority:** P0 (Critical - core CLI feature)

### Phase 2: Polish (Days 4-5, 4 SP)

**Goal:** Configure entry point and add user-friendly features
**Deliverable:** Production-ready CLI installable via pip

#### Tasks

**CLI-005: Configure Entry Point**

- **Description:** Add [project.scripts] entry point in pyproject.toml so pytoon command is available after pip install, and create **main**.py for python -m pytoon
- **Acceptance:**
  - [ ] pyproject.toml has [project.scripts] pytoon = "pytoon.cli:main"
  - [ ] pytoon/cli/**main**.py enables python -m pytoon
  - [ ] After pip install, pytoon command works
  - [ ] After pip install, python -m pytoon works
  - [ ] Help text accessible: pytoon --help
  - [ ] Version accessible: pytoon --version
  - [ ] Tests verify entry point configuration
  - [ ] mypy --strict passes
- **Effort:** 2 story points (3-4 hours)
- **Owner:** Backend Developer
- **Dependencies:** CLI-002 (argument parser)
- **Priority:** P0 (Blocker - installability)

**CLI-006: Implement Token Statistics Flag**

- **Description:** Add --stats flag that displays token count comparison (TOON vs JSON) after encoding, using TokenCounter from utils module
- **Acceptance:**
  - [ ] --stats flag available on encode command
  - [ ] Output format: "TOON: X tokens | JSON: Y tokens | Savings: Z%"
  - [ ] Uses TokenCounter.compare() for accurate stats
  - [ ] Statistics printed to stderr (data to stdout)
  - [ ] Works with file output (stats still printed)
  - [ ] Handles missing tiktoken gracefully (uses estimation)
  - [ ] Unit tests for stats formatting
  - [ ] mypy --strict passes
- **Effort:** 2 story points (3-4 hours)
- **Owner:** Backend Developer
- **Dependencies:** UTILS-003 (TokenCounter)
- **Priority:** P0 (Important - demonstrates value)

## Critical Path

```plaintext
CORE-006 → CLI-002 → CLI-003 → CLI-005
                 ↓
             CLI-004
```

**Bottlenecks:**

- CLI-002: Argument parsing design affects all commands
- CLI-005: Entry point config critical for user experience

**Parallel Tracks:**

- CLI-003 and CLI-004 can be developed in parallel
- CLI-006 can be added after main commands work

## Quick Wins (Days 1-2)

1. **CLI-002**: Argument parser enables all CLI work
2. **CLI-003**: Encode command demonstrates immediate value

## Risk Mitigation

| Task | Risk | Mitigation | Contingency |
|------|------|------------|-------------|
| CLI-003/004 | Platform-specific path issues | Use pathlib, test on macOS/Linux | Add Windows-specific tests |
| CLI-005 | Entry point misconfiguration | Follow setuptools documentation | Test in clean virtual environment |
| CLI-006 | tiktoken not installed | Graceful fallback with note | Document optional dependency |

## Testing Strategy

### Automated Testing Tasks

- Unit tests for argument parsing (all flags)
- Integration tests with subprocess for real CLI invocation
- Tests for stdin/stdout piping
- Tests for file I/O (read/write)
- Error handling tests (bad JSON, bad TOON, missing files)
- Entry point installation tests

### Quality Gates

- mypy --strict passes
- 85%+ code coverage
- Exit codes correct (0 success, 1 error)
- Error messages written to stderr
- Help text clear and includes examples
- Works on macOS and Linux

## Team Allocation

**Backend Developer (0.5 FTE)**

- CLI design (CLI-002)
- Command handlers (CLI-003, CLI-004)
- Entry point config (CLI-005)
- Statistics feature (CLI-006)

## Sprint Planning

**Week 4: CLI Module (13 SP)**

| Day | Focus | Story Points | Deliverables |
|-----|-------|--------------|--------------|
| Day 1 | Argument Parser | 3 SP | CLI-002: argparse setup |
| Day 2 | Encode Command | 3 SP | CLI-003: JSON → TOON |
| Day 3 | Decode Command | 3 SP | CLI-004: TOON → JSON |
| Day 4 | Entry Point | 2 SP | CLI-005: pip install |
| Day 5 | Statistics | 2 SP | CLI-006: --stats flag |

## Usage Examples (for Help Text)

```bash
# Basic encoding
pytoon encode data.json -o output.toon

# Encoding with tab delimiter
pytoon encode data.json --delimiter tab -o output.toon

# Encoding from stdin
echo '{"x": 1}' | pytoon encode

# Encoding with statistics
pytoon encode data.json --stats

# Basic decoding
pytoon decode data.toon -o output.json

# Lenient decoding
pytoon decode data.toon --lenient

# Pipeline usage
cat input.json | pytoon encode | pytoon decode
```

## Definition of Done

- Code reviewed and approved
- Tests written and passing (85%+ coverage)
- mypy --strict passes
- Entry point works after pip install
- Help text includes usage examples
- Error messages are user-friendly
- Exit codes correct (0/1)
- Works on macOS and Linux
- README includes CLI documentation
