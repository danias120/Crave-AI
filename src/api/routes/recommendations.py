"""Recommendation endpoint — the core API route."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.api.dependencies import get_store
from src.data.store import RestaurantStore
from src.models.preferences import UserPreferences
from src.models.recommendation import RecommendationResponse
from src.services.orchestrator import get_recommendations

logger = logging.getLogger(__name__)

router = APIRouter(tags=["recommendations"])


class RecommendationRequest(BaseModel):
    """Request body for the recommendation endpoint."""

    location: str = Field(..., description="Target locality or city")
    budget: str = Field(
        default="medium",
        description="Budget tier: 'low', 'medium', 'high', or numeric amount like '1500'",
    )
    cuisine: Optional[str] = Field(default=None, description="Preferred cuisine or None for any")
    min_rating: float = Field(default=3.5, ge=0.0, le=5.0, description="Minimum rating (0-5)")
    additional_preferences: Optional[str] = Field(
        default=None, max_length=500, description="Free-text preferences"
    )
    is_veg_only: bool = Field(
        default=False, description="Filter exclusively for pure vegetarian restaurants"
    )


class ErrorResponse(BaseModel):
    """Structured error response."""

    error: str
    detail: str
    status_code: int


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get AI-powered restaurant recommendations",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        503: {"model": ErrorResponse, "description": "Gemini service unavailable"},
    },
)
def recommend(
    request: RecommendationRequest,
    store: RestaurantStore = Depends(get_store),
) -> RecommendationResponse:
    """Accept user preferences, filter restaurants, call Gemini, and return ranked recommendations."""
    try:
        prefs = UserPreferences(
            location=request.location,
            budget=request.budget,
            cuisine=request.cuisine,
            min_rating=request.min_rating,
            additional_preferences=request.additional_preferences,
            is_veg_only=request.is_veg_only,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = get_recommendations(store, prefs)
        return result
    except RuntimeError as e:
        error_msg = str(e)
        if "GEMINI_API_KEY" in error_msg or "Gemini API" in error_msg:
            raise HTTPException(
                status_code=503,
                detail=f"Recommendation engine unavailable: {error_msg}",
            )
        raise HTTPException(status_code=500, detail=f"Internal error: {error_msg}")
    except Exception as e:
        logger.exception("Unexpected error in recommendation endpoint")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
