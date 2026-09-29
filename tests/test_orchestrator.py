"""Unit tests for recommendation orchestrator and fallback handling."""

from typing import List
import pytest

from src.data.store import RestaurantStore
from src.models.preferences import UserPreferences
from src.models.recommendation import GeminiRawResponse, GeminiRecommendationItem
from src.models.restaurant import BudgetTier, Restaurant
from src.services.orchestrator import generate_fallback_recommendations, get_recommendations


class MockGeminiClient:
    """Mock Gemini client returning predefined responses or raising errors."""

    def __init__(self, raw_response: GeminiRawResponse = None, raise_error: bool = False):
        self.raw_response = raw_response
        self.raise_error = raise_error
        self.call_count = 0

    def generate_recommendations(self, system_instruction: str, user_prompt: str) -> GeminiRawResponse:
        self.call_count += 1
        if self.raise_error:
            raise RuntimeError("Simulated Gemini API 503 error")
        return self.raw_response or GeminiRawResponse(summary="Mock summary", recommendations=[])


@pytest.fixture
def mock_store() -> RestaurantStore:
    """Fixture with mock restaurants."""
    restaurants = [
        Restaurant(
            id="rest_1",
            name="Alpha Dining",
            location="Bellandur",
            cuisines=["Continental", "Italian"],
            rating=4.5,
            cost_for_two=1400,
            budget_tier=BudgetTier.HIGH,
            votes=1200,
        ),
        Restaurant(
            id="rest_2",
            name="Beta Bar",
            location="Bellandur",
            cuisines=["American", "BBQ"],
            rating=4.3,
            cost_for_two=1600,
            budget_tier=BudgetTier.HIGH,
            votes=800,
        ),
        Restaurant(
            id="rest_3",
            name="Gamma Grill",
            location="Bellandur",
            cuisines=["North Indian"],
            rating=4.2,
            cost_for_two=1500,
            budget_tier=BudgetTier.HIGH,
            votes=950,
        ),
    ]
    return RestaurantStore(auto_load=False, initial_restaurants=restaurants)


def test_orchestrator_successful_gemini_flow(mock_store: RestaurantStore):
    """Test orchestrator correctly hydrations recommendations from Gemini response."""
    mock_raw = GeminiRawResponse(
        summary="Top spots in Bellandur for high-end dining.",
        recommendations=[
            GeminiRecommendationItem(
                restaurant_id="rest_2",
                rank=1,
                explanation="Exceptional BBQ with vibrant ambiance.",
            ),
            GeminiRecommendationItem(
                restaurant_id="rest_1",
                rank=2,
                explanation="Outstanding Continental dishes and artisanal cocktails.",
            ),
        ],
    )
    mock_client = MockGeminiClient(raw_response=mock_raw)

    prefs = UserPreferences(
        location="Bellandur",
        budget="high",  # type: ignore
        min_rating=4.2,
    )

    response = get_recommendations(mock_store, prefs, top_k=2, gemini_client=mock_client)  # type: ignore

    assert mock_client.call_count == 1
    assert response.summary == "Top spots in Bellandur for high-end dining."
    assert len(response.recommendations) == 2
    assert response.recommendations[0].rank == 1
    assert response.recommendations[0].restaurant.name == "Beta Bar"
    assert response.recommendations[0].explanation == "Exceptional BBQ with vibrant ambiance."
    assert response.recommendations[1].rank == 2
    assert response.recommendations[1].restaurant.name == "Alpha Dining"
    assert response.meta is not None
    assert response.meta.candidate_count == 3


def test_orchestrator_hallucinated_id_ignored(mock_store: RestaurantStore):
    """Test that hallucinated restaurant IDs from LLM are ignored."""
    mock_raw = GeminiRawResponse(
        summary="Some picks",
        recommendations=[
            GeminiRecommendationItem(
                restaurant_id="hallucinated_fake_id",
                rank=1,
                explanation="This restaurant does not exist in dataset.",
            ),
            GeminiRecommendationItem(
                restaurant_id="rest_1",
                rank=2,
                explanation="Real restaurant.",
            ),
        ],
    )
    mock_client = MockGeminiClient(raw_response=mock_raw)

    prefs = UserPreferences(
        location="Bellandur",
        budget="high",  # type: ignore
        min_rating=4.2,
    )

    response = get_recommendations(mock_store, prefs, top_k=5, gemini_client=mock_client)  # type: ignore

    assert len(response.recommendations) == 1
    assert response.recommendations[0].restaurant.id == "rest_1"
    assert response.recommendations[0].rank == 1  # Re-indexed to 1


def test_orchestrator_zero_candidates_early_exit(mock_store: RestaurantStore):
    """Test zero candidate scenario exits early without calling Gemini."""
    mock_client = MockGeminiClient()
    prefs = UserPreferences(
        location="NonExistentCity",
        budget="low",  # type: ignore
        min_rating=4.9,
    )
    response = get_recommendations(mock_store, prefs, gemini_client=mock_client)  # type: ignore
    assert mock_client.call_count == 0
    assert len(response.recommendations) == 0
    assert "No restaurants found" in (response.summary or "")


def test_orchestrator_gemini_failure_triggers_fallback(mock_store: RestaurantStore):
    """Test that an error during Gemini generation triggers rating-based fallback."""
    mock_client = MockGeminiClient(raise_error=True)
    prefs = UserPreferences(
        location="Bellandur",
        budget="high",  # type: ignore
        min_rating=4.2,
    )
    response = get_recommendations(mock_store, prefs, top_k=2, gemini_client=mock_client)  # type: ignore
    assert len(response.recommendations) == 2
    assert response.recommendations[0].restaurant.name == "Alpha Dining"
    assert response.recommendations[1].restaurant.name == "Beta Bar"
    assert response.recommendations[0].rank == 1
