"""PyToon CLI module.

This module provides the command-line interface for TOON encoding and decoding
operations. It supports subcommands for encode/decode with configurable options.

Exports:
    main: Main CLI entry point function.
    create_parser: Create the argument parser.
"""

from pytoon.cli.main import create_parser, main

__all__ = ["main", "create_parser"]
