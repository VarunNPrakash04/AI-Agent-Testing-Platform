"""
SQLAlchemy ORM Models
=====================

Defines the relational database schema using SQLAlchemy 2.0 declarative
models. These models map directly to the database schema documented in
the LLD (Section 4).

Tables:
    - ``agents``: Registered AI agent configurations.
    - ``test_suites``: Test suite metadata (uploaded files).
    - ``test_cases``: Individual test cases within a suite.
    - ``execution_runs``: Test execution run records.
    - ``execution_results``: Per-test-case execution results.
    - ``evaluation_scores``: Individual evaluator scores per result.

Design Decision:
    JSON fields are stored as TEXT columns and serialized/deserialized at
    the application layer. SQLite's JSON support is limited, so we keep
    the schema simple and handle structure in Pydantic models.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


def _generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    """Generate a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class AgentModel(Base):
    """
    ORM model for registered AI agents.

    Stores the complete agent configuration including connection details,
    schemas, and metadata. Corresponds to the ``AGENTS`` table in the LLD.
    """

    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=_generate_uuid)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, default="")
    agent_type = Column(String(50), nullable=False)
    connector_type = Column(String(50), nullable=False)
    endpoint = Column(String(500), nullable=True)
    python_class_path = Column(String(500), nullable=True)
    auth_config_json = Column(Text, nullable=True)
    input_schema_json = Column(Text, nullable=False, default="{}")
    output_schema_json = Column(Text, nullable=False, default="{}")
    supports_rag = Column(Boolean, default=False)
    supports_tool_calling = Column(Boolean, default=False)
    timeout_seconds = Column(Integer, default=30)
    metadata_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class TestSuiteModel(Base):
    """
    ORM model for test suites (collections of test cases).

    Each suite represents a single uploaded file and contains
    one or more test cases.
    """

    __tablename__ = "test_suites"

    id = Column(String, primary_key=True, default=_generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    source_file = Column(String(500), nullable=True)
    source_format = Column(String(20), nullable=True)
    total_cases = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utcnow)
    metadata_json = Column(Text, default="{}")


class TestCaseModel(Base):
    """
    ORM model for individual test cases within a suite.

    Stores the test input, expected output, context, and ground truth
    as JSON text columns for flexibility across different agent types.
    """

    __tablename__ = "test_cases"

    id = Column(String, primary_key=True, default=_generate_uuid)
    suite_id = Column(String, nullable=False, index=True)
    test_id = Column(String(255), nullable=False)
    input_json = Column(Text, nullable=False)
    expected_output_json = Column(Text, nullable=True)
    context_json = Column(Text, nullable=True)
    ground_truth = Column(Text, nullable=True)
    metadata_json = Column(Text, default="{}")
    tags_json = Column(Text, default="[]")
    sort_order = Column(Integer, default=0)


class ExecutionRunModel(Base):
    """
    ORM model for test execution runs.

    Tracks the lifecycle of a complete test run from creation to
    completion, including aggregate statistics.
    """

    __tablename__ = "execution_runs"

    id = Column(String, primary_key=True, default=_generate_uuid)
    agent_id = Column(String, nullable=False, index=True)
    suite_id = Column(String, nullable=False)
    evaluator_names_json = Column(Text, nullable=False, default="[]")
    status = Column(String(30), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    overall_score = Column(Float, default=0.0)
    run_config_json = Column(Text, default="{}")
    error_message = Column(Text, nullable=True)


class ExecutionResultModel(Base):
    """
    ORM model for per-test-case execution results.

    Each row records the outcome of executing a single test case
    against an agent, including the agent's output and timing.
    """

    __tablename__ = "execution_results"

    id = Column(String, primary_key=True, default=_generate_uuid)
    run_id = Column(String, nullable=False, index=True)
    test_case_id = Column(String, nullable=False)
    agent_output_json = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    latency_ms = Column(Float, default=0.0)
    token_usage_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    overall_passed = Column(Boolean, default=False)
    executed_at = Column(DateTime, default=_utcnow)


class EvaluationScoreModel(Base):
    """
    ORM model for individual evaluation scores.

    Each row represents one evaluator's assessment of one test case
    result. A single execution result may have multiple score rows
    (one per evaluator).
    """

    __tablename__ = "evaluation_scores"

    id = Column(String, primary_key=True, default=_generate_uuid)
    result_id = Column(String, nullable=False, index=True)
    evaluator_name = Column(String(100), nullable=False)
    score = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    explanation = Column(Text, default="")
    details_json = Column(Text, default="{}")
    evaluated_at = Column(DateTime, default=_utcnow)
