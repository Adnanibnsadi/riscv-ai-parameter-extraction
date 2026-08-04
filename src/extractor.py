import os
import json
from pathlib import Path

import yaml
from dotenv import load_dotenv
from google import genai
from typing import Literal
from pydantic import BaseModel


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

Extract architectural parameters only when the provided specification explicitly
states that they are implementation-specific, implementation-defined, optional,
or otherwise variable by implementation.

Use only information explicitly present in the provided snippet.
Do not add information, examples, units, or constraints from general knowledge.
Do not infer constraints that are not explicitly stated.

For each parameter, return:
- name
- description
- type
- implementation_defined
- implementation_specific
- constraints
- evidence
- confidence
The confidence field must be exactly one of:
"high", "medium", or "low".
Parameter names must be lowercase snake_case identifiers.

Set implementation_defined or implementation_specific to true only when explicitly
supported by the specification. Do not treat these terms as interchangeable.

The evidence field must be a list of strings containing only supporting statements
from the provided specification.

The constraints field must contain only constraints explicitly supported by the
provided specification.

The type field must describe the parameter's value type, using concise values
such as "size", "integer", "boolean", "enum", "address", or "string".
Choose the type based only on the specification and the parameter itself.

The top-level response must always be:

{
  "parameters": [...]
}

If no qualifying parameters are found, return:

{
  "parameters": []
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
    snippets = list(data_directory.glob("*.txt"))

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