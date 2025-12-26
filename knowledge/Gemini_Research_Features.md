# Gemini for Research Capabilities

## Core Features

* **Fine-tuning**: Customize models for specific modalities/domains.
* **Output Control**:
  * `Logprobs`: Analyze token probabilities for uncertainty/confidence scoring.
  * `CitationMetadata`: Retrieve rigorous sourcing information.
  * `responseSchema`: Enforce strict output structures (JSON).
  * `topP` / `topK`: Control generation diversity.
* **Multimodal**: Native processing of Images, Audio, and Video.
* **Long Context**:
  * Flash: 1M+ tokens.
  * Pro: 2M+ tokens.

## SDK Usage (Python)

```python
from google import genai
client = genai.Client()

# Generate with Logprobs & Config
response = client.models.generate_content(
    model="gemini-2.0-flash", # Or gemini-3-*
    contents="Query...",
    config=types.GenerateContentConfig(
        response_logprobs=True,
        response_mime_type="application/json",
        response_schema={...}
    )
)
```

## Academic Use Cases

* **Uncertainty Quantification**: Use Logprobs to flag low-confidence claims.
* **Fact Verification**: Use CitationMetadata.
* **Long-Form Analysis**: Ingest entire papers/books via Long Context.
