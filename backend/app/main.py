"""
ShadeWise FastAPI entrypoint.

Run from the backend/ directory:
  uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings

# Avoid logging request bodies or secrets.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shadewise")

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not settings.has_openai_key:
        logger.warning(
            "OPENAI_API_KEY is not set. /api/analyze-shade will return 503 until configured."
        )
    else:
        logger.info("ShadeWise backend ready (OpenAI configured).")
    yield


app = FastAPI(
    title="ShadeWise API",
    description="Foundation shade mismatch analysis — Phase 1",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)
