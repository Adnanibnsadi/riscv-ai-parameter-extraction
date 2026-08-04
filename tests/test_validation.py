import json

import pytest
from pydantic import ValidationError

from src.extractor import (
    ExtractionResult,
    extract_parameters,
    normalize_response,
)


def test_valid_response_is_accepted():
    """A correctly structured response should pass validation."""

    data = {
        "parameters": [
            {
                "name": "cache_capacity",
                "description": "The capacity of a cache.",
                "type": "size",
                "implementation_defined": False,
                "implementation_specific": True,
                "constraints": [],
                "evidence": [
                    "The capacity of a cache is implementation-specific."
                ],
                "confidence": "high",
            }
        ]
    }

    result = ExtractionResult.model_validate(data)

    assert len(result.parameters) == 1
    assert result.parameters[0].name == "cache_capacity"


def test_empty_response_is_accepted():
    """A response with no parameters should be valid."""

    data = {
        "parameters": []
    }

    result = ExtractionResult.model_validate(data)

    assert result.parameters == []


def test_evidence_string_is_normalized():
    """A string evidence value should be converted to a list."""

    data = {
        "parameters": [
            {
                "name": "cache_capacity",
                "description": "The capacity of a cache.",
                "type": "size",
                "implementation_defined": False,
                "implementation_specific": True,
                "constraints": [],
                "evidence": "The capacity is implementation-specific.",
                "confidence": "high",
            }
        ]
    }

    normalized = normalize_response(data)

    assert isinstance(
        normalized["parameters"][0]["evidence"],
        list,
    )


def test_invalid_confidence_is_rejected():
    """An invalid confidence value should fail validation."""

    data = {
        "parameters": [
            {
                "name": "cache_capacity",
                "description": "The capacity of a cache.",
                "type": "size",
                "implementation_defined": False,
                "implementation_specific": True,
                "constraints": [],
                "evidence": [
                    "The capacity is implementation-specific."
                ],
                "confidence": True,
            }
        ]
    }

    with pytest.raises(ValidationError):
        ExtractionResult.model_validate(data)


def test_missing_required_field_is_rejected():
    """A parameter missing a required field should fail validation."""

    data = {
        "parameters": [
            {
                "name": "cache_capacity",
                "description": "The capacity of a cache.",
                "type": "size",
                "implementation_defined": False,
                "implementation_specific": True,
                "constraints": [],
                "evidence": [
                    "The capacity is implementation-specific."
                ],
                # confidence is intentionally missing
            }
        ]
    }

    with pytest.raises(ValidationError):
        ExtractionResult.model_validate(data)

def test_extract_parameters_with_mocked_gemini(monkeypatch):
    """Test the complete extraction pipeline without calling Gemini."""

    fake_gemini_response = {
        "parameters": [
            {
                "name": "cache_capacity",
                "description": "The capacity of a cache.",
                "type": "size",
                "implementation_defined": False,
                "implementation_specific": True,
                "constraints": [],
                "evidence": [
                    "The capacity and organization of a cache are implementation-specific."
                ],
                "confidence": "high",
            }
        ]
    }

    class FakeResponse:
        text = json.dumps(fake_gemini_response)

    def fake_generate_content(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.extractor.client.models.generate_content",
        fake_generate_content,
    )

    result = extract_parameters(
        "The capacity and organization of a cache are implementation-specific."
    )

    assert len(result["parameters"]) == 1
    assert result["parameters"][0]["name"] == "cache_capacity"
    assert result["parameters"][0]["implementation_specific"] is True


def test_extract_parameters_with_empty_result(monkeypatch):
    """Test that the extractor correctly handles no parameters."""

    fake_gemini_response = {
        "parameters": []
    }

    class FakeResponse:
        text = json.dumps(fake_gemini_response)

    def fake_generate_content(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.extractor.client.models.generate_content",
        fake_generate_content,
    )

    result = extract_parameters(
        "This specification describes a fixed architectural convention."
    )

    assert result == {
        "parameters": []
    }


def test_extract_parameters_rejects_invalid_json(monkeypatch):
    """Test that invalid JSON from Gemini raises a ValueError."""

    class FakeResponse:
        text = "This is not valid JSON."

    def fake_generate_content(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.extractor.client.models.generate_content",
        fake_generate_content,
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        extract_parameters("Test specification snippet.")


def test_extract_parameters_rejects_empty_response(monkeypatch):
    """Test that an empty Gemini response raises a ValueError."""

    class FakeResponse:
        text = ""

    def fake_generate_content(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "src.extractor.client.models.generate_content",
        fake_generate_content,
    )

    with pytest.raises(
        ValueError,
        match="empty response",
    ):
        extract_parameters("Test specification snippet.")


def test_extract_parameters_handles_api_error(monkeypatch):
    """Test that Gemini API errors are converted to RuntimeError."""

    def fake_generate_content(*args, **kwargs):
        raise Exception("Simulated Gemini API failure")

    monkeypatch.setattr(
        "src.extractor.client.models.generate_content",
        fake_generate_content,
    )

    with pytest.raises(
        RuntimeError,
        match="Gemini API request failed",
    ):
        extract_parameters("Test specification snippet.")        