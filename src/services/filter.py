"""Restaurant candidate filtering service based on user preferences."""

import logging
from typing import List, Optional

from src.config import settings
from src.data.store import RestaurantStore
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


LOCALITY_CLUSTERS = {
    "church street": [
        "church street",
        "brigade road",
        "mg road",
        "residency road",
        "lavelle road",
        "st. marks road",
        "richmond road",
        "central bangalore",
    ],
    "brigade road": [
        "brigade road",
        "church street",
        "mg road",
        "residency road",
        "lavelle road",
        "st. marks road",
        "richmond road",
    ],
    "mg road": [
        "mg road",
        "church street",
        "brigade road",
        "residency road",
        "lavelle road",
        "st. marks road",
    ],
    "residency road": [
        "residency road",
        "church street",
        "brigade road",
        "mg road",
        "lavelle road",
    ],
    "lavelle road": [
        "lavelle road",
        "church street",
        "residency road",
        "st. marks road",
        "mg road",
    ],
    "koramangala": [
        "koramangala",
        "koramangala 1st block",
        "koramangala 2nd block",
        "koramangala 3rd block",
        "koramangala 4th block",
        "koramangala 5th block",
        "koramangala 6th block",
        "koramangala 7th block",
        "koramangala 8th block",
    ],
    "indiranagar": [
        "indiranagar",
        "100ft road",
        "12th main",
        "old airport road",
        "domlur",
    ],
    "hsr": [
        "hsr",
        "hsr layout",
        "sector 1",
        "sector 2",
        "sector 3",
        "sector 4",
        "sector 5",
        "sector 6",
        "sector 7",
    ],
    "jayanagar": [
        "jayanagar",
        "jayanagar 3rd block",
        "jayanagar 4th block",
        "jayanagar 5th block",
        "jp nagar",
        "basavanagudi",
    ],
    "jp nagar": [
        "jp nagar",
        "jp nagar 1st phase",
        "jp nagar 2nd phase",
        "jp nagar 3rd phase",
        "jp nagar 6th phase",
        "jayanagar",
    ],
    "whitefield": [
        "whitefield",
        "itpl",
        "marathahalli",
        "brookefield",
        "hoodi",
    ],
}

RELATED_CUISINES = {
    "bakery": ["bakery", "desserts", "cafe", "fast food"],
    "cafe": ["cafe", "bakery", "desserts", "beverages"],
    "desserts": ["desserts", "bakery", "ice cream", "cafe"],
    "mughlai": ["mughlai", "north indian", "biryani", "kebab", "arabian"],
    "biryani": ["biryani", "north indian", "south indian", "mughlai", "andhra", "arabian"],
    "italian": ["italian", "pizza", "pasta"],
    "pizza": ["pizza", "italian", "fast food"],
    "burger": ["burger", "fast food", "american"],
    "chinese": ["chinese", "dim sum", "asian", "momos"],
    "japanese": ["japanese", "sushi", "ramen"],
    "korean": ["korean"],
    "african": ["african", "ethiopian"],
    "arabian": ["arabian", "middle eastern", "lebanese", "mandi"],
    "afghani": ["afghani", "mughlai", "kebab"],
}


def matches_location(
    restaurant_location: str,
    target_location: str,
    restaurant_address: Optional[str] = None,
    allow_clusters: bool = False,
) -> bool:
    """Case-insensitive location matching supporting exact match, substring match, address match, and locality clusters."""
    r_loc = restaurant_location.strip().lower()
    t_loc = target_location.strip().lower()

    if r_loc == t_loc or t_loc in r_loc or r_loc in t_loc:
        return True

    if restaurant_address and t_loc in restaurant_address.strip().lower():
        return True

    if allow_clusters and t_loc in LOCALITY_CLUSTERS:
        cluster = LOCALITY_CLUSTERS[t_loc]
        if any(c in r_loc or r_loc in c for c in cluster):
            return True
        if restaurant_address:
            addr_lower = restaurant_address.lower()
            if any(c in addr_lower for c in cluster):
                return True

    return False


def matches_cuisine(
    restaurant_cuisines: List[str],
    target_cuisine: Optional[str],
    allow_related: bool = False,
) -> bool:
    """Case-insensitive cuisine matching supporting exact cuisine, Afghan/Afghani equivalence, and related cuisines."""
    if not target_cuisine or target_cuisine.strip().lower() in ("any", "all"):
        return True

    t_cuisine = target_cuisine.strip().lower()
    if t_cuisine == "afghan":
        t_cuisine = "afghani"

    for c in restaurant_cuisines:
        c_clean = c.strip().lower()
        if c_clean == "afghan":
            c_clean = "afghani"
        if c_clean == t_cuisine or t_cuisine in c_clean or c_clean in t_cuisine:
            return True

    if allow_related and t_cuisine in RELATED_CUISINES:
        related_list = RELATED_CUISINES[t_cuisine]
        for c in restaurant_cuisines:
            c_clean = c.strip().lower()
            if c_clean == "afghan":
                c_clean = "afghani"
            if any(rel in c_clean or c_clean in rel for rel in related_list):
                return True

    return False


def filter_restaurants(
    store: RestaurantStore,
    prefs: UserPreferences,
    max_candidates: Optional[int] = None,
    progressive_relaxation: bool = False,
) -> List[Restaurant]:
    """Filter restaurants deterministically based on user preferences.

    Applies progressive filter relaxation if strict criteria return 0 candidates:
    - Pass 1: Strict match (exact location/address, exact cuisine, target budget, min_rating)
    - Pass 2: Expand to nearby locality cluster & address matches
    - Pass 3: Expand budget constraints
    - Pass 4: Lower min_rating threshold
    - Pass 5: Related cuisines fallback
    """
    limit = max_candidates if max_candidates is not None else settings.max_candidates_for_gemini
    all_restaurants = store.get_all()

    is_halal_req = "halal" in (prefs.additional_preferences or "").lower()

    # Pass 1: Strict matching
    candidates: List[Restaurant] = []
    for r in all_restaurants:
        if prefs.is_veg_only and not r.is_veg:
            continue
        if is_halal_req and not r.is_halal:
            continue
        if not matches_location(r.location, prefs.location, r.address, allow_clusters=False):
            continue
        if not matches_cuisine(r.cuisines, prefs.cuisine, allow_related=False):
            continue
        if r.rating < prefs.min_rating:
            continue
        if r.budget_tier != prefs.budget:
            continue
        candidates.append(r)

    if candidates or not progressive_relaxation:
        candidates.sort(
            key=lambda r: (1 if (is_halal_req and r.is_halal) else 0, r.rating, r.votes or 0),
            reverse=True,
        )
        return candidates[:limit]

    seen_ids = {r.id for r in candidates}

    # Pass 2: Expand to nearby locality cluster
    for r in all_restaurants:
        if r.id in seen_ids:
            continue
        if prefs.is_veg_only and not r.is_veg:
            continue
        if is_halal_req and not r.is_halal:
            continue
        if not matches_location(r.location, prefs.location, r.address, allow_clusters=True):
            continue
        if not matches_cuisine(r.cuisines, prefs.cuisine, allow_related=False):
            continue
        if r.rating < prefs.min_rating:
            continue
        if r.budget_tier != prefs.budget:
            continue
        candidates.append(r)
        seen_ids.add(r.id)

    if candidates:
        candidates.sort(
            key=lambda r: (1 if (is_halal_req and r.is_halal) else 0, r.rating, r.votes or 0),
            reverse=True,
        )
        return candidates[:limit]

    # Pass 3: Broaden budget tier
    for r in all_restaurants:
        if r.id in seen_ids:
            continue
        if prefs.is_veg_only and not r.is_veg:
            continue
        if is_halal_req and not r.is_halal:
            continue
        if not matches_location(r.location, prefs.location, r.address, allow_clusters=True):
            continue
        if not matches_cuisine(r.cuisines, prefs.cuisine, allow_related=False):
            continue
        if r.rating < prefs.min_rating:
            continue
        candidates.append(r)
        seen_ids.add(r.id)

    if candidates:
        candidates.sort(
            key=lambda r: (1 if (is_halal_req and r.is_halal) else 0, r.rating, r.votes or 0),
            reverse=True,
        )
        return candidates[:limit]

    # Pass 4: Lower rating floor
    for r in all_restaurants:
        if r.id in seen_ids:
            continue
        if prefs.is_veg_only and not r.is_veg:
            continue
        if is_halal_req and not r.is_halal:
            continue
        if not matches_location(r.location, prefs.location, r.address, allow_clusters=True):
            continue
        if not matches_cuisine(r.cuisines, prefs.cuisine, allow_related=False):
            continue
        if r.rating < max(3.0, prefs.min_rating - 0.7):
            continue
        candidates.append(r)
        seen_ids.add(r.id)

    if candidates:
        candidates.sort(
            key=lambda r: (1 if (is_halal_req and r.is_halal) else 0, r.rating, r.votes or 0),
            reverse=True,
        )
        return candidates[:limit]

    # Pass 5: Related cuisines
    for r in all_restaurants:
        if r.id in seen_ids:
            continue
        if prefs.is_veg_only and not r.is_veg:
            continue
        if is_halal_req and not r.is_halal:
            continue
        if not matches_location(r.location, prefs.location, r.address, allow_clusters=True):
            continue
        if not matches_cuisine(r.cuisines, prefs.cuisine, allow_related=True):
            continue
        candidates.append(r)
        seen_ids.add(r.id)

    # Sort deterministically: halal match first (if requested), highest rating, then highest votes count
    candidates.sort(
        key=lambda r: (1 if (is_halal_req and r.is_halal) else 0, r.rating, r.votes or 0),
        reverse=True,
    )

    truncated = candidates[:limit]

    logger.info(
        "Filtered %d restaurants -> %d candidates (capped at %d) for location='%s', cuisine='%s', budget='%s', min_rating=%.1f",
        len(all_restaurants),
        len(truncated),
        limit,
        prefs.location,
        prefs.cuisine or "Any",
        prefs.budget.value,
        prefs.min_rating,
    )

    return truncated
