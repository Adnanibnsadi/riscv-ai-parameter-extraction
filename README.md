# RISC-V AI Parameter Extraction

An AI-assisted tool for extracting architectural parameters from the RISC-V ISA specification using Google's Gemini API.

The project analyzes RISC-V specification snippets and identifies parameters whose behavior or values are explicitly described as implementation-specific, implementation-defined, optional, or otherwise variable by implementation.

The extracted information is validated using Pydantic and saved as structured YAML files.

---

## Project Overview

RISC-V specifications contain a large amount of architectural information, including parameters that may vary between implementations.

Manually identifying these parameters across a large specification can be time-consuming. This project explores an AI-assisted approach to automatically identify and structure such information.

The current pipeline is:

```text
RISC-V Specification Snippet
            │
            ▼
      Gemini AI Model
            │
            ▼
       JSON Response
            │
            ▼
    Response Normalization
            │
            ▼
     Pydantic Validation
            │
            ▼
       YAML Output
```

The project is designed as an initial prototype that can be extended to process larger portions of the RISC-V ISA specification.

---

## Features

* Extracts architectural parameters from RISC-V specification snippets.
* Uses Google's Gemini API for AI-assisted extraction.
* Identifies implementation-specific and implementation-defined parameters.
* Handles optional or implementation-variable behavior when explicitly stated.
* Produces structured JSON responses from Gemini.
* Validates AI-generated responses using Pydantic.
* Normalizes common response inconsistencies before validation.
* Converts validated results into YAML files.
* Processes multiple `.txt` specification snippets automatically.
* Includes automated unit and validation tests using Pytest.
* Keeps API credentials outside the source code using environment variables.

---

## Extracted Parameter Schema

Each extracted architectural parameter contains the following fields:

| Field                     | Description                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------ |
| `name`                    | Unique parameter name in lowercase `snake_case`                                            |
| `description`             | Description of the architectural parameter                                                 |
| `type`                    | Parameter value type, such as `size`, `integer`, `boolean`, `enum`, `address`, or `string` |
| `implementation_defined`  | Whether the parameter is explicitly implementation-defined                                 |
| `implementation_specific` | Whether the parameter is explicitly implementation-specific                                |
| `constraints`             | Explicit constraints found in the specification                                            |
| `evidence`                | Supporting statements from the specification                                               |
| `confidence`              | Extraction confidence: `high`, `medium`, or `low`                                          |

The top-level output structure is:

```yaml
parameters:
  - name: example_parameter
    description: Example description
    type: size
    implementation_defined: false
    implementation_specific: true
    constraints:
      - Example constraint
    evidence:
      - Supporting statement from the specification
    confidence: high
```

If no qualifying architectural parameters are identified:

```yaml
parameters: []
```

---

## Example

### Input

A specification snippet describing cache properties:

```text
The capacity and organization of a cache and the size of a cache block
are both implementation-specific, and the execution environment provides
software a means to discover information about the caches and cache blocks
in a system.
```

### Extracted Output

The system identifies parameters such as:

```yaml
parameters:
  - name: cache_capacity
    description: The capacity of a cache.
    type: size
    implementation_defined: false
    implementation_specific: true
    constraints: []
    evidence:
      - The capacity and organization of a cache and the size of a cache block are both implementation-specific
    confidence: high

  - name: cache_organization
    description: The organization of a cache.
    type: string
    implementation_defined: false
    implementation_specific: true
    constraints: []
    evidence:
      - The capacity and organization of a cache and the size of a cache block are both implementation-specific
    confidence: high

  - name: cache_block_size
    description: The size of a cache block.
    type: size
    implementation_defined: false
    implementation_specific: true
    constraints:
      - shall be uniform throughout the system
    evidence:
      - The capacity and organization of a cache and the size of a cache block are both implementation-specific
      - In the initial set of CMO extensions, the size of a cache block shall be uniform throughout the system.
    confidence: high
```

A snippet that contains no qualifying architectural parameters produces:

```yaml
parameters: []
```

---

## Project Structure

```text
riscv-ai-parameter-extraction/
│
├── data/
│   ├── snippet_1.txt
│   └── snippet_2.txt
│
├── output/
│   ├── snippet_1.yaml
│   └── snippet_2.yaml
│
├── src/
│   ├── __init__.py
│   └── extractor.py
│
├── tests/
│   ├── test_extractor.py
│   └── test_validation.py
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Requirements

* Python 3.10 or newer
* Google Gemini API key
* Internet connection
* Python packages listed in `requirements.txt`

---

## Installation

Clone the repository:

```bash
git clone https://github.com/Adnanibnsadi/riscv-ai-parameter-extraction.git
cd riscv-ai-parameter-extraction
```

Create a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell prevents script execution, you can run the project using the virtual environment's Python executable directly or adjust the PowerShell execution policy for your user account.

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

## API Configuration

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_gemini_api_key_here
```

The application loads the API key using `python-dotenv`.

**Never commit your API key to GitHub.**

The `.gitignore` file excludes `.env` from Git tracking.

---

## Running the Extractor

Place RISC-V specification snippets as `.txt` files inside:

```text
data/
```

For example:

```text
data/snippet_1.txt
data/snippet_2.txt
```

Run:

```powershell
python src/extractor.py
```

The program processes every `.txt` file in the `data` directory.

The resulting YAML files are written to:

```text
output/
```

For example:

```text
output/snippet_1.yaml
output/snippet_2.yaml
```

If an output file with the same name already exists, it will be **overwritten with the newly generated result**.

The program does not create duplicate files with different names.

---

## Running Tests

The project includes automated tests for:

* Pydantic schema validation
* Empty parameter results
* Required fields
* Evidence normalization
* Constraint normalization
* Invalid confidence values
* Missing required fields
* Mocked Gemini responses
* Invalid JSON responses
* Empty API responses
* Simulated API failures
* Existing YAML output validation

Run the test suite using:

```powershell
python -m pytest -q
```

Current test status:

```text
16 passed, 1 warning
```

The tests use mocked Gemini responses where appropriate, so the test suite does not require making real Gemini API calls.

---

## Validation and Normalization

AI-generated responses can occasionally contain minor formatting inconsistencies.

For example, Gemini may return:

```json
{
  "evidence": "This is supporting evidence."
}
```

while the expected schema requires:

```json
{
  "evidence": [
    "This is supporting evidence."
  ]
}
```

The `normalize_response()` function converts string values into lists before Pydantic validation.

Pydantic then validates the normalized response against the following models:

```python
class ArchitecturalParameter(BaseModel):
    name: str
    description: str
    type: str
    implementation_defined: bool
    implementation_specific: bool
    constraints: list[str]
    evidence: list[str]
    confidence: Literal["high", "medium", "low"]
```

This provides a validation layer between the AI-generated response and the final YAML output.

---

## Testing Strategy

The project uses two complementary testing approaches.

### Unit and Validation Tests

`tests/test_validation.py` tests the behavior of the extraction and validation logic, including mocked Gemini responses.

### Output Tests

`tests/test_extractor.py` validates the generated YAML files and checks that:

* Expected parameters are present.
* Parameter names are correct.
* Required fields exist.
* Evidence is stored as a list.
* Confidence values are valid.
* Empty extraction results are handled correctly.

This separation helps verify both the extraction pipeline and the generated output.

---

## Limitations

This project is currently a prototype and has several limitations:

* Extraction quality depends on the Gemini model's interpretation of the specification.
* The system only processes the snippets provided as input.
* The current implementation does not automatically download or parse the complete RISC-V ISA specification.
* AI-generated results require validation and may still require human review.
* The current extraction logic is focused on explicitly stated implementation-specific, implementation-defined, optional, or implementation-variable behavior.
* The system does not yet maintain a persistent database of extracted parameters.
* Large-scale processing and benchmarking against a manually annotated ground-truth dataset have not yet been implemented.

---

## Future Improvements

Potential future work includes:

* Processing the complete RISC-V ISA and Privileged Architecture specifications.
* Automatically splitting large specification documents into manageable sections.
* Adding section numbers and document references to extracted parameters.
* Improving evidence extraction and traceability.
* Creating a manually annotated benchmark dataset.
* Evaluating extraction precision, recall, and F1 score.
* Adding duplicate parameter detection.
* Supporting incremental processing of specification updates.
* Comparing extracted parameters across different RISC-V specification versions.
* Adding a command-line interface.
* Adding structured logging and error reporting.
* Exploring local or open-source language models as alternative inference backends.
* Adding support for multiple AI providers through a common interface.

---

## Project Status

This project is currently an initial working prototype.

The current implementation successfully demonstrates an end-to-end pipeline:

```text
RISC-V Text
    ↓
AI-Assisted Extraction
    ↓
JSON Parsing
    ↓
Response Normalization
    ↓
Pydantic Validation
    ↓
YAML Serialization
    ↓
Automated Testing
```

The prototype currently includes two example RISC-V specification snippets and a test suite covering the extraction, validation, normalization, and output layers.

---

## Author

**Adnan Sadi Gul**

GitHub: `Adnanibnsadi`

This project was developed as part of an exploration into AI-assisted extraction of architectural parameters from the RISC-V ISA specification.
