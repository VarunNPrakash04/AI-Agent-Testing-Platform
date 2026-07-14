"""
Pydantic Domain Models
======================

Central domain models shared across all modules. These Pydantic v2 models
serve as the single source of truth for data shapes flowing through the
system — from API request/response validation to database serialization
and inter-module communication.

Design Principles:
    - **Immutable by default**: Models use ``model_config = frozen`` where
      appropriate to prevent accidental mutation.
    - **Optional fields are explicit**: Fields that may not be present
      (e.g., ``expected_output``) are typed as ``T | None``.
    - **Serialization-ready**: All models serialize cleanly to JSON for
      API responses and database storage.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.core.enums import AuthType, ConnectorType, EvaluatorCategory, RunStatus


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


class AuthConfig(BaseModel):
    """
    Authentication configuration for agent connectors.

    Supports multiple auth strategies. Token values may reference environment
    variables using the ``env:VARIABLE_NAME`` syntax, which the connector
    resolves at runtime to avoid storing secrets in config/database.

    Attributes:
        auth_type: Authentication strategy to use.
        token: Bearer token or API key value (or ``env:VAR`` reference).
        username: Username for HTTP Basic auth.
        password: Password for HTTP Basic auth (or ``env:VAR`` reference).
        header_name: Custom header name for API key auth (default: ``X-API-Key``).
    """

    auth_type: AuthType = AuthType.NONE
    token: str | None = None
    username: str | None = None
    password: str | None = None
    header_name: str = "X-API-Key"


# ---------------------------------------------------------------------------
# Agent Configuration & Metadata
# ---------------------------------------------------------------------------


class AgentConfig(BaseModel):
    """
    Complete configuration for registering an AI agent on the platform.

    This model captures everything the platform needs to connect to, invoke,
    and categorize an agent. It is stored in the database and used to
    instantiate the appropriate connector at execution time.

    Attributes:
        agent_name: Unique human-readable name for the agent.
        description: What the agent does.
        agent_type: Categorization for evaluator compatibility filtering.
        connector_type: How to connect (REST API or Python class).
        endpoint: URL for REST API agents.
        python_class_path: Dotted import path for Python class agents.
        auth_config: Authentication settings.
        input_schema: JSON Schema defining expected input structure.
        output_schema: JSON Schema defining expected output structure.
        supports_rag: Whether the agent uses retrieval-augmented generation.
        supports_tool_calling: Whether the agent invokes external tools.
        timeout_seconds: Max time to wait for agent response.
        metadata: Arbitrary key-value metadata.
    """

    agent_name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    agent_type: str = "custom"
    connector_type: ConnectorType = ConnectorType.REST_API
    endpoint: str | None = None
    python_class_path: str | None = None
    auth_config: AuthConfig | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    supports_rag: bool = False
    supports_tool_calling: bool = False
    timeout_seconds: int = Field(default=180, ge=1, le=600)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("connector_type", mode="before")
    @classmethod
    def normalize_connector_type(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"python", "python_class", "python-class"}:
                return ConnectorType.PYTHON_CLASS
            if normalized in {"rest", "rest_api", "rest-api"}:
                return ConnectorType.REST_API
        return value


class AgentRecord(BaseModel):
    """
    Full agent record as stored in the database, including system fields.

    Extends ``AgentConfig`` with platform-managed fields like ``id``,
    timestamps, and active status.
    """

    id: str
    agent_name: str
    description: str = ""
    agent_type: str
    connector_type: ConnectorType
    endpoint: str | None = None
    python_class_path: str | None = None
    auth_config: AuthConfig | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    supports_rag: bool = False
    supports_tool_calling: bool = False
    timeout_seconds: int = 30
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AgentSummary(BaseModel):
    """Lightweight agent info for list endpoints."""

    id: str
    agent_name: str
    agent_type: str
    connector_type: ConnectorType
    is_active: bool
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------


class TestCase(BaseModel):
    """
    A single test case to execute against an agent.

    Attributes:
        test_id: User-facing unique identifier within the suite.
        input: The input payload to send to the agent.
        expected_output: Optional expected output for comparison.
        context: Optional retrieval context (for RAG evaluation).
        ground_truth: Optional ground truth answer string.
        metadata: Arbitrary metadata attached to this test case.
        tags: Tags for filtering (e.g., ``["smoke", "regression"]``).
    """

    test_id: str
    input: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    context: list[str] | None = None
    ground_truth: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class TestSuiteInfo(BaseModel):
    """
    Metadata about a collection of test cases.

    Attributes:
        id: Platform-generated UUID.
        name: Human-readable suite name.
        description: What the test suite covers.
        source_file: Original filename that was uploaded.
        source_format: Format of the uploaded file.
        total_cases: Number of test cases in the suite.
        created_at: When the suite was created.
    """

    id: str
    name: str
    description: str = ""
    source_file: str | None = None
    source_format: str | None = None
    total_cases: int = 0
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Agent Output
# ---------------------------------------------------------------------------


class TokenUsage(BaseModel):
    """
    Token consumption metrics from an agent call.

    Attributes:
        prompt_tokens: Tokens in the input/prompt.
        completion_tokens: Tokens in the agent's response.
        total_tokens: Sum of prompt + completion tokens.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AgentOutput(BaseModel):
    """
    Captured output from a single agent invocation.

    Attributes:
        output: The agent's response payload.
        latency_ms: Time taken for the agent to respond, in milliseconds.
        token_usage: Optional token consumption metrics.
        raw_response: Optional full raw HTTP/class response for debugging.
        error: Error message if the agent call failed.
        success: Whether the agent call succeeded.
    """

    output: Any = None
    latency_ms: float = 0.0
    token_usage: TokenUsage | None = None
    raw_response: dict[str, Any] | None = None
    error: str | None = None
    success: bool = True


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


class EvaluationResult(BaseModel):
    """
    Result of a single evaluator applied to a single test case.

    Attributes:
        evaluator_name: Which evaluator produced this result.
        score: Numeric score (0.0 to 1.0 for most evaluators).
        passed: Whether the test case passed this evaluation.
        explanation: Human-readable explanation of the score.
        details: Evaluator-specific additional information.
        evaluated_at: Timestamp of evaluation.
    """

    evaluator_name: str
    score: float = 0.0
    passed: bool = False
    explanation: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class EvaluatorInfo(BaseModel):
    """
    Metadata about a registered evaluator plugin, returned by discovery endpoints.

    Attributes:
        name: Unique evaluator name (used in RunConfig).
        description: What this evaluator measures.
        category: Type of evaluation (LLM-based, rule-based, etc.).
        supported_agent_types: Which agent types this evaluator supports.
        requires_expected_output: Whether expected_output is needed.
        requires_context: Whether retrieval context is needed.
    """

    name: str
    description: str = ""
    category: EvaluatorCategory = EvaluatorCategory.RULE_BASED
    supported_agent_types: list[str] = Field(default_factory=lambda: ["*"])
    requires_expected_output: bool = False
    requires_context: bool = False


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


class RunConfig(BaseModel):
    """
    Configuration for a test execution run.

    Attributes:
        agent_id: ID of the registered agent to test.
        test_suite_id: ID of the uploaded test suite.
        evaluator_names: List of evaluator names to apply.
        evaluator_configs: Per-evaluator configuration overrides.
        parallel: Whether to execute test cases in parallel.
        max_retries: Number of retries for failed agent calls.
        timeout_per_test: Timeout in seconds per individual test case.
    """

    agent_id: str
    test_suite_id: str
    evaluator_names: list[str] = Field(default_factory=list)
    evaluator_configs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    parallel: bool = False
    max_retries: int = Field(default=0, ge=0, le=5)
    timeout_per_test: int = Field(default=180, ge=1, le=600)


class TestCaseResult(BaseModel):
    """
    Result of executing and evaluating a single test case.

    Attributes:
        test_case: The original test case.
        agent_output: The captured agent response.
        evaluation_results: Scores from all applied evaluators.
        overall_passed: True if all evaluators passed.
        execution_time_ms: Total time for execution + evaluation.
    """

    test_case: TestCase
    agent_output: AgentOutput
    evaluation_results: list[EvaluationResult] = Field(default_factory=list)
    overall_passed: bool = False
    execution_time_ms: float = 0.0


class ExecutionRunResult(BaseModel):
    """
    Aggregate result of a complete test execution run.

    Attributes:
        run_id: Unique run identifier.
        agent_id: ID of the agent that was tested.
        suite_id: ID of the test suite that was used.
        status: Final status of the run.
        started_at: When execution began.
        completed_at: When execution finished.
        total_tests: Total number of test cases.
        passed_tests: Number of test cases that passed all evaluators.
        failed_tests: Number of test cases that failed at least one evaluator.
        test_results: Per-test-case detailed results.
        overall_score: Aggregate score across all tests and evaluators.
        error_message: Top-level error message if the run failed.
    """

    run_id: str
    agent_id: str
    suite_id: str
    status: RunStatus = RunStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    test_results: list[TestCaseResult] = Field(default_factory=list)
    overall_score: float = 0.0
    error_message: str | None = None


class RunSummary(BaseModel):
    """Lightweight run info for list/history endpoints."""

    run_id: str
    agent_id: str
    agent_name: str = ""
    suite_id: str
    status: RunStatus
    total_tests: int = 0
    passed_tests: int = 0
    overall_score: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class DashboardStats(BaseModel):
    """High-level metrics for the dashboard overview."""

    total_agents: int = 0
    total_runs: int = 0
    total_datasets: int = 0
    average_evaluation_score: float = 0.0
    average_latency_ms: float = 0.0
    success_rate: float = 0.0
    failed_runs: int = 0


class DashboardOverview(BaseModel):
    """Dashboard payload consumed by the UI."""

    stats: DashboardStats
    recent_runs: list[RunSummary] = Field(default_factory=list)
    framework_breakdown: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# History / Regression Comparison
# ---------------------------------------------------------------------------


class TestCaseComparison(BaseModel):
    """
    Comparison of a single test case across two runs.

    Attributes:
        test_id: The user-facing test case ID.
        score_a: Score from run A.
        score_b: Score from run B.
        delta: Score change (B - A). Positive = improvement.
        status: One of ``improved``, ``degraded``, ``unchanged``.
    """

    test_id: str
    score_a: float
    score_b: float
    delta: float = 0.0
    status: str = "unchanged"  # improved | degraded | unchanged


class ComparisonResult(BaseModel):
    """
    Aggregate comparison between two execution runs.

    Attributes:
        run_id_a: The baseline run.
        run_id_b: The comparison run.
        overall_score_a: Aggregate score of run A.
        overall_score_b: Aggregate score of run B.
        overall_delta: Change in overall score.
        improved_count: Number of test cases that improved.
        degraded_count: Number of test cases that degraded.
        unchanged_count: Number of test cases unchanged.
        comparisons: Per-test-case comparisons.
    """

    run_id_a: str
    run_id_b: str
    overall_score_a: float = 0.0
    overall_score_b: float = 0.0
    overall_delta: float = 0.0
    improved_count: int = 0
    degraded_count: int = 0
    unchanged_count: int = 0
    comparisons: list[TestCaseComparison] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


class ReportInfo(BaseModel):
    """
    Metadata about a generated report.

    Attributes:
        run_id: The execution run this report covers.
        format: Report file format (e.g., ``html``).
        file_path: Filesystem path to the generated report.
        generated_at: When the report was generated.
    """

    run_id: str
    format: str = "html"
    file_path: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------


class HealthStatus(BaseModel):
    """Result of an agent health check."""

    agent_id: str
    healthy: bool
    message: str = ""
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Observability / Trace
# ---------------------------------------------------------------------------


class TraceData(BaseModel):
    """
    Trace data for observability logging.

    Captures the complete context of a single test execution for
    downstream observability tools (e.g., Langfuse).

    Attributes:
        trace_id: Unique identifier for this trace.
        run_id: Parent execution run ID.
        test_case_id: Test case that was executed.
        input: Agent input payload.
        output: Agent output payload.
        latency_ms: Response time in milliseconds.
        token_usage: Token consumption metrics.
        evaluation_scores: Evaluation results for this test case.
        metadata: Additional trace metadata.
    """

    trace_id: str
    run_id: str
    test_case_id: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: Any = None
    latency_ms: float = 0.0
    token_usage: TokenUsage | None = None
    evaluation_scores: list[EvaluationResult] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
