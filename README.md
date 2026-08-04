# RISC-V Architectural Parameter Extractor

An AI-assisted tool for extracting architectural parameters from the RISC-V ISA specification using Google's Gemini API.

The project analyzes RISC-V specification snippets, identifies implementation-defined and implementation-specific architectural parameters, validates the AI-generated results using Pydantic, and exports the structured results as YAML files.

This project is being developed as part of an exploration of AI-assisted extraction of architectural parameters from the RISC-V ISA specification.

---

## Overview

The RISC-V ISA specification contains a large amount of technical information describing architectural behavior, implementation choices, constraints, and conventions.

Manually identifying and extracting architectural parameters from the specification can be time-consuming and difficult to scale.

This project uses a Large Language Model (LLM) to assist with this process.

The current implementation:

1. Reads RISC-V specification snippets from text files.
2. Sends each snippet to Google's Gemini model.
3. Uses a structured system prompt to identify architectural parameters.
4. Extracts relevant parameter information from the model response.
5. Parses the response as JSON.
6. Normalizes inconsistent list fields returned by the LLM.
7. Validates the result using Pydantic models.
8. Saves validated results as YAML files.
9. Uses automated tests to verify the extraction and validation pipeline.

---

## Features

* AI-assisted architectural parameter extraction
* Gemini API integration
* Structured JSON responses from the LLM
* Pydantic-based schema validation
* Response normalization for inconsistent LLM output
* YAML output generation
* Batch processing of RISC-V specification snippets
* Error handling for:

  * Gemini API failures
  * Empty API responses
  * Invalid JSON responses
  * Invalid response schemas
* Automated testing with pytest
* Mocked Gemini API tests that do not consume API quota

---

## Architecture

The current processing pipeline is:

```text
RISC-V Specification Snippet
            |
            v
      Text Input File
            |
            v
       Python Extractor
            |
            v
       Gemini 2.5 Flash
            |
            v
        JSON Response
            |
            v
    Response Normalization
            |
            v
     Pydantic Validation
            |
            v
       Validated Data
            |
            v
        YAML Output
```

---

## Project Structure

```text
riscv-parameter-extractor/
|
├── data/
│   ├── snippet_1.txt
│   └── snippet_2.txt
│
├── src/
│   ├── __init__.py
│   └── extractor.py
│
├── tests/
│   ├── test_extractor.py
│   └── test_validation.py
│
├── output/
│   └── Generated YAML files
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

> The `.env`, `.venv/`, `output/`, Python cache files, and other generated files are excluded from version control through `.gitignore`.

---

## Extracted Parameter Schema

Each extracted architectural parameter is represented using the following fields:

| Field                     | Description                                          |
| ------------------------- | ---------------------------------------------------- |
| `name`                    | Name of the architectural parameter                  |
| `description`             | Description of the parameter                         |
| `type`                    | Type or nature of the parameter                      |
| `implementation_defined`  | Whether the parameter is implementation-defined      |
| `implementation_specific` | Whether the parameter is implementation-specific     |
| `constraints`             | Constraints imposed by the RISC-V specification      |
| `evidence`                | Supporting evidence extracted from the specification |
| `confidence`              | Confidence level: `high`, `medium`, or `low`         |

Example:

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
```

---

## Example

Given a RISC-V specification snippet describing cache behavior:

```text
The capacity and organization of a cache and the size of a cache block
are both implementation-specific, and the execution environment provides
software a means to discover information about the caches and cache blocks
in a system.
```

The system can identify parameters such as:

* `cache_capacity`
* `cache_organization`
* `cache_block_size`

The extracted information is then validated and saved in YAML format.

---

## Installation

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd riscv-parameter-extractor
```

### 2. Create a virtual environment

On Windows:

```powershell
python -m venv .venv
```

Activate it using PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell prevents script execution, you can use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## Configuration

The application requires a Gemini API key.

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_api_key_here
```

**Never commit your `.env` file or API key to GitHub.**

The `.env` file is excluded through `.gitignore`.

---

## Running the Extractor

Place RISC-V specification snippets in the `data/` directory.

For example:

```text
data/snippet_1.txt
data/snippet_2.txt
```

Run the extractor with:

```powershell
python src/extractor.py
```

The program processes the input snippets and generates YAML output files in the `output/` directory.

---

## Running Tests

The project uses `pytest` for automated testing.

Run all tests using:

```powershell
python -m pytest
```

The current test suite contains **16 automated tests** covering:

* Output structure validation
* Pydantic schema validation
* Response normalization
* Empty parameter results
* Invalid JSON responses
* Empty Gemini responses
* Gemini API failures
* Mocked Gemini extraction
* Invalid confidence values
* Missing required fields

The latest test run:

```text
16 passed, 1 warning
```

The warning originates from the Google GenAI dependency and does not affect the test results.

---

## Testing Strategy

The project uses two types of testing.

### 1. Validation Tests

These tests verify that extracted data follows the expected schema.

For example:

* Required fields must be present.
* `constraints` must be a list.
* `evidence` must be a list.
* `confidence` must be `high`, `medium`, or `low`.
* Implementation flags must be Boolean values.

### 2. Mocked API Tests

The Gemini API is mocked during testing.

This means tests do not:

* Consume Gemini API quota.
* Require a live API connection.
* Depend on Gemini availability.
* Require a valid API key.

The mocked tests verify that the extraction pipeline correctly handles both successful and failed Gemini responses.

---

## Current Limitations

The current implementation is an initial prototype and has several areas for future improvement.

### 1. LLM-dependent extraction

The accuracy of parameter extraction depends on the quality and consistency of the LLM response.

### 2. Prompt-based extraction

The current system relies heavily on a structured system prompt to guide Gemini in identifying architectural parameters.

### 3. Limited specification coverage

The current prototype has been tested with a small number of RISC-V specification snippets.

A larger evaluation dataset is required to measure extraction accuracy across the complete RISC-V specification.

### 4. No duplicate detection

The current implementation does not yet automatically detect and merge duplicate parameters extracted from different sections.

### 5. No persistent parameter database

Extracted parameters are currently saved as YAML files rather than being stored in a searchable database or consolidated parameter repository.

---

## Future Improvements

Potential future improvements include:

* Process the complete RISC-V ISA specification automatically.
* Add support for both unprivileged and privileged specifications.
* Improve parameter classification.
* Distinguish between:

  * Implementation-defined parameters
  * Implementation-specific parameters
  * Architectural constants
  * Architectural conventions
* Add parameter identifiers and specification section references.
* Improve evidence extraction and traceability.
* Add duplicate parameter detection.
* Build a consolidated parameter database.
* Add confidence scoring and evaluation metrics.
* Compare extracted parameters against manually annotated ground truth.
* Add support for alternative LLM providers.
* Improve retry and rate-limit handling.
* Add structured logging.
* Add CI/CD testing using GitHub Actions.

---

## Security

API credentials are stored in environment variables using a `.env` file.

The following files and directories are excluded from Git version control:

```text
.env
.venv/
__pycache__/
*.pyc
output/
```

API keys should never be hard-coded in the source code or committed to a public repository.

---

## Technology Stack

* **Python**
* **Google Gemini API**
* **Gemini 2.5 Flash**
* **Pydantic**
* **PyYAML**
* **pytest**
* **python-dotenv**

---

## Project Status

The project currently provides a functional prototype capable of:

* Reading RISC-V specification snippets
* Sending snippets to Gemini
* Extracting architectural parameters
* Normalizing LLM responses
* Validating structured output using Pydantic
* Generating YAML output
* Handling API and parsing errors
* Running 16 automated tests with mocked API calls

The project is currently being developed and improved toward a more scalable AI-assisted pipeline for extracting architectural parameters from the RISC-V ISA specification.

---

## License

This project is currently under development. License information will be added as the project is prepared for public release.
