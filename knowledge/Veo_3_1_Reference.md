# Veo 3.1 & Nano Banana (Gemini Image) Reference

*Dec 2025 Specifications*

## Nano Banana (Image Generation)

"Nano Banana" refers to Gemini's native image generation capabilities.

| Version | Model Name | Use Case |
| :--- | :--- | :--- |
| **Nano Banana** | `gemini-2.5-flash-image` | High-volume, low-latency, speed. |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | Professional asset production, high fidelity, reasoning. |

### Protocol

Use `client.models.generate_content` (NOT `generate_images`).

```python
response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="Prompt here",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        media_resolution="media_resolution_high" 
    )
)

for part in response.parts:
    if part.inline_data:
        image = part.as_image()
        image.save("output.png")
```

---

## Veo 3.1 (Video Generation)

State-of-the-art 1080p video generation with native audio.

| Model | ID | Features |
| :--- | :--- | :--- |
| **Veo 3.1 Preview** | `veo-3.1-generate-preview` | Text-to-Video, Image-to-Video, Video Extension, 8s max. |
| **Veo 3.1 Fast** | `veo-3.1-fast-generate-preview` | Optimized for speed/business. |

### Key Features

1. **Native Audio**: Always on for Veo 3.x.
2. **Reference Images**: Up to 3 images (Asset references).
3. **Interpolation**: Define First and Last frames.
4. **Extension**: Extend Veo videos by 7s (input video must be < 141s).

### Protocol

Use `client.models.generate_videos` + Polling.

```python
# Standard Generation
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="Cinematic shot...",
    config=types.GenerateVideosConfig(
        aspect_ratio="16:9",
        resolution="1080p", # Only for 8s duration
        duration_seconds=8, # 4, 6, or 8
        person_generation="allow_adult"
    )
)

# Polling Loop
while not operation.done:
    print("Waiting...")
    time.sleep(10)
    operation = client.operations.get(operation)

# Save
video = operation.response.generated_videos[0]
video.video.save("output.mp4")
```

### Image-to-Video

Pass `image` (Nano Banana output) to `generate_videos`.

```python
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="Animate this...",
    image=previous_image_response.parts[0].as_image()
)
```

### Reference Images (Veo 3.1 Only)

```python
ref_img = types.VideoGenerationReferenceImage(
    image=image_asset,
    reference_type="asset"
)
config = types.GenerateVideosConfig(reference_images=[ref_img])
```
