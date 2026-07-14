import os
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status

from src.api.dependencies import get_test_case_manager
from src.core.models import TestSuiteInfo, TestCase
from src.testcases.manager import TestCaseManager

router = APIRouter(prefix="/test-suites", tags=["Test Suites"])


@router.post("/upload", response_model=TestSuiteInfo, status_code=status.HTTP_201_CREATED)
def upload_test_suite(
    file: UploadFile = File(...),
    manager: TestCaseManager = Depends(get_test_case_manager),
):
    # Save uploaded file to temp path
    fd, path = tempfile.mkstemp(suffix=Path(file.filename).suffix)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(file.file.read())
        
        # Load through manager
        return manager.load_from_file(Path(path), suite_name=Path(file.filename).stem)
    finally:
        os.unlink(path)


@router.get("", response_model=list[TestSuiteInfo])
def list_test_suites(
    manager: Annotated[TestCaseManager, Depends(get_test_case_manager)],
):
    return manager.list_suites()


@router.get("/{suite_id}", response_model=TestSuiteInfo)
def get_test_suite(
    suite_id: str,
    manager: Annotated[TestCaseManager, Depends(get_test_case_manager)],
):
    return manager.get_suite(suite_id)


@router.get("/{suite_id}/cases", response_model=list[TestCase])
def get_test_cases(
    suite_id: str,
    manager: Annotated[TestCaseManager, Depends(get_test_case_manager)],
):
    return manager.get_test_cases(suite_id)


@router.delete("/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_suite(
    suite_id: str,
    manager: Annotated[TestCaseManager, Depends(get_test_case_manager)],
):
    manager.delete_suite(suite_id)
