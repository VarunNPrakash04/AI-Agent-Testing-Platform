"""
JSON Test Case Parser
=====================

Parses test cases from JSON files. Expected format is a JSON array
of test case objects, each containing at minimum ``test_id`` and ``input``.

Example JSON::

    [
        {
            "test_id": "TC001",
            "input": {"query": "What is AI?"},
            "expected_output": {"answer": "Artificial Intelligence"},
            "context": ["AI is a branch of computer science..."],
            "ground_truth": "Artificial Intelligence",
            "tags": ["smoke"]
        }
    ]
"""

import json
import logging
from pathlib import Path

from src.core.models import TestCase

logger = logging.getLogger(__name__)


class JsonTestCaseParser:
    """
    Parser for JSON-formatted test case files.

    Expects a JSON file containing an array of test case objects.
    """

    def parse(self, file_path: Path) -> list[TestCase]:
        """
        Parse test cases from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            List of parsed TestCase objects.

        Raises:
            json.JSONDecodeError: If the file contains invalid JSON.
            ValidationError: If test case data fails Pydantic validation.
        """
        logger.debug("Parsing JSON test cases from '%s'", file_path)
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "test_cases" in data:
            data = data["test_cases"]

        test_cases = [TestCase(**item) for item in data]
        logger.info("Parsed %d test cases from '%s'", len(test_cases), file_path.name)
        return test_cases
