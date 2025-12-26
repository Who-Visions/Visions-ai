# Gemini Audio Understanding Reference

*Dec 2025 Specifications*

## Capabilities

- **Tasks**: Description, Summarization, Q&A, Transcription.
- **Timestamps**: Can reference specific segments (e.g., "02:30 to 03:29").
- **Non-speech**: capable of understanding birdsong, sirens, etc.

## Input Methods

1. **File API (> 20MB)**: Recommended. Supports up to 9.5 hours total.
2. **Inline (< 20MB)**: Base64 encoded.

## Supported Formats

- WAV, MP3, AIFF, AAC, OGG Vorbis, FLAC.

## Technical Details

- **Token Usage**: 32 tokens per second (approx 1,920 tokens/min).
- **Sampling**: Downsampled to 16 Kbps, mono.
- **Model**: `gemini-2.5-flash` is the recommended model for audio understanding.

## Code Example

```python
contents=[
    "Generate a transcript.",
    types.Part.from_uri(file_uri=uploaded_file.uri, mime_type='audio/mp3')
]
```
