"""Decoder module for TOON format parsing.

This module provides components for parsing TOON-formatted strings back into
Python objects through lexical analysis, syntax parsing, and validation.

Components:
    - StateMachine: Manages parser state transitions and indentation stack
    - Lexer: Tokenizes TOON input into token stream
    - Parser: Builds hierarchical Python objects
    - Validator: Enforces TOON v1.5 spec rules
    - PathExpander: Reverses key folding
"""

from pytoon.decoder.lexer import Lexer, Token, TokenType
from pytoon.decoder.parser import Parser
from pytoon.decoder.pathexpander import PathExpander
from pytoon.decoder.statemachine import ParserState, StateMachine
from pytoon.decoder.validator import ValidationWarning, Validator

__all__ = [
    "Lexer",
    "Parser",
    "ParserState",
    "PathExpander",
    "StateMachine",
    "Token",
    "TokenType",
    "ValidationWarning",
    "Validator",
]
