"""PyToon core module - central entry point for TOON operations.

This module provides the Encoder and Decoder classes for TOON format
conversion, along with the TOONSpec class containing specification constants.
"""

from pytoon.core.spec import TOONSpec

# These will be imported as they are implemented
# from pytoon.core.encoder import Encoder
# from pytoon.core.decoder import Decoder

__all__: list[str] = [
    "TOONSpec",
    # "Encoder",
    # "Decoder",
]
