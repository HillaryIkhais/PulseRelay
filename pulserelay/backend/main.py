"""PulseRelay - Hands-free AI agent for paramedic patient transport."""

import os
import sys
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router

app = FastAPI(
    title="PulseRelay",
    description="Hands-free AI agent for paramedic patient transport",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "service": "PulseRelay",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "environment": os.environ.get("ENVIRONMENT", "development"),
    }


app.include_router(router, prefix="/api")

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
