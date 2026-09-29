"""User preferences model with input validation, numeric budget mapping, and sanitization."""

import re
from typing import Any, Optional, Union
from pydantic import BaseModel, Field, field_validator

from src.data.loader import determine_budget_tier
from src.models.restaurant import BudgetTier


class UserPreferences(BaseModel):
    """Validated user preferences for restaurant recommendations."""

    location: str = Field(..., description="Target locality or city (e.g. Bangalore, Bellandur)")
    budget: BudgetTier = Field(
        default=BudgetTier.MEDIUM, description="Target budget tier (low, medium, high)"
    )
    cuisine: Optional[str] = Field(
        default=None, description="Preferred cuisine (e.g. North Indian, Italian, or None for any)"
    )
    min_rating: float = Field(
        default=3.5, ge=0.0, le=5.0, description="Minimum acceptable restaurant rating (0.0 - 5.0)"
    )
    additional_preferences: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional free-text preferences (e.g. 'outdoor seating, family-friendly')",
    )
    is_veg_only: bool = Field(
        default=False,
        description="If True, strictly filter and recommend only vegetarian restaurants",
    )

    @field_validator("location", mode="before")
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Ensure location is a non-empty string."""
        if v is None:
            raise ValueError("Location cannot be None")
        cleaned = str(v).strip()
        if not cleaned:
            raise ValueError("Location cannot be empty")
        return cleaned

    @field_validator("cuisine", mode="before")
    @classmethod
    def sanitize_cuisine(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize cuisine string; empty or 'any'/'all' strings become None."""
        if v is None:
            return None
        cleaned = str(v).strip()
        if not cleaned or cleaned.lower() in ("any", "all", "none"):
            return None
        return cleaned

    @field_validator("budget", mode="before")
    @classmethod
    def coerce_budget_tier(cls, v: Any) -> BudgetTier:
        """Coerce string, numeric amount (e.g. 1500, '1500'), or BudgetTier enum."""
        if isinstance(v, BudgetTier):
            return v
        if isinstance(v, (int, float)):
            return determine_budget_tier(int(v))
        if isinstance(v, str):
            val_clean = v.strip().replace(",", "")
            # Check if numeric string e.g. "1500"
            try:
                numeric_val = int(float(val_clean))
                return determine_budget_tier(numeric_val)
            except ValueError:
                pass
            val_lower = val_clean.lower()
            try:
                return BudgetTier(val_lower)
            except ValueError:
                raise ValueError(
                    f"Invalid budget '{v}'. Must be numeric (e.g. 1500) or one of 'low', 'medium', 'high'"
                )
        raise ValueError(f"Invalid budget value: {v}")

    @field_validator("min_rating", mode="before")
    @classmethod
    def clamp_rating(cls, v: Any) -> float:
        """Coerce and validate rating between 0.0 and 5.0."""
        try:
            val = float(v)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid rating value: {v}")
        if not (0.0 <= val <= 5.0):
            raise ValueError(f"Rating must be between 0.0 and 5.0, got {val}")
        return round(val, 2)

    @field_validator("additional_preferences", mode="before")
    @classmethod
    def sanitize_free_text(cls, v: Optional[str]) -> Optional[str]:
        """Strip control characters, trim whitespace, and enforce max length."""
        if v is None:
            return None
        text = str(v).strip()
        if not text:
            return None
        # Remove ASCII control characters except standard whitespace
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
        sanitized = sanitized.strip()
        if len(sanitized) > 500:
            sanitized = sanitized[:500].rstrip()
        return sanitized

    @field_validator("is_veg_only", mode="before")
    @classmethod
    def coerce_veg_only(cls, v: Any) -> bool:
        """Coerce boolean, numeric or string representation to bool."""
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes", "y", "on")
        return False
