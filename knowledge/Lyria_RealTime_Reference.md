# Lyria RealTime Music Generation

*Dec 2025 Specifications*

**Model ID:** `models/lyria-realtime-exp` (Experimental)
**Protocol:** WebSocket (Bidirectional, Low-Latency Streaming)

## Overview

Lyria RealTime uses a persistent WebSocket connection to generate steerable, instrumental music in real-time. It is distinct from the Live API but shares the WebSocket architecture.

## Capabilities

- **Real-Time Steering:** smoothly transition styles/moods using `WeightedPrompts`.
- **Live Config Updates:** BPM, Density, Brightness, Scale (requires `reset_context()` for major changes like BPM/Scale).
- **Output:** Raw 16-bit PCM Audio, 48kHz, Stereo.

## Best Practices

- **Robust Buffering:** Essential to handle network jitter.
- **Gradual Steering:** Use weights to blend new prompts rather than hard switching.
- **Instrumental Only:** No vocals (unless `music_generation_mode=VOCALIZATION` is set to treat vocals as an instrument).

## Python Implementation (Async)

```python
import asyncio
from google import genai
from google.genai import types

client = genai.Client(http_options={'api_version': 'v1alpha'})

# Connect
async with client.aio.live.music.connect(model='models/lyria-realtime-exp') as session:
    
    # 1. Initial Config
    await session.set_weighted_prompts(
        prompts=[types.WeightedPrompt(text='minimal techno', weight=1.0)]
    )
    await session.set_music_generation_config(
        config=types.LiveMusicGenerationConfig(bpm=90, temperature=1.0)
    )

    # 2. Start Streaming
    await session.play()

    # 3. Receive Loop
    async for message in session.receive():
        audio_data = message.server_content.audio_chunks[0].data
        # Process PCM16 audio...
        
    # 4. Steer (Runtime)
    await session.set_weighted_prompts(
        prompts=[
            types.WeightedPrompt(text='minimal techno', weight=0.3),
            types.WeightedPrompt(text='dubstep drop', weight=0.7)
        ]
    )
```

## Configuration Options

- **BPM:** [60-200]
- **Guidance:** [0.0-6.0] (Default 4.0) - Prompt adherence vs. smoothness.
- **Density:** [0.0-1.0] - Note density.
- **Brightness:** [0.0-1.0] - Tonal quality.
- **Scale:** `C_MAJOR_A_MINOR`, `D_MAJOR_B_MINOR`, etc. or `SCALE_UNSPECIFIED`.
- **Music Generation Mode:** `QUALITY` (Default), `DIVERSITY`, `VOCALIZATION`.

## Limitations

- **Latency:** Requires robust client-side handling.
- **Safety:** Prompts filtered for safety; explanation in `filtered_prompt`.
- **Watermarking:** SynthID watermarking is always active.
