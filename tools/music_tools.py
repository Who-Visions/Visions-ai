"""
Lyria RealTime Music Generation Tools
Implements capabilities to interact with the experimental Lyria model via Gemini API.
"""
import asyncio
import os
import logging
from typing import List, Dict, Optional, AsyncGenerator

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("⚠️ google.genai not found. Please install: pip install google-genai")
    genai = None
    types = None

# Configure logging
logger = logging.getLogger(__name__)

class LyriaMusicSession:
    """
    Manages a real-time music generation session with Lyria (models/lyria-realtime-exp).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not genai:
            raise ImportError("The 'google.genai' package is required for LyriaMusicSession.")
        
        # Initialize client with experimental API version
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
             # Fallback to vertex/default creds if configured in environment, but explicit key is safer for separate genai lib
             pass
             
        # Initialize client. API key might be implicit if using Vertex, 
        # but for google-genai library direct usage often needs key or env var.
        # Assuming environment is set up or Vertex AI Auth is handled.
        # Note: Lyria RealTime is currently on v1alpha
        self.client = genai.Client(http_options={'api_version': 'v1alpha'})
        self.session = None

    async def connect_and_stream(self, 
                               initial_prompts: List[Dict[str, float]], 
                               bpm: int = 120, 
                               temperature: float = 1.0):
        """
        Connects to the Lyria model, configures the session, and yields audio chunks.
        
        Args:
            initial_prompts: List of dicts with 'text' and 'weight'.
                             Example: [{'text': 'Techno', 'weight': 1.0}]
            bpm: Beats per minute.
            temperature: Creativity control.
            
        Yields:
            bytes: Raw PCM 16-bit audio chunks.
        """
        model_id = 'models/lyria-realtime-exp'
        
        # Convert dict prompts to types.WeightedPrompt
        weighted_prompts = [
            types.WeightedPrompt(text=p['text'], weight=p['weight']) 
            for p in initial_prompts
        ]

        logger.info(f"🎵 Connecting to Lyria ({model_id})...")
        
        try:
            async with self.client.aio.live.music.connect(model=model_id) as session:
                self.session = session
                
                # 1. Set Initial Prompts
                await session.set_weighted_prompts(prompts=weighted_prompts)
                
                # 2. Set Configuration
                await session.set_music_generation_config(
                    config=types.LiveMusicGenerationConfig(
                        bpm=bpm, 
                        temperature=temperature
                    )
                )
                
                # 3. Start Playing
                logger.info("▶️ Starting Playback...")
                await session.play()
                
                # 4. Stream Audio
                async for message in session.receive():
                    if message.server_content and message.server_content.audio_chunks:
                        for chunk in message.server_content.audio_chunks:
                            yield chunk.data
                    
                    # Yield control to event loop
                    await asyncio.sleep(0)
                    
        except Exception as e:
            logger.error(f"❌ Lyria Session Error: {e}")
            raise e
        finally:
            self.session = None
            logger.info("⏹️ Lyria Session Closed.")

    async def update_prompts(self, prompts: List[Dict[str, float]]):
        """
        Updates the weighted prompts in real-time.
        """
        if not self.session:
            logger.warning("⚠️ No active session to update prompts.")
            return

        weighted_prompts = [
            types.WeightedPrompt(text=p['text'], weight=p['weight']) 
            for p in prompts
        ]
        
        await self.session.set_weighted_prompts(prompts=weighted_prompts)
        logger.info(f"🎛️ Updated Prompts: {prompts}")

    async def update_config(self, bpm: Optional[int] = None, 
                            scale: Optional[str] = None,
                            temperature: float = 1.0):
        """
        Updates configuration. Note: changing BPM or Scale requires context reset.
        """
        if not self.session:
            logger.warning("⚠️ No active session to update config.")
            return

        config_args = {'temperature': temperature}
        if bpm: config_args['bpm'] = bpm
        
        # Handle Scale Enum conversion if needed, simplified here
        # if scale == 'C_MAJOR_A_MINOR': config_args['scale'] = types.Scale.C_MAJOR_A_MINOR
        
        await self.session.set_music_generation_config(
            config=types.LiveMusicGenerationConfig(**config_args)
        )
        
        # If BPM or Scale changed, we might need to reset context for it to take effect smoothly
        if bpm or scale:
            await self.session.reset_context()
            logger.info("🔄 Context Reset for Config Update")

    async def stop(self):
        """Stops the playback."""
        if self.session:
            await self.session.stop()
            logger.info("II Paused/Stopped Playback")
