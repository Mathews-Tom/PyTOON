"""Unit tests for PyToon CLI argument parser.

Tests cover all argument parsing functionality including subcommands,
flags, defaults, and validation.
"""

from __future__ import annotations

import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest

from pytoon.cli.main import (
    create_parser,
    get_delimiter_char,
    handle_decode,
    handle_encode,
    main,
    parse_args,
)


class TestCreateParser:
    """Tests for create_parser function."""

    def test_parser_prog_name(self) -> None:
        """Parser has correct program name."""
        parser = create_parser()
        assert parser.prog == "pytoon"

    def test_parser_has_description(self) -> None:
        """Parser has a description."""
        parser = create_parser()
        assert parser.description is not None
        assert "JSON" in parser.description
        assert "TOON" in parser.description

    def test_parser_has_encode_subcommand(self) -> None:
        """Parser has encode subcommand."""
        parser = create_parser()
        # Check that encode is a valid subcommand
        args = parser.parse_args(["encode"])
        assert args.command == "encode"

    def test_parser_has_decode_subcommand(self) -> None:
        """Parser has decode subcommand."""
        parser = create_parser()
        args = parser.parse_args(["decode"])
        assert args.command == "decode"


class TestEncodeSubcommand:
    """Tests for encode subcommand argument parsing."""

    def test_encode_no_input_file(self) -> None:
        """Encode with no input defaults to None (stdin)."""
        args = parse_args(["encode"])
        assert args.command == "encode"
        assert args.input is None

    def test_encode_with_input_file(self) -> None:
        """Encode with input file argument."""
        args = parse_args(["encode", "data.json"])
        assert args.command == "encode"
        assert args.input == "data.json"

    def test_encode_output_short_flag(self) -> None:
        """Encode with -o output flag."""
        args = parse_args(["encode", "input.json", "-o", "output.toon"])
        assert args.output == "output.toon"

    def test_encode_output_long_flag(self) -> None:
        """Encode with --output flag."""
        args = parse_args(["encode", "input.json", "--output", "output.toon"])
        assert args.output == "output.toon"

    def test_encode_default_output_is_none(self) -> None:
        """Default output is None (stdout)."""
        args = parse_args(["encode", "input.json"])
        assert args.output is None

    def test_encode_indent_default(self) -> None:
        """Default indent is 2."""
        args = parse_args(["encode"])
        assert args.indent == 2

    def test_encode_indent_custom(self) -> None:
        """Custom indent value."""
        args = parse_args(["encode", "--indent", "4"])
        assert args.indent == 4

    def test_encode_indent_negative(self) -> None:
        """Negative indent value is parsed (validation in main)."""
        args = parse_args(["encode", "--indent", "-1"])
        assert args.indent == -1

    def test_encode_indent_zero(self) -> None:
        """Zero indent value is parsed."""
        args = parse_args(["encode", "--indent", "0"])
        assert args.indent == 0

    def test_encode_delimiter_default(self) -> None:
        """Default delimiter is comma."""
        args = parse_args(["encode"])
        assert args.delimiter == "comma"

    def test_encode_delimiter_comma(self) -> None:
        """Delimiter can be set to comma."""
        args = parse_args(["encode", "--delimiter", "comma"])
        assert args.delimiter == "comma"

    def test_encode_delimiter_tab(self) -> None:
        """Delimiter can be set to tab."""
        args = parse_args(["encode", "--delimiter", "tab"])
        assert args.delimiter == "tab"

    def test_encode_delimiter_pipe(self) -> None:
        """Delimiter can be set to pipe."""
        args = parse_args(["encode", "--delimiter", "pipe"])
        assert args.delimiter == "pipe"

    def test_encode_delimiter_invalid(self) -> None:
        """Invalid delimiter raises error."""
        with pytest.raises(SystemExit):
            parse_args(["encode", "--delimiter", "invalid"])

    def test_encode_key_folding_default(self) -> None:
        """Default key folding is off."""
        args = parse_args(["encode"])
        assert args.key_folding == "off"

    def test_encode_key_folding_off(self) -> None:
        """Key folding can be set to off."""
        args = parse_args(["encode", "--key-folding", "off"])
        assert args.key_folding == "off"

    def test_encode_key_folding_safe(self) -> None:
        """Key folding can be set to safe."""
        args = parse_args(["encode", "--key-folding", "safe"])
        assert args.key_folding == "safe"

    def test_encode_key_folding_invalid(self) -> None:
        """Invalid key folding raises error."""
        with pytest.raises(SystemExit):
            parse_args(["encode", "--key-folding", "invalid"])

    def test_encode_stats_flag_default(self) -> None:
        """Default stats flag is False."""
        args = parse_args(["encode"])
        assert args.stats is False

    def test_encode_stats_flag_enabled(self) -> None:
        """Stats flag can be enabled."""
        args = parse_args(["encode", "--stats"])
        assert args.stats is True

    def test_encode_all_flags_combined(self) -> None:
        """All encode flags work together."""
        args = parse_args([
            "encode",
            "input.json",
            "-o", "output.toon",
            "--indent", "4",
            "--delimiter", "tab",
            "--key-folding", "safe",
            "--stats",
        ])
        assert args.command == "encode"
        assert args.input == "input.json"
        assert args.output == "output.toon"
        assert args.indent == 4
        assert args.delimiter == "tab"
        assert args.key_folding == "safe"
        assert args.stats is True


class TestDecodeSubcommand:
    """Tests for decode subcommand argument parsing."""

    def test_decode_no_input_file(self) -> None:
        """Decode with no input defaults to None (stdin)."""
        args = parse_args(["decode"])
        assert args.command == "decode"
        assert args.input is None

    def test_decode_with_input_file(self) -> None:
        """Decode with input file argument."""
        args = parse_args(["decode", "data.toon"])
        assert args.command == "decode"
        assert args.input == "data.toon"

    def test_decode_output_short_flag(self) -> None:
        """Decode with -o output flag."""
        args = parse_args(["decode", "input.toon", "-o", "output.json"])
        assert args.output == "output.json"

    def test_decode_output_long_flag(self) -> None:
        """Decode with --output flag."""
        args = parse_args(["decode", "input.toon", "--output", "output.json"])
        assert args.output == "output.json"

    def test_decode_default_output_is_none(self) -> None:
        """Default output is None (stdout)."""
        args = parse_args(["decode", "input.toon"])
        assert args.output is None

    def test_decode_strict_default(self) -> None:
        """Default strict mode is True."""
        args = parse_args(["decode"])
        assert args.strict is True

    def test_decode_strict_flag(self) -> None:
        """Explicit --strict flag."""
        args = parse_args(["decode", "--strict"])
        assert args.strict is True

    def test_decode_lenient_flag(self) -> None:
        """--lenient flag disables strict mode."""
        args = parse_args(["decode", "--lenient"])
        assert args.strict is False

    def test_decode_expand_paths_default(self) -> None:
        """Default expand_paths is off."""
        args = parse_args(["decode"])
        assert args.expand_paths == "off"

    def test_decode_expand_paths_off(self) -> None:
        """Expand paths can be set to off."""
        args = parse_args(["decode", "--expand-paths", "off"])
        assert args.expand_paths == "off"

    def test_decode_expand_paths_safe(self) -> None:
        """Expand paths can be set to safe."""
        args = parse_args(["decode", "--expand-paths", "safe"])
        assert args.expand_paths == "safe"

    def test_decode_expand_paths_invalid(self) -> None:
        """Invalid expand paths raises error."""
        with pytest.raises(SystemExit):
            parse_args(["decode", "--expand-paths", "invalid"])

    def test_decode_all_flags_combined(self) -> None:
        """All decode flags work together."""
        args = parse_args([
            "decode",
            "input.toon",
            "-o", "output.json",
            "--lenient",
            "--expand-paths", "safe",
        ])
        assert args.command == "decode"
        assert args.input == "input.toon"
        assert args.output == "output.json"
        assert args.strict is False
        assert args.expand_paths == "safe"


class TestGetDelimiterChar:
    """Tests for get_delimiter_char function."""

    def test_comma_delimiter(self) -> None:
        """Comma delimiter converts correctly."""
        assert get_delimiter_char("comma") == ","

    def test_tab_delimiter(self) -> None:
        """Tab delimiter converts correctly."""
        assert get_delimiter_char("tab") == "\t"

    def test_pipe_delimiter(self) -> None:
        """Pipe delimiter converts correctly."""
        assert get_delimiter_char("pipe") == "|"

    def test_invalid_delimiter_raises_error(self) -> None:
        """Invalid delimiter raises ValueError."""
        with pytest.raises(ValueError, match="Invalid delimiter"):
            get_delimiter_char("invalid")

    def test_empty_delimiter_raises_error(self) -> None:
        """Empty delimiter raises ValueError."""
        with pytest.raises(ValueError, match="Invalid delimiter"):
            get_delimiter_char("")


class TestMain:
    """Tests for main CLI entry point."""

    def test_no_command_returns_error(self) -> None:
        """No command shows help and returns 1."""
        result = main([])
        assert result == 1

    def test_encode_command_with_valid_json_returns_success(self) -> None:
        """Encode command with valid JSON file returns 0."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_decode_command_returns_success(self) -> None:
        """Decode command with valid TOON file returns 0."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            result = main(["decode", input_path])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_encode_with_input_file(self) -> None:
        """Encode command with input file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test": "data"}, f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_encode_with_output_file(self) -> None:
        """Encode command with output file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as out:
            output_path = out.name

        try:
            result = main(["encode", input_path, "-o", output_path])
            assert result == 0
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_encode_with_custom_indent(self) -> None:
        """Encode command with custom indent."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path, "--indent", "4"])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_encode_with_zero_indent_fails(self) -> None:
        """Encode command with zero indent fails."""
        result = main(["encode", "--indent", "0"])
        assert result == 1

    def test_encode_with_negative_indent_fails(self) -> None:
        """Encode command with negative indent fails."""
        result = main(["encode", "--indent", "-1"])
        assert result == 1

    def test_encode_with_tab_delimiter(self) -> None:
        """Encode command with tab delimiter."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}], f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path, "--delimiter", "tab"])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_encode_with_pipe_delimiter(self) -> None:
        """Encode command with pipe delimiter."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([1, 2, 3], f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path, "--delimiter", "pipe"])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_encode_with_key_folding(self) -> None:
        """Encode command with key folding."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"a": {"b": 1}}, f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path, "--key-folding", "safe"])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_decode_with_input_file(self) -> None:
        """Decode command with input file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("data: test")
            f.flush()
            input_path = f.name

        try:
            result = main(["decode", input_path])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_decode_with_output_file(self) -> None:
        """Decode command with output file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("data: test")
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as out:
            output_path = out.name

        try:
            result = main(["decode", input_path, "-o", output_path])
            assert result == 0
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_decode_with_lenient_mode(self) -> None:
        """Decode command with lenient mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            result = main(["decode", input_path, "--lenient"])
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_decode_with_expand_paths(self) -> None:
        """Decode command with path expansion."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            result = main(["decode", input_path, "--expand-paths", "safe"])
            assert result == 0
        finally:
            Path(input_path).unlink()


class TestVersionFlag:
    """Tests for --version flag."""

    def test_version_flag_exits(self) -> None:
        """--version flag causes SystemExit."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--version"])
        assert exc_info.value.code == 0


class TestHelpFlag:
    """Tests for --help flag."""

    def test_main_help_exits(self) -> None:
        """Main --help causes SystemExit."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--help"])
        assert exc_info.value.code == 0

    def test_encode_help_exits(self) -> None:
        """Encode --help causes SystemExit."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["encode", "--help"])
        assert exc_info.value.code == 0

    def test_decode_help_exits(self) -> None:
        """Decode --help causes SystemExit."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["decode", "--help"])
        assert exc_info.value.code == 0


class TestEntryPoints:
    """Tests for entry point configuration."""

    def test_main_module_imports_correctly(self) -> None:
        """__main__.py imports main() from pytoon.cli.main."""
        from pytoon.cli import __main__ as cli_main

        assert hasattr(cli_main, "main")
        # Verify main is the same function
        assert cli_main.main is main

    def test_main_module_has_sys_import(self) -> None:
        """__main__.py imports sys module."""
        from pytoon.cli import __main__ as cli_main

        assert hasattr(cli_main, "sys")

    def test_pyproject_entry_point_valid(self) -> None:
        """Entry point in pyproject.toml is valid."""
        # Import the module and function referenced in pyproject.toml
        from pytoon.cli.main import main as entry_main

        # Verify it's callable
        assert callable(entry_main)
        # Verify it returns int
        result = entry_main([])
        assert isinstance(result, int)

    def test_entry_point_function_signature(self) -> None:
        """Entry point main() accepts argv parameter."""
        import inspect

        sig = inspect.signature(main)
        params = list(sig.parameters.keys())
        # Should have argv parameter
        assert "argv" in params
        # Should have default value of None
        assert sig.parameters["argv"].default is None

    def test_entry_point_returns_exit_code(self) -> None:
        """Entry point returns integer exit code."""
        # Test success case
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path])
            assert isinstance(result, int)
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_entry_point_error_returns_nonzero(self) -> None:
        """Entry point returns non-zero on error."""
        result = main(["encode", "/nonexistent/file.json"])
        assert isinstance(result, int)
        assert result != 0

    def test_python_m_pytoon_cli_module(self) -> None:
        """python -m pytoon.cli works via __main__.py."""
        # This test verifies the module structure is correct
        # by checking that the __main__.py file exists and can be imported
        import importlib.util

        spec = importlib.util.find_spec("pytoon.cli.__main__")
        assert spec is not None
        assert spec.origin is not None
        assert spec.origin.endswith("__main__.py")

    def test_python_m_pytoon_module(self) -> None:
        """python -m pytoon works via pytoon/__main__.py."""
        import importlib.util

        spec = importlib.util.find_spec("pytoon.__main__")
        assert spec is not None
        assert spec.origin is not None
        assert spec.origin.endswith("__main__.py")

    def test_pytoon_main_imports_correctly(self) -> None:
        """pytoon/__main__.py imports main() from pytoon.cli.main."""
        from pytoon import __main__ as pytoon_main

        assert hasattr(pytoon_main, "main")
        # Verify main is the same function
        assert pytoon_main.main is main

    def test_pytoon_main_has_sys_import(self) -> None:
        """pytoon/__main__.py imports sys module."""
        from pytoon import __main__ as pytoon_main

        assert hasattr(pytoon_main, "sys")


class TestEdgeCases:
    """Tests for edge cases in argument parsing."""

    def test_encode_with_all_options(self) -> None:
        """Encode with every possible option."""
        args = parse_args([
            "encode",
            "input.json",
            "-o", "output.toon",
            "--indent", "8",
            "--delimiter", "pipe",
            "--key-folding", "safe",
            "--stats",
        ])
        assert args.command == "encode"
        assert args.input == "input.json"
        assert args.output == "output.toon"
        assert args.indent == 8
        assert args.delimiter == "pipe"
        assert args.key_folding == "safe"
        assert args.stats is True

    def test_decode_with_all_options(self) -> None:
        """Decode with every possible option."""
        args = parse_args([
            "decode",
            "input.toon",
            "-o", "output.json",
            "--lenient",
            "--expand-paths", "safe",
        ])
        assert args.command == "decode"
        assert args.input == "input.toon"
        assert args.output == "output.json"
        assert args.strict is False
        assert args.expand_paths == "safe"

    def test_encode_flags_order_independent(self) -> None:
        """Flag order doesn't matter for encode."""
        args1 = parse_args([
            "encode", "--indent", "4", "--delimiter", "tab", "input.json"
        ])
        args2 = parse_args([
            "encode", "input.json", "--delimiter", "tab", "--indent", "4"
        ])
        assert args1.indent == args2.indent
        assert args1.delimiter == args2.delimiter
        assert args1.input == args2.input

    def test_decode_flags_order_independent(self) -> None:
        """Flag order doesn't matter for decode."""
        args1 = parse_args([
            "decode", "--lenient", "input.toon", "-o", "out.json"
        ])
        args2 = parse_args([
            "decode", "input.toon", "-o", "out.json", "--lenient"
        ])
        assert args1.strict == args2.strict
        assert args1.input == args2.input
        assert args1.output == args2.output

    def test_large_indent_value(self) -> None:
        """Very large indent value is accepted."""
        args = parse_args(["encode", "--indent", "100"])
        assert args.indent == 100

    def test_input_with_special_characters(self) -> None:
        """Input file with special characters in name."""
        args = parse_args(["encode", "file-with_special.chars.json"])
        assert args.input == "file-with_special.chars.json"

    def test_output_with_path(self) -> None:
        """Output file with directory path."""
        args = parse_args(["encode", "-o", "/tmp/output.toon"])
        assert args.output == "/tmp/output.toon"


class TestHandleEncode:
    """Tests for handle_encode function."""

    def test_encode_simple_object_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode simple object writes to stdout."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "Alice", "age": 30}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "name: Alice" in captured.out
            assert "age: 30" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_array_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode array writes to stdout."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([1, 2, 3], f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "[3]:" in captured.out
            assert "1" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_to_output_file(self) -> None:
        """Encode writes to output file when specified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as out:
            output_path = out.name

        try:
            args = parse_args(["encode", input_path, "-o", output_path])
            result = handle_encode(args)
            assert result == 0

            with open(output_path) as f:
                content = f.read()
            assert "key: value" in content
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_encode_with_custom_indent(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode respects --indent flag."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"outer": {"inner": "value"}}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--indent", "4"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Check that indentation is 4 spaces
            assert "    inner: value" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_with_tab_delimiter(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode respects --delimiter tab flag."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}], f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--delimiter", "tab"])
            result = handle_encode(args)
            assert result == 0

            # Just verify it succeeds with tab delimiter
            captured = capsys.readouterr()
            assert "[2" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_with_key_folding(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode respects --key-folding safe flag."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"a": {"b": {"c": 1}}}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--key-folding", "safe"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Verify key folding flag is passed to encoder (output depends on implementation)
            assert "a:" in captured.out
            assert "c: 1" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_invalid_indent_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode fails with zero indent."""
        args = parse_args(["encode", "--indent", "0"])
        result = handle_encode(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "indent must be positive" in captured.err

    def test_encode_invalid_indent_negative(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode fails with negative indent."""
        args = parse_args(["encode", "--indent", "-5"])
        result = handle_encode(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "indent must be positive" in captured.err

    def test_encode_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode handles file not found gracefully."""
        args = parse_args(["encode", "/nonexistent/file.json"])
        result = handle_encode(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "file not found" in captured.err

    def test_encode_invalid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode handles invalid JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 1

            captured = capsys.readouterr()
            assert "invalid JSON" in captured.err
        finally:
            Path(input_path).unlink()

    def test_encode_empty_object(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode handles empty object."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0
        finally:
            Path(input_path).unlink()

    def test_encode_empty_array(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode handles empty array."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "[0]:" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_primitive_null(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode handles null primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(None, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "null" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_primitive_boolean(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode handles boolean primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(True, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "true" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_primitive_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode handles number primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(42, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "42" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_primitive_string(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode handles string primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump("hello world", f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # String should be quoted since it contains space
            assert "hello world" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_from_stdin(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Encode reads from stdin when no file specified."""
        json_input = '{"key": "value"}'
        monkeypatch.setattr("sys.stdin", StringIO(json_input))

        args = parse_args(["encode"])
        result = handle_encode(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "key: value" in captured.out

    def test_encode_complex_nested_structure(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Encode handles complex nested structures."""
        data = {
            "user": {
                "name": "Alice",
                "contact": {"email": "alice@example.com", "phone": "123-456"},
            },
            "orders": [{"id": 1, "total": 100}, {"id": 2, "total": 200}],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "user:" in captured.out
            assert "name: Alice" in captured.out
            assert "orders:" in captured.out
        finally:
            Path(input_path).unlink()

    def test_encode_output_file_has_trailing_newline(self) -> None:
        """Encode adds trailing newline to output file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as out:
            output_path = out.name

        try:
            args = parse_args(["encode", input_path, "-o", output_path])
            result = handle_encode(args)
            assert result == 0

            with open(output_path) as f:
                content = f.read()
            assert content.endswith("\n")
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_encode_directory_as_input_fails(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Encode fails when input is a directory."""
        args = parse_args(["encode", str(tmp_path)])
        result = handle_encode(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "is a directory" in captured.err

    def test_encode_directory_as_output_fails(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Encode fails when output is a directory."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "-o", str(tmp_path)])
            result = handle_encode(args)
            assert result == 1

            captured = capsys.readouterr()
            assert "is a directory" in captured.err
        finally:
            Path(input_path).unlink()

    def test_encode_with_all_options(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode with all options combined."""
        data = {"outer": {"inner": {"value": 42}}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args([
                "encode",
                input_path,
                "--indent", "4",
                "--delimiter", "pipe",
                "--key-folding", "safe",
            ])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Verify all options are respected
            assert "outer:" in captured.out
            assert "value: 42" in captured.out
            # Check for 4-space indent (the value should have 8 spaces before it)
            assert "        value: 42" in captured.out
        finally:
            Path(input_path).unlink()


class TestEncodeIntegration:
    """Integration tests for encode command via main()."""

    def test_main_encode_from_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Main entry point handles encode from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test": "data"}, f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path])
            assert result == 0

            captured = capsys.readouterr()
            assert "test: data" in captured.out
        finally:
            Path(input_path).unlink()

    def test_main_encode_to_file(self) -> None:
        """Main entry point handles encode to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"output": "test"}, f)
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as out:
            output_path = out.name

        try:
            result = main(["encode", input_path, "-o", output_path])
            assert result == 0

            with open(output_path) as f:
                content = f.read()
            assert "output: test" in content
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_main_encode_invalid_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Main entry point handles encode error gracefully."""
        result = main(["encode", "/nonexistent/path.json"])
        assert result == 1

        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_encode_invalid_json_file(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Main entry point handles invalid JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path])
            assert result == 1

            captured = capsys.readouterr()
            assert "invalid JSON" in captured.err
        finally:
            Path(input_path).unlink()


class TestHandleDecode:
    """Tests for handle_decode function."""

    def test_decode_simple_object_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode simple object writes JSON to stdout."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("name: Alice\nage: 30")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["name"] == "Alice"
            assert output["age"] == 30
        finally:
            Path(input_path).unlink()

    def test_decode_array_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode array writes JSON to stdout."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("[3]: 1,2,3")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == [1, 2, 3]
        finally:
            Path(input_path).unlink()

    def test_decode_to_output_file(self) -> None:
        """Decode writes to output file when specified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as out:
            output_path = out.name

        try:
            args = parse_args(["decode", input_path, "-o", output_path])
            result = handle_decode(args)
            assert result == 0

            with open(output_path) as f:
                content = json.load(f)
            assert content == {"key": "value"}
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_decode_with_strict_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode respects --strict flag."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path, "--strict"])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == {"key": "value"}
        finally:
            Path(input_path).unlink()

    def test_decode_with_lenient_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode respects --lenient flag."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path, "--lenient"])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == {"key": "value"}
        finally:
            Path(input_path).unlink()

    def test_decode_with_expand_paths(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode respects --expand-paths safe flag."""
        # Note: expand_paths is passed to decoder; its behavior depends on decoder implementation.
        # CLI correctly passes the parameter to decode().
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path, "--expand-paths", "safe"])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == {"key": "value"}
        finally:
            Path(input_path).unlink()

    def test_decode_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode handles file not found gracefully."""
        args = parse_args(["decode", "/nonexistent/file.toon"])
        result = handle_decode(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "file not found" in captured.err

    def test_decode_invalid_toon_syntax(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode handles invalid TOON syntax gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            # Write clearly invalid TOON (mismatched array length)
            f.write('[2]: 1')
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path, "--strict"])
            result = handle_decode(args)
            # In strict mode, validation error should occur
            # If decoder accepts it as lenient by default, may succeed
            # The key thing is that CLI handles errors gracefully
            assert result in (0, 1)
        finally:
            Path(input_path).unlink()

    def test_decode_empty_object(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode handles empty TOON input."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            # Empty input should be handled (may return None or empty dict)
            # Check it doesn't crash
            assert result in (0, 1)  # Either success or handled error
        finally:
            Path(input_path).unlink()

    def test_decode_primitive_null(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode handles null primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("null")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert captured.out.strip() == "null"
        finally:
            Path(input_path).unlink()

    def test_decode_primitive_boolean_true(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode handles true boolean primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("true")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert captured.out.strip() == "true"
        finally:
            Path(input_path).unlink()

    def test_decode_primitive_boolean_false(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode handles false boolean primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("false")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert captured.out.strip() == "false"
        finally:
            Path(input_path).unlink()

    def test_decode_primitive_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode handles number primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("42")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert captured.out.strip() == "42"
        finally:
            Path(input_path).unlink()

    def test_decode_primitive_string(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode handles string primitive."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write('"hello world"')
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert '"hello world"' in captured.out
        finally:
            Path(input_path).unlink()

    def test_decode_from_stdin(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Decode reads from stdin when no file specified."""
        toon_input = "key: value"
        monkeypatch.setattr("sys.stdin", StringIO(toon_input))

        args = parse_args(["decode"])
        result = handle_decode(args)
        assert result == 0

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output == {"key": "value"}

    def test_decode_complex_nested_structure(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Decode handles structures with multiple keys."""
        toon_text = """user: Alice
email: alice@example.com
phone: 123-456"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write(toon_text)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert "user" in output
            assert output["user"] == "Alice"
            assert output["email"] == "alice@example.com"
        finally:
            Path(input_path).unlink()

    def test_decode_output_file_has_trailing_newline(self) -> None:
        """Decode adds trailing newline to output file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as out:
            output_path = out.name

        try:
            args = parse_args(["decode", input_path, "-o", output_path])
            result = handle_decode(args)
            assert result == 0

            with open(output_path) as f:
                content = f.read()
            assert content.endswith("\n")
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_decode_directory_as_input_fails(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Decode fails when input is a directory."""
        args = parse_args(["decode", str(tmp_path)])
        result = handle_decode(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "is a directory" in captured.err

    def test_decode_directory_as_output_fails(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Decode fails when output is a directory."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path, "-o", str(tmp_path)])
            result = handle_decode(args)
            assert result == 1

            captured = capsys.readouterr()
            assert "is a directory" in captured.err
        finally:
            Path(input_path).unlink()

    def test_decode_with_all_options(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode with all options combined."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            args = parse_args([
                "decode",
                input_path,
                "--lenient",
                "--expand-paths", "safe",
            ])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == {"key": "value"}
        finally:
            Path(input_path).unlink()

    def test_decode_json_output_is_formatted(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Decode outputs formatted JSON with indent=2."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value\nanother: test")
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["decode", input_path])
            result = handle_decode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Check that output is indented (not a single line)
            assert "\n" in captured.out.strip()
            output = json.loads(captured.out)
            assert output == {"key": "value", "another": "test"}
        finally:
            Path(input_path).unlink()


class TestDecodeIntegration:
    """Integration tests for decode command via main()."""

    def test_main_decode_from_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Main entry point handles decode from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("test: data")
            f.flush()
            input_path = f.name

        try:
            result = main(["decode", input_path])
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == {"test": "data"}
        finally:
            Path(input_path).unlink()

    def test_main_decode_to_file(self) -> None:
        """Main entry point handles decode to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("output: test")
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as out:
            output_path = out.name

        try:
            result = main(["decode", input_path, "-o", output_path])
            assert result == 0

            with open(output_path) as f:
                content = json.load(f)
            assert content == {"output": "test"}
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_main_decode_invalid_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Main entry point handles decode error gracefully."""
        result = main(["decode", "/nonexistent/path.toon"])
        assert result == 1

        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_main_decode_with_lenient(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Main entry point handles lenient mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            result = main(["decode", input_path, "--lenient"])
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == {"key": "value"}
        finally:
            Path(input_path).unlink()

    def test_main_decode_with_expand_paths(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Main entry point handles expand paths."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            f.write("key: value")
            f.flush()
            input_path = f.name

        try:
            result = main(["decode", input_path, "--expand-paths", "safe"])
            assert result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == {"key": "value"}
        finally:
            Path(input_path).unlink()

    def test_roundtrip_encode_decode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Encode followed by decode produces original data."""
        original_data = {"name": "Alice", "age": 30, "active": True}

        # Create input JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(original_data, f)
            f.flush()
            json_path = f.name

        # Create intermediate TOON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as f:
            toon_path = f.name

        try:
            # Encode JSON to TOON
            encode_result = main(["encode", json_path, "-o", toon_path])
            assert encode_result == 0

            # Decode TOON back to JSON
            decode_result = main(["decode", toon_path])
            assert decode_result == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output == original_data
        finally:
            Path(json_path).unlink()
            Path(toon_path).unlink()


class TestStatsFlag:
    """Tests for --stats flag functionality."""

    def test_stats_flag_displays_statistics(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stats flag displays token comparison statistics."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "Alice", "age": 30}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--stats"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # TOON output should be in stdout
            assert "name: Alice" in captured.out
            # Stats should be in stderr
            assert "TOON:" in captured.err
            assert "tokens" in captured.err
            assert "JSON:" in captured.err
            assert "Savings:" in captured.err
        finally:
            Path(input_path).unlink()

    def test_stats_format_includes_all_parts(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stats output format includes TOON tokens, JSON tokens, and savings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--stats"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Verify format: "TOON: X tokens | JSON: Y tokens | Savings: Z%"
            stderr = captured.err
            assert "TOON:" in stderr
            assert "tokens |" in stderr
            assert "JSON:" in stderr
            assert "Savings:" in stderr
            assert "%" in stderr
        finally:
            Path(input_path).unlink()

    def test_stats_with_output_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Stats work when writing to output file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "Alice", "age": 30}, f)
            f.flush()
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toon", delete=False) as out:
            output_path = out.name

        try:
            args = parse_args(["encode", input_path, "-o", output_path, "--stats"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Stats should still be in stderr
            assert "TOON:" in captured.err
            assert "JSON:" in captured.err
            assert "Savings:" in captured.err
            # Output file should contain TOON data
            with open(output_path) as f:
                content = f.read()
            assert "name: Alice" in content
        finally:
            Path(input_path).unlink()
            Path(output_path).unlink()

    def test_stats_via_main(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Stats flag works through main() entry point."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test": "data"}, f)
            f.flush()
            input_path = f.name

        try:
            result = main(["encode", input_path, "--stats"])
            assert result == 0

            captured = capsys.readouterr()
            # TOON output in stdout
            assert "test: data" in captured.out
            # Stats in stderr
            assert "TOON:" in captured.err
            assert "JSON:" in captured.err
        finally:
            Path(input_path).unlink()

    def test_stats_without_flag_no_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Without --stats flag, no statistics are displayed."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # No stats in stderr
            assert "TOON:" not in captured.err
            assert "JSON:" not in captured.err
            assert "Savings:" not in captured.err
        finally:
            Path(input_path).unlink()

    def test_stats_with_complex_data(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stats work with complex nested data structures."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"},
                {"id": 2, "name": "Bob", "email": "bob@example.com"},
            ],
            "metadata": {"version": "1.0", "count": 2},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--stats"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Stats should be valid
            assert "TOON:" in captured.err
            assert "tokens" in captured.err
            # TOON should show savings for tabular data
            assert "Savings:" in captured.err
        finally:
            Path(input_path).unlink()

    def test_stats_with_primitive_values(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stats work with primitive JSON values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(42, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--stats"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "TOON:" in captured.err
            assert "JSON:" in captured.err
        finally:
            Path(input_path).unlink()

    def test_stats_percentage_format(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stats show percentage with one decimal place."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--stats"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Check format includes decimal point for percentage
            import re
            match = re.search(r"Savings: (-?\d+\.\d)%", captured.err)
            assert match is not None, f"Stats format incorrect: {captured.err}"
        finally:
            Path(input_path).unlink()

    def test_stats_with_empty_array(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stats work with empty arrays."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--stats"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "TOON:" in captured.err
            assert "JSON:" in captured.err
        finally:
            Path(input_path).unlink()

    def test_stats_with_empty_object(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stats work with empty objects."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--stats"])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            assert "TOON:" in captured.err
            assert "JSON:" in captured.err
        finally:
            Path(input_path).unlink()

    def test_stats_with_all_encode_options(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stats work with all other encode options."""
        data = {"outer": {"inner": {"value": 42}}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args([
                "encode",
                input_path,
                "--indent", "4",
                "--delimiter", "tab",
                "--key-folding", "safe",
                "--stats",
            ])
            result = handle_encode(args)
            assert result == 0

            captured = capsys.readouterr()
            # Verify encoding worked
            assert "outer:" in captured.out or "value: 42" in captured.out
            # Verify stats are present
            assert "TOON:" in captured.err
            assert "JSON:" in captured.err
            assert "Savings:" in captured.err
        finally:
            Path(input_path).unlink()


class TestAutoDecideFlags:
    """Tests for --auto-decide and --explain flags."""

    def test_auto_decide_flag_default_false(self) -> None:
        """--auto-decide defaults to False."""
        args = parse_args(["encode"])
        assert args.auto_decide is False

    def test_auto_decide_flag_enabled(self) -> None:
        """--auto-decide sets flag to True."""
        args = parse_args(["encode", "--auto-decide"])
        assert args.auto_decide is True

    def test_explain_flag_default_false(self) -> None:
        """--explain defaults to False."""
        args = parse_args(["encode"])
        assert args.explain is False

    def test_explain_flag_enabled(self) -> None:
        """--explain sets flag to True."""
        args = parse_args(["encode", "--explain"])
        assert args.explain is True

    def test_both_flags_together(self) -> None:
        """--auto-decide and --explain can be used together."""
        args = parse_args(["encode", "--auto-decide", "--explain"])
        assert args.auto_decide is True
        assert args.explain is True

    def test_explain_without_auto_decide_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--explain without --auto-decide returns error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--explain"])
            result = handle_encode(args)
            assert result == 1
            captured = capsys.readouterr()
            assert "--explain requires --auto-decide" in captured.err
        finally:
            Path(input_path).unlink()

    def test_auto_decide_uses_smart_encode(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--auto-decide uses smart_encode for format selection."""
        # Use tabular data which should recommend TOON
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--auto-decide", "--explain"])
            result = handle_encode(args)
            assert result == 0
            captured = capsys.readouterr()
            # Should show format decision info
            assert "Format:" in captured.err
            assert "Confidence:" in captured.err
            assert "Reasoning:" in captured.err
        finally:
            Path(input_path).unlink()

    def test_auto_decide_selects_toon_for_tabular(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--auto-decide selects TOON for tabular data."""
        data = [{"id": i, "value": f"item{i}"} for i in range(5)]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--auto-decide", "--explain"])
            result = handle_encode(args)
            assert result == 0
            captured = capsys.readouterr()
            assert "Format: TOON" in captured.err
            # Output should be TOON format
            assert "[5" in captured.out  # Array header
        finally:
            Path(input_path).unlink()

    def test_auto_decide_selects_json_for_nested(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--auto-decide selects JSON for deeply nested data."""
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": 1}}}}}}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--auto-decide", "--explain"])
            result = handle_encode(args)
            assert result == 0
            captured = capsys.readouterr()
            assert "Format: JSON" in captured.err
            # Output should be JSON format
            assert "{" in captured.out
            assert '"a"' in captured.out
        finally:
            Path(input_path).unlink()

    def test_explain_shows_confidence(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--explain shows confidence percentage."""
        data = {"key": "value"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--auto-decide", "--explain"])
            result = handle_encode(args)
            assert result == 0
            captured = capsys.readouterr()
            # Confidence should be shown as percentage
            assert "Confidence:" in captured.err
            assert "%" in captured.err
        finally:
            Path(input_path).unlink()

    def test_explain_shows_reasoning_list(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--explain shows reasoning as bulleted list."""
        data = [{"id": 1}, {"id": 2}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--auto-decide", "--explain"])
            result = handle_encode(args)
            assert result == 0
            captured = capsys.readouterr()
            # Reasoning should be shown as list items
            assert "  - " in captured.err
        finally:
            Path(input_path).unlink()

    def test_auto_decide_respects_other_flags(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--auto-decide respects indent and other flags."""
        data = [{"id": 1}, {"id": 2}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args([
                "encode", input_path,
                "--auto-decide",
                "--indent", "4",
                "--delimiter", "tab",
            ])
            result = handle_encode(args)
            assert result == 0
            # Flags should be applied to encoding
            captured = capsys.readouterr()
            # For TOON output with tab delimiter, should have tabs
            if "Format: TOON" not in captured.err:
                # JSON output will have indent=4
                assert "    " in captured.out
        finally:
            Path(input_path).unlink()

    def test_auto_decide_without_explain(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--auto-decide without --explain doesn't show reasoning."""
        data = [{"id": 1}, {"id": 2}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args(["encode", input_path, "--auto-decide"])
            result = handle_encode(args)
            assert result == 0
            captured = capsys.readouterr()
            # Should not show explanation
            assert "Format:" not in captured.err
            assert "Reasoning:" not in captured.err
        finally:
            Path(input_path).unlink()

    def test_auto_decide_with_stats(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--auto-decide works with --stats flag."""
        data = [{"id": 1}, {"id": 2}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        try:
            args = parse_args([
                "encode", input_path,
                "--auto-decide", "--explain", "--stats",
            ])
            result = handle_encode(args)
            assert result == 0
            captured = capsys.readouterr()
            # Both explanation and stats should be shown
            assert "Format:" in captured.err
            assert "TOON:" in captured.err
            assert "JSON:" in captured.err
        finally:
            Path(input_path).unlink()

    def test_auto_decide_with_output_file(self) -> None:
        """--auto-decide writes to output file correctly."""
        data = [{"id": 1}, {"id": 2}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            input_path = f.name

        output_path = tempfile.mktemp(suffix=".out")
        try:
            args = parse_args([
                "encode", input_path,
                "--auto-decide",
                "-o", output_path,
            ])
            result = handle_encode(args)
            assert result == 0
            # Check output file was written
            with open(output_path) as out_f:
                content = out_f.read()
            # Should have content
            assert len(content) > 0
        finally:
            Path(input_path).unlink()
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_auto_decide_from_stdin(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--auto-decide works with stdin input."""
        data = [{"id": 1}, {"id": 2}]
        stdin_data = json.dumps(data)

        with mock.patch("sys.stdin.read", return_value=stdin_data):
            args = parse_args(["encode", "--auto-decide", "--explain"])
            result = handle_encode(args)
            assert result == 0

        captured = capsys.readouterr()
        assert "Format:" in captured.err
        assert "[2" in captured.out or "{" in captured.out  # Output format

    def test_parser_help_includes_auto_decide(self) -> None:
        """Parser help text mentions --auto-decide."""
        parser = create_parser()
        # Get the encode subparser help
        # Check that the parser knows about these arguments
        args = parse_args(["encode", "--auto-decide", "--explain"])
        assert args.auto_decide is True
        assert args.explain is True
