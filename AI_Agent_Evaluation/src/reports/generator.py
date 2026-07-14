"""
HTML Report Generator
=====================

Generates static HTML reports from execution results using Jinja2 templates.
"""

import logging
from pathlib import Path
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

from src.core.interfaces import BaseReportGenerator
from src.core.models import ExecutionRunResult, ReportInfo
from src.core.config import get_settings

logger = logging.getLogger(__name__)


class HTMLReportGenerator(BaseReportGenerator):
    """
    Generates HTML reports using Jinja2.

    The templates are loaded from ``src/reports/templates/``.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        template_dir = Path(__file__).parent / "templates"
        self._env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)

        # Ensure reports directory exists
        self._settings.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, result: ExecutionRunResult) -> ReportInfo:
        """
        Generate an HTML report and save it to the configured reports directory.

        Args:
            result: The execution run result to format.

        Returns:
            ReportInfo pointing to the generated file.
        """
        filename = f"report_{result.agent_id}_{result.run_id}.html"
        output_path = self._settings.reports_dir / filename
        return ReportInfo(
            run_id=result.run_id,
            format="html",
            file_path=str(self.export(result, output_path)),
            generated_at=datetime.now(timezone.utc),
        )

    def export(self, result: ExecutionRunResult, output_path: Path) -> Path:
        """
        Render the HTML template and write it to disk.

        Args:
            result: The execution run result to format.
            output_path: Where to save the file.

        Returns:
            The absolute path to the generated file.
        """
        template = self._env.get_template("report.html")
        html_content = template.render(result=result)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("Generated HTML report at '%s'", output_path)
        return output_path.resolve()

    def get_supported_formats(self) -> list[str]:
        return ["html"]
