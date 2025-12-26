# Gemini Video Understanding Reference

*Dec 2025 Specifications*

## Input Methods

1. **File API (> 20MB)**: Upload video. Default sampling: 1 FPS.

    ```python
    file = client.files.upload(file="video.mp4")
    ```

2. **Inline (< 20MB)**: Small clips only.
3. **YouTube URL**: Pass directly.

    ```python
    types.Part.from_uri(file_uri='https://youtube.com/watch?v=...', mime_type='video/*')
    ```

## Customization (Video Metadata)

Control how the model "sees" the video.

```python
video_metadata=types.VideoMetadata(
    start_offset='10s',
    end_offset='20s',
    fps=5  # Custom sampling rate
)
```

## Capabilities

- **Summary & Q&A**: "Summarize video..."
- **Timestamps**: "What happens at 01:15?"
- **Detailed Extraction**: Audio + Visual processing.

## Token Usage

- **Default (1 FPS)**: ~300 tokens/sec.
- **Low Res**: ~100 tokens/sec.
- **Audio**: 32 tokens/sec.
