"""Metadata and health-check endpoints."""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends

from src.api.dependencies import get_store
from src.data.store import RestaurantStore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["metadata"])


@router.get("/health", summary="Health check")
def health_check(store: RestaurantStore = Depends(get_store)) -> Dict:
    """Return service health status and loaded restaurant count."""
    return {
        "status": "ok",
        "restaurant_count": len(store.get_all()),
    }


@router.get("/locations", summary="List distinct locations")
def get_locations(store: RestaurantStore = Depends(get_store)) -> List[str]:
    """Return sorted list of distinct restaurant locations."""
    return sorted(store.distinct_locations())


@router.get("/cuisines", summary="List distinct cuisines")
def get_cuisines(store: RestaurantStore = Depends(get_store)) -> List[str]:
    """Return sorted list of distinct cuisines across all restaurants."""
    return sorted(store.distinct_cuisines())
