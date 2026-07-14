"""
Agent Service
=============

Business logic layer for agent operations. Sits between the API routes
and the agent registry, providing higher-level operations like agent
instantiation with the appropriate connector.

This service implements the ``BaseAgent`` interface via ``RegisteredAgent``,
which combines an ``AgentConfig`` with a ``BaseConnector`` to create a
callable agent wrapper used by the execution engine.
"""

import logging
import time
from typing import Any

from src.agents.registry import AgentRegistry
from src.connectors.registry import ConnectorRegistry
from src.core.interfaces import BaseAgent, BaseConnector
from src.core.models import AgentConfig, AgentOutput, HealthStatus

logger = logging.getLogger(__name__)


class RegisteredAgent(BaseAgent):
    """
    Default implementation of ``BaseAgent`` that wraps a configuration
    and connector pair.

    The execution engine uses this class to invoke agents. It handles
    timing measurement and error wrapping around the connector's
    ``execute()`` call.

    Args:
        config: The agent's registered configuration.
        connector: An instantiated and connected connector.
    """

    def __init__(self, config: AgentConfig, connector: BaseConnector) -> None:
        self._config = config
        self._connector = connector

    def run(self, input_data: dict[str, Any]) -> AgentOutput:
        """
        Execute the agent with the given input.

        Measures latency and wraps connector errors into the AgentOutput.

        Args:
            input_data: Test case input payload.

        Returns:
            AgentOutput with response, latency, and success status.
        """
        start_time = time.perf_counter()
        try:
            output = self._connector.execute(input_data)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            output.latency_ms = elapsed_ms
            return output
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Agent '%s' execution failed: %s", self._config.agent_name, str(e))
            return AgentOutput(
                output=None,
                latency_ms=elapsed_ms,
                success=False,
                error=str(e),
            )

    def get_config(self) -> AgentConfig:
        """Return the agent's configuration."""
        return self._config


class AgentService:
    """
    Service layer for agent operations.

    Provides methods to create runnable agent instances by combining
    registry lookups with connector instantiation.

    Args:
        agent_registry: Registry for agent CRUD operations.
        connector_registry: Registry for connector plugin lookup.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        connector_registry: ConnectorRegistry,
    ) -> None:
        self._agent_registry = agent_registry
        self._connector_registry = connector_registry

    def create_runnable_agent(self, agent_id: str) -> RegisteredAgent:
        """
        Create a runnable agent instance from a registered agent ID.

        Looks up the agent config, instantiates the appropriate connector,
        establishes the connection, and returns a ``RegisteredAgent`` wrapper.

        Args:
            agent_id: The registered agent's UUID.

        Returns:
            A ``RegisteredAgent`` ready to execute test cases.

        Raises:
            AgentNotFoundError: If the agent ID is not registered.
            ConnectorNotFoundError: If the connector type is unknown.
        """
        record = self._agent_registry.get_agent(agent_id)

        # Reconstruct AgentConfig from the record
        config = AgentConfig(
            agent_name=record.agent_name,
            description=record.description,
            agent_type=record.agent_type,
            connector_type=record.connector_type,
            endpoint=record.endpoint,
            python_class_path=record.python_class_path,
            auth_config=record.auth_config,
            input_schema=record.input_schema,
            output_schema=record.output_schema,
            supports_rag=record.supports_rag,
            supports_tool_calling=record.supports_tool_calling,
            timeout_seconds=record.timeout_seconds,
            metadata=record.metadata,
        )

        # Get and instantiate connector
        connector_cls = self._connector_registry.get(record.connector_type)
        connector: BaseConnector = connector_cls()
        connector.connect(config)

        logger.info(
            "Created runnable agent '%s' with connector '%s'",
            config.agent_name,
            record.connector_type,
        )
        return RegisteredAgent(config=config, connector=connector)

    def health_check(self, agent_id: str) -> HealthStatus:
        """
        Run a health check on a registered agent.

        Args:
            agent_id: The agent's UUID.

        Returns:
            HealthStatus with reachability information.
        """
        agent = self.create_runnable_agent(agent_id)
        return agent._connector.health_check()
