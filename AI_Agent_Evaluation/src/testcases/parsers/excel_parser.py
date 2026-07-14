"""
Excel Test Case Parser
======================

Parses test cases from Excel workbooks (.xlsx) using pandas + openpyxl.
Reads the first sheet by default unless a ``sheet_name`` is specified.

Column mapping is identical to the CSV parser.
"""

import json
import logging
from pathlib import Path

import pandas as pd

from src.core.models import TestCase

logger = logging.getLogger(__name__)


class ExcelTestCaseParser:
    """
    Parser for Excel-formatted test case files (.xlsx).

    Uses pandas with the openpyxl engine to read Excel workbooks.
    """

    def __init__(self, sheet_name: str | int = 0) -> None:
        """
        Args:
            sheet_name: Sheet to read (name string or 0-based index). Default: first sheet.
        """
        self._sheet_name = sheet_name

    def parse(self, file_path: Path) -> list[TestCase]:
        """
        Parse test cases from an Excel file.

        Args:
            file_path: Path to the .xlsx file.

        Returns:
            List of parsed TestCase objects.
        """
        logger.debug("Parsing Excel test cases from '%s' (sheet=%s)", file_path, self._sheet_name)
        df = pd.read_excel(file_path, sheet_name=self._sheet_name, engine="openpyxl")
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
        """Attempt to parse a JSON string."""
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
        """Parse tags from comma-separated or JSON array string."""
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
