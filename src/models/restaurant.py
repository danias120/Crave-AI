"""Domain models for restaurants and pricing tiers."""

from enum import Enum
import math
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class BudgetTier(str, Enum):
    """Budget category for restaurant pricing."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Restaurant(BaseModel):
    """Canonical model for a restaurant in the dataset."""

    id: str = Field(..., description="Unique identifier for the restaurant")
    name: str = Field(..., description="Name of the restaurant")
    location: str = Field(..., description="Locality or city of the restaurant")
    cuisines: List[str] = Field(default_factory=list, description="List of cuisines served")
    rating: float = Field(..., ge=0.0, le=5.0, description="Rating between 0.0 and 5.0")
    cost_for_two: Optional[int] = Field(
        default=None, ge=0, description="Approximate cost for two people in INR"
    )
    budget_tier: BudgetTier = Field(
        default=BudgetTier.MEDIUM, description="Categorized budget tier (low, medium, high)"
    )
    address: Optional[str] = Field(default=None, description="Full address")
    votes: Optional[int] = Field(default=0, ge=0, description="Number of user votes/ratings")
    is_veg: bool = Field(default=False, description="Whether the restaurant is purely vegetarian")
    is_halal: bool = Field(default=False, description="Whether the restaurant is Halal-certified or serves Halal meat")
    raw: Dict[str, Any] = Field(
        default_factory=dict, description="Raw source fields for debugging or extensions"
    )

    @field_validator("rating")
    @classmethod
    def validate_rating_bounds(cls, v: float) -> float:
        """Ensure rating is within the 0.0 to 5.0 scale."""
        if not (0.0 <= v <= 5.0):
            raise ValueError(f"Rating must be between 0.0 and 5.0, got {v}")
        return round(v, 2)

    @field_validator("cost_for_two", mode="before")
    @classmethod
    def sanitize_cost_for_two(cls, v: Any) -> Optional[int]:
        """Sanitize cost_for_two, converting NaN / None / float to int or None."""
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        try:
            val = int(float(v))
            return val if val >= 0 else None
        except (ValueError, TypeError):
            return None

    @field_validator("votes", mode="before")
    @classmethod
    def sanitize_votes(cls, v: Any) -> int:
        """Sanitize votes count."""
        if v is None:
            return 0
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return 0
        try:
            return max(0, int(float(v)))
        except (ValueError, TypeError):
            return 0

    @field_validator("address", mode="before")
    @classmethod
    def sanitize_address(cls, v: Any) -> Optional[str]:
        """Sanitize address string."""
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("cuisines", mode="before")
    @classmethod
    def normalize_cuisines_list(cls, v: Any) -> List[str]:
        """Ensure cuisines is always a list of non-empty strings."""
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return []
        if isinstance(v, str):
            return [c.strip() for c in v.split(",") if c.strip()]
        if isinstance(v, (list, tuple)):
            return [str(c).strip() for c in v if str(c).strip()]
        return []
