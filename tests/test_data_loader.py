"""Unit tests for dataset loading, parsing functions, and RestaurantStore."""

import pytest
from src.data.loader import (
    determine_budget_tier,
    normalize_cuisines,
    normalize_location,
    normalize_record,
    parse_cost,
    parse_rating,
)
from src.data.store import RestaurantStore
from src.models.restaurant import BudgetTier, Restaurant


def test_parse_rating():
    """Test rating parsing from varied string formats and invalid edge cases."""
    assert parse_rating("4.1/5") == 4.1
    assert parse_rating("4.5") == 4.5
    assert parse_rating(" 3.8/5 ") == 3.8
    assert parse_rating("NEW") is None
    assert parse_rating("-") is None
    assert parse_rating("") is None
    assert parse_rating(None) is None
    assert parse_rating("6.0/5") is None


def test_parse_cost():
    """Test cost parsing from string and integer formats."""
    assert parse_cost("800") == 800
    assert parse_cost("1,200") == 1200
    assert parse_cost("2,500") == 2500
    assert parse_cost(" 400 ") == 400
    assert parse_cost(500) == 500
    assert parse_cost(None) is None
    assert parse_cost("-") is None
    assert parse_cost("invalid") is None


def test_determine_budget_tier():
    """Test budget tier classification thresholds."""
    assert determine_budget_tier(300) == BudgetTier.LOW
    assert determine_budget_tier(400) == BudgetTier.LOW
    assert determine_budget_tier(401) == BudgetTier.MEDIUM
    assert determine_budget_tier(800) == BudgetTier.MEDIUM
    assert determine_budget_tier(801) == BudgetTier.HIGH
    assert determine_budget_tier(1500) == BudgetTier.HIGH
    assert determine_budget_tier(None) == BudgetTier.MEDIUM


def test_normalize_location_and_cuisines():
    """Test location and cuisines cleaning."""
    assert normalize_location("  Banashankari  ") == "Banashankari"
    assert normalize_location(None) == "Unknown"

    cuisines = normalize_cuisines("North Indian, Chinese , North Indian , Fast Food")
    assert cuisines == ["North Indian", "Chinese", "Fast Food"]
    assert normalize_cuisines(None) == []


def test_cuisine_standardization_afghan_to_afghani():
    """Test that 'Afghan' is standardized to 'Afghani' and deduplicated."""
    assert normalize_cuisines("Afghan, North Indian") == ["Afghani", "North Indian"]
    assert normalize_cuisines("Afghani, Mughlai") == ["Afghani", "Mughlai"]
    assert normalize_cuisines("Afghan, Afghani, Biryani") == ["Afghani", "Biryani"]


def test_clean_text():
    """Test repairing mojibake and removing encoding artifacts."""
    from src.data.loader import clean_text
    assert clean_text("WAFL CafÃ\x83Â\x83Ã\x82Â\x83Ã\x83Â\x82Ã\x82Â\x83Ã\x83Â\x83Ã\x82Â\x82Ã\x83Â\x82Ã\x82Â©") == "WAFL Café"
    assert clean_text("CafÃ\x83Â\x83Ã\x82Â\x83Ã\x83Â\x82Ã\x82Â\x83Ã\x83Â\x83Ã\x82Â\x82Ã\x83Â\x82Ã\x82Â© Down The Alley") == "Café Down The Alley"
    assert clean_text("E2 - EntrÃ\x83Â\x83Ã\x82Â\x83Ã\x83Â\x82Ã\x82Â\x83Ã\x83Â\x83Ã\x82Â\x82Ã\x83Â\x82Ã\x82Â©e Envoy") == "E2 - Entrée Envoy"


def test_normalize_record_valid():
    """Test converting raw dataset row into normalized Restaurant."""
    raw = {
        "name": "Truffles",
        "rate": "4.6/5",
        "location": "Koramangala 5th Block",
        "cuisines": "American, Burgers, Fast Food",
        "approx_cost(for two people)": "900",
        "votes": "14500",
        "address": "St. Marks Road",
        "rest_type": "Casual Dining",
        "dish_liked": "Burgers, Pasta",
    }
    restaurant = normalize_record(raw, "rest_101")
    assert restaurant is not None
    assert restaurant.id == "rest_101"
    assert restaurant.name == "Truffles"
    assert restaurant.rating == 4.6
    assert restaurant.cost_for_two == 900
    assert restaurant.budget_tier == BudgetTier.HIGH
    assert restaurant.votes == 14500
    assert "Burgers" in restaurant.cuisines


def test_normalize_record_invalid():
    """Test that missing name, rating, or location returns None."""
    assert normalize_record({"name": "", "rate": "4.0/5"}, "r1") is None
    assert normalize_record({"name": "Place", "rate": "NEW"}, "r2") is None
    assert normalize_record({"name": "Place", "rate": "4.0/5", "location": None}, "r3") is None


def test_restaurant_store_in_memory():
    """Test RestaurantStore query and distinct value methods."""
    sample_restaurants = [
        Restaurant(
            id="r1",
            name="Alpha Cafe",
            location="Indiranagar",
            cuisines=["Cafe", "Italian"],
            rating=4.2,
            cost_for_two=500,
            budget_tier=BudgetTier.MEDIUM,
        ),
        Restaurant(
            id="r2",
            name="Beta Biryani",
            location="Koramangala",
            cuisines=["Biryani", "North Indian"],
            rating=4.5,
            cost_for_two=350,
            budget_tier=BudgetTier.LOW,
        ),
        Restaurant(
            id="r3",
            name="Gamma Grill",
            location="Indiranagar",
            cuisines=["Barbecue", "North Indian"],
            rating=4.0,
            cost_for_two=1200,
            budget_tier=BudgetTier.HIGH,
        ),
    ]

    store = RestaurantStore(auto_load=False, initial_restaurants=sample_restaurants)

    assert len(store) == 3
    assert len(store.get_all()) == 3

    # Test lookup by ID
    r2 = store.get_by_id("r2")
    assert r2 is not None
    assert r2.name == "Beta Biryani"
    assert store.get_by_id("non_existent") is None

    # Test distinct locations (sorted)
    locations = store.distinct_locations()
    assert locations == ["Indiranagar", "Koramangala"]

    # Test distinct cuisines (sorted, flattened, unique)
    cuisines = store.distinct_cuisines()
    assert cuisines == ["Barbecue", "Biryani", "Cafe", "Italian", "North Indian"]
