"""Pydantic models for advanced Crave AI features (Dish Radar, Compare, Roulette, Group Dining, Trails)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.models.restaurant import BudgetTier, Restaurant


# --- 1. Dish Radar ---
class DishSearchRequest(BaseModel):
    dish_query: str = Field(..., min_length=1, description="Dish name or keyword e.g. 'Ramen', 'Dosa', 'Shawarma'")
    location: Optional[str] = Field(default=None, description="Optional target locality")
    budget: Optional[str] = Field(default=None, description="Optional budget tier (low, medium, high)")
    is_veg_only: bool = Field(default=False, description="Strictly vegetarian only")
    is_halal: bool = Field(default=False, description="Strictly Halal friendly only")
    min_rating: float = Field(default=3.5, ge=0.0, le=5.0)


class DishSearchResult(BaseModel):
    rank: int
    restaurant: Restaurant
    matched_dish_text: str
    relevance_score: float
    dish_highlight: str


class DishSearchResponse(BaseModel):
    dish_query: str
    total_matches: int
    summary: str
    results: List[DishSearchResult]


# --- 2. Food Face-Off (Compare) ---
class CompareRequest(BaseModel):
    restaurant_id_1: str = Field(..., description="ID or name of restaurant 1")
    restaurant_id_2: str = Field(..., description="ID or name of restaurant 2")
    occasion: Optional[str] = Field(default=None, description="e.g. 'Date Night', 'Casual Lunch', 'Budget Feast'")


class CompareWinner(BaseModel):
    category: str
    winner_name: str
    reason: str


class CompareResponse(BaseModel):
    restaurant_1: Restaurant
    restaurant_2: Restaurant
    summary_verdict: str
    category_winners: List[CompareWinner]
    recommended_pick: str


# --- 3. Crave Roulette ---
class RouletteRequest(BaseModel):
    location: str = Field(..., description="Target locality")
    budget: Optional[str] = Field(default=None, description="Optional budget tier")
    is_veg_only: bool = Field(default=False)
    is_halal: bool = Field(default=False)


class RouletteResponse(BaseModel):
    restaurant: Restaurant
    roulette_headline: str
    why_it_won: str
    must_order_dish: str
    pro_tip: str


# --- 4. Group Dining Solver ---
class GroupMember(BaseModel):
    name: str = Field(..., description="Name of the person")
    diet: str = Field(default="any", description="'veg', 'non_veg', 'halal', or 'any'")
    craving: Optional[str] = Field(default=None, description="e.g. 'Biryani', 'Pizza', 'Desserts', 'Korean'")
    budget_preference: Optional[str] = Field(default=None, description="'low', 'medium', 'high'")


class GroupDiningRequest(BaseModel):
    location: str = Field(..., description="Meeting locality")
    members: List[GroupMember] = Field(..., min_length=2, description="Group members list")


class MemberSatisfaction(BaseModel):
    member_name: str
    satisfied: bool
    what_they_eat: str


class GroupMatch(BaseModel):
    rank: int
    restaurant: Restaurant
    harmony_score: int  # 0 to 100%
    satisfactions: List[MemberSatisfaction]
    why_good_for_group: str


class GroupDiningResponse(BaseModel):
    location: str
    total_members: int
    harmony_verdict: str
    recommendations: List[GroupMatch]


# --- 5. Bangalore Food Trails ---
class TrailStop(BaseModel):
    order: int
    stop_name: str
    restaurant_id: Optional[str] = None
    stop_type: str
    address: str
    rating: float
    must_try: str
    vibe: str
    estimated_cost: str


class FoodTrail(BaseModel):
    id: str
    title: str
    subtitle: str
    neighborhood: str
    emoji: str
    duration: str
    total_stops: int
    highlights: List[str]
    stops: List[TrailStop]
