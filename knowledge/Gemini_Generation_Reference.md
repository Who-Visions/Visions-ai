# Gemini Generation Reference

*Dec 2025 Specifications*

## Thinking with Gemini

Gemini 3 models support "Thinking" to reason before responding.
**Control**: Use `ThinkingConfig` to set a budget.
**Default**: Enabled by default on supported models.

### Python Implementation

```python
from google.genai import types

config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=1024) # Set token budget
)
```

*Note: Set `thinking_budget=0` to disable thinking.*

## Temperature Policy

**Gemini 3 Recommendation**: Keep `temperature` at **1.0**.

- Lowering usage (< 1.0) can significantly degrade reasoning and math performance.
- Do not lower temperature for "more deterministic" results with Gemini 3; let the Thinking process handle accuracy.

## System Instructions

Guide behavior via `system_instruction` in `GenerateContentConfig`.

```python
config = types.GenerateContentConfig(
    system_instruction="You are a coding expert."
)
```

## Multimodal Inputs

Combine text, images, audio, and video in `contents`.

```python
from PIL import Image
image = Image.open("file.png")
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[image, "Describe this."]
)
```

## Streaming

Use `generate_content_stream` for incremental responses.

```python
for chunk in client.models.generate_content_stream(...):
    print(chunk.text, end="")
```
