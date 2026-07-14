"""
Abstract Interfaces (Plugin Contracts)
======================================

Defines the abstract base classes that form the **plugin contracts** of the
platform. Any new connector, evaluator, or report generator is added by
subclassing the appropriate interface and registering it with the
corresponding registry — zero changes to the core engine are required.

Interfaces Defined:
    - ``BaseConnector``: How the platform connects to and invokes AI agents.
    - ``BaseEvaluator``: How the platform evaluates agent outputs.
    - ``BaseAgent``: Wrapper that combines config + connector for an agent.
    - ``BaseReportGenerator``: How the platform produces test reports.
    - ``BaseObservabilityLogger``: How the platform logs traces and metrics.

Design Decision:
    Using ``ABC`` (Abstract Base Class) rather than ``Protocol`` because we want
    to enforce method implementation at class instantiation time (fail-fast),
    and ABCs provide richer error messages when abstract methods are not implemented.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.core.models import (
    AgentConfig,
    AgentOutput,
    EvaluationResult,
    EvaluatorInfo,
    ExecutionRunResult,
    HealthStatus,
    ReportInfo,
    TestCase,
    TraceData,
)


# ---------------------------------------------------------------------------
# Connector Interface
# ---------------------------------------------------------------------------


class BaseConnector(ABC):
    """
    Abstract interface for AI agent connectors.

    A connector encapsulates the communication protocol with an AI agent.
    Each connector type (REST, Python class, gRPC, etc.) implements this
    interface, allowing the execution engine to invoke any agent through
    a uniform ``execute()`` call.

    Lifecycle:
        1. ``connect(config)`` — establish connection / validate endpoint.
        2. ``execute(input_data)`` — invoke the agent and capture output.
        3. ``health_check()`` — verify the agent is reachable.
        4. ``disconnect()`` — release resources.

    Subclasses must set ``connector_type`` as a class attribute matching
    the value in ``ConnectorType`` enum.
    """

    connector_type: str = ""

    @abstractmethod
    def connect(self, config: AgentConfig) -> None:
        """
        Initialize connection to the agent using the provided configuration.

        Args:
            config: Agent configuration containing endpoint, auth, etc.

        Raises:
            AgentConnectionError: If connection cannot be established.
        """
        ...

    @abstractmethod
    def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """
        Send input to the agent and capture the response.

        Args:
            input_data: The test case input payload to send to the agent.

        Returns:
            AgentOutput with the agent's response, latency, and metadata.

        Raises:
            AgentExecutionTimeoutError: If the agent does not respond in time.
            AgentConnectionError: If communication fails.
        """
        ...

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """
        Check whether the agent is reachable and responsive.

        Returns:
            HealthStatus indicating whether the agent is healthy.
        """
        ...

    def disconnect(self) -> None:
        """
        Release any resources held by the connector.

        Default implementation is a no-op. Override if your connector
        manages persistent connections, sessions, or file handles.
        """
        pass


# ---------------------------------------------------------------------------
# Evaluator Interface
# ---------------------------------------------------------------------------


class BaseEvaluator(ABC):
    """
    Abstract interface for evaluation plugins.

    Each evaluator implements a specific evaluation strategy (e.g., answer
    relevancy, business rules, latency thresholds). The evaluation engine
    dispatches to registered evaluators based on the user's selection.

    Contract:
        - ``evaluate()`` is **stateless** — each call is independent.
        - Return an ``EvaluationResult`` with score, pass/fail, and explanation.
        - ``supports_agent_type()`` enables filtering evaluators by agent type.

    Subclasses must set ``evaluator_name`` as a class attribute.
    """

    evaluator_name: str = ""

    @abstractmethod
    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        """
        Evaluate an agent's output against a test case.

        Args:
            test_case: The test case with input, expected output, context, etc.
            agent_output: The captured agent response.

        Returns:
            EvaluationResult with score, pass/fail status, and explanation.
        """
        ...

    def supports_agent_type(self, agent_type: str) -> bool:
        """
        Check if this evaluator is applicable to the given agent type.

        Default implementation returns True (evaluator works for all types).
        Override to restrict evaluator to specific agent types (e.g., RAGAS
        only for RAG agents).

        Args:
            agent_type: The agent's type string.

        Returns:
            True if this evaluator can evaluate the given agent type.
        """
        return True

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate evaluator-specific configuration.

        Called before execution to ensure the evaluator has everything
        it needs (thresholds, model name, API keys, etc.).

        Args:
            config: Evaluator configuration dictionary.

        Returns:
            True if configuration is valid.
        """
        return True

    def get_info(self) -> EvaluatorInfo:
        """
        Return metadata about this evaluator for discovery endpoints.

        Returns:
            EvaluatorInfo with name, description, category, etc.
        """
        return EvaluatorInfo(name=self.evaluator_name)


# ---------------------------------------------------------------------------
# Agent Interface
# ---------------------------------------------------------------------------


class BaseAgent(ABC):
    """
    Abstract interface for agent wrappers.

    Combines an ``AgentConfig`` with a ``BaseConnector`` to provide a
    high-level ``run()`` method. The execution engine interacts with
    agents exclusively through this interface.

    Note:
        In most cases, the default ``RegisteredAgent`` implementation
        (in ``src/agents/service.py``) is sufficient. Custom subclasses
        are only needed for agents that require special pre/post-processing.
    """

    @abstractmethod
    def run(self, input_data: dict[str, Any]) -> AgentOutput:
        """
        Execute the agent with the given input and return the output.

        This is the primary entry point used by the execution engine.

        Args:
            input_data: Test case input payload.

        Returns:
            AgentOutput with response, latency, token usage, etc.
        """
        ...

    @abstractmethod
    def get_config(self) -> AgentConfig:
        """
        Return the agent's configuration.

        Returns:
            AgentConfig for this agent.
        """
        ...


# ---------------------------------------------------------------------------
# Report Generator Interface
# ---------------------------------------------------------------------------


class BaseReportGenerator(ABC):
    """
    Abstract interface for report generators.

    Report generators transform execution results into human-readable
    formats (HTML, PDF, etc.). Multiple generators can coexist to support
    different output formats.
    """

    @abstractmethod
    def generate(self, result: ExecutionRunResult) -> ReportInfo:
        """
        Generate a report from execution results.

        Args:
            result: The complete execution run result.

        Returns:
            ReportInfo with metadata about the generated report.
        """
        ...

    @abstractmethod
    def export(self, result: ExecutionRunResult, output_path: Path) -> Path:
        """
        Export the report to a specific file path.

        Args:
            result: The complete execution run result.
            output_path: Where to write the report file.

        Returns:
            Path to the generated report file.
        """
        ...

    def get_supported_formats(self) -> list[str]:
        """
        List output formats this generator supports.

        Returns:
            List of format strings (e.g., ``["html"]``).
        """
        return ["html"]


# ---------------------------------------------------------------------------
# Observability Logger Interface
# ---------------------------------------------------------------------------


class BaseObservabilityLogger(ABC):
    """
    Abstract interface for observability/tracing integrations.

    Implementations capture execution traces, metrics, and evaluation
    scores for downstream analysis. The Langfuse integration will
    implement this interface in a future milestone.

    For Milestone 1, a ``NoOpLogger`` implementation is provided that
    silently discards all log calls.
    """

    @abstractmethod
    def log_trace(self, trace: TraceData) -> None:
        """
        Log a complete execution trace (one per test case).

        Args:
            trace: Trace data including input, output, scores, latency.
        """
        ...

    @abstractmethod
    def log_metric(self, name: str, value: float, metadata: dict[str, Any] | None = None) -> None:
        """
        Log a single named metric.

        Args:
            name: Metric name (e.g., ``total_latency_ms``).
            value: Metric value.
            metadata: Optional context for the metric.
        """
        ...

    @abstractmethod
    def log_evaluation(self, result: EvaluationResult, run_id: str, test_case_id: str) -> None:
        """
        Log an individual evaluation result.

        Args:
            result: The evaluation result to log.
            run_id: Parent execution run ID.
            test_case_id: Test case that was evaluated.
        """
        ...

    def flush(self) -> None:
        """
        Flush any buffered log data to the backend.

        Default implementation is a no-op. Override for batched logging.
        """
        pass
