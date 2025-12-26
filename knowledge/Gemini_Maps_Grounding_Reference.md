# Gemini Maps Grounding Reference

*Dec 2025 Specifications*

## Constraints

- **Model Support**: Gemini 2.5 (Pro/Flash/Flash-Lite), Gemini 2.0 Flash.
- **NOT Supported**: Gemini 3.0.
- **Billing**: Charged per query.

## Implementation

1. **Enable Tool**: `tools=[types.Tool(google_maps=types.GoogleMaps(enable_widget=True))]`
2. **Optional Config**: `tool_config` with `retrieval_config` (LatLng).
3. **Process Response**:
    - `groundingMetadata.google_maps_widget_context_token`: Use with Google Maps JS API.
    - `groundingChunks`: Attribution sources (MUST display).

## Use Cases

- "Coffee near me"
- "Plan a trip to SF"
