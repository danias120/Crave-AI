import logging
from typing import Optional
from fastapi import Request

from src.data.store import RestaurantStore

logger = logging.getLogger(__name__)

_global_store: Optional[RestaurantStore] = None


def get_store(request: Request) -> RestaurantStore:
    """Retrieve the RestaurantStore from app state or lazy-initialize singleton fallback."""
    global _global_store
    if request is not None:
        store = getattr(getattr(request, "app", None), "state", None)
        if store is not None and hasattr(store, "store") and store.store is not None:
            return store.store

    if _global_store is None:
        logger.info("Initializing global RestaurantStore instance...")
        _global_store = RestaurantStore()
    return _global_store
