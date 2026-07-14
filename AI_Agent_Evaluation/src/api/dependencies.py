"""
Dependency Injection Providers
==============================

Provides all service dependencies for FastAPI routes.
Registers singletons and yields request-scoped services.
"""

from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from src.agents.registry import AgentRegistry
from src.agents.service import AgentService
from src.connectors.registry import ConnectorRegistry, connector_registry
from src.core.interfaces import BaseObservabilityLogger, BaseReportGenerator
from src.evaluation.engine import EvaluationEngine
from src.evaluation.registry import EvaluatorRegistry, evaluator_registry
from src.execution.engine import ExecutionEngine
from src.history.manager import HistoryManager
from src.observability.logger import NoOpLogger
from src.reports.generator import HTMLReportGenerator
from src.testcases.manager import TestCaseManager

# DB session generator
from src.db.database import get_db_session

# Type alias for Depends(get_db_session)
DbSession = Annotated[Session, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# Registries (Singletons)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_connector_registry() -> ConnectorRegistry:
    """Return the global connector registry singleton."""
    return connector_registry


@lru_cache(maxsize=1)
def get_evaluator_registry() -> EvaluatorRegistry:
    """Return the global evaluator registry singleton."""
    return evaluator_registry


# ---------------------------------------------------------------------------
# Core Services (Stateless Singletons)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_observability_logger() -> BaseObservabilityLogger:
    """Return the configured observability logger."""
    import os
    from src.observability.logger import LangfuseLogger, NoOpLogger
    
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST")
    
    if public_key and secret_key:
        try:
            return LangfuseLogger(public_key=public_key, secret_key=secret_key, host=host)
        except Exception:
            return NoOpLogger()
            
    return NoOpLogger()


@lru_cache(maxsize=1)
def get_report_generator() -> BaseReportGenerator:
    """Return the configured report generator."""
    return HTMLReportGenerator()


# ---------------------------------------------------------------------------
# Application Services (Request-Scoped via DB Session)
# ---------------------------------------------------------------------------


def get_agent_registry(db: DbSession) -> AgentRegistry:
    return AgentRegistry(db)


def get_history_manager(db: DbSession) -> HistoryManager:
    return HistoryManager(db)


def get_test_case_manager(db: DbSession) -> TestCaseManager:
    return TestCaseManager(db)


def get_agent_service(
    registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
    connectors: Annotated[ConnectorRegistry, Depends(get_connector_registry)],
) -> AgentService:
    return AgentService(registry, connectors)


def get_evaluation_engine(
    evaluators: Annotated[EvaluatorRegistry, Depends(get_evaluator_registry)]
) -> EvaluationEngine:
    return EvaluationEngine(evaluators)


def get_execution_engine(
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
    test_case_manager: Annotated[TestCaseManager, Depends(get_test_case_manager)],
    evaluation_engine: Annotated[EvaluationEngine, Depends(get_evaluation_engine)],
    history_manager: Annotated[HistoryManager, Depends(get_history_manager)],
    logger: Annotated[BaseObservabilityLogger, Depends(get_observability_logger)],
) -> ExecutionEngine:
    return ExecutionEngine(
        agent_service=agent_service,
        test_case_manager=test_case_manager,
        evaluation_engine=evaluation_engine,
        history_manager=history_manager,
        observability_logger=logger,
    )
