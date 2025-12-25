"""
Visions Desktop - Siri-like AI Assistant
System tray app with wake word, voice I/O, and smart home control.

Requirements:
    pip install pystray pillow sounddevice numpy pvporcupine edge-tts google-generativeai
"""

import os
import sys
import threading
import asyncio
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


class VisionsDesktop:
    """Main Visions Desktop Application."""
    
    def __init__(self):
        self.running = False
        self.listening = False
        self.muted = False
        
        # Components (lazy loaded)
        self._wake_word = None
        self._voice_io = None
        self._brain = None
        self._tray = None
    
    def start(self):
        """Start the Visions Desktop application."""
        print("🚀 Starting Visions Desktop...")
        self.running = True
        
        # Start tray icon in main thread
        from visions_desktop.tray import VisionsTray
        self._tray = VisionsTray(self)
        
        # Start voice listener in background
        self._start_voice_thread()
        
        # Run tray (blocks main thread)
        self._tray.run()
    
    def _start_voice_thread(self):
        """Start the voice listening thread."""
        def voice_loop():
            from visions_desktop.voice_io import VoiceIO
            self._voice_io = VoiceIO(self)
            self._voice_io.start_listening()
        
        thread = threading.Thread(target=voice_loop, daemon=True)
        thread.start()
    
    def on_wake_word(self):
        """Called when wake word is detected."""
        print("🎯 Wake word detected!")
        self.listening = True
        if self._tray:
            self._tray.set_status("Listening...")
    
    def on_command(self, text: str):
        """Process a voice command."""
        print(f"📝 Command: {text}")
        
        # Process with brain
        from visions_desktop.brain import VisionsBrain
        if not self._brain:
            self._brain = VisionsBrain()
        
        response = self._brain.process(text)
        print(f"💬 Response: {response}")
        
        # Speak response
        if not self.muted and self._voice_io:
            self._voice_io.speak(response)
        
        # Update tray
        if self._tray:
            self._tray.set_status("Ready")
            self._tray.notify("Visions", response[:100])
        
        self.listening = False
    
    def toggle_mute(self):
        """Toggle voice output."""
        self.muted = not self.muted
        status = "muted" if self.muted else "unmuted"
        print(f"🔇 Voice {status}")
        if self._tray:
            self._tray.set_status(f"Voice {status}")
    
    def stop(self):
        """Stop the application."""
        print("🛑 Stopping Visions Desktop...")
        self.running = False
        if self._tray:
            self._tray.stop()


def main():
    app = VisionsDesktop()
    app.start()


if __name__ == "__main__":
    main()
