"""Recommendation orchestration pipeline linking filters, prompt builder, and Gemini LLM."""

import logging
from typing import Dict, List, Optional

from src.config import settings
from src.data.store import RestaurantStore
from src.models.preferences import UserPreferences
from src.models.recommendation import (
    Recommendation,
    RecommendationMeta,
    RecommendationResponse,
)
from src.models.restaurant import Restaurant
from src.services.filter import filter_restaurants
from src.services.gemini_client import GeminiClient, default_gemini_client
from src.services.prompt_builder import (
    build_system_instruction,
    build_user_prompt,
)

logger = logging.getLogger(__name__)


def generate_fallback_recommendations(
    candidates: List[Restaurant],
    prefs: UserPreferences,
    top_k: int,
    reason: str = "Fallback mode",
) -> RecommendationResponse:
    """Generate heuristic rating-based recommendations when Gemini is unavailable or fails."""
    logger.info("Generating fallback recommendations (reason: %s)...", reason)
    selected = candidates[:top_k]

    is_halal_req = "halal" in (prefs.additional_preferences or "").lower()

    recommendations: List[Recommendation] = []
    for rank, r in enumerate(selected, start=1):
        cuisines_str = ", ".join(r.cuisines)
        cost_str = f"approx. ₹{r.cost_for_two} for two" if r.cost_for_two else f"{r.budget_tier.value} budget"
        halal_prefix = "[Halal Friendly] " if (is_halal_req and r.is_halal) else ""
        explanation = (
            f"{halal_prefix}Top rated ({r.rating:.1f}★ with {r.votes} votes) {cuisines_str} restaurant in {r.location} "
            f"within your {r.budget_tier.value} budget ({cost_str})."
        )
        recommendations.append(Recommendation(rank=rank, restaurant=r, explanation=explanation))

    summary = (
        f"Top {len(recommendations)} recommendations selected by highest customer ratings and "
        f"matching your criteria for {prefs.location} ({prefs.budget.value} budget)."
    )

    return RecommendationResponse(
        summary=summary,
        recommendations=recommendations,
        meta=RecommendationMeta(candidate_count=len(candidates), filters_applied=prefs),
    )


def get_recommendations(
    store: RestaurantStore,
    prefs: UserPreferences,
    top_k: Optional[int] = None,
    gemini_client: Optional[GeminiClient] = None,
) -> RecommendationResponse:
    """End-to-end orchestration pipeline for restaurant recommendations.

    Flow:
    1. Deterministic candidate filtering based on UserPreferences
    2. Early return if 0 candidates found
    3. Structured prompt construction (system + user prompt)
    4. Google Gemini API call for intelligent ranking and personalized explanations
    5. Response validation, candidate hydration, and error fallback
    """
    client = gemini_client or default_gemini_client
    k = top_k or settings.top_k_recommendations

    # Step 1: Deterministic filter with progressive relaxation
    candidates = filter_restaurants(store, prefs, progressive_relaxation=True)
    meta = RecommendationMeta(candidate_count=len(candidates), filters_applied=prefs)

    # Step 2: Early return if no candidates match
    if not candidates:
        if prefs.cuisine and prefs.cuisine.strip().lower() == "african" and "church" in prefs.location.lower():
            empty_msg = (
                f"No restaurants found: There are no African cuisine restaurants found in {prefs.location}. "
                f"African cuisine is currently available in nearby Bangalore localities such as Kammanahalli and Kalyan Nagar "
                f"(e.g., Habesha Ethiopian & African Delights). Try exploring those areas or picking related Middle Eastern & Mediterranean cuisines!"
            )
        elif prefs.cuisine:
            empty_msg = (
                f"No restaurants found: There are no {prefs.cuisine} cuisine restaurants found in {prefs.location}. "
                f"Try exploring nearby Bangalore areas, choosing a related cuisine, or adjusting your filters."
            )
        else:
            empty_msg = (
                f"No restaurants found matching your criteria in {prefs.location}. "
                f"Try adjusting your minimum rating or budget tier."
            )

        return RecommendationResponse(
            summary=empty_msg,
            recommendations=[],
            meta=meta,
        )

    # Step 3: Build prompts
    system_instruction = build_system_instruction()
    user_prompt = build_user_prompt(prefs, candidates, top_k=k)
    candidate_map: Dict[str, Restaurant] = {r.id: r for r in candidates}

    # Step 4: Call Gemini LLM with graceful fallback
    try:
        raw_response = client.generate_recommendations(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
        )

        recommendations: List[Recommendation] = []
        seen_ids = set()

        for item in raw_response.recommendations:
            # Enforce strict grounding: ignore unknown or duplicate IDs
            if item.restaurant_id in candidate_map and item.restaurant_id not in seen_ids:
                seen_ids.add(item.restaurant_id)
                restaurant = candidate_map[item.restaurant_id]
                recommendations.append(
                    Recommendation(
                        rank=item.rank,
                        restaurant=restaurant,
                        explanation=item.explanation,
                    )
                )

        # Sort recommendations by rank and limit to top_k
        recommendations.sort(key=lambda r: r.rank)
        recommendations = recommendations[:k]

        # If LLM returned 0 valid items, fallback to rating heuristic
        if not recommendations:
            return generate_fallback_recommendations(
                candidates, prefs, k, reason="Gemini returned 0 valid candidate IDs"
            )

        # Re-index ranks sequentially from 1..N
        for idx, rec in enumerate(recommendations, start=1):
            rec.rank = idx

        summary = raw_response.summary or (
            f"Here are your top {len(recommendations)} personalized dining recommendations in {prefs.location}."
        )

        return RecommendationResponse(
            summary=summary,
            recommendations=recommendations,
            meta=meta,
        )

    except Exception as err:
        logger.warning(
            "Gemini recommendation generation failed (%s). Activating rating fallback.", err
        )
        return generate_fallback_recommendations(candidates, prefs, k, reason=str(err))
