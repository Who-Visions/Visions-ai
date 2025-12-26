# Gemini Image Understanding Reference

*Dec 2025 Specifications*

## Capabilities

- **Generative**: Captioning, Q&A.
- **Computer Vision**: Object Detection (Gemini 2.0+), Segmentation (Gemini 2.5+).

## Input Methods

1. **Inline (< 20MB)**: Base64 encoded.

    ```python
    types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg')
    ```

2. **File API (> 20MB)**: Upload first.

    ```python
    file = client.files.upload(file="path/to/img.jpg")
    ```

## specialized Tasks

### Object Detection (Gemini 2.0+)

Returns 2D bounding boxes normalized [0, 1000].

```python
config = types.GenerateContentConfig(response_mime_type="application/json")
prompt = "Detect items. Output box_2d [ymin, xmin, ymax, xmax]..."
```

### Segmentation (Gemini 2.5+)

Returns JSON with `box_2d`, `label`, and `mask` (base64 PNG).
**Recommendation**: Set `thinking_budget=0` for best results.

```python
prompt = "Give segmentation masks..."
```

## Token Usage

- **Standard**: 258 tokens (tiled).
- **Media Resolution**: Controlled via `media_resolution` param (Low/Medium/High).
