"""
CSV Test Case Parser
====================

Parses test cases from CSV files. Expected columns:

    - ``test_id`` (required)
    - ``input`` (required, JSON string)
    - ``expected_output`` (optional, JSON string)
    - ``context`` (optional, JSON string — array of strings)
    - ``ground_truth`` (optional, plain text)
    - ``tags`` (optional, comma-separated or JSON array)

Milestone 1 Status:
    Skeleton with basic pandas-based parsing logic.
"""

import json
import logging
from pathlib import Path

import pandas as pd

from src.core.models import TestCase

logger = logging.getLogger(__name__)


class CsvTestCaseParser:
    """
    Parser for CSV-formatted test case files.

    Uses pandas to read CSV files and converts each row to a TestCase.
    JSON fields (input, expected_output, context) are parsed from string columns.
    """

    def parse(self, file_path: Path) -> list[TestCase]:
        """
        Parse test cases from a CSV file.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of parsed TestCase objects.
        """
        logger.debug("Parsing CSV test cases from '%s'", file_path)
        df = pd.read_csv(file_path)
        df = df.fillna("")

        test_cases = []
        for _, row in df.iterrows():
            tc = TestCase(
                test_id=str(row.get("test_id", "")),
                input=self._parse_json_field(row.get("input", "{}")),
                expected_output=self._parse_json_field(row.get("expected_output")) if row.get("expected_output") else None,
                context=self._parse_json_field(row.get("context")) if row.get("context") else None,
                ground_truth=str(row.get("ground_truth", "")) or None,
                tags=self._parse_tags(row.get("tags", "")),
            )
            test_cases.append(tc)

        logger.info("Parsed %d test cases from '%s'", len(test_cases), file_path.name)
        return test_cases

    @staticmethod
    def _parse_json_field(value) -> dict | list | None:
        """Attempt to parse a JSON string; return as-is if not valid JSON."""
        if not value or (isinstance(value, str) and not value.strip()):
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {"raw": value}
        return value

    @staticmethod
    def _parse_tags(value) -> list[str]:
        """Parse tags from comma-separated string or JSON array."""
        if not value or (isinstance(value, str) and not value.strip()):
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                return [t.strip() for t in value.split(",") if t.strip()]
        return []
