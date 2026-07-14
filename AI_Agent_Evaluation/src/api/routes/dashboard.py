from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import get_history_manager, get_test_case_manager
from src.history.manager import HistoryManager
from src.testcases.manager import TestCaseManager
from src.core.models import DashboardOverview, DashboardStats, RunSummary, RunStatus
from src.agents.registry import AgentRegistry
from src.api.dependencies import get_agent_registry

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def dashboard_overview(
    history_manager: Annotated[HistoryManager, Depends(get_history_manager)],
    test_case_manager: Annotated[TestCaseManager, Depends(get_test_case_manager)],
    agent_registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
):
    runs = history_manager.list_runs()
    suites = test_case_manager.list_suites()
    agents = agent_registry.list_agents(active_only=True)

    completed_runs = [run for run in runs if run.status == RunStatus.COMPLETED]
    failed_runs = [run for run in runs if run.status in {RunStatus.FAILED, RunStatus.PARTIAL_FAILURE}]

    avg_score = sum(run.overall_score for run in completed_runs) / len(completed_runs) if completed_runs else 0.0
    avg_latency = 0.0
    success_rate = (len(completed_runs) / len(runs) * 100.0) if runs else 0.0

    framework_breakdown: dict[str, int] = {}
    for run in runs:
        framework = "deepeval"
        framework_breakdown[framework] = framework_breakdown.get(framework, 0) + 1

    return DashboardOverview(
        stats=DashboardStats(
            total_agents=len(agents),
            total_runs=len(runs),
            total_datasets=len(suites),
            average_evaluation_score=avg_score,
            average_latency_ms=avg_latency,
            success_rate=success_rate,
            failed_runs=len(failed_runs),
        ),
        recent_runs=runs[:5],
        framework_breakdown=framework_breakdown,
    )
