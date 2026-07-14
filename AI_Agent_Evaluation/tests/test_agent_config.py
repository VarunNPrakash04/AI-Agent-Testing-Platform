from src.core.enums import ConnectorType
from src.core.models import AgentConfig


def test_agent_config_accepts_legacy_python_connector_value():
    config = AgentConfig(agent_name="Sample agent", connector_type="python")

    assert config.connector_type == ConnectorType.PYTHON_CLASS
    assert config.connector_type.value == "python_class"
