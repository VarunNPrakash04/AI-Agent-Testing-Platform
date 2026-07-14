"""
Text Test Case Parser
=====================

Parses plain-text scenario files. Each non-empty line is treated as one
individual test case with the line content stored as the input text.
"""

import logging
from pathlib import Path

from src.core.models import TestCase

logger = logging.getLogger(__name__)


class TextTestCaseParser:
    """Parser for plain-text test case files (.txt)."""

    def parse(self, file_path: Path) -> list[TestCase]:
        logger.debug("Parsing text test cases from '%s'", file_path)

        with open(file_path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        test_cases = []
        for index, line in enumerate(lines, start=1):
            test_cases.append(
                TestCase(
                    test_id=f"TC_TXT_{index:03d}",
                    input={"text": line},
                    expected_output=None,
                    context=None,
                    ground_truth=line,
                    metadata={"source": "text_upload"},
                    tags=[],
                )
            )

        logger.info("Parsed %d test cases from '%s'", len(test_cases), file_path.name)
        return test_cases
