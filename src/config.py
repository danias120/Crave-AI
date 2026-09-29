"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_CACHE_DIR = PROJECT_ROOT / "data" / "cache"
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Runtime settings for the restaurant recommendation service."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")
    gemini_max_output_tokens: int = Field(
        default=2048, validation_alias="GEMINI_MAX_OUTPUT_TOKENS"
    )
    gemini_temperature: float = Field(default=0.3, validation_alias="GEMINI_TEMPERATURE")
    top_k_recommendations: int = Field(default=5, validation_alias="TOP_K_RECOMMENDATIONS")
    max_candidates_for_gemini: int = Field(
        default=30, validation_alias="MAX_CANDIDATES_FOR_GEMINI"
    )

    @field_validator("gemini_temperature")
    @classmethod
    def clamp_temperature(cls, value: float) -> float:
        return max(0.0, min(1.0, value))

    @field_validator("top_k_recommendations", "max_candidates_for_gemini")
    @classmethod
    def validate_at_least_one(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be at least 1")
        return value

    @property
    def has_gemini_api_key(self) -> bool:
        return bool(self.gemini_api_key.strip())


settings = Settings()
