"""
Evaluation Engine
=================

The evaluation engine dispatches test case results to selected evaluators
and collects their scores. It acts as a mediator between the execution
engine and the evaluator plugins.

Responsibility:
    - Instantiate selected evaluators from the registry.
    - Run each evaluator against a (test_case, agent_output) pair.
    - Aggregate results into a list of ``EvaluationResult`` objects.
    - Handle evaluator failures gracefully (log and continue).
"""

import logging
from typing import Any

from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, TestCase
from src.evaluation.registry import EvaluatorRegistry

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """
    Dispatches evaluation tasks to registered evaluator plugins.

    The evaluation engine is instantiated with a reference to the
    evaluator registry and orchestrates the evaluation of agent outputs
    against test cases using user-selected evaluators.

    Args:
        registry: The evaluator registry to look up evaluator classes.
    """

    def __init__(self, registry: EvaluatorRegistry) -> None:
        self._registry = registry

    def evaluate(
        self,
        test_case: TestCase,
        agent_output: AgentOutput,
        evaluator_names: list[str],
        evaluator_configs: dict[str, dict[str, Any]] | None = None,
        agent_config: Any | None = None,
    ) -> list[EvaluationResult]:
        """
        Run all selected evaluators on a single test case result.

        Each evaluator is instantiated, optionally configured, and then
        called with the test case and agent output. If an evaluator fails,
        the error is logged and a failed ``EvaluationResult`` is returned
        for that evaluator (fail-open, not fail-fast).

        Args:
            test_case: The test case that was executed.
            agent_output: The agent's captured response.
            evaluator_names: List of evaluator names to run.
            evaluator_configs: Optional per-evaluator config overrides.
            agent_config: The agent's configuration for capability checks.

        Returns:
            List of ``EvaluationResult`` objects, one per evaluator.
        """
        results: list[EvaluationResult] = []
        configs = evaluator_configs or {}

        for name in evaluator_names:
            if name == "ragas":
                if not agent_config or not getattr(agent_config, "supports_rag", False):
                    results.append(
                        EvaluationResult(
                            evaluator_name=name,
                            score=0.0,
                            passed=False,
                            explanation="RAGAS evaluation skipped: Agent is not RAG-enabled.",
                        )
                    )
                    continue

            try:
                evaluator_cls = self._registry.get(name)
                evaluator: BaseEvaluator = evaluator_cls()

                # Validate evaluator config if provided
                eval_config = configs.get(name, {})
                if eval_config:
                    evaluator.validate_config(eval_config)

                # Run evaluation
                result = evaluator.evaluate(test_case, agent_output)
                results.append(result)

                logger.debug(
                    "Evaluator '%s' scored %.2f (passed=%s) for test '%s'",
                    name,
                    result.score,
                    result.passed,
                    test_case.test_id,
                )

            except Exception as e:
                logger.error(
                    "Evaluator '%s' failed for test '%s': %s",
                    name,
                    test_case.test_id,
                    str(e),
                )
                results.append(
                    EvaluationResult(
                        evaluator_name=name,
                        score=0.0,
                        passed=False,
                        explanation=f"Evaluator error: {str(e)}",
                    )
                )

        return results
