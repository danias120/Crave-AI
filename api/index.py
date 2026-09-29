"""Vercel Serverless Function entrypoint for FastAPI backend."""

import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from src.api.app import app
except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="Crave AI Error Handler")

    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def catch_all(path_name: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Serverless Initialization Error",
                "detail": str(e),
                "traceback": traceback.format_exc(),
            },
        )

# Export ASGI app and handler for universal Vercel Python runtime compatibility
handler = app
__all__ = ["app", "handler"]
