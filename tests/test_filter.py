"""Unit tests for UserPreferences model and restaurant filter service."""

import pytest
from pydantic import ValidationError

from src.data.store import RestaurantStore
from src.models.preferences import UserPreferences
from src.models.restaurant import BudgetTier, Restaurant
from src.services.filter import filter_restaurants, matches_cuisine, matches_location


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_store() -> RestaurantStore:
    """Fixture providing a mock store with controlled restaurant records."""
    restaurants = [
        Restaurant(
            id="r1",
            name="Spice Terrace",
            location="MG Road",
            cuisines=["North Indian", "Mughlai"],
            rating=4.6,
            cost_for_two=1500,
            budget_tier=BudgetTier.HIGH,
            votes=1200,
        ),
        Restaurant(
            id="r2",
            name="Pasta Street",
            location="Indiranagar",
            cuisines=["Italian", "Pizza", "Pasta"],
            rating=4.4,
            cost_for_two=750,
            budget_tier=BudgetTier.MEDIUM,
            votes=850,
        ),
        Restaurant(
            id="r3",
            name="Milano Pizzeria",
            location="Indiranagar",
            cuisines=["Italian", "Pizza"],
            rating=4.1,
            cost_for_two=600,
            budget_tier=BudgetTier.MEDIUM,
            votes=400,
        ),
        Restaurant(
            id="r4",
            name="Budget Bites",
            location="Indiranagar",
            cuisines=["Italian", "Fast Food"],
            rating=3.8,
            cost_for_two=300,
            budget_tier=BudgetTier.LOW,
            votes=150,
        ),
        Restaurant(
            id="r5",
            name="Dosa Corner",
            location="Basavanagudi",
            cuisines=["South Indian", "Fast Food"],
            rating=4.5,
            cost_for_two=200,
            budget_tier=BudgetTier.LOW,
            votes=2300,
        ),
        Restaurant(
            id="r6",
            name="Chinatown Express",
            location="Koramangala",
            cuisines=["Chinese", "Asian"],
            rating=3.9,
            cost_for_two=500,
            budget_tier=BudgetTier.MEDIUM,
            votes=310,
        ),
        Restaurant(
            id="r7",
            name="Dragon House",
            location="Koramangala",
            cuisines=["Chinese", "Thai"],
            rating=4.7,
            cost_for_two=1200,
            budget_tier=BudgetTier.HIGH,
            votes=1900,
        ),
    ]
    return RestaurantStore(auto_load=False, initial_restaurants=restaurants)


# ==============================================================================
# UserPreferences Model Tests
# ==============================================================================


def test_user_preferences_valid():
    """Test valid UserPreferences instantiation."""
    prefs = UserPreferences(
        location="Indiranagar",
        budget="medium",  # type: ignore
        cuisine="Italian",
        min_rating=4.0,
        additional_preferences="quiet atmosphere, romantic",
    )
    assert prefs.location == "Indiranagar"
    assert prefs.budget == BudgetTier.MEDIUM
    assert prefs.cuisine == "Italian"
    assert prefs.min_rating == 4.0
    assert prefs.additional_preferences == "quiet atmosphere, romantic"


def test_user_preferences_empty_fields():
    """Test that empty location raises ValidationError and empty cuisine converts to None."""
    with pytest.raises(ValidationError):
        UserPreferences(location="   ", budget="medium", cuisine="Italian")  # type: ignore

    # Empty cuisine should be accepted as None (meaning any cuisine)
    prefs = UserPreferences(location="Indiranagar", budget="medium", cuisine="")  # type: ignore
    assert prefs.cuisine is None


def test_user_preferences_budget_coercion():
    """Test budget tier string coercion and invalid enum rejection."""
    p1 = UserPreferences(location="Delhi", budget="LOW", cuisine="North Indian")  # type: ignore
    assert p1.budget == BudgetTier.LOW

    p2 = UserPreferences(location="Delhi", budget="high", cuisine="North Indian")  # type: ignore
    assert p2.budget == BudgetTier.HIGH

    with pytest.raises(ValidationError):
        UserPreferences(location="Delhi", budget="ultra-luxury", cuisine="North Indian")  # type: ignore


def test_user_preferences_rating_validation():
    """Test rating bounds and invalid values."""
    with pytest.raises(ValidationError):
        UserPreferences(location="Delhi", budget="low", cuisine="North Indian", min_rating=5.5)  # type: ignore

    with pytest.raises(ValidationError):
        UserPreferences(location="Delhi", budget="low", cuisine="North Indian", min_rating=-0.5)  # type: ignore


def test_user_preferences_free_text_sanitization():
    """Test that control characters are stripped and long text is capped."""
    prefs = UserPreferences(
        location="Delhi",
        budget="low",  # type: ignore
        cuisine="North Indian",
        additional_preferences="Family friendly \x00\x07with kids",
    )
    assert prefs.additional_preferences == "Family friendly with kids"

    # Empty string should become None
    prefs_empty = UserPreferences(
        location="Delhi",
        budget="low",  # type: ignore
        cuisine="North Indian",
        additional_preferences="   ",
    )
    assert prefs_empty.additional_preferences is None


# ==============================================================================
# Helper Matching Tests
# ==============================================================================


def test_matches_location():
    """Test case-insensitive and locality containment matching."""
    assert matches_location("Indiranagar", "indiranagar")
    assert matches_location("Koramangala 5th Block", "Koramangala")
    assert matches_location("Koramangala", "Koramangala 5th Block")
    assert not matches_location("Whitefield", "Indiranagar")


def test_matches_cuisine():
    """Test case-insensitive cuisine matching."""
    cuisines = ["North Indian", "Mughlai", "Biryani"]
    assert matches_cuisine(cuisines, "north indian")
    assert matches_cuisine(cuisines, "Indian")
    assert matches_cuisine(cuisines, "biryani")
    assert not matches_cuisine(cuisines, "Italian")


# ==============================================================================
# Filter Service Tests
# ==============================================================================


def test_filter_by_location_and_cuisine(sample_store: RestaurantStore):
    """Test filtering by location and cuisine returns matching subset."""
    prefs = UserPreferences(
        location="Indiranagar",
        budget=BudgetTier.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
    )
    results = filter_restaurants(sample_store, prefs)
    assert len(results) == 2
    assert {r.id for r in results} == {"r2", "r3"}
    # Verify sorted by rating desc
    assert results[0].id == "r2"
    assert results[0].rating == 4.4
    assert results[1].id == "r3"
    assert results[1].rating == 4.1


def test_filter_by_rating_floor(sample_store: RestaurantStore):
    """Test that rating threshold excludes lower-rated candidates."""
    prefs = UserPreferences(
        location="Indiranagar",
        budget=BudgetTier.LOW,
        cuisine="Italian",
        min_rating=4.0,  # Budget Bites has rating 3.8
    )
    results = filter_restaurants(sample_store, prefs)
    assert len(results) == 0


def test_filter_by_budget_tier(sample_store: RestaurantStore):
    """Test budget tier filtering separates high vs medium vs low."""
    prefs_high = UserPreferences(
        location="Koramangala",
        budget=BudgetTier.HIGH,
        cuisine="Chinese",
        min_rating=3.5,
    )
    results_high = filter_restaurants(sample_store, prefs_high)
    assert len(results_high) == 1
    assert results_high[0].id == "r7"

    prefs_med = UserPreferences(
        location="Koramangala",
        budget=BudgetTier.MEDIUM,
        cuisine="Chinese",
        min_rating=3.5,
    )
    results_med = filter_restaurants(sample_store, prefs_med)
    assert len(results_med) == 1
    assert results_med[0].id == "r6"


def test_filter_zero_matches(sample_store: RestaurantStore):
    """Test scenario where strict or non-existent criteria yield zero matches."""
    prefs = UserPreferences(
        location="NonExistentCity",
        budget=BudgetTier.LOW,
        cuisine="Mexican",
        min_rating=4.9,
    )
    results = filter_restaurants(sample_store, prefs)
    assert results == []


def test_filter_over_cap_truncation(sample_store: RestaurantStore):
    """Test that candidate list is truncated to max_candidates and highest ranked are kept."""
    prefs = UserPreferences(
        location="Indiranagar",
        budget=BudgetTier.MEDIUM,
        cuisine="Italian",
        min_rating=3.0,
    )
    # Both r2 (4.4) and r3 (4.1) match, but cap at 1
    results = filter_restaurants(sample_store, prefs, max_candidates=1)
    assert len(results) == 1
    assert results[0].id == "r2"
    assert results[0].rating == 4.4


def test_filter_real_cache_store():
    """Test filter against the real cached restaurant dataset."""
    store = RestaurantStore()
    assert len(store) > 0

    prefs = UserPreferences(
        location="Banashankari",
        budget=BudgetTier.MEDIUM,
        cuisine="North Indian",
        min_rating=4.0,
    )
    results = filter_restaurants(store, prefs)
    assert len(results) > 0
    assert len(results) <= 30
    for r in results:
        assert r.rating >= 4.0
        assert r.budget_tier == BudgetTier.MEDIUM
        assert any("indian" in c.lower() for c in r.cuisines)


def test_filter_church_street_bakery():
    """Test that searching Church Street + Bakery returns rich results."""
    store = RestaurantStore()
    prefs = UserPreferences(
        location="Church Street",
        budget=BudgetTier.MEDIUM,
        cuisine="Bakery",
        min_rating=3.5,
    )
    results = filter_restaurants(store, prefs, progressive_relaxation=True)
    assert len(results) >= 5
    # Verify top spots like Lavonne, Brik Oven, Glen's Bakehouse are returned
    names = [r.name for r in results]
    assert any("Glen's Bakehouse" in n or "Magnolia" in n or "Brik Oven" in n or "Lavonne" in n for n in names)


def test_filter_progressive_relaxation():
    """Test that progressive relaxation finds results for tight criteria across nearby clusters."""
    store = RestaurantStore()
    # High rating requirement on Church Street for French cuisine
    prefs = UserPreferences(
        location="Church Street",
        budget=BudgetTier.HIGH,
        cuisine="French",
        min_rating=4.0,
    )
    results = filter_restaurants(store, prefs, progressive_relaxation=True)
    assert len(results) > 0


def test_filter_pure_veg_only():
    """Test that setting is_veg_only=True returns exclusively vegetarian restaurants."""
    store = RestaurantStore()
    prefs = UserPreferences(
        location="Basavanagudi",
        budget=BudgetTier.LOW,
        cuisine="South Indian",
        min_rating=4.0,
        is_veg_only=True,
    )
    results = filter_restaurants(store, prefs)
    assert len(results) > 0
    for r in results:
        assert r.is_veg is True
