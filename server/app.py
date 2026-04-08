"""
Email Triage Environment - FastAPI Server Entry Point

This module serves as the OpenEnv-compliant entry point for the email triage environment.
It imports and exposes the FastAPI application from app.main for deployment.
"""

from app.main import app

__all__ = ["app"]
