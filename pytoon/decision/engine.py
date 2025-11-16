"""DecisionEngine class for intelligent format selection.

This module provides the core decision-making logic for recommending
optimal serialization formats based on data structure analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pytoon.decision.metrics import DataMetrics


@dataclass(frozen=True)
class FormatDecision:
    """Container for format recommendation with confidence and reasoning.

    Attributes:
        recommended_format: Suggested format ('toon', 'json', 'graph', 'hybrid').
        confidence: Confidence score from 0.0 to 1.0.
        reasoning: List of explanations for the decision.
        metrics: DataMetrics used to make the decision.

    Examples:
        >>> from pytoon.decision.engine import DecisionEngine
        >>> engine = DecisionEngine()
        >>> decision = engine.analyze({"users": [{"id": 1}, {"id": 2}]})
        >>> decision.recommended_format
        'toon'
        >>> decision.confidence
        0.9
        >>> "High uniformity" in str(decision.reasoning)
        True
    """

    recommended_format: Literal["toon", "json", "graph", "hybrid"]
    confidence: float
    reasoning: list[str]
    metrics: DataMetrics


class DecisionEngine:
    """Analyzes data structure and recommends optimal serialization format.

    The DecisionEngine uses heuristics based on structural metrics to
    determine whether TOON, JSON, graph, or hybrid format is most appropriate.

    Heuristics:
        - Depth > 6 levels: favor JSON (complex nesting)
        - Uniformity > 70%: strongly favor TOON (tabular data)
        - Uniformity < 30%: favor JSON (heterogeneous data)
        - Reference density > 20%: recommend graph format

    Examples:
        >>> from pytoon.decision.engine import DecisionEngine
        >>> engine = DecisionEngine()

        >>> # Tabular data -> TOON
        >>> decision = engine.analyze([{"id": 1}, {"id": 2}])
        >>> decision.recommended_format
        'toon'

        >>> # Deeply nested -> JSON
        >>> deep = {"a": {"b": {"c": {"d": {"e": {"f": {"g": 1}}}}}}}
        >>> decision = engine.analyze(deep)
        >>> decision.recommended_format
        'json'
    """

    # Threshold constants
    MAX_FAVORABLE_DEPTH = 6
    HIGH_UNIFORMITY_THRESHOLD = 70.0
    LOW_UNIFORMITY_THRESHOLD = 30.0
    HIGH_REFERENCE_DENSITY_THRESHOLD = 20.0

    def analyze(self, data: Any) -> FormatDecision:
        """Analyze data structure and recommend optimal format.

        Args:
            data: Any Python object to analyze.

        Returns:
            FormatDecision with recommended format, confidence, and reasoning.

        Examples:
            >>> engine = DecisionEngine()

            >>> # Highly uniform data -> TOON with high confidence
            >>> data = [{"id": i, "name": f"Item {i}"} for i in range(10)]
            >>> decision = engine.analyze(data)
            >>> decision.recommended_format
            'toon'
            >>> decision.confidence > 0.8
            True

            >>> # Complex nested structure -> JSON
            >>> data = {"a": {"b": {"c": {"d": {"e": {"f": {"g": 1}}}}}}}
            >>> decision = engine.analyze(data)
            >>> decision.recommended_format
            'json'
        """
        metrics = DataMetrics.analyze(data)
        reasoning: list[str] = []
        scores: dict[str, float] = {
            "toon": 0.5,  # Base score (neutral)
            "json": 0.5,
            "graph": 0.0,
            "hybrid": 0.0,
        }

        # Analyze depth
        self._analyze_depth(metrics, scores, reasoning)

        # Analyze uniformity
        self._analyze_uniformity(metrics, scores, reasoning)

        # Analyze reference density
        self._analyze_reference_density(metrics, scores, reasoning)

        # Analyze data size
        self._analyze_data_size(metrics, scores, reasoning)

        # Determine recommended format
        recommended_format = self._determine_format(scores)

        # Calculate confidence
        confidence = self._calculate_confidence(scores, recommended_format)

        # Add summary reasoning
        self._add_summary_reasoning(metrics, reasoning, recommended_format)

        return FormatDecision(
            recommended_format=recommended_format,
            confidence=confidence,
            reasoning=reasoning,
            metrics=metrics,
        )

    def _analyze_depth(
        self,
        metrics: DataMetrics,
        scores: dict[str, float],
        reasoning: list[str],
    ) -> None:
        """Analyze nesting depth and adjust scores.

        Args:
            metrics: Computed data metrics.
            scores: Score dictionary to update.
            reasoning: Reasoning list to append to.
        """
        if metrics.max_depth > self.MAX_FAVORABLE_DEPTH:
            scores["json"] += 0.3
            scores["toon"] -= 0.2
            reasoning.append(
                f"Deep nesting ({metrics.max_depth} levels) favors JSON over TOON"
            )
        elif metrics.max_depth <= 3:
            scores["toon"] += 0.1
            reasoning.append(f"Shallow structure ({metrics.max_depth} levels) suits TOON")
        else:
            reasoning.append(f"Moderate nesting depth ({metrics.max_depth} levels)")

    def _analyze_uniformity(
        self,
        metrics: DataMetrics,
        scores: dict[str, float],
        reasoning: list[str],
    ) -> None:
        """Analyze array uniformity and adjust scores.

        Args:
            metrics: Computed data metrics.
            scores: Score dictionary to update.
            reasoning: Reasoning list to append to.
        """
        if metrics.uniformity_score >= self.HIGH_UNIFORMITY_THRESHOLD:
            scores["toon"] += 0.4
            scores["json"] -= 0.2
            reasoning.append(
                f"High uniformity ({metrics.uniformity_score:.1f}%) strongly favors TOON"
            )
        elif metrics.uniformity_score < self.LOW_UNIFORMITY_THRESHOLD:
            scores["json"] += 0.2
            scores["toon"] -= 0.1
            reasoning.append(
                f"Low uniformity ({metrics.uniformity_score:.1f}%) favors JSON"
            )
        elif metrics.uniformity_score > 0:
            scores["toon"] += 0.1
            reasoning.append(
                f"Moderate uniformity ({metrics.uniformity_score:.1f}%)"
            )

        # Tabular eligibility bonus
        if metrics.tabular_eligibility > 0:
            bonus = min(0.2, metrics.tabular_eligibility * 0.05)
            scores["toon"] += bonus
            reasoning.append(
                f"{metrics.tabular_eligibility} array(s) eligible for tabular encoding"
            )

    def _analyze_reference_density(
        self,
        metrics: DataMetrics,
        scores: dict[str, float],
        reasoning: list[str],
    ) -> None:
        """Analyze reference density and adjust scores.

        Args:
            metrics: Computed data metrics.
            scores: Score dictionary to update.
            reasoning: Reasoning list to append to.
        """
        if metrics.reference_density > self.HIGH_REFERENCE_DENSITY_THRESHOLD:
            scores["graph"] += 0.5
            scores["toon"] -= 0.1
            reasoning.append(
                f"High reference density ({metrics.reference_density:.1f}%) recommends graph format"
            )
        elif metrics.reference_density > 0:
            scores["graph"] += metrics.reference_density / 100.0
            reasoning.append(
                f"Some shared references detected ({metrics.reference_density:.1f}%)"
            )

    def _analyze_data_size(
        self,
        metrics: DataMetrics,
        scores: dict[str, float],
        reasoning: list[str],
    ) -> None:
        """Analyze data size characteristics.

        Args:
            metrics: Computed data metrics.
            scores: Score dictionary to update.
            reasoning: Reasoning list to append to.
        """
        # Large datasets benefit more from TOON compression
        if metrics.value_count > 1000:
            scores["toon"] += 0.1
            reasoning.append(
                f"Large dataset ({metrics.value_count} values) benefits from TOON compression"
            )
        elif metrics.value_count < 10:
            reasoning.append(f"Small dataset ({metrics.value_count} values)")

    def _determine_format(
        self, scores: dict[str, float]
    ) -> Literal["toon", "json", "graph", "hybrid"]:
        """Determine the recommended format from scores.

        Args:
            scores: Dictionary of format scores.

        Returns:
            The format with the highest score.
        """
        # Get format with highest score
        best_format = max(scores.keys(), key=lambda k: scores[k])

        # Check if hybrid is warranted (close scores between toon and json)
        toon_score = scores["toon"]
        json_score = scores["json"]
        graph_score = scores["graph"]

        # If graph score is highest, recommend graph
        if graph_score > toon_score and graph_score > json_score:
            return "graph"

        # If toon and json are very close, consider hybrid
        if abs(toon_score - json_score) < 0.1 and toon_score > 0.4 and json_score > 0.4:
            return "hybrid"

        # Cast to literal type
        if best_format == "toon":
            return "toon"
        elif best_format == "json":
            return "json"
        elif best_format == "graph":
            return "graph"
        else:
            return "hybrid"

    def _calculate_confidence(
        self, scores: dict[str, float], recommended_format: str
    ) -> float:
        """Calculate confidence score for the recommendation.

        Args:
            scores: Dictionary of format scores.
            recommended_format: The selected format.

        Returns:
            Confidence score from 0.0 to 1.0.
        """
        # Normalize the recommended format's score
        recommended_score = scores[recommended_format]

        # Get second highest score
        other_scores = [s for f, s in scores.items() if f != recommended_format]
        second_best = max(other_scores) if other_scores else 0.0

        # Confidence is based on margin over second best
        margin = recommended_score - second_best

        # Base confidence from the score itself (normalized to 0-1)
        base_confidence = min(1.0, max(0.0, recommended_score))

        # Boost confidence based on margin
        margin_boost = min(0.3, margin * 0.5)

        confidence = min(1.0, base_confidence + margin_boost)

        # Ensure reasonable bounds
        return max(0.1, min(1.0, confidence))

    def _add_summary_reasoning(
        self,
        metrics: DataMetrics,
        reasoning: list[str],
        recommended_format: str,
    ) -> None:
        """Add summary reasoning to the decision.

        Args:
            metrics: Computed data metrics.
            reasoning: Reasoning list to append to.
            recommended_format: The selected format.
        """
        summary = f"Recommendation: {recommended_format.upper()} format"

        if recommended_format == "toon":
            if metrics.uniformity_score >= self.HIGH_UNIFORMITY_THRESHOLD:
                summary += " (optimal for uniform tabular data)"
            else:
                summary += " (good balance of structure and compression)"
        elif recommended_format == "json":
            if metrics.max_depth > self.MAX_FAVORABLE_DEPTH:
                summary += " (better for complex nested structures)"
            else:
                summary += " (suitable for heterogeneous data)"
        elif recommended_format == "graph":
            summary += " (optimal for data with circular references)"
        else:  # hybrid
            summary += " (mixed data characteristics)"

        reasoning.append(summary)
