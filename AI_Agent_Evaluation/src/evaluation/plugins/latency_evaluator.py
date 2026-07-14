"""
Latency Evaluator Plugin (Placeholder)
=======================================

Measures agent response time and evaluates it against configurable
thresholds. This is a performance evaluator that checks whether the
agent responds within acceptable time limits.

Configuration:
    - ``max_latency_ms``: Hard fail threshold (default: 5000ms).
    - ``warn_latency_ms``: Warning threshold (default: 2000ms).

Scoring:
    - score = 1.0 if latency < warn_latency_ms
    - score = 0.5 if warn_latency_ms <= latency < max_latency_ms
    - score = 0.0 if latency >= max_latency_ms (fail)
"""

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator


@register_evaluator("latency")
class LatencyEvaluator(BaseEvaluator):
    """
    Response time threshold evaluator.

    Scores agent responses based on how quickly they were returned.

    Attributes:
        evaluator_name: ``"latency"``
        max_latency_ms: Hard failure threshold in milliseconds.
        warn_latency_ms: Warning threshold in milliseconds.
    """

    evaluator_name = "latency"

    def __init__(self, max_latency_ms: float = 5000, warn_latency_ms: float = 2000) -> None:
        self.max_latency_ms = max_latency_ms
        self.warn_latency_ms = warn_latency_ms

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        """
        Evaluate agent response latency against thresholds.

        Args:
            test_case: The test case (unused for latency evaluation).
            agent_output: Contains ``latency_ms`` measurement.

        Returns:
            EvaluationResult with latency score and threshold details.
        """
        latency = agent_output.latency_ms

        if latency < self.warn_latency_ms:
            score = 1.0
            passed = True
            explanation = f"Latency {latency:.0f}ms is within acceptable range (< {self.warn_latency_ms:.0f}ms)."
        elif latency < self.max_latency_ms:
            score = 0.5
            passed = True
            explanation = f"Latency {latency:.0f}ms exceeds warning threshold ({self.warn_latency_ms:.0f}ms) but is within max ({self.max_latency_ms:.0f}ms)."
        else:
            score = 0.0
            passed = False
            explanation = f"Latency {latency:.0f}ms exceeds maximum threshold ({self.max_latency_ms:.0f}ms)."

        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=passed,
            explanation=explanation,
            details={
                "latency_ms": latency,
                "max_latency_ms": self.max_latency_ms,
                "warn_latency_ms": self.warn_latency_ms,
            },
        )

    def get_info(self) -> EvaluatorInfo:
        """Return metadata about this evaluator."""
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Measures agent response time and evaluates against configurable latency thresholds.",
            category=EvaluatorCategory.PERFORMANCE,
            supported_agent_types=["*"],
            requires_expected_output=False,
            requires_context=False,
        )
