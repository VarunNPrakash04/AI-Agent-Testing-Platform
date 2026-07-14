from typing import Annotated
from fastapi import APIRouter, Depends

from src.api.dependencies import get_history_manager
from src.core.models import ComparisonResult, RunSummary
from src.history.manager import HistoryManager

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/{agent_id}", response_model=list[RunSummary])
def get_agent_history(
    agent_id: str,
    manager: Annotated[HistoryManager, Depends(get_history_manager)],
):
    return manager.list_runs(agent_id=agent_id)


@router.get("/compare/{run_id_a}/{run_id_b}", response_model=ComparisonResult)
def compare_runs(
    run_id_a: str,
    run_id_b: str,
    manager: Annotated[HistoryManager, Depends(get_history_manager)],
):
    return manager.compare_runs(run_id_a, run_id_b)
