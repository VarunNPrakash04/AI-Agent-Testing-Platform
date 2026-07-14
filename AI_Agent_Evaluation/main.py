"""
Main Entry Point
================
Starts the FastAPI server via Uvicorn.
"""

import uvicorn
from src.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.api.app:create_app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        factory=True,
    )
