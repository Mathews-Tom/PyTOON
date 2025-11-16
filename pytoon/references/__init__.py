"""Reference support module for relational data and circular references.

This module provides reference detection, encoding, and decoding capabilities
for PyToon, enabling support for relational data (v1.1) and circular references (v1.2).

Key Components:
    - ReferenceInfo: Dataclass containing detected reference information
    - ReferenceEncoder: Encoder that tracks shared objects and generates schemas
    - ReferenceDecoder: Decoder that resolves reference IDs to objects
    - GraphEncoder: Encoder for circular reference normalization (v1.2)
    - GraphDecoder: Decoder for graph reconstruction (v1.2)
"""

from pytoon.references.decoder import ReferenceDecoder
from pytoon.references.encoder import ReferenceEncoder, ReferenceInfo
from pytoon.references.graph import GraphDecoder, GraphEncoder

__all__ = [
    "GraphDecoder",
    "GraphEncoder",
    "ReferenceDecoder",
    "ReferenceEncoder",
    "ReferenceInfo",
]
