"""Unit tests for Restaurant domain model and BudgetTier enum."""

import pytest
from pydantic import ValidationError

from src.models.restaurant import BudgetTier, Restaurant


def test_restaurant_model_valid():
    """Test creating a valid Restaurant model."""
    restaurant = Restaurant(
        id="rest_1",
        name="Test Cafe",
        location="Koramangala",
        cuisines=["Cafe", "Italian"],
        rating=4.5,
        cost_for_two=600,
        budget_tier=BudgetTier.MEDIUM,
    )
    assert restaurant.id == "rest_1"
    assert restaurant.name == "Test Cafe"
    assert restaurant.location == "Koramangala"
    assert restaurant.cuisines == ["Cafe", "Italian"]
    assert restaurant.rating == 4.5
    assert restaurant.cost_for_two == 600
    assert restaurant.budget_tier == BudgetTier.MEDIUM


def test_restaurant_rating_bounds():
    """Test rating validator bounds (0.0 to 5.0)."""
    with pytest.raises(ValidationError):
        Restaurant(
            id="rest_invalid",
            name="Invalid Rating",
            location="Indiranagar",
            rating=5.5,
            budget_tier=BudgetTier.LOW,
        )

    with pytest.raises(ValidationError):
        Restaurant(
            id="rest_invalid",
            name="Invalid Rating Negative",
            location="Indiranagar",
            rating=-0.1,
            budget_tier=BudgetTier.LOW,
        )


def test_restaurant_cuisines_coercion():
    """Test cuisines string splitting and list cleanup."""
    rest1 = Restaurant(
        id="rest_1",
        name="Pasta Place",
        location="Indiranagar",
        cuisines="Italian, European , Pizza",  # type: ignore
        rating=4.2,
    )
    assert rest1.cuisines == ["Italian", "European", "Pizza"]

    rest2 = Restaurant(
        id="rest_2",
        name="Burger Place",
        location="Indiranagar",
        cuisines=None,  # type: ignore
        rating=4.0,
    )
    assert rest2.cuisines == []


def test_restaurant_nan_cost_sanitization():
    """Test that float NaN cost is sanitized to None."""
    import math

    rest = Restaurant(
        id="rest_nan",
        name="No Cost Place",
        location="Whitefield",
        rating=3.8,
        cost_for_two=float("nan"),  # type: ignore
    )
    assert rest.cost_for_two is None
