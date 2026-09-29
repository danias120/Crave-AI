"""FastAPI route handlers for Dish Radar, Compare, Roulette, Group Dining, and Trails."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.api.dependencies import get_store
from src.data.store import RestaurantStore
from src.models.features import (
    CompareRequest,
    CompareResponse,
    DishSearchRequest,
    DishSearchResponse,
    FoodTrail,
    GroupDiningRequest,
    GroupDiningResponse,
    RouletteRequest,
    RouletteResponse,
)
from src.models.restaurant import Restaurant
from src.services.features_service import (
    compare_restaurants_service,
    get_curated_trails_service,
    search_dishes_service,
    solve_group_dining_service,
    spin_roulette_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Features"])


@router.post("/dish-search", response_model=DishSearchResponse)
def search_dishes_endpoint(
    req: DishSearchRequest,
    store: RestaurantStore = Depends(get_store),
):
    """Search for restaurants excelling at a specific dish or craving."""
    try:
        return search_dishes_service(store, req)
    except Exception as err:
        logger.exception("Dish search failed: %s", err)
        raise HTTPException(status_code=500, detail=f"Dish search failed: {str(err)}")


@router.post("/compare", response_model=CompareResponse)
def compare_restaurants_endpoint(
    req: CompareRequest,
    store: RestaurantStore = Depends(get_store),
):
    """Perform side-by-side comparison of two restaurants with an AI verdict."""
    try:
        return compare_restaurants_service(store, req)
    except Exception as err:
        logger.exception("Compare failed: %s", err)
        raise HTTPException(status_code=500, detail=f"Compare failed: {str(err)}")


@router.post("/roulette", response_model=RouletteResponse)
def spin_roulette_endpoint(
    req: RouletteRequest,
    store: RestaurantStore = Depends(get_store),
):
    """Spin the Crave Roulette for a surprise top-rated dining spot."""
    try:
        return spin_roulette_service(store, req)
    except Exception as err:
        logger.exception("Roulette spin failed: %s", err)
        raise HTTPException(status_code=500, detail=f"Roulette spin failed: {str(err)}")


@router.post("/group-recommendations", response_model=GroupDiningResponse)
def group_dining_endpoint(
    req: GroupDiningRequest,
    store: RestaurantStore = Depends(get_store),
):
    """Find group dining recommendations that harmonize conflicting tastes."""
    try:
        return solve_group_dining_service(store, req)
    except Exception as err:
        logger.exception("Group dining solver failed: %s", err)
        raise HTTPException(status_code=500, detail=f"Group dining failed: {str(err)}")


@router.get("/trails", response_model=List[FoodTrail])
def get_trails_endpoint():
    """Get curated Bangalore food crawls and trails."""
    return get_curated_trails_service()


@router.get("/restaurants/search", response_model=List[Restaurant])
def search_restaurants_quick(
    q: str = Query(..., min_length=1),
    store: RestaurantStore = Depends(get_store),
):
    """Quick search for restaurant names (useful for auto-complete and compare selectors)."""
    q_lower = q.strip().lower()
    matches = []
    for r in store.get_all():
        if q_lower in r.name.lower() or q_lower in r.location.lower():
            matches.append(r)
        if len(matches) >= 20:
            break
    return matches
