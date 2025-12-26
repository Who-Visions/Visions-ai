# Gemini Image Generation Reference

*Dec 2025 Specifications*

## Models

- **High-Fidelity**: `gemini-3-pro-image-preview` (aka **Nano Banana Pro**)
  - Supports "Thinking" (Logic/Composition refinement).
  - Up to 14 reference images (mixing styles/characters).
  - 1K, 2K, 4K resolution.
  - Grounding with Google Search.
- **Fast**: `gemini-2.5-flash-image` (aka **Nano Banana**)
  - standard text-to-image, faster inference.

## Capabilities

### 1. Text-to-Image

```python
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="A photorealistic close-up...",
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="16:9", image_size="2K")
    )
)
```

### 2. Image Editing (Inpainting/Modification)

Provide the base image + text instruction.

```python
contents = [
    types.Part.from_image(Image.open("room.png")),
    "Change the blue sofa to a brown leather one. Keep lighting same."
]
```

### 3. Multi-Turn Editing (Chat)

Use `client.chats.create` to iterate.
**Critical**: `gemini-3-pro-image-preview` emits `thought_signature` in responses.

- If using SDK `chat` object: **Handled automatically**.
- If manually managing history: Must pass `thought_signature` back in next turn.

### 4. Grounding

Generate images based on real-time data.

```python
tools = [types.Tool(google_search=types.GoogleSearch())]
```

### 5. Reference Images (Gemini 3 Only)

Mix up to 14 images (e.g., 5 character refs, 9 style refs).

```python
contents = ["Group photo...", img1, img2, img3, ...]
```

## Thought Signatures (Gemini 3 Pro Image)

Encrypted representations of the model's internal thought process.

- **Rule**: All `inline_data` (images) and the first text part after thoughts have a signature.
- **Handling**: Pass back exactly as received in the next turn's history.

## Output Handling

Images come as `inline_data` (base64).

```python
for part in response.parts:
    if part.inline_data:
        img = Image.open(io.BytesIO(part.inline_data.data))
```
