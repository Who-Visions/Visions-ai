# Gemini URL Context Reference

*Dec 2025 Specifications*

## Overview

Allows model to read and analyze content from specific URLs (Search Grounding finds URLs; this tool *reads* them).

## Capabilities

- **Limit**: Up to 20 URLs per request.
- **Content Types**: HTML, PDF, CSV, Text. (Paywalled/YouTube not supported).
- **Billing**: Content counts as Input Tokens.

## Usage (Python)

```python
tools = [{"url_context": {}}]
contents = ["Compare https://site1.com and https://site2.com"]
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(tools=tools)
)
```

## Combined with Search

Can combine `google_search` (to find pages) with `url_context` (to deeper reading).
