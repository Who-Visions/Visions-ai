# Gemini Grounding Reference

*Dec 2025 Specifications*

## Overview

Connects Gemini to real-time web info via Google Search.

- **Gemini 3 Policy**: Billing starts Jan 5, 2026. Charged *per search query*, not per prompt.
- **Model Support**: All Flash/Pro models (2.0+).

## Implementation

1. **Enable Tool**: `tools=[types.Tool(google_search=types.GoogleSearch())]`
2. **Process Response**:
    - Response includes `groundingMetadata`.
    - `webSearchQueries`: What the model searched for.
    - `groundingChunks`: The sources (URIs).
    - `groundingSupports`: Mapping text segments to sources.

## Citation Parsing (Python)

```python
supports = candidate.grounding_metadata.grounding_supports
chunks = candidate.grounding_metadata.grounding_chunks
# Iterate supports, find matching chunk indices, insert [N](url) into text.
# Sort supports in descending order to avoid index shifting!
```

## Legacy Notes

- Gemini 1.5 used `google_search_retrieval` with `dynamic_threshold`. New format is just `google_search`.
