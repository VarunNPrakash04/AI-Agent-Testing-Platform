"""
REST API Connector
==================

Connector plugin for AI agents exposed via HTTP REST APIs.

This connector sends test inputs as JSON POST requests to the agent's
endpoint and captures the response. It supports configurable authentication
(Bearer, API Key, Basic) and timeout settings.
"""

import time
from typing import Any

import httpx

from src.connectors.registry import register_connector
from src.core.interfaces import BaseConnector
from src.core.models import AgentConfig, AgentOutput, HealthStatus


@register_connector("rest_api")
class RESTConnector(BaseConnector):
    """
    Connector for agents accessible via HTTP REST APIs.

    Sends JSON payloads to the agent's endpoint and parses the response.
    Supports Bearer token, API key, and Basic authentication.
    """

    connector_type = "rest_api"

    def __init__(self) -> None:
        self._config: AgentConfig | None = None
        self._base_url: str = ""
        self._client: httpx.Client | None = None

    def connect(self, config: AgentConfig) -> None:
        """
        Store configuration and prepare HTTP client.

        Initializes an ``httpx.Client`` with appropriate auth headers
        and timeout settings.

        Args:
            config: Agent configuration with endpoint and auth details.
        """
        self._config = config
        self._base_url = config.endpoint or ""
        
        headers = {}
        if config.auth_config:
            auth_type = getattr(config.auth_config, "auth_type", None)
            if auth_type == "bearer":
                token = getattr(config.auth_config, "token", None) or ""
                headers["Authorization"] = f"Bearer {token}"
            elif auth_type == "api_key":
                header_name = getattr(config.auth_config, "header_name", "X-API-Key")
                token = getattr(config.auth_config, "token", None) or ""
                headers[header_name] = token
                
        self._client = httpx.Client(
            base_url=self._base_url if not self._base_url.endswith("/") else self._base_url[:-1],
            headers=headers,
            timeout=config.timeout_seconds
        )

    def execute(self, input_data: dict[str, Any]) -> AgentOutput:
        """
        Send input to the agent's REST endpoint and capture the response.

        Performs HTTP POST via httpx.

        Args:
            input_data: Test case input payload.

        Returns:
            AgentOutput with the agent's response.
        """
        if not self._client or not self._config:
            return AgentOutput(success=False, error="Connector not initialized", latency_ms=0.0)

        auth = None
        if self._config and self._config.auth_config:
            auth_type = getattr(self._config.auth_config, "auth_type", None)
            if auth_type == "basic":
                username = getattr(self._config.auth_config, "username", None) or ""
                password = getattr(self._config.auth_config, "password", None) or ""
                auth = (username, password)

        start_time = time.perf_counter()
        try:
            # Assuming the agent accepts POST to its base endpoint or a /run endpoint
            # We'll just post to the base URL configured
            response = self._client.post("", json=input_data, auth=auth)
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            if response.status_code >= 400:
                return AgentOutput(
                    success=False,
                    error=f"HTTP Error {response.status_code}: {response.text}",
                    latency_ms=elapsed_ms
                )
                
            try:
                output_json = response.json()
            except ValueError:
                output_json = {"raw_text": response.text}
                
            return AgentOutput(
                output=output_json,
                latency_ms=elapsed_ms,
                success=True,
            )
            
        except httpx.RequestError as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return AgentOutput(
                success=False,
                error=f"Request failed: {str(exc)}",
                latency_ms=elapsed_ms
            )

    def health_check(self) -> HealthStatus:
        """
        Check if the agent endpoint is reachable.

        Performs HTTP GET to the endpoint (or a derived /health endpoint).

        Returns:
            HealthStatus with reachability information.
        """
        if not self._client or not self._config:
            return HealthStatus(agent_id="unknown", healthy=False, message="Not initialized")
            
        agent_id = self._config.agent_name
        try:
            # Try a GET request to the root or a /health path. We'll just try root for generic POC.
            response = self._client.get("")
            if response.status_code < 500:
                return HealthStatus(agent_id=agent_id, healthy=True, message=f"Connected. Status {response.status_code}")
            else:
                return HealthStatus(agent_id=agent_id, healthy=False, message=f"Server returned {response.status_code}")
        except httpx.RequestError as exc:
            return HealthStatus(agent_id=agent_id, healthy=False, message=f"Connection failed: {str(exc)}")

    def disconnect(self) -> None:
        """Release HTTP client resources."""
        if self._client:
            self._client.close()
            self._client = None
        self._config = None
        self._base_url = ""
