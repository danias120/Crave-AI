"""In-memory store for querying restaurants, locations, and cuisines."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.config import DATA_CACHE_DIR
from src.data.loader import DEFAULT_CACHE_FILE, load_and_process_dataset
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


class RestaurantStore:
    """In-memory collection of restaurants with fast lookup and filtering capabilities."""

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        auto_load: bool = True,
        initial_restaurants: Optional[List[Restaurant]] = None,
    ) -> None:
        self.cache_path = cache_path or DEFAULT_CACHE_FILE
        self._restaurants: List[Restaurant] = []
        self._by_id: Dict[str, Restaurant] = {}
        self._distinct_locations: List[str] = []
        self._distinct_cuisines: List[str] = []

        if initial_restaurants is not None:
            self.set_restaurants(initial_restaurants)
        elif auto_load:
            self.load()

    def load(self, force_reload: bool = False) -> None:
        """Load restaurants from cache or fetch from Hugging Face dataset."""
        restaurants = load_and_process_dataset(cache_path=self.cache_path, force_reload=force_reload)
        self.set_restaurants(restaurants)

    def set_restaurants(self, restaurants: List[Restaurant]) -> None:
        """Populate store with a list of restaurants and rebuild index and metadata."""
        self._restaurants = restaurants
        self._by_id = {r.id: r for r in restaurants}

        # Precompute distinct sorted locations
        locations_set = {r.location for r in restaurants if r.location}
        self._distinct_locations = sorted(locations_set)

        # Precompute distinct sorted cuisines (flattened)
        cuisines_set = {c for r in restaurants for c in r.cuisines if c}
        self._distinct_cuisines = sorted(cuisines_set)

        logger.info(
            "RestaurantStore initialized with %d restaurants, %d locations, %d cuisines",
            len(self._restaurants),
            len(self._distinct_locations),
            len(self._distinct_cuisines),
        )

    def get_all(self) -> List[Restaurant]:
        """Return all restaurants in the store."""
        return list(self._restaurants)

    def get_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        """Look up a restaurant by its unique ID."""
        return self._by_id.get(restaurant_id)

    def distinct_locations(self) -> List[str]:
        """Return sorted list of all unique restaurant locations/cities."""
        return list(self._distinct_locations)

    def distinct_cuisines(self) -> List[str]:
        """Return sorted list of all unique cuisines."""
        return list(self._distinct_cuisines)

    def __len__(self) -> int:
        return len(self._restaurants)


if __name__ == "__main__":
    store = RestaurantStore()
    print(f"Total restaurants loaded: {len(store)}")
    print(f"Sample locations (5/{len(store.distinct_locations())}): {store.distinct_locations()[:5]}")
    print(f"Sample cuisines (5/{len(store.distinct_cuisines())}): {store.distinct_cuisines()[:5]}")
    sample_rest = store.get_all()[0] if store else None
    if sample_rest:
        print(f"Sample restaurant: {sample_rest.name} ({sample_rest.location}) - Rating: {sample_rest.rating}, Budget: {sample_rest.budget_tier.value}")
