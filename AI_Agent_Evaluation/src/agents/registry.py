"""
Agent Registry
==============

Provides CRUD operations for managing registered AI agents in the
database. This is the persistence layer for agent configurations.

The registry stores agent metadata (name, type, endpoint, schemas)
and retrieves it when the execution engine needs to invoke an agent.

Architecture:
    The registry receives a SQLAlchemy session via dependency injection
    and performs all database operations through ORM models. It converts
    between ORM models and Pydantic domain models at the boundary.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.core.exceptions import AgentAlreadyExistsError, AgentNotFoundError
from src.core.models import AgentConfig, AgentRecord, AgentSummary
from src.db.models import AgentModel

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    CRUD operations for agent configurations.

    All methods receive and return Pydantic models. The internal
    conversion to/from SQLAlchemy ORM models is encapsulated here.

    Args:
        db: SQLAlchemy session (injected via FastAPI Depends).
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def register_agent(self, config: AgentConfig) -> AgentRecord:
        """
        Register a new agent with the platform.

        Args:
            config: Agent configuration to register.

        Returns:
            The created AgentRecord with generated ID and timestamps.

        Raises:
            AgentAlreadyExistsError: If an agent with the same name exists.
        """
        # Check for duplicate name
        existing = (
            self._db.query(AgentModel)
            .filter(AgentModel.name == config.agent_name)
            .first()
        )
        if existing:
            raise AgentAlreadyExistsError(config.agent_name)

        agent = AgentModel(
            id=str(uuid.uuid4()),
            name=config.agent_name,
            description=config.description,
            agent_type=config.agent_type,
            connector_type=config.connector_type.value,
            endpoint=config.endpoint,
            python_class_path=config.python_class_path,
            auth_config_json=json.dumps(config.auth_config.model_dump()) if config.auth_config else None,
            input_schema_json=json.dumps(config.input_schema),
            output_schema_json=json.dumps(config.output_schema),
            supports_rag=config.supports_rag,
            supports_tool_calling=config.supports_tool_calling,
            timeout_seconds=config.timeout_seconds,
            metadata_json=json.dumps(config.metadata),
        )

        self._db.add(agent)
        self._db.commit()
        self._db.refresh(agent)

        logger.info("Registered agent '%s' (id=%s)", config.agent_name, agent.id)
        return self._to_record(agent)

    def get_agent(self, agent_id: str) -> AgentRecord:
        """
        Retrieve an agent by ID.

        Args:
            agent_id: The agent's UUID.

        Returns:
            The agent's full record.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        agent = self._db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if not agent:
            raise AgentNotFoundError(agent_id)
        return self._to_record(agent)

    def list_agents(self, active_only: bool = True) -> list[AgentSummary]:
        """
        List all registered agents.

        Args:
            active_only: If True, only return active agents.

        Returns:
            List of agent summaries.
        """
        query = self._db.query(AgentModel)
        if active_only:
            query = query.filter(AgentModel.is_active == True)  # noqa: E712
        agents = query.order_by(AgentModel.created_at.desc()).all()
        return [self._to_summary(a) for a in agents]

    def update_agent(self, agent_id: str, config: AgentConfig) -> AgentRecord:
        """
        Update an existing agent's configuration.

        Args:
            agent_id: The agent's UUID.
            config: Updated agent configuration.

        Returns:
            The updated agent record.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        agent = self._db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if not agent:
            raise AgentNotFoundError(agent_id)

        agent.name = config.agent_name
        agent.description = config.description
        agent.agent_type = config.agent_type
        agent.connector_type = config.connector_type.value
        agent.endpoint = config.endpoint
        agent.python_class_path = config.python_class_path
        agent.auth_config_json = json.dumps(config.auth_config.model_dump()) if config.auth_config else None
        agent.input_schema_json = json.dumps(config.input_schema)
        agent.output_schema_json = json.dumps(config.output_schema)
        agent.supports_rag = config.supports_rag
        agent.supports_tool_calling = config.supports_tool_calling
        agent.timeout_seconds = config.timeout_seconds
        agent.metadata_json = json.dumps(config.metadata)
        agent.updated_at = datetime.now(timezone.utc)

        self._db.commit()
        self._db.refresh(agent)

        logger.info("Updated agent '%s' (id=%s)", config.agent_name, agent_id)
        return self._to_record(agent)

    def delete_agent(self, agent_id: str) -> None:
        """
        Soft-delete an agent (set is_active=False).

        Args:
            agent_id: The agent's UUID.

        Raises:
            AgentNotFoundError: If the agent does not exist.
        """
        agent = self._db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if not agent:
            raise AgentNotFoundError(agent_id)

        agent.is_active = False
        agent.updated_at = datetime.now(timezone.utc)
        self._db.commit()

        logger.info("Deactivated agent id=%s", agent_id)

    # ---------------------------------------------------------------------------
    # Internal Helpers
    # ---------------------------------------------------------------------------

    @staticmethod
    def _to_record(agent: AgentModel) -> AgentRecord:
        """Convert ORM model to Pydantic AgentRecord."""
        return AgentRecord(
            id=agent.id,
            agent_name=agent.name,
            description=agent.description or "",
            agent_type=agent.agent_type,
            connector_type=agent.connector_type,
            endpoint=agent.endpoint,
            python_class_path=agent.python_class_path,
            auth_config=json.loads(agent.auth_config_json) if agent.auth_config_json else None,
            input_schema=json.loads(agent.input_schema_json) if agent.input_schema_json else {},
            output_schema=json.loads(agent.output_schema_json) if agent.output_schema_json else {},
            supports_rag=agent.supports_rag or False,
            supports_tool_calling=agent.supports_tool_calling or False,
            timeout_seconds=agent.timeout_seconds or 30,
            metadata=json.loads(agent.metadata_json) if agent.metadata_json else {},
            is_active=agent.is_active if agent.is_active is not None else True,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    @staticmethod
    def _to_summary(agent: AgentModel) -> AgentSummary:
        """Convert ORM model to lightweight AgentSummary."""
        return AgentSummary(
            id=agent.id,
            agent_name=agent.name,
            agent_type=agent.agent_type,
            connector_type=agent.connector_type,
            is_active=agent.is_active if agent.is_active is not None else True,
            created_at=agent.created_at,
        )
