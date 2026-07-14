"""
Connector Plugins Package
==========================

Contains concrete implementations of ``BaseConnector`` for different
communication protocols. Each plugin auto-registers itself via the
``@register_connector`` decorator on import.

Available Plugins:
    - ``rest_connector.py``: HTTP REST API connector.
    - ``python_connector.py``: In-process Python class connector.

To add a new connector:
    1. Create a new file in this directory.
    2. Subclass ``BaseConnector`` and implement all abstract methods.
    3. Decorate the class with ``@register_connector("your_type")``.
    4. Import the module in this ``__init__.py``.
"""

# Import plugins to trigger auto-registration
from src.connectors.plugins.rest_connector import RESTConnector  # noqa: F401
from src.connectors.plugins.python_connector import PythonClassConnector  # noqa: F401
