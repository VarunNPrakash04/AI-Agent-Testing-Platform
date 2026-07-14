"""
Connectors Package
==================

Agent connectors encapsulate the communication protocol with AI agents.
Each connector type (REST, Python class, etc.) is implemented as a plugin
in the ``plugins/`` sub-package and registered with the ``ConnectorRegistry``.

The execution engine uses the registry to look up the appropriate connector
based on the agent's ``connector_type`` configuration.
"""
