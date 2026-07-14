"""Workspace-level launcher for the AI Agent Evaluation app."""

from pathlib import Path
import runpy
import sys


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent / "AI_Agent_Evaluation"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    runpy.run_path(str(project_root / "main.py"), run_name="__main__")
