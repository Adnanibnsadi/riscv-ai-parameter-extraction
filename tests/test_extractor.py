from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"


def load_yaml(filename: str) -> dict:
    """Load a YAML output file."""

    file_path = RESULTS_DIR / filename

    with open(file_path, encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_snippet_1_contains_parameters():
    """Snippet 1 should contain extracted architectural parameters."""

    data = load_yaml("snippet_1.yaml")

    assert "parameters" in data
    assert len(data["parameters"]) == 3


def test_snippet_2_contains_no_parameters():
    """Snippet 2 should contain no architectural parameters."""

    data = load_yaml("snippet_2.yaml")

    assert "parameters" in data
    assert data["parameters"] == []


def test_snippet_1_parameter_names():
    """Snippet 1 should extract the expected parameter names."""

    data = load_yaml("snippet_1.yaml")

    names = {parameter["name"] for parameter in data["parameters"]}

    expected_names = {
        "cache_capacity",
        "cache_organization",
        "cache_block_size",
    }

    assert names == expected_names


def test_parameters_have_required_fields():
    """Every extracted parameter should contain all required fields."""

    data = load_yaml("snippet_1.yaml")

    required_fields = {
        "name",
        "description",
        "type",
        "implementation_defined",
        "implementation_specific",
        "constraints",
        "evidence",
        "confidence",
    }

    for parameter in data["parameters"]:
        assert required_fields.issubset(parameter.keys())


def test_evidence_is_a_list():
    """Evidence should always be stored as a list."""

    data = load_yaml("snippet_1.yaml")

    for parameter in data["parameters"]:
        assert isinstance(parameter["evidence"], list)


def test_confidence_values_are_valid():
    """Confidence must be high, medium, or low."""

    data = load_yaml("snippet_1.yaml")

    valid_values = {
        "high",
        "medium",
        "low",
    }

    for parameter in data["parameters"]:
        assert parameter["confidence"] in valid_values
