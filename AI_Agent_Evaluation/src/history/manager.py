"""
History Manager
===============

Handles database persistence and retrieval of execution results,
and provides logic for comparing two execution runs for regression testing.
"""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from src.core.exceptions import ExecutionRunNotFoundError
from src.core.models import (
    AgentOutput,
    ComparisonResult,
    EvaluationResult,
    ExecutionRunResult,
    RunStatus,
    RunSummary,
    TestCase,
    TestCaseComparison,
    TestCaseResult,
)
from src.db.models import (
    EvaluationScoreModel,
    ExecutionResultModel,
    ExecutionRunModel,
    TestCaseModel,
)

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    CRUD and comparison operations for execution history.

    Args:
        db: SQLAlchemy session.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def save_run(self, result: ExecutionRunResult) -> None:
        """
        Persist a complete execution run to the database.

        Args:
            result: The run result to save.
        """
        run_model = ExecutionRunModel(
            id=result.run_id,
            agent_id=result.agent_id,
            suite_id=result.suite_id,
            status=result.status.value,
            started_at=result.started_at,
            completed_at=result.completed_at,
            total_tests=result.total_tests,
            passed_tests=result.passed_tests,
            failed_tests=result.failed_tests,
            overall_score=result.overall_score,
            error_message=result.error_message,
        )
        self._db.add(run_model)

        for tr in result.test_results:
            tc_result_model = ExecutionResultModel(
                run_id=result.run_id,
                test_case_id=tr.test_case.test_id,
                agent_output_json=json.dumps(tr.agent_output.output) if tr.agent_output.output else None,
                success=tr.agent_output.success,
                latency_ms=tr.agent_output.latency_ms,
                token_usage_json=json.dumps(tr.agent_output.token_usage.model_dump()) if tr.agent_output.token_usage else None,
                error_message=tr.agent_output.error,
                overall_passed=tr.overall_passed,
            )
            self._db.add(tc_result_model)
            self._db.flush()  # To get tc_result_model.id

            for er in tr.evaluation_results:
                score_model = EvaluationScoreModel(
                    result_id=tc_result_model.id,
                    evaluator_name=er.evaluator_name,
                    score=er.score,
                    passed=er.passed,
                    explanation=er.explanation,
                    details_json=json.dumps(er.details),
                )
                self._db.add(score_model)

        self._db.commit()
        logger.info("Saved execution run '%s'", result.run_id)

    def get_run(self, run_id: str) -> ExecutionRunResult:
        """
        Retrieve a complete execution run by ID.

        Milestone 1 Implementation Note:
        For simplicity in this POC, we reconstruct the run from the DB models.
        In a production system with massive runs, you might paginate or
        only load test cases on demand.
        """
        run_model = self._db.query(ExecutionRunModel).filter(ExecutionRunModel.id == run_id).first()
        if not run_model:
            raise ExecutionRunNotFoundError(run_id)

        # Retrieve test results
        tc_results = self._db.query(ExecutionResultModel).filter(ExecutionResultModel.run_id == run_id).all()
        test_results_out = []

        for tcr in tc_results:
            # We only store test_case_id in result, need to fetch actual TestCase if needed.
            # For POC, we construct a dummy TestCase with just the ID.
            dummy_tc = TestCase(test_id=tcr.test_case_id, input={})
            
            agent_out = AgentOutput(
                output=json.loads(tcr.agent_output_json) if tcr.agent_output_json else None,
                latency_ms=tcr.latency_ms,
                success=tcr.success,
                error=tcr.error_message,
            )

            scores = self._db.query(EvaluationScoreModel).filter(EvaluationScoreModel.result_id == tcr.id).all()
            eval_results = [
                EvaluationResult(
                    evaluator_name=s.evaluator_name,
                    score=s.score,
                    passed=s.passed,
                    explanation=s.explanation,
                    details=json.loads(s.details_json) if s.details_json else {},
                )
                for s in scores
            ]

            test_results_out.append(
                TestCaseResult(
                    test_case=dummy_tc,
                    agent_output=agent_out,
                    evaluation_results=eval_results,
                    overall_passed=tcr.overall_passed,
                    execution_time_ms=tcr.latency_ms,
                )
            )

        return ExecutionRunResult(
            run_id=run_model.id,
            agent_id=run_model.agent_id,
            suite_id=run_model.suite_id,
            status=RunStatus(run_model.status),
            started_at=run_model.started_at,
            completed_at=run_model.completed_at,
            total_tests=run_model.total_tests,
            passed_tests=run_model.passed_tests,
            failed_tests=run_model.failed_tests,
            test_results=test_results_out,
            overall_score=run_model.overall_score,
            error_message=run_model.error_message,
        )

    def list_runs(self, agent_id: str | None = None) -> list[RunSummary]:
        """List execution runs, optionally filtered by agent."""
        query = self._db.query(ExecutionRunModel)
        if agent_id:
            query = query.filter(ExecutionRunModel.agent_id == agent_id)
        
        runs = query.order_by(ExecutionRunModel.started_at.desc()).all()
        
        return [
            RunSummary(
                run_id=r.id,
                agent_id=r.agent_id,
                suite_id=r.suite_id,
                status=RunStatus(r.status),
                total_tests=r.total_tests,
                passed_tests=r.passed_tests,
                overall_score=r.overall_score,
                started_at=r.started_at,
                completed_at=r.completed_at,
            )
            for r in runs
        ]

    def compare_runs(self, run_id_a: str, run_id_b: str) -> ComparisonResult:
        """
        Compare test case scores between two runs (Run A -> Baseline, Run B -> New).
        """
        run_a = self.get_run(run_id_a)
        run_b = self.get_run(run_id_b)

        # Map scores by test_id
        # Simple implementation: we take the average score of all evaluators for a test case
        def get_test_scores(run: ExecutionRunResult) -> dict[str, float]:
            scores = {}
            for tr in run.test_results:
                if tr.evaluation_results:
                    avg_score = sum(er.score for er in tr.evaluation_results) / len(tr.evaluation_results)
                    scores[tr.test_case.test_id] = avg_score
                else:
                    scores[tr.test_case.test_id] = 0.0
            return scores

        scores_a = get_test_scores(run_a)
        scores_b = get_test_scores(run_b)

        comparisons = []
        improved = degraded = unchanged = 0

        # Compare matching test cases
        all_test_ids = set(scores_a.keys()).union(set(scores_b.keys()))
        
        for tid in all_test_ids:
            sa = scores_a.get(tid, 0.0)
            sb = scores_b.get(tid, 0.0)
            delta = sb - sa
            
            if delta > 0.01:
                status = "improved"
                improved += 1
            elif delta < -0.01:
                status = "degraded"
                degraded += 1
            else:
                status = "unchanged"
                unchanged += 1
                
            comparisons.append(
                TestCaseComparison(
                    test_id=tid,
                    score_a=sa,
                    score_b=sb,
                    delta=delta,
                    status=status
                )
            )

        return ComparisonResult(
            run_id_a=run_id_a,
            run_id_b=run_id_b,
            overall_score_a=run_a.overall_score,
            overall_score_b=run_b.overall_score,
            overall_delta=run_b.overall_score - run_a.overall_score,
            improved_count=improved,
            degraded_count=degraded,
            unchanged_count=unchanged,
            comparisons=comparisons,
        )
