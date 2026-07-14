"""
Test Case Manager
=================

Unified manager for loading, validating, and persisting test cases.
Supports JSON, CSV, and Excel file formats through format-specific
parsers in the ``parsers/`` sub-package.

Responsibilities:
    - Detect file format from extension.
    - Delegate parsing to the appropriate parser.
    - Validate parsed test cases against the ``TestCase`` schema.
    - Persist test suites and cases to the database.
    - Retrieve test cases for execution.

Architecture:
    The manager uses the **Strategy Pattern** for parsers — each file
    format has a dedicated parser class. The manager selects the parser
    based on file extension.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from src.core.enums import TestCaseSourceFormat
from src.core.exceptions import TestSuiteNotFoundError, UnsupportedFileFormatError
from src.core.models import TestCase, TestSuiteInfo
from src.db.models import TestCaseModel, TestSuiteModel
from src.testcases.parsers.json_parser import JsonTestCaseParser
from src.testcases.parsers.csv_parser import CsvTestCaseParser
from src.testcases.parsers.excel_parser import ExcelTestCaseParser
from src.testcases.parsers.text_parser import TextTestCaseParser

logger = logging.getLogger(__name__)

# Map file extensions to parsers
_PARSERS = {
    ".json": JsonTestCaseParser,
    ".csv": CsvTestCaseParser,
    ".xlsx": ExcelTestCaseParser,
    ".xls": ExcelTestCaseParser,
    ".txt": TextTestCaseParser,
}

# Map extensions to source format enum
_FORMAT_MAP = {
    ".json": TestCaseSourceFormat.JSON,
    ".csv": TestCaseSourceFormat.CSV,
    ".xlsx": TestCaseSourceFormat.EXCEL,
    ".xls": TestCaseSourceFormat.EXCEL,
    ".txt": TestCaseSourceFormat.TEXT,
}


class TestCaseManager:
    """
    Manages test case lifecycle: loading, validation, storage, and retrieval.

    Args:
        db: SQLAlchemy session for persistence operations.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def load_from_file(self, file_path: Path, suite_name: str | None = None) -> TestSuiteInfo:
        """
        Load test cases from a file, persist them, and return suite info.

        The file format is detected from the extension. Test cases are
        parsed, validated, and stored in the database as a new test suite.

        Args:
            file_path: Path to the test case file.
            suite_name: Optional name for the test suite. Defaults to filename.

        Returns:
            TestSuiteInfo with the created suite metadata.

        Raises:
            UnsupportedFileFormatError: If the file extension is not supported.
        """
        ext = file_path.suffix.lower()
        if ext not in _PARSERS:
            raise UnsupportedFileFormatError(file_path.name)

        # Parse test cases from file
        parser = _PARSERS[ext]()
        test_cases = parser.parse(file_path)

        # Create suite record
        suite_id = str(uuid.uuid4())
        name = suite_name or file_path.stem
        source_format = _FORMAT_MAP[ext]

        suite = TestSuiteModel(
            id=suite_id,
            name=name,
            source_file=file_path.name,
            source_format=source_format.value,
            total_cases=len(test_cases),
            created_at=datetime.now(timezone.utc),
        )
        self._db.add(suite)

        # Store individual test cases
        for i, tc in enumerate(test_cases):
            tc_model = TestCaseModel(
                id=str(uuid.uuid4()),
                suite_id=suite_id,
                test_id=tc.test_id,
                input_json=json.dumps(tc.input),
                expected_output_json=json.dumps(tc.expected_output) if tc.expected_output else None,
                context_json=json.dumps(tc.context) if tc.context else None,
                ground_truth=tc.ground_truth,
                metadata_json=json.dumps(tc.metadata),
                tags_json=json.dumps(tc.tags),
                sort_order=i,
            )
            self._db.add(tc_model)

        self._db.commit()
        logger.info("Loaded %d test cases into suite '%s' (id=%s)", len(test_cases), name, suite_id)

        return TestSuiteInfo(
            id=suite_id,
            name=name,
            source_file=file_path.name,
            source_format=source_format.value,
            total_cases=len(test_cases),
            created_at=suite.created_at,
        )

    def get_suite(self, suite_id: str) -> TestSuiteInfo:
        """
        Retrieve test suite metadata.

        Args:
            suite_id: The suite's UUID.

        Returns:
            TestSuiteInfo for the requested suite.

        Raises:
            TestSuiteNotFoundError: If the suite does not exist.
        """
        suite = self._db.query(TestSuiteModel).filter(TestSuiteModel.id == suite_id).first()
        if not suite:
            raise TestSuiteNotFoundError(suite_id)
        return TestSuiteInfo(
            id=suite.id,
            name=suite.name,
            description=suite.description or "",
            source_file=suite.source_file,
            source_format=suite.source_format,
            total_cases=suite.total_cases or 0,
            created_at=suite.created_at,
        )

    def get_test_cases(self, suite_id: str) -> list[TestCase]:
        """
        Retrieve all test cases for a suite.

        Args:
            suite_id: The suite's UUID.

        Returns:
            List of TestCase objects, ordered by sort_order.

        Raises:
            TestSuiteNotFoundError: If the suite does not exist.
        """
        # Verify suite exists
        self.get_suite(suite_id)

        cases = (
            self._db.query(TestCaseModel)
            .filter(TestCaseModel.suite_id == suite_id)
            .order_by(TestCaseModel.sort_order)
            .all()
        )

        return [
            TestCase(
                test_id=tc.test_id,
                input=json.loads(tc.input_json) if tc.input_json else {},
                expected_output=json.loads(tc.expected_output_json) if tc.expected_output_json else None,
                context=json.loads(tc.context_json) if tc.context_json else None,
                ground_truth=tc.ground_truth,
                metadata=json.loads(tc.metadata_json) if tc.metadata_json else {},
                tags=json.loads(tc.tags_json) if tc.tags_json else [],
            )
            for tc in cases
        ]

    def list_suites(self) -> list[TestSuiteInfo]:
        """
        List all test suites.

        Returns:
            List of TestSuiteInfo objects, ordered by creation date (newest first).
        """
        suites = self._db.query(TestSuiteModel).order_by(TestSuiteModel.created_at.desc()).all()
        return [
            TestSuiteInfo(
                id=s.id,
                name=s.name,
                description=s.description or "",
                source_file=s.source_file,
                source_format=s.source_format,
                total_cases=s.total_cases or 0,
                created_at=s.created_at,
            )
            for s in suites
        ]

    def delete_suite(self, suite_id: str) -> None:
        """
        Delete a test suite and all its test cases.

        Args:
            suite_id: The suite's UUID.

        Raises:
            TestSuiteNotFoundError: If the suite does not exist.
        """
        suite = self._db.query(TestSuiteModel).filter(TestSuiteModel.id == suite_id).first()
        if not suite:
            raise TestSuiteNotFoundError(suite_id)

        self._db.query(TestCaseModel).filter(TestCaseModel.suite_id == suite_id).delete()
        self._db.delete(suite)
        self._db.commit()
        logger.info("Deleted suite '%s' (id=%s)", suite.name, suite_id)
