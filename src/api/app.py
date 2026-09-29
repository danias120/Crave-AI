"""FastAPI application factory for Crave AI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.data.store import RestaurantStore
from src.api.routes.metadata import router as metadata_router
from src.api.routes.recommendations import router as recommendations_router
from src.api.routes.features import router as features_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load RestaurantStore on startup, clean up on shutdown."""
    logger.info("Loading RestaurantStore...")
    store = RestaurantStore()
    count = len(store.get_all())
    logger.info("RestaurantStore loaded with %d restaurants.", count)
    app.state.store = store
    yield
    logger.info("Shutting down Crave AI API.")


app = FastAPI(
    title="Crave AI — Restaurant Recommendation API",
    description=(
        "AI-powered restaurant recommendation service using Google Gemini. "
        "Filters real Zomato dataset restaurants and returns personalized, "
        "ranked recommendations with AI-generated explanations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Vite dev server and common local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(metadata_router)
app.include_router(recommendations_router)
app.include_router(features_router)


@app.get("/", include_in_schema=False)
def root():
    """Redirect root to API docs."""
    return {
        "message": "Crave AI API is running. Visit /docs for Swagger UI.",
        "docs": "/docs",
    }
