# Gemini Long Context Reference

*Dec 2025 Specifications*

## Capabilities

- **Window Size**: 1 Million+ tokens.
- **Modalities**: Text, Video, Audio, Code.
- **Equivalent**: ~50k lines of code, 8 novels, 200 podcast episodes.

## Optimization: Context Caching

- **Use Case**: When reusing same large context (files, docs) multiple times.
- **Benefit**: Significantly reduces cost (approx 4x cheaper for cached input) and latency.
- **Strategy**: Cache the static "haystack", query with dynamic "needles".

## Best Practices

- **Query Placement**: Put query/question at the *end* of the prompt (after context).
- **Latency**: Longer context = higher time-to-first-token. Caching helps.
