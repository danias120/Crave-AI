"""Tests for configuration settings and environment variable loading."""

import pytest
from pydantic import ValidationError

from src.config import Settings


def test_settings_defaults(monkeypatch):
    """Test that default settings initialize with expected values."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    settings = Settings(_env_file=None)
    assert settings.gemini_model == "gemini-2.5-flash"
    assert settings.gemini_max_output_tokens == 2048
    assert settings.gemini_temperature == 0.3
    assert settings.top_k_recommendations == 5
    assert settings.max_candidates_for_gemini == 30
    assert settings.has_gemini_api_key is False


def test_temperature_clamping():
    """Test that temperature is clamped to the [0.0, 1.0] range."""
    settings_high = Settings(GEMINI_TEMPERATURE=1.5)
    assert settings_high.gemini_temperature == 1.0

    settings_low = Settings(GEMINI_TEMPERATURE=-0.5)
    assert settings_low.gemini_temperature == 0.0


def test_positive_integer_validation():
    """Test that candidate and top_k limits must be at least 1."""
    with pytest.raises(ValidationError):
        Settings(TOP_K_RECOMMENDATIONS=0)

    with pytest.raises(ValidationError):
        Settings(MAX_CANDIDATES_FOR_GEMINI=0)
