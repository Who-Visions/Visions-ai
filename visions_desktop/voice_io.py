"""
Visions Desktop - Voice Input/Output
Wake word detection, speech recognition, and TTS.
"""

import os
import struct
import wave
import tempfile
import asyncio
import threading
from pathlib import Path

# Audio libs
try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    print("Install: pip install sounddevice numpy")
    sd = None
    np = None

# Picovoice wake word
try:
    import pvporcupine
except ImportError:
    print("Install: pip install pvporcupine")
    pvporcupine = None

# Edge TTS
try:
    import edge_tts
except ImportError:
    print("Install: pip install edge-tts")
    edge_tts = None


class VoiceIO:
    """Handle voice input (wake word, STT) and output (TTS)."""
    
    def __init__(self, app):
        self.app = app
        self.porcupine = None
        self.stream = None
        
        # Audio settings
        self.sample_rate = 16000
        self.frame_length = 512  # Porcupine frame size
        
        # TTS settings
        self.tts_voice = "en-US-GuyNeural"  # Deep male voice
        
        # State
        self.recording = False
        self.recorded_frames = []
    
    def start_listening(self):
        """Start listening for wake word."""
        if not pvporcupine:
            print("⚠️ Picovoice not installed - using fallback mode")
            self._fallback_listen()
            return
        
        access_key = os.getenv("PICOVOICE_ACCESS_KEY")
        if not access_key:
            print("⚠️ PICOVOICE_ACCESS_KEY not set - using fallback mode")
            self._fallback_listen()
            return
        
        try:
            # Initialize Porcupine with built-in wake words
            # For custom "Visions", you need to train on Picovoice Console
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=["computer", "hey google", "jarvis"]  # Built-in options
                # For custom: keyword_paths=["path/to/visions.ppn"]
            )
            
            print(f"🎤 Listening for wake word...")
            print(f"   Sample rate: {self.porcupine.sample_rate}")
            print(f"   Frame length: {self.porcupine.frame_length}")
            
            # Start audio stream
            self._start_audio_stream()
            
        except Exception as e:
            print(f"❌ Porcupine error: {e}")
            self._fallback_listen()
    
    def _start_audio_stream(self):
        """Start the audio input stream."""
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"Audio status: {status}")
            
            # Convert to int16
            audio_data = (indata[:, 0] * 32767).astype(np.int16)
            
            # Process with Porcupine
            if self.porcupine and not self.recording:
                # Split into frames
                for i in range(0, len(audio_data) - self.porcupine.frame_length, self.porcupine.frame_length):
                    frame = audio_data[i:i + self.porcupine.frame_length]
                    result = self.porcupine.process(frame)
                    if result >= 0:
                        # Wake word detected!
                        self.app.on_wake_word()
                        self._start_recording()
                        break
            
            # If recording, capture audio
            if self.recording:
                self.recorded_frames.append(audio_data.copy())
                
                # Simple silence detection (stop after 2 seconds of silence)
                if len(self.recorded_frames) > 100:  # ~3 seconds
                    self._stop_recording()
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            blocksize=self.frame_length,
            callback=audio_callback
        )
        self.stream.start()
        
        # Keep alive
        while self.app.running:
            sd.sleep(100)
    
    def _start_recording(self):
        """Start recording user speech."""
        self.recording = True
        self.recorded_frames = []
        print("🔴 Recording...")
    
    def _stop_recording(self):
        """Stop recording and process."""
        self.recording = False
        print("⏹️ Recording stopped")
        
        if self.recorded_frames:
            # Concatenate frames
            audio_data = np.concatenate(self.recorded_frames)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                with wave.open(f.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())
                
                # Transcribe with Whisper or Gemini
                text = self._transcribe(f.name)
                os.unlink(f.name)
                
                if text:
                    self.app.on_command(text)
    
    def _transcribe(self, audio_path: str) -> str:
        """Transcribe audio file to text."""
        # Use Gemini for transcription
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.0-flash")
                
                # Upload and transcribe
                with open(audio_path, "rb") as f:
                    audio_data = f.read()
                
                response = model.generate_content([
                    "Transcribe this audio. Return only the transcription, nothing else.",
                    {"mime_type": "audio/wav", "data": audio_data}
                ])
                return response.text.strip()
        except Exception as e:
            print(f"❌ Transcription error: {e}")
        
        return ""
    
    def _fallback_listen(self):
        """Fallback mode without Picovoice - just watch Wispr Flow."""
        print("📝 Fallback mode: Watching Wispr Flow only")
        # The main app already has Flow Watcher running
        while self.app.running:
            import time
            time.sleep(1)
    
    def speak(self, text: str):
        """Speak text using Edge TTS."""
        if not edge_tts or not text:
            return
        
        async def _speak():
            try:
                communicate = edge_tts.Communicate(text, self.tts_voice)
                
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    await communicate.save(f.name)
                    
                    # Play audio
                    self._play_audio(f.name)
                    os.unlink(f.name)
            except Exception as e:
                print(f"❌ TTS error: {e}")
        
        # Run async TTS
        asyncio.run(_speak())
    
    def _play_audio(self, path: str):
        """Play an audio file."""
        try:
            import subprocess
            # Use Windows Media Player or ffplay
            subprocess.run(
                ["powershell", "-Command", f"(New-Object Media.SoundPlayer '{path}').PlaySync()"],
                capture_output=True
            )
        except Exception as e:
            print(f"❌ Audio playback error: {e}")
    
    def stop(self):
        """Stop listening."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.porcupine:
            self.porcupine.delete()
