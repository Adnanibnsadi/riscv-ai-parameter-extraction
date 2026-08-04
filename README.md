# AI-Assisted Extraction of Architectural Parameters from RISC-V Specifications

An AI-assisted tool that extracts architectural parameters from RISC-V specification snippets and produces structured YAML output.

The project uses Google's **Gemini 2.5 Flash** model to identify parameters that are explicitly described as **implementation-specific**, **implementation-defined**, **optional**, or otherwise variable by implementation.

The extracted results are parsed, normalized, validated using **Pydantic**, and serialized to YAML.

## Features

* AI-assisted extraction of architectural parameters
* Gemini 2.5 Flash integration
* Structured JSON responses
* Pydantic schema validation
* Response normalization for minor LLM formatting inconsistencies
* YAML output generation
* Evidence and constraints for extracted parameters
* Automated tests using pytest
* Prompt-based mitigation of unsupported inference and hallucination

## Extraction Pipeline

```text
RISC-V Specification Snippet
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
        YAML Output
```

## LLM Details

* **Provider:** Google
* **Model:** Gemini 2.5 Flash
* **SDK:** Google GenAI Python SDK
* **Temperature:** 0
* **Response format:** JSON
* **Input token limit:** 1,048,576 tokens
* **Output token limit:** 65,536 tokens
* **Validation:** Pydantic

The model is prompted to extract only parameters supported by the supplied specification text and to provide evidence for each extracted parameter.

Detailed information about prompt development, prompt refinement, hallucination mitigation, testing, limitations, and future improvements is available in:

```text
docs/prompt-development.md
```

## Project Structure

```text
riscv-ai-parameter-extraction/
├── data/
│   ├── snippet_1.txt
│   └── snippet_2.txt
├── docs/
│   └── prompt-development.md
├── results/
│   ├── snippet_1.yaml
│   └── snippet_2.yaml
├── src/
│   ├── __init__.py
│   └── extractor.py
├── tests/
│   ├── test_extractor.py
│   └── test_validation.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/Adnanibnsadi/riscv-ai-parameter-extraction.git
cd riscv-ai-parameter-extraction

python -m venv .venv
```

Activate the virtual environment on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root by copying `.env.example`:

```powershell
Copy-Item .env.example .env
```

Then open `.env` and add your Gemini API key:

```text
GEMINI_API_KEY=your_api_key_here
```

The `.env` file is excluded from Git using `.gitignore` and should never be committed to the repository.

## Running the Extractor

Place RISC-V specification snippets as `.txt` files inside:

```text
data/
```

Run the extractor with:

```powershell
python src/extractor.py
```

The extractor processes all `.txt` files in the `data/` directory and generates corresponding YAML files in the runtime output directory:

```text
output/
```

For example:

```text
data/snippet_1.txt
```

produces:

```text
output/snippet_1.yaml
```

If a file with the same name already exists in `output/`, it is overwritten.

The `output/` directory is used for runtime-generated results and is not part of the committed challenge deliverables.

## Challenge Results

The `results/` directory contains the final YAML outputs generated for the two RISC-V specification snippets provided in the coding challenge.

### Snippet 1 — Cache Parameters

The extractor identifies three implementation-specific parameters:

* `cache_capacity`
* `cache_organization`
* `cache_block_size`

The `cache_block_size` parameter also includes the explicit constraint that the size of a cache block shall be uniform throughout the system in the initial set of CMO extensions.

### Snippet 2 — CSR Accessibility

The extractor returns:

```yaml
parameters: []
```

The snippet describes fixed CSR address-mapping conventions and encoding rules rather than parameters that are explicitly implementation-specific, implementation-defined, optional, or otherwise variable by implementation.

The complete results are available in:

```text
results/snippet_1.yaml
results/snippet_2.yaml
```

## Testing

Run the complete test suite with:

```powershell
python -m pytest -q
```

The current test suite contains **16 tests** covering:

* Pydantic schema validation
* Required fields
* Empty extraction results
* Evidence normalization
* Constraint normalization
* Confidence validation
* Missing required fields
* Mocked Gemini responses
* Invalid JSON handling
* Empty API responses
* API error handling
* YAML output validation

The current test suite passes successfully.

## Limitations

The current implementation is a prototype that processes individual text snippets.

A larger-scale implementation would require:

* Complete RISC-V specification ingestion
* Automatic document chunking
* Section and source location tracking
* Duplicate parameter detection
* A manually annotated evaluation dataset
* Precision, recall, and F1 measurement
* Evaluation across a larger portion of the RISC-V specifications
* Comparison of multiple LLMs and prompting strategies

## Documentation

Detailed documentation covering the prompt development process, prompt refinement, hallucination mitigation, structured validation, testing methodology, limitations, and future improvements is available in:

```text
docs/prompt-development.md
```
