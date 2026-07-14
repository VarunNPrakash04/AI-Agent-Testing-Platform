"""
Connector Registry
==================

Central registry for agent connector plugins. Provides decorator-based
auto-registration and lookup by connector type string.

Architecture:
    The registry follows the **Registry + Strategy** pattern. Connector
    classes are registered at import time via the ``@register_connector``
    decorator. The execution engine looks up connectors by type string
    and instantiates them on demand.

Usage::

    from src.connectors.registry import register_connector, connector_registry

    @register_connector("my_protocol")
    class MyConnector(BaseConnector):
        ...

    # Later, to retrieve:
    ConnectorClass = connector_registry.get("my_protocol")
    connector = ConnectorClass()
"""

from typing import Type

from src.core.exceptions import ConnectorNotFoundError
from src.core.interfaces import BaseConnector


class ConnectorRegistry:
    """
    Registry for connector plugins.

    Maintains a mapping of connector type strings to their implementing
    classes. Supports both decorator-based and explicit registration.

    Attributes:
        _connectors: Internal dictionary mapping type strings to classes.
    """

    def __init__(self) -> None:
        self._connectors: dict[str, Type[BaseConnector]] = {}

    def register(self, connector_type: str, cls: Type[BaseConnector]) -> None:
        """
        Register a connector class for the given type.

        Args:
            connector_type: Unique string identifier (e.g., ``"rest_api"``).
            cls: The connector class to register.

        Raises:
            ValueError: If the connector type is already registered.
        """
        if connector_type in self._connectors:
            raise ValueError(
                f"Connector type '{connector_type}' is already registered "
                f"by {self._connectors[connector_type].__name__}."
            )
        self._connectors[connector_type] = cls

    def get(self, connector_type: str) -> Type[BaseConnector]:
        """
        Look up a connector class by type string.

        Args:
            connector_type: The type string to look up.

        Returns:
            The registered connector class.

        Raises:
            ConnectorNotFoundError: If no connector is registered for the type.
        """
        if connector_type not in self._connectors:
            raise ConnectorNotFoundError(connector_type)
        return self._connectors[connector_type]

    def list_connectors(self) -> list[str]:
        """
        List all registered connector type strings.

        Returns:
            Sorted list of registered connector type names.
        """
        return sorted(self._connectors.keys())

    def has(self, connector_type: str) -> bool:
        """
        Check if a connector type is registered.

        Args:
            connector_type: The type string to check.

        Returns:
            True if a connector is registered for the given type.
        """
        return connector_type in self._connectors


# ---------------------------------------------------------------------------
# Global singleton registry instance
# ---------------------------------------------------------------------------
connector_registry = ConnectorRegistry()


def register_connector(connector_type: str):
    """
    Decorator to auto-register a connector class with the global registry.

    Usage::

        @register_connector("rest_api")
        class RESTConnector(BaseConnector):
            ...

    Args:
        connector_type: The type string to register the class under.

    Returns:
        Decorator function that registers the class and returns it unchanged.
    """

    def decorator(cls: Type[BaseConnector]) -> Type[BaseConnector]:
        connector_registry.register(connector_type, cls)
        cls.connector_type = connector_type
        return cls

    return decorator
