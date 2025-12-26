# Gemini Document Processing Reference

*Dec 2025 Specifications*

## Capabilities

- **Supported Format**: PDF (up to 1000 pages, 50MB).
- **Processing**: Native vision (charts, diagrams) + Text extraction.
- **Token Usage**: 258 tokens per page.
- **Change in Gemini 3**: PDF pages count as `IMAGE` modality in `usage_metadata`, NOT `DOCUMENT`.

## Input Methods

1. **Inline (< 20MB)**: base64 `application/pdf`.
2. **Files API (> 20MB)**: Upload, wait for processing state.

## Gemini 3 Updates

- **Media Resolution**: Can set low/medium/high resolution for PDF pages.
- **Billing**: Native text in PDFs is **free** (not charged as tokens).

## Code Example

```python
contents=[
    types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
    "Summarize this."
]
```
