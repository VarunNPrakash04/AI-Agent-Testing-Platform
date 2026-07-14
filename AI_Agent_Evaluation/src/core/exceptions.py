"""
Custom Exception Hierarchy
===========================

Defines a structured exception hierarchy for the platform. All custom
exceptions inherit from ``PlatformError`` to allow broad exception
catching at the API layer while preserving specific error types for
targeted handling.

Architecture Note:
    The API layer (``src/api/``) catches these exceptions and maps them
    to appropriate HTTP status codes via FastAPI exception handlers.
    Domain/service layers raise these exceptions instead of returning
    error codes, following the "exceptions for exceptional conditions" pattern.
"""


class PlatformError(Exception):
    """
    Base exception for all platform-specific errors.

    All custom exceptions inherit from this class so that the API layer
    can catch ``PlatformError`` as a broad fallback while still handling
    specific subtypes individually.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code for API responses.
        details: Optional dictionary with additional error context.
    """

    def __init__(
        self,
        message: str,
        code: str = "PLATFORM_ERROR",
        details: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Agent Errors
# ---------------------------------------------------------------------------


class AgentNotFoundError(PlatformError):
    """Raised when an agent with the given ID does not exist."""

    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent with id '{agent_id}' does not exist.",
            code="AGENT_NOT_FOUND",
            details={"agent_id": agent_id},
        )


class AgentAlreadyExistsError(PlatformError):
    """Raised when attempting to register an agent with a duplicate name."""

    def __init__(self, agent_name: str):
        super().__init__(
            message=f"Agent with name '{agent_name}' already exists.",
            code="AGENT_ALREADY_EXISTS",
            details={"agent_name": agent_name},
        )


class AgentConnectionError(PlatformError):
    """Raised when a connector fails to reach the agent endpoint."""

    def __init__(self, agent_id: str, reason: str):
        super().__init__(
            message=f"Failed to connect to agent '{agent_id}': {reason}",
            code="AGENT_CONNECTION_ERROR",
            details={"agent_id": agent_id, "reason": reason},
        )


# ---------------------------------------------------------------------------
# Connector Errors
# ---------------------------------------------------------------------------


class ConnectorNotFoundError(PlatformError):
    """Raised when a requested connector type is not registered."""

    def __init__(self, connector_type: str):
        super().__init__(
            message=f"Connector type '{connector_type}' is not registered.",
            code="CONNECTOR_NOT_FOUND",
            details={"connector_type": connector_type},
        )


# ---------------------------------------------------------------------------
# Evaluator Errors
# ---------------------------------------------------------------------------


class EvaluatorNotFoundError(PlatformError):
    """Raised when a requested evaluator name is not registered."""

    def __init__(self, evaluator_name: str):
        super().__init__(
            message=f"Evaluator '{evaluator_name}' is not registered.",
            code="EVALUATOR_NOT_FOUND",
            details={"evaluator_name": evaluator_name},
        )


# ---------------------------------------------------------------------------
# Test Case Errors
# ---------------------------------------------------------------------------


class TestSuiteNotFoundError(PlatformError):
    """Raised when a test suite with the given ID does not exist."""

    def __init__(self, suite_id: str):
        super().__init__(
            message=f"Test suite with id '{suite_id}' does not exist.",
            code="TEST_SUITE_NOT_FOUND",
            details={"suite_id": suite_id},
        )


class TestCaseValidationError(PlatformError):
    """Raised when uploaded test cases fail schema validation."""

    def __init__(self, errors: list[str]):
        super().__init__(
            message=f"Test case validation failed with {len(errors)} error(s).",
            code="TEST_CASE_VALIDATION_ERROR",
            details={"errors": errors},
        )


class UnsupportedFileFormatError(PlatformError):
    """Raised when the uploaded test case file format is not supported."""

    def __init__(self, filename: str):
        super().__init__(
            message=f"Unsupported file format for '{filename}'. Supported: json, csv, xlsx, xls, txt.",
            code="UNSUPPORTED_FILE_FORMAT",
            details={"filename": filename},
        )


# ---------------------------------------------------------------------------
# Execution Errors
# ---------------------------------------------------------------------------


class ExecutionRunNotFoundError(PlatformError):
    """Raised when an execution run with the given ID does not exist."""

    def __init__(self, run_id: str):
        super().__init__(
            message=f"Execution run with id '{run_id}' does not exist.",
            code="EXECUTION_RUN_NOT_FOUND",
            details={"run_id": run_id},
        )


class ExecutionError(PlatformError):
    """Raised when the execution engine encounters a fatal error during a run."""

    def __init__(self, run_id: str, reason: str):
        super().__init__(
            message=f"Execution run '{run_id}' failed: {reason}",
            code="EXECUTION_ERROR",
            details={"run_id": run_id, "reason": reason},
        )


class AgentExecutionTimeoutError(PlatformError):
    """Raised when an agent does not respond within the configured timeout."""

    def __init__(self, agent_id: str, timeout_seconds: int):
        super().__init__(
            message=f"Agent '{agent_id}' timed out after {timeout_seconds}s.",
            code="AGENT_TIMEOUT",
            details={"agent_id": agent_id, "timeout_seconds": timeout_seconds},
        )


# ---------------------------------------------------------------------------
# Report Errors
# ---------------------------------------------------------------------------


class ReportGenerationError(PlatformError):
    """Raised when the report generator fails to produce a report."""

    def __init__(self, run_id: str, reason: str):
        super().__init__(
            message=f"Failed to generate report for run '{run_id}': {reason}",
            code="REPORT_GENERATION_ERROR",
            details={"run_id": run_id, "reason": reason},
        )
