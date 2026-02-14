"""
Gemini Text-to-Speech (TTS) Service
Implements capabilities to generate high-fidelity audio from text using Gemini 2.5 TTS models.
"""
import os
import logging
import base64
from typing import List, Optional, Dict, Union

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("⚠️ google.genai not found. Please install: pip install google-genai")
    genai = None
    types = None

# Configure logging
logger = logging.getLogger(__name__)

class AudioService:
    """
    Manages text-to-speech generation using Gemini 2.5 TTS models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not genai:
            raise ImportError("The 'google.genai' package is required for AudioService.")
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        # Initialize client
        self.client = genai.Client(http_options={'api_version': 'v1beta'})
        self.model = "gemini-2.5-flash-preview-tts"

    def generate_speech(self, 
                       text: str, 
                       voice_name: str = "Kore", 
                       output_path: str = "generated_speech.wav") -> Optional[str]:
        """
        Generates single-speaker audio from text.
        
        Args:
            text: The text to speak.
            voice_name: Name of the prebuilt voice (e.g., 'Kore', 'Puck', 'Fenrir').
            output_path: Path to save the generated wav file.
            
        Returns:
            Path to the saved audio file, or None if failed.
        """
        logger.info(f"🗣️ Generating speech: '{text[:50]}...' using voice {voice_name}")
        
        try:
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        )
                    )
                )
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=config
            )

            return self._save_audio(response, output_path)

        except Exception as e:
            logger.error(f"❌ Speech Generation Failed: {e}")
            return None

    def generate_conversation(self, 
                            conversation_text: str, 
                            speakers: List[Dict[str, str]], 
                            output_path: str = "conversation.wav") -> Optional[str]:
        """
        Generates multi-speaker audio from a conversation script.
        
        Args:
            conversation_text: The conversation script (e.g., "Joe: Hi\nJane: Hello").
            speakers: List of dicts mapping speaker names to voice names. 
                      Example: [{'name': 'Joe', 'voice': 'Kore'}, {'name': 'Jane', 'voice': 'Puck'}]
            output_path: Path to save the generated wav file.
            
        Returns:
            Path to the saved audio file, or None if failed.
        """
        logger.info(f"🗣️👥 Generating conversation with {len(speakers)} speakers...")
        
        try:
            speaker_configs = []
            for spk in speakers:
                speaker_configs.append(
                    types.SpeakerVoiceConfig(
                        speaker=spk['name'],
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=spk['voice']
                            )
                        )
                    )
                )

            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=speaker_configs
                    )
                )
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=conversation_text,
                config=config
            )

            return self._save_audio(response, output_path)

        except Exception as e:
            logger.error(f"❌ Conversation Generation Failed: {e}")
            return None

    def _save_audio(self, response, output_path: str) -> Optional[str]:
        """
        Internal helper to save audio data from response.
        """
        try:
            # Check for candidates and content
            if not response.candidates or not response.candidates[0].content.parts:
                logger.error("❌ No content returned in response.")
                return None
                
            part = response.candidates[0].content.parts[0]
            
            if part.inline_data:
                audio_data = part.inline_data.data
                
                import wave
                
                logger.info(f"💾 Saving audio to {output_path}...")
                
                with wave.open(output_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(24000)
                    wf.writeframes(audio_data)
                    
                logger.info(f"✅ Audio saved: {output_path}")
                return output_path
            else:
                 logger.error("❌ No inline data in response part.")
                 return None

        except Exception as e:
            logger.error(f"❌ Saving Audio Failed: {e}")
            return None
