"""
Security Evaluator Plugin (Placeholder)
========================================

Extension point for security-focused evaluations. Future implementations
will include:

    - **Prompt Injection Detection**: Check if agent outputs contain
      injected instructions or bypass attempts.
    - **PII Detection**: Scan agent responses for personally identifiable
      information that should not be exposed.
    - **Guardrails Compliance**: Verify agent behavior against safety
      policies and content guidelines.

This is an explicit extensibility placeholder as specified in the PRD.
"""

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator


@register_evaluator("security")
class SecurityEvaluator(BaseEvaluator):
    """
    Security evaluation placeholder.

    Milestone 1: Returns placeholder scores.
    Milestone 3+: Will implement prompt injection detection,
    PII scanning, and guardrails compliance checks.

    Attributes:
        evaluator_name: ``"security"``
    """

    evaluator_name = "security"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        """
        Run security evaluations on agent output.

        TODO (Milestone 3): Implement security checks.

        Args:
            test_case: The test case.
            agent_output: The agent's response to scan.

        Returns:
            EvaluationResult with security scan findings.
        """
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=0.0,
            passed=False,
            explanation="Security evaluator not yet implemented. Placeholder score.",
            details={"status": "placeholder", "milestone": 3, "checks": []},
        )

    def get_info(self) -> EvaluatorInfo:
        """Return metadata about this evaluator."""
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Security checks: prompt injection detection, PII scanning, guardrails compliance (future).",
            category=EvaluatorCategory.SECURITY,
            supported_agent_types=["*"],
            requires_expected_output=False,
            requires_context=False,
        )
