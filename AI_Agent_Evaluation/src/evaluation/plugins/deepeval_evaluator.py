"""
DeepEval Evaluator Plugin
=========================

Evaluates output using a combination of heuristics and rules. 
Checks for:
- Exact match with expected output
- Answer length and completeness
- No errors in agent output

This is a working baseline implementation. In production, this would integrate
with the DeepEval library for LLM-based evaluation.
"""

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator


@register_evaluator("deepeval")
class DeepEvalEvaluator(BaseEvaluator):
    """
    DeepEval-style evaluator using heuristics.

    Evaluates based on:
    - Agent output success
    - Expected output match (if provided)
    - Answer completeness
    """

    evaluator_name = "deepeval"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        """
        Evaluate using heuristic scoring.

        Scoring logic:
        - Start at 0.8 if agent succeeded
        - Add 0.2 for exact match with expected_output (if provided)
        - Subtract points for missing/empty output

        Args:
            test_case: The test case with expected output and context.
            agent_output: The agent's response.

        Returns:
            EvaluationResult with DeepEval-style scores.
        """
        score = 0.0
        explanation_parts = []

        # Check agent success
        if not agent_output.success:
            explanation = f"Agent failed: {agent_output.error}"
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation=explanation,
            )

        # Base score for successful response
        score = 0.5
        explanation_parts.append("Agent responded successfully")

        # Check if output is empty/null
        if agent_output.output is None or (isinstance(agent_output.output, str) and not agent_output.output.strip()):
            score = 0.0
            explanation_parts = ["Agent output is empty"]
        else:
            # Add points for non-empty output
            score += 0.3
            explanation_parts.append("Output is non-empty")

            # Check for exact match with expected output
            if test_case.expected_output is not None:
                if agent_output.output == test_case.expected_output:
                    score += 0.2
                    explanation_parts.append("Exact match with expected output")
                else:
                    explanation_parts.append("Output differs from expected")

        passed = score >= 0.7
        explanation = "; ".join(explanation_parts)

        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=passed,
            explanation=explanation,
            details={"scoring": "heuristic-based", "success": agent_output.success},
        )

    def supports_agent_type(self, agent_type: str) -> bool:
        """DeepEval supports all agent types."""
        return True

    def get_info(self) -> EvaluatorInfo:
        """Return metadata about this evaluator."""
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="DeepEval-style heuristic evaluation: checks success, output completeness, and expected match.",
            category=EvaluatorCategory.RULE_BASED,
            supported_agent_types=["*"],
            requires_expected_output=False,
            requires_context=False,
        )
