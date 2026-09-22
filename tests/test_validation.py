import json

import pytest
import yaml
from pydantic import ValidationError

from src.extractor import (
    DEFAULT_MODEL,
    ExtractionResult,
    create_client,
    extract_parameters,
    normalize_response,
    save_as_yaml,
)

VALID_PARAMETER = {
    "name": "cache_capacity",
    "description": "The capacity of a cache.",
    "type": "size",
    "implementation_defined": False,
    "implementation_specific": True,
    "constraints": [],
    "evidence": ["The capacity of a cache is implementation-specific."],
    "confidence": "high",
}


class SimulatedApiError(Exception):
    """Test-only API failure."""


class FakeResponse:
    def __init__(self, text: str):
        self.text = text


class FakeModels:
    def __init__(self, text: str = "", error: Exception | None = None):
        self.text = text
        self.error = error
        self.last_call = None

    def generate_content(self, **kwargs):
        self.last_call = kwargs
        if self.error:
            raise self.error
        return FakeResponse(self.text)


class FakeClient:
    def __init__(self, text: str = "", error: Exception | None = None):
        self.models = FakeModels(text=text, error=error)


def test_valid_response_is_accepted():
    """A correctly structured response should pass validation."""

    result = ExtractionResult.model_validate({"parameters": [VALID_PARAMETER]})

    assert len(result.parameters) == 1
    assert result.parameters[0].name == "cache_capacity"


def test_empty_response_is_accepted():
    """A response with no parameters should be valid."""

    result = ExtractionResult.model_validate({"parameters": []})

    assert result.parameters == []


def test_evidence_string_is_normalized():
    """A string evidence value should be converted to a list."""

    parameter = {**VALID_PARAMETER, "evidence": "Supported by the specification."}
    normalized = normalize_response({"parameters": [parameter]})

    assert normalized["parameters"][0]["evidence"] == [
        "Supported by the specification."
    ]


def test_constraints_string_is_normalized():
    """A string constraint should be converted to a list."""

    parameter = {**VALID_PARAMETER, "constraints": "Must be uniform."}
    normalized = normalize_response({"parameters": [parameter]})

    assert normalized["parameters"][0]["constraints"] == ["Must be uniform."]


def test_invalid_confidence_is_rejected():
    """An invalid confidence value should fail validation."""

    parameter = {**VALID_PARAMETER, "confidence": True}

    with pytest.raises(ValidationError):
        ExtractionResult.model_validate({"parameters": [parameter]})


def test_invalid_parameter_type_is_rejected():
    """Types outside the controlled vocabulary should fail validation."""

    parameter = {**VALID_PARAMETER, "type": "number-like"}

    with pytest.raises(ValidationError):
        ExtractionResult.model_validate({"parameters": [parameter]})


def test_missing_required_field_is_rejected():
    """A parameter missing a required field should fail validation."""

    parameter = {key: value for key, value in VALID_PARAMETER.items() if key != "name"}

    with pytest.raises(ValidationError):
        ExtractionResult.model_validate({"parameters": [parameter]})


def test_unexpected_field_is_rejected():
    """Unexpected model fields should not silently enter the output."""

    parameter = {**VALID_PARAMETER, "unsupported_field": "unexpected"}

    with pytest.raises(ValidationError):
        ExtractionResult.model_validate({"parameters": [parameter]})


def test_extract_parameters_with_mocked_gemini():
    """The complete extraction pipeline should work without a network call."""

    fake_client = FakeClient(json.dumps({"parameters": [VALID_PARAMETER]}))

    result = extract_parameters(
        "The capacity of a cache is implementation-specific.",
        client=fake_client,
    )

    assert result["parameters"][0]["name"] == "cache_capacity"
    assert fake_client.models.last_call["model"] == DEFAULT_MODEL
    assert "<specification_snippet>" in fake_client.models.last_call["contents"]


def test_extract_parameters_with_empty_result():
    """The extractor should correctly handle a snippet with no parameters."""

    fake_client = FakeClient(json.dumps({"parameters": []}))

    result = extract_parameters(
        "This specification describes a fixed architectural convention.",
        client=fake_client,
    )

    assert result == {"parameters": []}


def test_extract_parameters_rejects_invalid_json():
    """Invalid JSON from the model should raise a clear ValueError."""

    fake_client = FakeClient("This is not valid JSON.")

    with pytest.raises(ValueError, match="invalid JSON"):
        extract_parameters("Test specification snippet.", client=fake_client)


def test_extract_parameters_rejects_empty_response():
    """An empty model response should raise a clear ValueError."""

    fake_client = FakeClient("")

    with pytest.raises(ValueError, match="empty response"):
        extract_parameters("Test specification snippet.", client=fake_client)


def test_extract_parameters_handles_api_error():
    """API errors should be converted to a pipeline-level RuntimeError."""

    fake_client = FakeClient(error=SimulatedApiError("simulated failure"))

    with pytest.raises(RuntimeError, match="Gemini API request failed"):
        extract_parameters("Test specification snippet.", client=fake_client)


def test_extract_parameters_rejects_empty_snippet():
    """Empty source text should be rejected before client creation."""

    with pytest.raises(ValueError, match="cannot be empty"):
        extract_parameters("   ")


def test_create_client_requires_api_key(monkeypatch):
    """Client creation should fail clearly when no API key is configured."""

    monkeypatch.setattr("src.extractor.load_dotenv", lambda *_args, **_kwargs: False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        create_client()


def test_save_as_yaml_creates_parent_directory(tmp_path):
    """YAML serialization should create a missing output directory."""

    output_path = tmp_path / "nested" / "result.yaml"
    save_as_yaml({"parameters": []}, output_path)

    assert yaml.safe_load(output_path.read_text(encoding="utf-8")) == {"parameters": []}
