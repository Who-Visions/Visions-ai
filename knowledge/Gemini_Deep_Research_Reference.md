# Gemini Deep Research Reference

*Dec 2025 Specifications*

## Overview

**Deep Research** is an autonomous agent (not just a model) that plans, searches, reads, and synthesizes multi-step research tasks.

## Key constraints

- **API**: Uses `Interactions API` (`client.interactions.create`), NOT `generate_content`.
- **Execution**: MUST use `background=True` (Async). Partial interaction headers returned immediately; poll for `status="completed"`.
- **Inputs**: Google Search (Default), URL Context, File Search (Previews).
- **Time**: Can take minutes to hours (Max 60 min).

## Usage Pattern (Python)

```python
interaction = client.interactions.create(
    input="Research tenure of Google Cloud CEOs",
    agent='deep-research-pro-preview-12-2025',
    background=True
)
# Poll for results
while True:
    status = client.interactions.get(interaction.id)
    if status.status == "completed":
        print(status.outputs[-1].text)
        break
    time.sleep(10)
```

## Best Practices

- **Steerability**: Explicitly define output format (e.g., "Table with columns X, Y, Z").
- **Unknowns**: Instruct agent on how to handle missing data ("State 'N/A' rather than guessing").
