from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from src.api.dependencies import get_history_manager, get_report_generator
from src.core.interfaces import BaseReportGenerator
from src.core.models import ReportInfo
from src.history.manager import HistoryManager

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/{run_id}", response_model=ReportInfo)
def generate_report(
    run_id: str,
    generator: Annotated[BaseReportGenerator, Depends(get_report_generator)],
    manager: Annotated[HistoryManager, Depends(get_history_manager)],
):
    result = manager.get_run(run_id)
    return generator.generate(result)


@router.get("/{run_id}/download")
def download_report(
    run_id: str,
    generator: Annotated[BaseReportGenerator, Depends(get_report_generator)],
    manager: Annotated[HistoryManager, Depends(get_history_manager)],
):
    result = manager.get_run(run_id)
    report_info = generator.generate(result)
    return FileResponse(
        path=report_info.file_path,
        filename=f"report_{run_id}.html",
        media_type="text/html",
    )
