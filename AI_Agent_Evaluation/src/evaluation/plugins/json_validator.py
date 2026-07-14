"""
JSON Validator Evaluator Plugin
===============================

Validates that the agent's response conforms to the expected JSON schema.

Logic:
    - Extracts the target schema from `test_case.metadata["output_schema"]`.
    - If no schema is found, it will fail gracefully or skip.
    - Uses `jsonschema` to validate the output structure.
"""

import jsonschema
from jsonschema.exceptions import ValidationError

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator


@register_evaluator("json_validator")
class JsonValidatorEvaluator(BaseEvaluator):
    """
    JSON schema validation evaluator.

    Validates agent output structure against a JSON Schema.
    """

    evaluator_name = "json_validator"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        """
        Validate agent output against JSON schema.

        Args:
            test_case: Test case containing `metadata["output_schema"]`.
            agent_output: The agent's response to validate.

        Returns:
            EvaluationResult indicating schema compliance.
        """
        schema = test_case.metadata.get("output_schema")
        if not schema:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="No output_schema provided in test_case.metadata.",
            )

        if not agent_output.output:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent returned no output.",
            )

        try:
            jsonschema.validate(instance=agent_output.output, schema=schema)
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=1.0,
                passed=True,
                explanation="Output successfully validates against the JSON schema.",
            )
        except ValidationError as e:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation=f"Schema validation failed: {e.message}",
                details={"schema_path": list(e.schema_path), "failed_value": e.instance}
            )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Validates agent response structure against the JSON schema defined in test case metadata.",
            category=EvaluatorCategory.SCHEMA,
            supported_agent_types=["*"],
            requires_expected_output=False,
            requires_context=False,
        )
