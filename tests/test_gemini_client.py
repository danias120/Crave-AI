"""Unit tests for GeminiClient wrapper."""

from unittest.mock import MagicMock, patch
import pytest

from src.models.recommendation import GeminiRawResponse
from src.services.gemini_client import GeminiClient


def test_gemini_client_missing_key_raises():
    """Test that calling generate_recommendations without an API key raises RuntimeError."""
    client = GeminiClient(api_key="")
    with pytest.raises(RuntimeError) as exc_info:
        client.generate_recommendations("System instruction", "User prompt")
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)


@patch("src.services.gemini_client.genai.GenerativeModel")
def test_gemini_client_successful_response(mock_model_cls):
    """Test successful response parsing from mocked Gemini GenerativeModel."""
    mock_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        '{"summary": "Curated picks for you.", "recommendations": '
        '[{"restaurant_id": "rest_1", "rank": 1, "explanation": "Top rated food."}]}'
    )
    mock_instance.generate_content.return_value = mock_response
    mock_model_cls.return_value = mock_instance

    client = GeminiClient(api_key="fake-api-key-for-testing")
    result = client.generate_recommendations("System instruction", "User prompt")

    assert isinstance(result, GeminiRawResponse)
    assert result.summary == "Curated picks for you."
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant_id == "rest_1"
    assert result.recommendations[0].rank == 1


@patch("src.services.gemini_client.genai.GenerativeModel")
def test_gemini_client_retry_on_malformed_json(mock_model_cls):
    """Test that malformed JSON triggers retry."""
    mock_instance = MagicMock()
    bad_response = MagicMock()
    bad_response.text = "NOT_JSON"

    good_response = MagicMock()
    good_response.text = '{"summary": "Fixed response", "recommendations": []}'

    mock_instance.generate_content.side_effect = [bad_response, good_response]
    mock_model_cls.return_value = mock_instance

    client = GeminiClient(api_key="fake-api-key-for-testing")
    result = client.generate_recommendations("System instruction", "User prompt")

    assert result.summary == "Fixed response"
    assert mock_instance.generate_content.call_count == 2
