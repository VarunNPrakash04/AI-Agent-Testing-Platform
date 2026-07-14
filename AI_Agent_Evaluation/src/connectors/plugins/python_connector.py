"""
Python Class Connector
======================

Connector plugin for AI agents implemented as importable Python classes.

This connector loads an agent class via ``importlib`` from a dotted path
(e.g., ``my_agents.harvest.HarvestAgent``), instantiates it, and calls
its ``run()`` method with the test input.

Agent Class Contract:
    Agent classes must implement a ``run(self, input_data: dict) -> dict`` method.
    The class must be importable from the platform's Python environment
    (i.e., the package must be installed or the path must be in ``sys.path``).
"""

import importlib
import time
from typing import Any

from src.connectors.registry import register_connector
from src.core.interfaces import BaseConnector
from src.core.models import AgentConfig, AgentOutput, HealthStatus


@register_connector("python_class")
class PythonClassConnector(BaseConnector):
    """
    Connector for agents implemented as Python classes.

    Dynamically imports and instantiates the agent class specified in
    ``config.python_class_path``, then calls ``run()`` with the input.
    """

    connector_type = "python_class"

    def __init__(self) -> None:
        self._config: AgentConfig | None = None
        self._agent_instance: Any = None

    def connect(self, config: AgentConfig) -> None:
        """
        Load and instantiate the agent class from the configured path.

        Uses ``importlib.import_module`` to dynamically load the class.

        Args:
            config: Agent configuration with ``python_class_path``.
        """
        self._config = config
        
        if not config.python_class_path:
            raise ValueError("python_class_path is required for PythonClassConnector")
            
        try:
            module_path, class_name = config.python_class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            agent_cls = getattr(module, class_name)
            self._agent_instance = agent_cls()
        except Exception as e:
            raise RuntimeError(f"Failed to load agent class '{config.python_class_path}': {e}") from e

    def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """
        Call the agent's ``run()`` method with the input data.

        Args:
            input_data: Test case input payload.

        Returns:
            AgentOutput with the agent's response.
        """
        if not self._agent_instance:
            return AgentOutput(success=False, error="Agent instance not loaded", latency_ms=0.0)

        start_time = time.perf_counter()
        try:
            # Enforce the contract: the agent instance must have a run() method
            if not hasattr(self._agent_instance, "run") or not callable(self._agent_instance.run):
                raise NotImplementedError(f"Agent class {self._agent_instance.__class__.__name__} missing callable 'run(input_data: dict)' method")
                
            result = self._agent_instance.run(input_data)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Ensure the output is a dictionary (for uniform processing)
            if not isinstance(result, dict):
                result = {"output": result}
                
            return AgentOutput(
                output=result,
                latency_ms=elapsed_ms,
                success=True,
            )
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return AgentOutput(
                success=False,
                error=f"Python Agent Error: {str(e)}",
                latency_ms=elapsed_ms
            )

    def health_check(self) -> HealthStatus:
        """
        Verify the agent class is loaded and callable.

        Returns:
            HealthStatus indicating whether the agent is instantiated.
        """
        if not self._config:
            return HealthStatus(agent_id="unknown", healthy=False, message="Not initialized")
            
        agent_id = self._config.agent_name
        if self._agent_instance and hasattr(self._agent_instance, "run") and callable(self._agent_instance.run):
            return HealthStatus(agent_id=agent_id, healthy=True, message="Agent loaded and callable")
            
        return HealthStatus(agent_id=agent_id, healthy=False, message="Agent failed to load or missing run() method")

    def disconnect(self) -> None:
        """Release the agent instance."""
        self._agent_instance = None
        self._config = None
