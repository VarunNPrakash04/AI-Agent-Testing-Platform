"""
Business Rule Evaluator Plugin
==============================

Custom evaluator for domain-specific business rules using a declarative approach.

Logic:
    - Reads rules from `test_case.metadata["business_rules"]`.
    - Expected format: list of dicts: `[{"field": "metrics", "condition": "exists"}, ...]`
    - Conditions supported:
        - `exists`: Check if a key exists in the output dictionary.
        - `not_empty`: Check if a field exists and is "truthy".
"""

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator


@register_evaluator("business_rules")
class BusinessRuleEvaluator(BaseEvaluator):
    """
    Deterministic declarative business rule evaluator.
    """

    evaluator_name = "business_rules"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        """
        Evaluate agent output against business rules defined in metadata.

        Args:
            test_case: Contains `metadata["business_rules"]`.
            agent_output: The agent's response to validate.

        Returns:
            EvaluationResult with aggregated business rule scores.
        """
        rules = test_case.metadata.get("business_rules", [])
        if not rules:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="No business_rules defined in test case metadata.",
            )

        if not isinstance(agent_output.output, dict):
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent output must be a dictionary to evaluate business rules.",
            )

        passed_count = 0
        details = []

        for rule in rules:
            field = rule.get("field")
            condition = rule.get("condition")
            
            rule_passed = False
            msg = ""
            
            if not field or not condition:
                msg = "Invalid rule format (missing field or condition)"
            else:
                if condition == "exists":
                    rule_passed = field in agent_output.output
                    msg = f"Field '{field}' exists" if rule_passed else f"Field '{field}' missing"
                elif condition == "not_empty":
                    val = agent_output.output.get(field)
                    rule_passed = bool(val)
                    msg = f"Field '{field}' is not empty" if rule_passed else f"Field '{field}' is missing or empty"
                else:
                    msg = f"Unknown condition: {condition}"
            
            if rule_passed:
                passed_count += 1
            details.append({"rule": rule, "passed": rule_passed, "message": msg})

        total_rules = len(rules)
        score = passed_count / total_rules if total_rules > 0 else 0.0
        
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=(score == 1.0),
            explanation=f"{passed_count}/{total_rules} business rules passed.",
            details={"rule_evaluations": details},
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Declarative business rules engine supporting 'exists' and 'not_empty' field checks.",
            category=EvaluatorCategory.RULE_BASED,
            supported_agent_types=["*"],
            requires_expected_output=False,
            requires_context=False,
        )
