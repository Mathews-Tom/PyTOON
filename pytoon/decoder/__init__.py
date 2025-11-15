"""Decoder module for TOON format parsing.

This module provides components for parsing TOON-formatted strings back into
Python objects through lexical analysis, syntax parsing, and validation.

Components:
    - StateMachine: Manages parser state transitions and indentation stack
    - Lexer: Tokenizes TOON input into token stream (coming soon)
    - Parser: Builds hierarchical Python objects (coming soon)
    - Validator: Enforces TOON v1.5 spec rules (coming soon)
    - PathExpander: Reverses key folding (coming soon)
"""

from pytoon.decoder.statemachine import ParserState, StateMachine

__all__ = [
    "ParserState",
    "StateMachine",
]
