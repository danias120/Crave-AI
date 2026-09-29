"""Dependency injection for FastAPI endpoints."""

import logging
from typing import Generator

from fastapi import Request

from src.data.store import RestaurantStore

logger = logging.getLogger(__name__)


def get_store(request: Request) -> RestaurantStore:
    """Retrieve the RestaurantStore from app state (loaded at startup)."""
    store: RestaurantStore = request.app.state.store
    return store
