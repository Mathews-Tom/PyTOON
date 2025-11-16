"""Decision Engine module for intelligent format selection.

This module provides intelligent format selection analyzing data structure
to recommend optimal serialization format (TOON, JSON, graph, or hybrid).

Key Components:
    - DataMetrics: Computes structural metrics (depth, uniformity, reference density)
    - DecisionEngine: Analyzes metrics and recommends optimal format
    - FormatDecision: Contains recommendation with confidence and reasoning
"""

from pytoon.decision.engine import DecisionEngine, FormatDecision
from pytoon.decision.metrics import DataMetrics

__all__ = [
    "DataMetrics",
    "DecisionEngine",
    "FormatDecision",
]
