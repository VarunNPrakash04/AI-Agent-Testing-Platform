from typing import Annotated
from fastapi import APIRouter, Depends

from src.api.dependencies import get_evaluator_registry
from src.core.models import EvaluatorInfo
from src.evaluation.registry import EvaluatorRegistry

router = APIRouter(prefix="/evaluators", tags=["Evaluators"])


@router.get("", response_model=list[EvaluatorInfo])
def list_evaluators(
    registry: Annotated[EvaluatorRegistry, Depends(get_evaluator_registry)],
    agent_type: str | None = None,
):
    if agent_type:
        names = registry.get_for_agent_type(agent_type)
        return [registry.get(name)().get_info() for name in names]
    return registry.list_evaluator_info()


@router.get("/{name}", response_model=EvaluatorInfo)
def get_evaluator(
    name: str,
    registry: Annotated[EvaluatorRegistry, Depends(get_evaluator_registry)],
):
    cls = registry.get(name)
    return cls().get_info()
