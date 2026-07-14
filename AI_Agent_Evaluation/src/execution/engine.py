"""
Execution Engine
================

The central orchestrator of the Generic AI Testing Platform.
Coordinates loading test cases, running agents, triggering evaluators,
aggregating results, and saving history.

Architecture:
    This is the mediator component in the application layer. It brings
    together the AgentService, TestCaseManager, EvaluationEngine,
    HistoryManager, and ObservabilityLogger.
"""

import logging
import uuid
from datetime import datetime, timezone

from src.agents.service import AgentService
from src.core.enums import RunStatus
from src.core.interfaces import BaseObservabilityLogger
from src.core.models import (
    ExecutionRunResult,
    RunConfig,
    TestCaseResult,
    TraceData,
)
from src.evaluation.engine import EvaluationEngine
from src.history.manager import HistoryManager
from src.testcases.manager import TestCaseManager

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Orchestrates the entire test execution workflow.

    Args:
        agent_service: For instantiating runnable agents.
        test_case_manager: For retrieving test cases.
        evaluation_engine: For dispatching evaluation tasks.
        history_manager: For saving execution results.
        observability_logger: For logging traces and metrics.
    """

    def __init__(
        self,
        agent_service: AgentService,
        test_case_manager: TestCaseManager,
        evaluation_engine: EvaluationEngine,
        history_manager: HistoryManager,
        observability_logger: BaseObservabilityLogger,
    ) -> None:
        self._agent_service = agent_service
        self._test_case_manager = test_case_manager
        self._evaluation_engine = evaluation_engine
        self._history_manager = history_manager
        self._observability_logger = observability_logger

    def execute_run(self, run_config: RunConfig) -> ExecutionRunResult:
        """
        Execute a complete test run based on the provided configuration.

        Workflow:
            1. Initialize run result record.
            2. Load test cases.
            3. Instantiate the agent.
            4. For each test case:
                a. Call agent with input.
                b. Evaluate response.
                c. Log trace.
            5. Aggregate results and calculate overall score.
            6. Save run history.

        Args:
            run_config: Configuration for the run (agent, suite, evaluators, etc.).

        Returns:
            The complete execution result.
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        logger.info("Starting execution run '%s' for agent '%s'", run_id, run_config.agent_id)

        # 1. Initialize result structure
        run_result = ExecutionRunResult(
            run_id=run_id,
            agent_id=run_config.agent_id,
            suite_id=run_config.test_suite_id,
            status=RunStatus.RUNNING,
            started_at=started_at,
        )

        try:
            # 2. Load test cases
            test_cases = self._test_case_manager.get_test_cases(run_config.test_suite_id)
            run_result.total_tests = len(test_cases)
            if not test_cases:
                run_result.status = RunStatus.COMPLETED
                run_result.completed_at = datetime.now(timezone.utc)
                self._history_manager.save_run(run_result)
                return run_result

            # 3. Instantiate agent
            agent = self._agent_service.create_runnable_agent(run_config.agent_id)

            # 4. Execute test cases
            for test_case in test_cases:
                # Execute agent
                agent_output = agent.run(test_case.input)

                # Evaluate response
                evaluation_results = self._evaluation_engine.evaluate(
                    test_case=test_case,
                    agent_output=agent_output,
                    evaluator_names=run_config.evaluator_names,
                    evaluator_configs=run_config.evaluator_configs,
                    agent_config=agent.get_config(),
                )

                # Determine overall pass/fail for this test case
                overall_passed = agent_output.success and all(er.passed for er in evaluation_results)

                test_result = TestCaseResult(
                    test_case=test_case,
                    agent_output=agent_output,
                    evaluation_results=evaluation_results,
                    overall_passed=overall_passed,
                    execution_time_ms=agent_output.latency_ms,
                )
                run_result.test_results.append(test_result)

                if overall_passed:
                    run_result.passed_tests += 1
                else:
                    run_result.failed_tests += 1

                # Log trace
                trace = TraceData(
                    trace_id=str(uuid.uuid4()),
                    run_id=run_id,
                    test_case_id=test_case.test_id,
                    input=test_case.input,
                    output=agent_output.output,
                    latency_ms=agent_output.latency_ms,
                    token_usage=agent_output.token_usage,
                    evaluation_scores=evaluation_results,
                    metadata={"overall_passed": overall_passed},
                )
                self._observability_logger.log_trace(trace)

            # 5. Aggregate results
            run_result.status = RunStatus.COMPLETED if run_result.failed_tests == 0 else RunStatus.PARTIAL_FAILURE
            
            # Simple average of all evaluation scores across all tests
            total_scores = sum(er.score for tr in run_result.test_results for er in tr.evaluation_results)
            total_evaluations = sum(len(tr.evaluation_results) for tr in run_result.test_results)
            run_result.overall_score = total_scores / total_evaluations if total_evaluations > 0 else 0.0

        except Exception as e:
            logger.error("Execution run '%s' failed: %s", run_id, str(e))
            run_result.status = RunStatus.FAILED
            run_result.error_message = str(e)

        finally:
            run_result.completed_at = datetime.now(timezone.utc)
            self._observability_logger.flush()

            # 6. Save history
            try:
                self._history_manager.save_run(run_result)
            except Exception as e:
                logger.error("Failed to save history for run '%s': %s", run_id, str(e))

        logger.info("Completed execution run '%s' with status '%s'", run_id, run_result.status)
        return run_result
