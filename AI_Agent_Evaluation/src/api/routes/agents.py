from typing import Annotated
from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_agent_registry, get_agent_service
from src.agents.registry import AgentRegistry
from src.agents.service import AgentService
from src.core.models import AgentConfig, AgentRecord, AgentSummary, HealthStatus

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("", response_model=AgentRecord, status_code=status.HTTP_201_CREATED)
def register_agent(
    config: AgentConfig,
    registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
):
    return registry.register_agent(config)


@router.get("", response_model=list[AgentSummary])
def list_agents(
    registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
    active_only: bool = True,
):
    return registry.list_agents(active_only=active_only)


@router.get("/{agent_id}", response_model=AgentRecord)
def get_agent(
    agent_id: str,
    registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
):
    return registry.get_agent(agent_id)


@router.put("/{agent_id}", response_model=AgentRecord)
def update_agent(
    agent_id: str,
    config: AgentConfig,
    registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
):
    return registry.update_agent(agent_id, config)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: str,
    registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
):
    registry.delete_agent(agent_id)


@router.post("/{agent_id}/health", response_model=HealthStatus)
def check_health(
    agent_id: str,
    service: Annotated[AgentService, Depends(get_agent_service)],
):
    return service.health_check(agent_id)
