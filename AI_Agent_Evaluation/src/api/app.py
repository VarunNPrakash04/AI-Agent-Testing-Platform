"""
FastAPI Application Factory
===========================
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from src.api.routes import agents, dashboard, evaluators, executions, history, reports, test_suites
from src.core.config import get_settings
from src.core.exceptions import PlatformError
from src.db.database import init_db
from src.db.database import SessionLocal
from src.db.models import AgentModel, TestSuiteModel
import json

# Import plugins to trigger auto-registration
import src.connectors.plugins  # noqa: F401
import src.evaluation.plugins  # noqa: F401


def seed_demo_data() -> None:
    init_db()
    session = SessionLocal()
    try:
        demo_exists = session.query(AgentModel).filter(AgentModel.name == "Sample Harvest Agent").first()
        if not demo_exists:
            session.add(
                AgentModel(
                    id="demo-agent",
                    name="Sample Harvest Agent",
                    description="Demo harvesting agent for the MVP experience",
                    agent_type="harvesting",
                    connector_type="python_class",
                    python_class_path="sample_agents.python_agent.DummyHarvestAgent",
                    input_schema_json=json.dumps({"datasource_id": "string", "metadata_type": "string"}),
                    output_schema_json=json.dumps({"status": "string", "metrics": []}),
                    supports_rag=False,
                    supports_tool_calling=False,
                    timeout_seconds=30,
                    metadata_json=json.dumps({"demo": True}),
                    is_active=True,
                )
            )
        sample_suite_exists = session.query(TestSuiteModel).filter(TestSuiteModel.name == "Sample Harvest Suite").first()
        if not sample_suite_exists:
            session.add(
                TestSuiteModel(
                    id="demo-suite",
                    name="Sample Harvest Suite",
                    description="Seeded sample suite for immediate testing",
                    source_file="sample_harvest_tests.json",
                    source_format="json",
                    total_cases=2,
                    metadata_json=json.dumps({"demo": True}),
                )
            )
        session.commit()
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    seed_demo_data()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    settings = get_settings()
    seed_demo_data()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        description="Generic AI Agent Testing Platform API",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handler
    @app.exception_handler(PlatformError)
    async def platform_error_handler(request: Request, exc: PlatformError):
        # Determine status code by exception code suffix
        status_code = 400
        if "NOT_FOUND" in exc.code:
            status_code = 404
        elif "UNAUTHORIZED" in exc.code:
            status_code = 401
            
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    # Routers
    app.include_router(agents.router, prefix=settings.api_prefix)
    app.include_router(dashboard.router, prefix=settings.api_prefix)
    app.include_router(test_suites.router, prefix=settings.api_prefix)
    app.include_router(evaluators.router, prefix=settings.api_prefix)
    app.include_router(executions.router, prefix=settings.api_prefix)
    app.include_router(reports.router, prefix=settings.api_prefix)
    app.include_router(history.router, prefix=settings.api_prefix)

    # Serve Frontend
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

    return app
