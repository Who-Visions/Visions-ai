"""
Wispr Flow Watcher for Visions
Monitors Wispr Flow's SQLite database for new dictations
and processes "Visions" commands automatically.

Usage: python flow_watcher.py
"""

import sqlite3
import time
import asyncio
from datetime import datetime
from typing import Optional, Callable
import google.generativeai as genai
import os

FLOW_DB_PATH = "C:/Users/super/AppData/Roaming/Wispr Flow/flow.sqlite"
TRIGGER_WORDS = ["visions", "hey visions", "vision"]
POLL_INTERVAL = 2  # seconds


class FlowWatcher:
    """Watch Wispr Flow for new dictations and process Visions commands."""
    
    def __init__(self, db_path: str = FLOW_DB_PATH):
        self.db_path = db_path
        self.last_timestamp = None
        self.running = False
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Load tools
        from tools.voice_tools import VoiceToolExecutor
        self.executor = VoiceToolExecutor()
        
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _get_latest_timestamp(self) -> Optional[int]:
        """Get the timestamp of the most recent dictation."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(timestamp) FROM History 
            WHERE formattedText IS NOT NULL AND formattedText != ''
        """)
        result = cursor.fetchone()[0]
        conn.close()
        return result
    
    def _get_new_dictations(self, since_timestamp: int) -> list:
        """Get dictations newer than the given timestamp."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, app, formattedText, editedText
            FROM History 
            WHERE timestamp > ? AND formattedText IS NOT NULL AND formattedText != ''
            ORDER BY timestamp ASC
        """, (since_timestamp,))
        
        results = []
        for row in cursor.fetchall():
            ts, app, formatted, edited = row
            results.append({
                "timestamp": ts,
                "app": app,
                "text": edited or formatted
            })
        
        conn.close()
        return results
    
    def _is_visions_command(self, text: str) -> tuple[bool, str]:
        """Check if text is a Visions command and extract the actual command."""
        text_lower = text.lower().strip()
        
        for trigger in TRIGGER_WORDS:
            if text_lower.startswith(trigger):
                # Extract command after trigger word
                command = text[len(trigger):].strip()
                if command.startswith(","):
                    command = command[1:].strip()
                return True, command
        
        return False, ""
    
    async def _process_command(self, command: str) -> str:
        """Process a Visions command - simple keyword matching for now."""
        print(f"🧠 Processing command: {command}")
        
        cmd_lower = command.lower()
        
        try:
            # Light control commands
            if any(word in cmd_lower for word in ["light", "lights", "lamp", "eve", "adam", "eden"]):
                from tools.lifx_tools import control_lights
                
                # Determine action
                if "off" in cmd_lower:
                    action = "off"
                elif "on" in cmd_lower:
                    action = "on"
                elif "toggle" in cmd_lower:
                    action = "toggle"
                else:
                    action = "color"
                
                # Determine selector
                selector = "all"
                for name in ["eve", "adam", "eden", "bedroom", "living room"]:
                    if name in cmd_lower:
                        selector = name.title()
                        break
                
                # Determine color
                color = None
                for c in ["red", "blue", "green", "purple", "orange", "pink", "white", "warm white"]:
                    if c in cmd_lower:
                        color = c
                        action = "color"
                        break
                
                # Determine kelvin
                kelvin = None
                import re
                k_match = re.search(r'(\d{4})k', cmd_lower)
                if k_match:
                    kelvin = int(k_match.group(1))
                    action = "kelvin"
                
                result = control_lights(action, selector, color, kelvin=kelvin)
                print(f"✅ {result}")
                return result
            
            # Flow context commands
            elif any(word in cmd_lower for word in ["dictation", "said", "history", "stats"]):
                from tools.flow_tools import get_flow_context
                if "stats" in cmd_lower:
                    result = get_flow_context("stats")
                else:
                    result = get_flow_context("recent", limit=5)
                print(f"✅ {result}")
                return result
            
            else:
                print("❓ Unrecognized command")
                return "Unrecognized command"
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return f"Error: {str(e)}"
    
    def _on_new_dictation(self, dictation: dict):
        """Handle a new dictation."""
        text = dictation["text"]
        app = dictation["app"]
        
        print(f"\n📝 New dictation [{app}]: {text[:80]}...")
        
        is_command, command = self._is_visions_command(text)
        
        if is_command and command:
            print(f"🎯 Visions command detected!")
            asyncio.run(self._process_command(command))
        else:
            print("   (Not a Visions command)")
    
    def start(self):
        """Start watching for new dictations."""
        print("🔍 Wispr Flow Watcher started")
        print(f"   Watching: {self.db_path}")
        print(f"   Trigger words: {TRIGGER_WORDS}")
        print(f"   Poll interval: {POLL_INTERVAL}s")
        print("\n💡 Dictate 'Visions, turn on the lights' into any app to test")
        print("   Press Ctrl+C to stop\n")
        
        # Get current latest timestamp
        self.last_timestamp = self._get_latest_timestamp() or 0
        self.running = True
        
        try:
            while self.running:
                # Check for new dictations
                new_dictations = self._get_new_dictations(self.last_timestamp)
                
                for dictation in new_dictations:
                    self._on_new_dictation(dictation)
                    self.last_timestamp = dictation["timestamp"]
                
                time.sleep(POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Watcher stopped")
            self.running = False
    
    def stop(self):
        """Stop watching."""
        self.running = False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    watcher = FlowWatcher()
    watcher.start()
