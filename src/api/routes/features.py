"""FastAPI route handlers for Dish Radar, Compare, Roulette, Group Dining, and Trails."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request

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

router = APIRouter(prefix="/api", tags=["Advanced Features"])


def _get_store(request: Request) -> RestaurantStore:
    store = getattr(request.app.state, "store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="RestaurantStore is not initialized yet.")
    return store


@router.post("/dish-search", response_model=DishSearchResponse)
def search_dishes_endpoint(req: DishSearchRequest, request: Request):
    """Search for restaurants excelling at a specific dish or craving."""
    store = _get_store(request)
    return search_dishes_service(store, req)


@router.post("/compare", response_model=CompareResponse)
def compare_restaurants_endpoint(req: CompareRequest, request: Request):
    """Perform side-by-side comparison of two restaurants with an AI verdict."""
    store = _get_store(request)
    return compare_restaurants_service(store, req)


@router.post("/roulette", response_model=RouletteResponse)
def spin_roulette_endpoint(req: RouletteRequest, request: Request):
    """Spin the Crave Roulette for a surprise top-rated dining spot."""
    store = _get_store(request)
    return spin_roulette_service(store, req)


@router.post("/group-recommendations", response_model=GroupDiningResponse)
def group_dining_endpoint(req: GroupDiningRequest, request: Request):
    """Find group dining recommendations that harmonize conflicting tastes."""
    store = _get_store(request)
    return solve_group_dining_service(store, req)


@router.get("/trails", response_model=List[FoodTrail])
def get_trails_endpoint():
    """Get curated Bangalore food crawls and trails."""
    return get_curated_trails_service()


@router.get("/restaurants/search", response_model=List[Restaurant])
def search_restaurants_quick(
    q: str = Query(..., min_length=1),
    request: Request = None,
):
    """Quick search for restaurant names (useful for auto-complete and compare selectors)."""
    store = _get_store(request)
    q_lower = q.strip().lower()
    matches = []
    for r in store.get_all():
        if q_lower in r.name.lower() or q_lower in r.location.lower():
            matches.append(r)
        if len(matches) >= 20:
            break
    return matches
