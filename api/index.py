"""Vercel Serverless Function entrypoint for FastAPI backend."""

import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.metadata import router as metadata_router
from src.api.routes.recommendations import router as recommendations_router
from src.api.routes.features import router as features_router

# Direct top-level FastAPI instantiation for Vercel AST parser
app = FastAPI(
    title="Crave AI — Restaurant Recommendation API",
    description="AI-powered restaurant recommendation engine for Bangalore.",
    version="1.0.0",
)

# Universal CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with dual-prefix for serverless compatibility
app.include_router(metadata_router, prefix="/api")
app.include_router(metadata_router)

app.include_router(recommendations_router, prefix="/api")
app.include_router(recommendations_router)

app.include_router(features_router, prefix="/api")
app.include_router(features_router)


@app.get("/", include_in_schema=False)
def root_endpoint():
    return {
        "status": "ok",
        "service": "Crave AI API",
        "message": "Welcome to Crave AI API on Vercel.",
    }


# Explicit top-level aliases for all Vercel detection patterns
application = app
handler = app

__all__ = ["app", "application", "handler"]
