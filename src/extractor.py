import os
import json
from pathlib import Path

import yaml
from dotenv import load_dotenv
from google import genai
from typing import Literal
from pydantic import BaseModel, ValidationError


# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from the project root
load_dotenv(BASE_DIR / ".env")

# Get the Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY was not found. "
        "Please make sure it is set in your .env file."
    )

# Create the Gemini client
client = genai.Client(
    api_key=api_key,  
    http_options={
        "timeout": 90000
    }
)

# Define Pydantic models for structured data validation
class ArchitecturalParameter(BaseModel):
    name: str
    description: str
    type: str
    implementation_defined: bool
    implementation_specific: bool
    constraints: list[str]
    evidence: list[str]
    confidence: Literal["high", "medium", "low"]


class ExtractionResult(BaseModel):
    parameters: list[ArchitecturalParameter]


# The extraction prompt
SYSTEM_PROMPT = """
You are an AI assistant analyzing the RISC-V ISA specification.

Your task is to extract architectural parameters from the provided RISC-V specification snippet.

An architectural parameter is a value, property, configuration, feature, or behavior that is explicitly described by the specification as variable, implementation-dependent, optional, configurable, or otherwise a meaningful parameter of an implementation.

Pay particular attention to parameters that are explicitly described as:

* implementation-defined
* implementation-specific
* optional
* optionally supported
* variable by implementation

Also consider fixed architectural parameters only when the specification explicitly defines a meaningful configurable value, range, width, limit, or constraint that should be represented as an architectural parameter.

Do not extract every number, bit range, encoding value, address range, or architectural constant appearing in the specification.

In particular, do NOT extract fixed encoding details, field positions, bit ranges, or encoding conventions as separate architectural parameters merely because they are explicitly stated. For example, a statement describing which CSR address bits encode privilege levels or read/write accessibility should not be treated as an architectural parameter unless the specification indicates that the encoding itself is variable, configurable, optional, or implementation-dependent.

Do not extract descriptive facts or fixed architectural conventions as parameters when they simply explain how the RISC-V architecture is defined.

Do not infer parameters that are not explicitly supported by the provided specification snippet.

Use only information explicitly present in the provided snippet.

Do not add information, examples, units, or constraints from general knowledge.

Do not infer constraints that are not explicitly stated.

Treat modal or optional language such as "may", "might", "should",
"optional", and "optionally" as potential indicators of an architectural parameter only when the surrounding specification text indicates that the behavior, value, feature, or support is variable by implementation or optional.

Do not extract a parameter solely because one of these words appears.

Use the surrounding context to determine whether the statement describes an actual architectural parameter.

When a parameter is explicitly described as implementation-defined or implementation-specific, preserve that distinction exactly.

Do not treat "implementation-defined" and "implementation-specific" as interchangeable.

For each extracted parameter, return:

* name
* description
* type
* implementation_defined
* implementation_specific
* constraints
* evidence
* confidence

The confidence field must be exactly one of:

"high", "medium", or "low".

Parameter names must be lowercase snake_case identifiers.

Set implementation_defined to true only when the specification explicitly describes the parameter as implementation-defined.

Set implementation_specific to true only when the specification explicitly describes the parameter as implementation-specific.

Do not set either field to true based on inference.

The evidence field must be a list of strings containing only supporting statements from the provided specification.

The evidence must preserve the meaning of the source text and must not introduce unsupported information.

The constraints field must contain only constraints explicitly supported by the provided specification.

Do not invent constraints based on general knowledge.

The type field must describe the parameter's value type, using concise values such as:

* "size"
* "integer"
* "boolean"
* "enum"
* "address"
* "string"

Choose the type based only on the specification and the parameter itself.

Use "string" only when the parameter represents a meaningful textual or structural property that cannot be more precisely represented by another appropriate type.

Avoid creating multiple parameters that represent different parts of the same fixed architectural convention.

If the snippet contains no genuine architectural parameters that satisfy the criteria above, return:

{
"parameters": []
}

The top-level response must always be:

{
"parameters": [...]
}

Return only valid JSON.

"""


def normalize_response(data: dict) -> dict:
    """
    Normalize Gemini's response before Pydantic validation.

    Ensures that fields requiring lists are represented as lists.
    """

    if "parameters" not in data:
        return data

    for parameter in data["parameters"]:

        # Convert evidence string to a list
        if isinstance(parameter.get("evidence"), str):
            parameter["evidence"] = [
                parameter["evidence"]
            ]

        # Convert constraints string to a list
        if isinstance(parameter.get("constraints"), str):
            parameter["constraints"] = [
                parameter["constraints"]
            ]

    return data

def extract_parameters(snippet: str) -> dict:
    """
    Send a RISC-V specification snippet to Gemini
    and return validated architectural parameters.
    """

    prompt = f"""
{SYSTEM_PROMPT}

Analyze the following RISC-V specification snippet.

RISC-V specification snippet:

{snippet}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0,
            },
        )

    except Exception as e:
        raise RuntimeError(
            f"Gemini API request failed: {e}"
        ) from e

    if not response.text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    try:
        # Parse Gemini's JSON response
        parsed_result = json.loads(response.text)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON:\n{response.text}"
            ) from e

    # Normalize the LLM response before validation
    normalized_result = normalize_response(parsed_result)

    try:
        # Validate Gemini's output using Pydantic
        validated_result = ExtractionResult.model_validate(
            normalized_result
        )

    except Exception as e:
        raise ValueError(
            f"Gemini response failed Pydantic validation:\n"
            f"{normalized_result}"
            f"{e}"
        ) from e

    # Return validated data as a dictionary
    return validated_result.model_dump()


def save_as_yaml(data: dict, output_path: Path):
    """
    Save extracted parameters as a YAML file.
    """

    with open(output_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            data,
            file,
            sort_keys=False,
            allow_unicode=True,
        )


def main():
    """
    Process all .txt snippets in the data directory.
    """

    data_directory = BASE_DIR / "data"
    output_directory = BASE_DIR / "output"

    # Create output directory if it doesn't exist
    output_directory.mkdir(exist_ok=True)

    # Find all text snippets
    snippets = sorted(data_directory.glob("*.txt"))

    if not snippets:
        print("No .txt specification snippets found in the data directory.")
        return

    for snippet_file in snippets:

        print(f"Processing: {snippet_file}")

        # Read the specification snippet
        snippet = snippet_file.read_text(encoding="utf-8")

        # Extract parameters using Gemini
        extracted_data = extract_parameters(snippet)

        # Define output filename
        output_file = output_directory / f"{snippet_file.stem}.yaml"

        # Save result as YAML
        save_as_yaml(extracted_data, output_file)

        print(f"Saved result to: {output_file}")


if __name__ == "__main__":
    main()