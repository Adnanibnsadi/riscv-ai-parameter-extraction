# Prompt Development and LLM Methodology

## 1. Overview

This project explores an AI-assisted approach for extracting architectural parameters from RISC-V ISA specifications.

The goal is to identify parameters whose values or behavior may vary between implementations or are explicitly described as implementation-specific, implementation-defined, optional, or otherwise variable.

The extraction pipeline uses a Large Language Model (LLM) to analyze specification snippets and produce structured data. The generated response is parsed, normalized, validated using Pydantic, and finally serialized as YAML.

The current pipeline is:

```text
RISC-V Specification Snippet
            │
            ▼
       Prompt + LLM
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

---

## 2. LLM Used

The current implementation uses Google's Gemini API.

### Model

* **Provider:** Google
* **Model:** Gemini 2.5 Flash
* **Model ID:** `gemini-2.5-flash`
* **Model status:** Stable
* **API:** Gemini API
* **Python SDK:** `google-genai`
* **Generation temperature:** `0`
* **Response format:** JSON
* **Output validation:** Pydantic

The model is configured to return JSON rather than free-form text. This makes the response easier to parse programmatically and allows the extracted data to be validated against a predefined schema.

The project does not rely solely on the LLM's output. The response passes through JSON parsing, normalization, and Pydantic validation before being written to the final YAML file.

### Context Length

According to the current Gemini 2.5 Flash model documentation:

* **Input token limit:** 1,048,576 tokens
* **Output token limit:** 65,536 tokens

The current implementation sends individual RISC-V specification snippets to the model rather than the complete ISA Manual in a single request.

The available context window is therefore substantially larger than the snippets used in this coding challenge. For a production-scale implementation processing the complete RISC-V specification, the document would still need to be segmented into logical chunks so that section boundaries, source references, and extraction traceability can be preserved.

---

## 3. Initial Prompt

The initial prompt was designed to test whether an LLM could identify architectural parameters from short RISC-V specification snippets.

The first version instructed the model to:

* Analyze a RISC-V specification snippet.
* Look for words such as:

  * `may`
  * `might`
  * `should`
  * `optional`
  * `optionally`
  * `implementation-defined`
  * `implementation-specific`
* Extract:

  * parameter name
  * description
  * type
  * constraints
* Return the result in YAML format.

The initial approach was intentionally simple so that the behavior of the model could first be evaluated against the supplied examples.

---

## 4. Initial Testing

Two specification snippets were used for initial evaluation.

### Snippet 1

The first snippet describes cache properties:

* Cache capacity
* Cache organization
* Cache block size

The specification explicitly states that these properties are implementation-specific.

The initial model output successfully identified these three parameters.

However, further testing showed that the model could vary in how it represented fields such as `type`, `constraints`, and `evidence`. This motivated the introduction of a stricter output schema and validation layer.

### Snippet 2

The second snippet describes conventional CSR accessibility and address encoding.

It specifies:

* A 12-bit CSR address space
* Up to 4,096 CSR encodings
* Encoding of read/write and read-only accessibility
* Encoding of the lowest privilege level that can access a CSR

The model returned:

```yaml
parameters: []
```

This result was retained because the current extraction definition focuses on parameters that are explicitly variable, optional, implementation-defined, or implementation-specific.

The second snippet describes fixed architectural conventions and encoding rules rather than implementation-variable parameters.

This distinction is important because the goal is not to extract every numerical value or architectural constant from the specification.

---

## 5. Prompt Refinement

The initial prompt was refined based on observed model behavior and output inconsistencies.

The refined prompt introduced several important changes.

### 5.1 Explicit Extraction Scope

The prompt was changed to extract parameters only when the specification explicitly states that they are:

* Implementation-specific
* Implementation-defined
* Optional
* Otherwise variable by implementation

This reduces the possibility of extracting unrelated constants, encoding values, or fixed architectural rules.

The scope is intentionally conservative. A parameter should not be extracted merely because the model believes that an implementation could theoretically choose different values.

---

### 5.2 Explicit Evidence

An `evidence` field was added.

Each extracted parameter must contain supporting statements from the input specification.

For example:

```yaml
evidence:
  - The capacity and organization of a cache and the size of a cache block are both implementation-specific
```

This provides traceability between the extracted parameter and the source specification.

The evidence requirement also helps reviewers determine whether the model's extraction is supported by the provided text.

---

### 5.3 Distinguishing Implementation-Defined and Implementation-Specific

The prompt explicitly instructs the model not to treat these terms as interchangeable.

The output therefore contains separate fields:

```yaml
implementation_defined: false
implementation_specific: true
```

These fields are set to `true` only when the specification explicitly supports the classification.

This was introduced to prevent the model from collapsing different specification concepts into a single category.

---

### 5.4 Preventing Unsupported Inference

The prompt was refined to explicitly instruct the model:

> Use only information explicitly present in the provided snippet.

> Do not add information, examples, units, or constraints from general knowledge.

> Do not infer constraints that are not explicitly stated.

These instructions were added to reduce hallucination and prevent the model from filling gaps using general knowledge about computer architecture or RISC-V.

For example, if a specification states that a cache's organization is implementation-specific, the model should not invent specific architectural constraints about associativity, cache sets, replacement policies, or mapping unless those details are explicitly present in the snippet.

---

### 5.5 Controlled Parameter Types

The prompt was refined to require concise parameter types such as:

* `size`
* `integer`
* `boolean`
* `enum`
* `address`
* `string`

The model is instructed to determine the type based only on the specification and the parameter itself.

This reduces inconsistent type descriptions across different extractions.

---

### 5.6 Controlled Confidence Values

The model was restricted to three confidence values:

```text
high
medium
low
```

This was implemented using both prompt instructions and Pydantic validation.

The Pydantic model defines:

```python
confidence: Literal["high", "medium", "low"]
```

Therefore, unexpected values are rejected during validation.

### 5.7 Distinguishing Architectural Parameters from Fixed Encoding Details

The prompt was further refined to prevent the model from treating every numerical
value, bit range, encoding field, or architectural constant as an independent
parameter.

The model is now explicitly instructed not to extract fixed encoding details,
field positions, or encoding conventions as separate architectural parameters
unless the specification indicates that they are variable, configurable,
optional, implementation-defined, or implementation-specific.

This refinement was motivated by the second challenge snippet, which describes
fixed CSR address-mapping conventions. Without this restriction, the model could
incorrectly extract parameters such as CSR address width, CSR encoding ranges,
and privilege-level encoding fields.

After refinement, the CSR snippet correctly produces:

```yaml
parameters: []
```

---

## 6. Model and Provider Scope

The current implementation uses Gemini 2.5 Flash through the `google-genai`
Python SDK. The provider-specific client is created only when a live extraction
is requested, so importing the validation models and running the offline tests do
not require an API key.

The prompt, normalization, validation, and serialization stages are conceptually
independent of the provider. The current code has not yet implemented a formal
multi-provider adapter, however, so provider portability remains a future
improvement rather than a demonstrated feature.

---

## 7. Handling Model Output Inconsistencies

During testing, Gemini occasionally returned fields in a different format from the expected schema.

For example, the model could return:

```json
{
  "evidence": "The parameter is implementation-specific."
}
```

while the expected schema required:

```json
{
  "evidence": [
    "The parameter is implementation-specific."
  ]
}
```

The same issue could occur with the `constraints` field.

To handle this, a normalization step was added before Pydantic validation.

The `normalize_response()` function converts string values into lists when necessary.

For example:

```python
if isinstance(parameter.get("evidence"), str):
    parameter["evidence"] = [parameter["evidence"]]
```

Similarly:

```python
if isinstance(parameter.get("constraints"), str):
    parameter["constraints"] = [parameter["constraints"]]
```

This allows minor formatting inconsistencies to be handled without weakening the final schema validation.

---

## 8. Structured Validation

The final LLM response is validated using Pydantic.

The expected parameter structure is:

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

The complete extraction result is represented as:

```python
class ExtractionResult(BaseModel):
    parameters: list[ArchitecturalParameter]
```

This creates a validation boundary between the LLM and the final output.

The pipeline is therefore:

```text
LLM Output
    ↓
JSON Parsing
    ↓
Normalization
    ↓
Pydantic Validation
    ↓
YAML Serialization
```

If the response does not satisfy the expected schema, the extraction process raises an error instead of silently producing invalid output.

---

## 9. Hallucination Mitigation Strategy

Several strategies were used to reduce hallucinations.

### 9.1 Evidence Requirement

Every extracted parameter must include evidence from the supplied specification.

This makes unsupported extractions easier to identify.

### 9.2 Explicit Source Restriction

The prompt instructs the model to use only information explicitly present in the supplied snippet.

The model is not allowed to introduce additional facts from general knowledge.

### 9.3 No Inferred Constraints

The prompt explicitly prohibits inventing constraints that are not stated in the source.

For example, the model should not infer additional cache properties simply because it knows common cache architectures.

### 9.4 Explicit Classification

The model must separately classify:

* `implementation_defined`
* `implementation_specific`

This reduces ambiguous categorization.

### 9.5 Structured Output

The model is instructed to return JSON with a fixed top-level structure:

```json
{
  "parameters": [...]
}
```

The output is then validated with Pydantic.

### 9.6 Automated Tests

The project includes tests for:

* Valid responses
* Empty results
* Required fields
* Invalid confidence values
* Missing required fields
* Evidence normalization
* Mocked Gemini responses
* Invalid JSON
* Empty model responses
* Simulated API failures
* Reviewed YAML fixture structure
* Required output fields
* Controlled parameter types and confidence values
* Missing and unexpected fields
* YAML serialization

The suite uses injected fake model responses and committed fixtures from the
`results/` directory. It therefore runs without a Gemini API key and does not
make external API requests.

---

## 10. Final Prompt

The current system prompt instructs the model to:

1. Extract only explicitly variable or implementation-dependent architectural parameters.
2. Use information only from the supplied specification snippet.
3. Avoid hallucinating information or constraints.
4. Return structured fields for each parameter.
5. Distinguish implementation-defined from implementation-specific behavior.
6. Provide supporting evidence.
7. Use controlled confidence values.
8. Use lowercase `snake_case` parameter names.
9. Return an empty parameter list when no qualifying parameters are found.
10. Return only valid JSON.

The final prompt is implemented directly in:

```text
src/extractor.py
```

The prompt evolved from a simple keyword-based extraction instruction into a more constrained specification-aware extraction prompt.

The main refinement was to treat the keyword list as an extraction signal rather than as an instruction to extract every sentence containing those words. This helps avoid false positives from fixed architectural conventions and constants.

---

## 11. Evaluation Results

The two provided challenge snippets were used as initial evaluation examples.

### Snippet 1: Cache Parameters

The extractor identified:

```text
cache_capacity
cache_organization
cache_block_size
```

These parameters were identified because the specification explicitly states that the cache capacity, cache organization, and cache block size are implementation-specific.

The cache block size also contains an explicit constraint requiring uniformity throughout the system for the initial set of CMO extensions.

### Snippet 2: CSR Accessibility

The extractor returned:

```yaml
parameters: []
```

The snippet describes fixed CSR address encoding conventions rather than implementation-variable parameters.

This demonstrates that the extraction process is intentionally scoped to parameters whose behavior or values are explicitly variable, optional, implementation-defined, or implementation-specific, rather than extracting every architectural constant or encoding rule.

---

## 12. Current Limitations

The current prototype has several limitations.

### Limited Evaluation Dataset

The initial evaluation uses only the two snippets supplied in the coding challenge.

A larger manually annotated dataset would be required to quantitatively evaluate extraction accuracy.

### No Quantitative Accuracy Metrics

Precision, recall, and F1 score have not yet been calculated.

These metrics would require a manually labeled ground-truth dataset covering a larger portion of the RISC-V specification.

### LLM Dependency

The quality of extraction depends partly on the behavior of the selected Gemini model.

Although prompt constraints and validation reduce errors, human review remains useful for high-confidence architectural analysis.

### Prototype-Scale Processing

The current implementation processes individual text snippets from the `data` directory.

A complete implementation would require:

* RISC-V document ingestion
* Automatic document segmentation
* Section tracking
* Source references
* Duplicate detection
* Large-scale evaluation

---

## 13. Future Improvements

Future versions could improve the system by:

* Processing the complete RISC-V ISA and Privileged Architecture specifications.
* Automatically splitting large documents into chunks.
* Preserving section numbers and page references.
* Adding source locations to evidence.
* Creating a manually annotated benchmark dataset.
* Measuring precision, recall, and F1 score.
* Comparing results across multiple LLMs.
* Evaluating different prompt strategies.
* Adding duplicate parameter detection.
* Supporting incremental specification updates.
* Comparing parameters across RISC-V specification versions.
* Supporting local or open-source LLMs.
* Adding human-in-the-loop review for uncertain extractions.

---

## 14. Summary

The project demonstrates an AI-assisted pipeline for extracting architectural parameters from RISC-V specifications.

The prompt was refined iteratively to address three main challenges:

1. **Extraction scope** — ensuring the model focuses on implementation-variable parameters rather than extracting every architectural constant.
2. **Hallucination control** — requiring evidence from the provided specification and prohibiting unsupported inference.
3. **Output reliability** — combining structured JSON generation, response normalization, Pydantic validation, and automated tests.

The current prototype successfully processes the provided example snippets and produces structured YAML output suitable for further analysis and review.

The methodology is designed to be extensible to larger portions of the RISC-V specification and to other LLM providers, while maintaining a validation layer that separates model-generated output from trusted structured data.
