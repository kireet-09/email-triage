"""
Email Triage Environment - FastAPI Server Entry Point

This module serves as the OpenEnv-compliant entry point for the email triage environment.
It imports and exposes the FastAPI application from app.main for deployment.
"""

import uvicorn

from app.main import app


def main():
    """
    Main entry point for the email triage environment server.
    
    Runs the FastAPI application using Uvicorn on port 7860
    (required for HF Spaces Docker SDK).
    """
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860,
        log_level="info"
    )


if __name__ == "__main__":
    main()


__all__ = ["app", "main"]
