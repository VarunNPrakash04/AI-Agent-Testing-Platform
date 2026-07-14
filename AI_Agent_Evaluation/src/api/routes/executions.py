from typing import Annotated
from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_execution_engine, get_history_manager
from src.core.models import ExecutionRunResult, RunConfig, RunSummary
from src.execution.engine import ExecutionEngine
from src.history.manager import HistoryManager

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.post("", response_model=ExecutionRunResult, status_code=status.HTTP_201_CREATED)
def execute_run(
    run_config: RunConfig,
    engine: Annotated[ExecutionEngine, Depends(get_execution_engine)],
):
    return engine.execute_run(run_config)


@router.get("", response_model=list[RunSummary])
def list_runs(
    manager: Annotated[HistoryManager, Depends(get_history_manager)],
    agent_id: str | None = None,
):
    return manager.list_runs(agent_id=agent_id)


@router.get("/{run_id}", response_model=ExecutionRunResult)
def get_run(
    run_id: str,
    manager: Annotated[HistoryManager, Depends(get_history_manager)],
):
    return manager.get_run(run_id)
