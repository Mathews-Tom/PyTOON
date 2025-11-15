"""PyToon core module - central entry point for TOON operations.

This module provides the Encoder and Decoder classes for TOON format
conversion, along with the TOONSpec class containing specification constants.
"""

from pytoon.core.decoder import Decoder
from pytoon.core.encoder import Encoder
from pytoon.core.spec import TOONSpec

__all__: list[str] = [
    "TOONSpec",
    "Encoder",
    "Decoder",
]
