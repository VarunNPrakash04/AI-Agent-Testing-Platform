"""
Core Enumerations
=================

Defines all enumeration types used across the platform. These enums provide
type-safe constants for statuses, agent types, connector types, and other
categorical values. They are used in both domain models and database schemas
to ensure consistency.

Design Decision:
    Using ``str`` + ``Enum`` (StrEnum) pattern so that enum values serialize
    naturally to JSON and are compatible with SQLite text columns without
    custom type adapters.
"""

from enum import StrEnum


class ConnectorType(StrEnum):
    """
    Supported agent connector types.

    Each connector type corresponds to a plugin in ``src/connectors/plugins/``
    that implements the ``BaseConnector`` interface.

    Attributes:
        REST_API: Connect to agents via HTTP REST endpoints.
        PYTHON_CLASS: Connect to agents via importable Python classes.
    """

    REST_API = "rest_api"
    PYTHON_CLASS = "python_class"


class RunStatus(StrEnum):
    """
    Lifecycle states of a test execution run.

    State transitions::

        PENDING → RUNNING → COMPLETED
                         ↘ FAILED
                         ↘ PARTIAL_FAILURE

    Attributes:
        PENDING: Run created but not yet started.
        RUNNING: Execution is in progress.
        COMPLETED: All tests executed and evaluated successfully.
        FAILED: Run encountered a fatal error and could not complete.
        PARTIAL_FAILURE: Some tests failed but the run completed.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_FAILURE = "partial_failure"


class AgentType(StrEnum):
    """
    Categorization of AI agent types.

    These types inform which evaluators are applicable to an agent.
    For example, RAG-specific evaluators (RAGAS) only apply to ``RAG_CHATBOT``.

    Attributes:
        HARVESTING: Agents that extract/harvest metadata.
        CANONICAL_FORMULA: Agents that produce clusters and formulas.
        TEST_AUTOMATION: Agents that read/execute/update test artifacts.
        RAG_CHATBOT: Retrieval-Augmented Generation chatbots.
        SQL_GENERATION: Agents that generate SQL queries.
        TOOL_CALLING: Agents that invoke external tools.
        CUSTOM: Any agent type not in the predefined list.
    """

    HARVESTING = "harvesting"
    CANONICAL_FORMULA = "canonical_formula"
    TEST_AUTOMATION = "test_automation"
    RAG_CHATBOT = "rag_chatbot"
    SQL_GENERATION = "sql_generation"
    TOOL_CALLING = "tool_calling"
    CUSTOM = "custom"


class TestCaseSourceFormat(StrEnum):
    """
    Supported formats for uploading test cases.

    Attributes:
        JSON: JSON file with array of test case objects.
        CSV: Comma-separated values file.
        EXCEL: Excel workbook (.xlsx/.xls) via OpenPyXL.
        TEXT: Plain-text scenario file (.txt).
    """

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    TEXT = "text"


class AuthType(StrEnum):
    """
    Supported authentication methods for agent connectors.

    Attributes:
        NONE: No authentication required.
        BEARER: Bearer token in Authorization header.
        API_KEY: API key in header or query parameter.
        BASIC: HTTP Basic authentication.
    """

    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"


class EvaluatorCategory(StrEnum):
    """
    Categorization of evaluator plugins for filtering and discovery.

    Attributes:
        LLM_BASED: Evaluators that use LLM-as-a-judge (DeepEval, RAGAS).
        RULE_BASED: Deterministic business rule evaluators.
        SCHEMA: Structural/schema validation evaluators.
        PERFORMANCE: Latency and throughput evaluators.
        SECURITY: Security-focused evaluators (prompt injection, PII).
    """

    LLM_BASED = "llm_based"
    RULE_BASED = "rule_based"
    SCHEMA = "schema"
    PERFORMANCE = "performance"
    SECURITY = "security"
