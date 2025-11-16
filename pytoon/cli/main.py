"""PyToon CLI - Token-Oriented Object Notation tool.

This module provides the main entry point for the PyToon command-line interface,
supporting encode and decode operations with configurable options.

Example:
    Encode JSON to TOON::

        $ pytoon encode data.json -o output.toon
        $ echo '{"x": 1}' | pytoon encode
        $ pytoon encode data.json --delimiter tab --indent 4

    Decode TOON to JSON::

        $ pytoon decode data.toon -o output.json
        $ cat data.toon | pytoon decode
        $ pytoon decode data.toon --lenient

    Show version::

        $ pytoon --version
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from pytoon.__version__ import __version__
from pytoon import encode as pytoon_encode
from pytoon import decode as pytoon_decode
from pytoon.utils.errors import TOONDecodeError, TOONEncodeError, TOONValidationError
from pytoon.utils.tokens import TokenCounter


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for PyToon CLI.

    Creates a parser with subcommands for encode and decode operations,
    along with global options like --version.

    Returns:
        argparse.ArgumentParser: Configured argument parser with all
            subcommands and flags.

    Examples:
        Create parser and parse arguments::

            >>> parser = create_parser()
            >>> args = parser.parse_args(['encode', 'data.json'])
            >>> args.command
            'encode'
            >>> args.input
            'data.json'
    """
    parser = argparse.ArgumentParser(
        prog="pytoon",
        description="Convert between JSON and TOON formats for token-efficient LLM communication",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Encode JSON to TOON:
    pytoon encode data.json -o output.toon
    echo '{"x": 1}' | pytoon encode
    pytoon encode data.json --delimiter tab --indent 4

  Decode TOON to JSON:
    pytoon decode data.toon -o output.json
    cat data.toon | pytoon decode

  With key folding enabled:
    pytoon encode data.json --key-folding safe
""",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"pytoon {__version__}",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands",
        metavar="COMMAND",
    )

    # Encode subcommand
    encode_parser = subparsers.add_parser(
        "encode",
        help="Encode JSON to TOON format",
        description="Read JSON data and encode it to TOON format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pytoon encode data.json -o output.toon
  echo '{"key": "value"}' | pytoon encode
  pytoon encode input.json --delimiter tab --indent 4
  pytoon encode data.json --key-folding safe
""",
    )
    encode_parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Input JSON file path (default: read from stdin)",
    )
    encode_parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path (default: write to stdout)",
    )
    encode_parser.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="Indentation spaces per level (default: 2)",
    )
    encode_parser.add_argument(
        "--delimiter",
        choices=["comma", "tab", "pipe"],
        default="comma",
        help="Delimiter for tabular arrays: comma (,), tab (\\t), or pipe (|) (default: comma)",
    )
    encode_parser.add_argument(
        "--key-folding",
        choices=["off", "safe"],
        default="off",
        dest="key_folding",
        help="Key folding mode: off (no folding) or safe (fold single-key chains) (default: off)",
    )
    encode_parser.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Display token count comparison statistics (TOON vs JSON)",
    )

    # Decode subcommand
    decode_parser = subparsers.add_parser(
        "decode",
        help="Decode TOON to JSON format",
        description="Read TOON data and decode it to JSON format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pytoon decode data.toon -o output.json
  cat data.toon | pytoon decode
  pytoon decode input.toon --lenient
  pytoon decode data.toon --expand-paths safe
""",
    )
    decode_parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Input TOON file path (default: read from stdin)",
    )
    decode_parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path (default: write to stdout)",
    )
    decode_parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        dest="strict",
        help="Enable strict validation mode (default: enabled)",
    )
    decode_parser.add_argument(
        "--lenient",
        action="store_false",
        dest="strict",
        help="Disable strict validation mode (lenient parsing)",
    )
    decode_parser.add_argument(
        "--expand-paths",
        choices=["off", "safe"],
        default="off",
        dest="expand_paths",
        help="Path expansion mode: off (no expansion) or safe (expand dotted keys) (default: off)",
    )

    return parser


def parse_args(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments to parse. If None, uses sys.argv.

    Returns:
        argparse.Namespace: Parsed arguments.

    Examples:
        Parse encode command::

            >>> ns = parse_args(['encode', 'data.json', '-o', 'out.toon'])
            >>> ns.command
            'encode'
            >>> ns.input
            'data.json'
            >>> ns.output
            'out.toon'
            >>> ns.indent
            2

        Parse decode command with options::

            >>> ns = parse_args(['decode', 'data.toon', '--lenient'])
            >>> ns.command
            'decode'
            >>> ns.strict
            False
    """
    parser = create_parser()
    return parser.parse_args(args)


def get_delimiter_char(delimiter: str) -> str:
    """Convert delimiter name to character.

    Args:
        delimiter: Delimiter name ('comma', 'tab', or 'pipe').

    Returns:
        str: The actual delimiter character.

    Raises:
        ValueError: If delimiter is not recognized.

    Examples:
        >>> get_delimiter_char('comma')
        ','
        >>> get_delimiter_char('tab')
        '\\t'
        >>> get_delimiter_char('pipe')
        '|'
    """
    delimiter_map = {
        "comma": ",",
        "tab": "\t",
        "pipe": "|",
    }
    if delimiter not in delimiter_map:
        raise ValueError(f"Invalid delimiter: {delimiter}")
    return delimiter_map[delimiter]


def handle_encode(args: argparse.Namespace) -> int:
    """Handle the encode command.

    Reads JSON from file or stdin, encodes to TOON format, and writes
    to file or stdout.

    Args:
        args: Parsed command-line arguments containing input, output,
            indent, delimiter, and key_folding options.

    Returns:
        int: Exit code (0 for success, 1 for error).

    Examples:
        Handle encode from stdin to stdout::

            >>> import argparse
            >>> ns = argparse.Namespace(
            ...     input=None,
            ...     output=None,
            ...     indent=2,
            ...     delimiter='comma',
            ...     key_folding='off'
            ... )
            >>> # Would read from stdin and write to stdout
    """
    # Validate indent
    if args.indent <= 0:
        print(f"Error: indent must be positive, got {args.indent}", file=sys.stderr)
        return 1

    # Convert delimiter name to character
    try:
        delimiter_char = get_delimiter_char(args.delimiter)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Read JSON input
    json_data: Any
    try:
        if args.input is None:
            # Read from stdin
            json_text = sys.stdin.read()
        else:
            # Read from file
            try:
                with open(args.input, encoding="utf-8") as f:
                    json_text = f.read()
            except FileNotFoundError:
                print(f"Error: file not found: {args.input}", file=sys.stderr)
                return 1
            except PermissionError:
                print(f"Error: permission denied: {args.input}", file=sys.stderr)
                return 1
            except IsADirectoryError:
                print(f"Error: is a directory: {args.input}", file=sys.stderr)
                return 1

        # Parse JSON
        try:
            json_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"Error: invalid JSON: {e}", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Error: failed to read input: {e}", file=sys.stderr)
        return 1

    # Encode to TOON
    try:
        toon_output = pytoon_encode(
            json_data,
            indent=args.indent,
            delimiter=delimiter_char,  # type: ignore[arg-type]
            key_folding=args.key_folding,
        )
    except TOONEncodeError as e:
        print(f"Error: encoding failed: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: invalid configuration: {e}", file=sys.stderr)
        return 1

    # Write TOON output
    try:
        if args.output is None:
            # Write to stdout
            print(toon_output)
        else:
            # Write to file
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(toon_output)
                    f.write("\n")  # Add trailing newline
            except PermissionError:
                print(f"Error: permission denied: {args.output}", file=sys.stderr)
                return 1
            except IsADirectoryError:
                print(f"Error: is a directory: {args.output}", file=sys.stderr)
                return 1
    except Exception as e:
        print(f"Error: failed to write output: {e}", file=sys.stderr)
        return 1

    # Display token statistics if requested
    if getattr(args, "stats", False):
        try:
            counter = TokenCounter()
            stats = counter.compare(json_data)
            stats_line = (
                f"TOON: {stats['toon_tokens']} tokens | "
                f"JSON: {stats['json_tokens']} tokens | "
                f"Savings: {stats['savings_percent']:.1f}%"
            )
            print(stats_line, file=sys.stderr)
        except Exception as e:
            # Handle case when tiktoken is not installed or other errors
            print(f"Warning: could not compute statistics: {e}", file=sys.stderr)

    return 0


def handle_decode(args: argparse.Namespace) -> int:
    """Handle the decode command.

    Reads TOON from file or stdin, decodes to Python objects, and writes
    JSON to file or stdout.

    Args:
        args: Parsed command-line arguments containing input, output,
            strict, and expand_paths options.

    Returns:
        int: Exit code (0 for success, 1 for error).

    Examples:
        Handle decode from stdin to stdout::

            >>> import argparse
            >>> ns = argparse.Namespace(
            ...     input=None,
            ...     output=None,
            ...     strict=True,
            ...     expand_paths='off'
            ... )
            >>> # Would read from stdin and write to stdout
    """
    # Read TOON input
    toon_text: str
    try:
        if args.input is None:
            # Read from stdin
            toon_text = sys.stdin.read()
        else:
            # Read from file
            try:
                with open(args.input, encoding="utf-8") as f:
                    toon_text = f.read()
            except FileNotFoundError:
                print(f"Error: file not found: {args.input}", file=sys.stderr)
                return 1
            except PermissionError:
                print(f"Error: permission denied: {args.input}", file=sys.stderr)
                return 1
            except IsADirectoryError:
                print(f"Error: is a directory: {args.input}", file=sys.stderr)
                return 1

    except Exception as e:
        print(f"Error: failed to read input: {e}", file=sys.stderr)
        return 1

    # Decode TOON to Python object
    decoded_data: Any
    try:
        decoded_data = pytoon_decode(
            toon_text,
            strict=args.strict,
            expand_paths=args.expand_paths,
        )
    except TOONValidationError as e:
        print(f"Error: validation failed: {e}", file=sys.stderr)
        return 1
    except TOONDecodeError as e:
        print(f"Error: invalid TOON syntax: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: invalid configuration: {e}", file=sys.stderr)
        return 1

    # Convert to JSON string
    try:
        json_output = json.dumps(decoded_data, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        print(f"Error: failed to serialize to JSON: {e}", file=sys.stderr)
        return 1

    # Write JSON output
    try:
        if args.output is None:
            # Write to stdout
            print(json_output)
        else:
            # Write to file
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(json_output)
                    f.write("\n")  # Add trailing newline
            except PermissionError:
                print(f"Error: permission denied: {args.output}", file=sys.stderr)
                return 1
            except IsADirectoryError:
                print(f"Error: is a directory: {args.output}", file=sys.stderr)
                return 1
    except Exception as e:
        print(f"Error: failed to write output: {e}", file=sys.stderr)
        return 1

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entry point.

    Parses arguments and dispatches to appropriate command handler.
    This function is the entry point for the 'pytoon' command.

    Args:
        argv: Command-line arguments. If None, uses sys.argv.

    Returns:
        int: Exit code (0 for success, 1 for error).

    Examples:
        Show help when no command given::

            >>> main([])  # No command
            1

        Parse version flag::

            >>> main(['--version'])  # doctest: +SKIP
            pytoon 1.0.0
            0
    """
    args = parse_args(argv)

    if args.command is None:
        parser = create_parser()
        parser.print_help(sys.stderr)
        return 1

    if args.command == "encode":
        return handle_encode(args)

    if args.command == "decode":
        return handle_decode(args)

    # Unknown command (should not happen with argparse)
    print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
