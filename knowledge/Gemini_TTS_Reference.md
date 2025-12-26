# Gemini Native TTS Reference

*Dec 2025 Specifications*

## Capabilities

- **Models**: `gemini-2.5-flash-preview-tts` (Fast/Pro).
- **Control**: Style, Accent, Pace, Tone via natural language prompts.
- **Output**: Audio-only (PCM/WAV).

## Usage

### Single Speaker

```python
config = types.GenerateContentConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Kore')
        )
    )
)
```

### Multi Speaker

```python
multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
    speaker_voice_configs=[
        types.SpeakerVoiceConfig(speaker='Joe', ...),
        types.SpeakerVoiceConfig(speaker='Jane', ...)
    ]
)
```

## Prompting (Audio Profiles)

- **Profile**: Name, Role.
- **Scene**: Environment, Context.
- **Director's Notes**: Style, Pacing, Accent.
- **Transcript**: The actual text.

## Voices (Select List)

- **Kore** (Firm), **Puck** (Upbeat), **Fenrir** (Excitable), **Enceladus** (Breathy).
