"""
Exact Match Evaluator Plugin
============================

Evaluates whether the agent's output exactly matches the expected output
provided in the test case.

Logic:
    - If expected output is not provided, skips evaluation.
    - If both actual and expected outputs are dictionaries, performs a
      deep equality check.
    - Otherwise, falls back to string comparison.
"""

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator


@register_evaluator("exact_match")
class ExactMatchEvaluator(BaseEvaluator):
    """
    Exact Match evaluator.

    Attributes:
        evaluator_name: ``"exact_match"``
    """

    evaluator_name = "exact_match"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        """
        Check if the agent output exactly matches the expected output.

        Args:
            test_case: Must include ``expected_output``.
            agent_output: The agent's response.

        Returns:
            EvaluationResult indicating pass (1.0) or fail (0.0).
        """
        expected = test_case.expected_output
        actual = agent_output.output

        if expected is None:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="No expected_output provided in test case.",
            )

        match = (actual == expected)
        
        if match:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=1.0,
                passed=True,
                explanation="Agent output exactly matches expected output.",
            )
        else:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent output does not match expected output.",
                details={"expected": expected, "actual": actual}
            )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Checks if the agent's output exactly matches the test case's expected output.",
            category=EvaluatorCategory.RULE_BASED,
            supported_agent_types=["*"],
            requires_expected_output=True,
            requires_context=False,
        )
