"""Unit tests for prompt builder service and recommendation models."""

import json
import pytest
from pydantic import ValidationError

from src.models.preferences import UserPreferences
from src.models.recommendation import (
    GeminiRawResponse,
    GeminiRecommendationItem,
    Recommendation,
    RecommendationMeta,
    RecommendationResponse,
)
from src.models.restaurant import BudgetTier, Restaurant
from src.services.prompt_builder import (
    build_output_schema_hint,
    build_system_instruction,
    build_user_prompt,
    format_candidate_for_prompt,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_candidates() -> list[Restaurant]:
    """Sample candidate restaurants for prompt builder testing."""
    return [
        Restaurant(
            id="rest_1",
            name="Truffles",
            location="Koramangala 5th Block",
            cuisines=["American", "Burgers", "Fast Food"],
            rating=4.6,
            cost_for_two=900,
            budget_tier=BudgetTier.HIGH,
            votes=14500,
            raw={"dish_liked": "Burgers, Pasta", "rest_type": "Casual Dining"},
        ),
        Restaurant(
            id="rest_2",
            name="Empire Restaurant",
            location="Koramangala 5th Block",
            cuisines=["North Indian", "Mughlai", "Biryani"],
            rating=4.2,
            cost_for_two=750,
            budget_tier=BudgetTier.MEDIUM,
            votes=9200,
            raw={"rest_type": "Casual Dining"},
        ),
        Restaurant(
            id="rest_3",
            name="Corner House Ice Cream",
            location="Koramangala 5th Block",
            cuisines=["Desserts", "Ice Cream"],
            rating=4.7,
            cost_for_two=250,
            budget_tier=BudgetTier.LOW,
            votes=11000,
        ),
    ]


@pytest.fixture
def sample_preferences() -> UserPreferences:
    """Sample user preferences."""
    return UserPreferences(
        location="Koramangala 5th Block",
        budget="medium",  # type: ignore
        cuisine="North Indian",
        min_rating=4.0,
        additional_preferences="good seating for family, quick service",
    )


# ==============================================================================
# System Instruction & Schema Hint Tests
# ==============================================================================


def test_build_system_instruction():
    """Verify system instruction contains guardrails against hallucination and specifies JSON output."""
    system_prompt = build_system_instruction()
    assert "STRICT GROUNDING" in system_prompt
    assert "ONLY recommend restaurants present in the provided candidate list" in system_prompt
    assert "Do NOT invent, hallucinate" in system_prompt
    assert "restaurant_id" in system_prompt
    assert "JSON" in system_prompt


def test_build_output_schema_hint():
    """Verify schema hint is valid JSON and has expected contract fields."""
    hint = build_output_schema_hint()
    parsed = json.loads(hint)
    assert "summary" in parsed
    assert "recommendations" in parsed
    assert isinstance(parsed["recommendations"], list)
    assert len(parsed["recommendations"]) == 1

    item = parsed["recommendations"][0]
    assert "restaurant_id" in item
    assert "rank" in item
    assert "explanation" in item


def test_format_candidate_for_prompt(sample_candidates: list[Restaurant]):
    """Verify candidate formatting produces compact dict with essential attributes and metadata."""
    cand = format_candidate_for_prompt(sample_candidates[0])
    assert cand["restaurant_id"] == "rest_1"
    assert cand["name"] == "Truffles"
    assert cand["location"] == "Koramangala 5th Block"
    assert cand["rating"] == 4.6
    assert cand["approx_cost_for_two"] == 900
    assert cand["budget_tier"] == "high"
    assert cand["popular_dishes"] == "Burgers, Pasta"
    assert cand["restaurant_type"] == "Casual Dining"


# ==============================================================================
# User Prompt Tests
# ==============================================================================


def test_build_user_prompt_structure(
    sample_preferences: UserPreferences, sample_candidates: list[Restaurant]
):
    """Verify that user preferences and all candidates are embedded in the prompt."""
    prompt = build_user_prompt(sample_preferences, sample_candidates, top_k=2)

    # Preferences embedded
    assert "USER PREFERENCES" in prompt
    assert "Koramangala 5th Block" in prompt
    assert "North Indian" in prompt
    assert "medium" in prompt
    assert "good seating for family, quick service" in prompt

    # Candidate list embedded
    assert "CANDIDATE RESTAURANTS (3 available)" in prompt
    for cand in sample_candidates:
        assert cand.id in prompt
        assert cand.name in prompt

    # Instructions and schema hint embedded
    assert "Select the top 2 best matching restaurants" in prompt
    assert "```json" in prompt


def test_build_user_prompt_without_optional_notes(sample_candidates: list[Restaurant]):
    """Verify prompt generation when additional preferences are absent."""
    prefs = UserPreferences(
        location="Indiranagar",
        budget="low",  # type: ignore
        cuisine="South Indian",
        min_rating=3.5,
    )
    prompt = build_user_prompt(prefs, sample_candidates)
    assert "Indiranagar" in prompt
    assert "South Indian" in prompt
    assert "additional_notes" not in prompt


# ==============================================================================
# Recommendation Models Tests
# ==============================================================================


def test_gemini_recommendation_item_validation():
    """Test validation on GeminiRecommendationItem."""
    item = GeminiRecommendationItem(
        restaurant_id="rest_1",
        rank=1,
        explanation="Excellent burgers with great ratings.",
    )
    assert item.restaurant_id == "rest_1"
    assert item.rank == 1

    with pytest.raises(ValidationError):
        GeminiRecommendationItem(restaurant_id="rest_1", rank=0, explanation="Invalid rank")


def test_gemini_raw_response_parsing():
    """Test parsing raw JSON from Gemini into GeminiRawResponse."""
    raw_json = {
        "summary": "Great picks for North Indian food in Koramangala.",
        "recommendations": [
            {
                "restaurant_id": "rest_2",
                "rank": 1,
                "explanation": "Famous for rich North Indian and Mughlai dishes.",
            }
        ],
    }
    parsed = GeminiRawResponse(**raw_json)
    assert parsed.summary == "Great picks for North Indian food in Koramangala."
    assert len(parsed.recommendations) == 1
    assert parsed.recommendations[0].restaurant_id == "rest_2"


def test_hydrated_recommendation_response(
    sample_preferences: UserPreferences, sample_candidates: list[Restaurant]
):
    """Test assembling final RecommendationResponse payload."""
    rec = Recommendation(
        rank=1,
        restaurant=sample_candidates[0],
        explanation="Top choice for burgers and continental food.",
    )
    meta = RecommendationMeta(
        candidate_count=len(sample_candidates),
        filters_applied=sample_preferences,
    )
    resp = RecommendationResponse(
        summary="Here are your top recommended dining spots.",
        recommendations=[rec],
        meta=meta,
    )
    assert len(resp.recommendations) == 1
    assert resp.recommendations[0].restaurant.name == "Truffles"
    assert resp.meta is not None
    assert resp.meta.candidate_count == 3
    assert resp.meta.filters_applied.location == "Koramangala 5th Block"
