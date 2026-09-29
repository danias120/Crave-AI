"""Google Gemini client for structured recommendation generation."""

import json
import logging
import time
from typing import Optional

import google.generativeai as genai

from src.config import settings
from src.models.recommendation import GeminiRawResponse

logger = logging.getLogger(__name__)


class GeminiClient:
    """Wrapper around Google Gemini API with structured JSON output and error handling."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        self.api_key = settings.gemini_api_key if api_key is None else api_key
        self.model_name = model_name or settings.gemini_model

        if not self.api_key:
            logger.warning(
                "Gemini API key is not configured. Set GEMINI_API_KEY in .env to use live LLM recommendations."
            )
        else:
            genai.configure(api_key=self.api_key)

    def generate_recommendations(
        self, system_instruction: str, user_prompt: str
    ) -> GeminiRawResponse:
        """Call Google Gemini with structured JSON mode and return parsed GeminiRawResponse."""
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. Please add your Gemini API key to .env"
            )

        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=settings.gemini_temperature,
            max_output_tokens=settings.gemini_max_output_tokens,
        )

        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction,
            generation_config=generation_config,
        )

        t0 = time.time()
        logger.info("Sending recommendation request to Gemini model '%s'...", self.model_name)

        try:
            response = model.generate_content(user_prompt)
            latency = time.time() - t0
            logger.info("Gemini response received in %.2fs", latency)
        except Exception as e:
            logger.error("Gemini API call failed after %.2fs: %s", time.time() - t0, e)
            raise RuntimeError(f"Gemini API generation failed: {e}") from e

        # Extract and parse raw JSON text
        raw_text = response.text or ""
        logger.debug("Raw Gemini response text: %s", raw_text)

        try:
            data = json.loads(raw_text)
            parsed = GeminiRawResponse(**data)
            return parsed
        except Exception as parse_err:
            logger.warning(
                "Failed to parse Gemini JSON output (%s). Retrying with JSON correction prompt...",
                parse_err,
            )
            # Retry once with follow-up instruction
            try:
                retry_prompt = (
                    f"{user_prompt}\n\n"
                    f"IMPORTANT: Your previous response was not valid JSON. "
                    f"Return ONLY valid JSON matching the exact schema without backticks or extra text."
                )
                retry_response = model.generate_content(retry_prompt)
                retry_data = json.loads(retry_response.text or "{}")
                return GeminiRawResponse(**retry_data)
            except Exception as retry_err:
                logger.error("Gemini JSON retry attempt failed: %s", retry_err)
                raise ValueError(
                    f"Could not parse valid JSON from Gemini response: {raw_text}"
                ) from retry_err


default_gemini_client = GeminiClient()
