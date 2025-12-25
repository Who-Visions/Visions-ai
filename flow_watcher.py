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
        
        # Initialize Gemini - try multiple API key env vars
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
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
        """Process a Visions command using Gemini for intelligent parsing."""
        print(f"🧠 Processing command: {command}")
        
        # Get current Eastern time (UTC-5)
        from datetime import datetime, timezone, timedelta
        eastern = timezone(timedelta(hours=-5))
        now = datetime.now(eastern)
        current_time = now.strftime("%I:%M %p on %A, %B %d, %Y")
        
        try:
            # Use Gemini to parse complex commands into structured actions
            parse_prompt = f"""Parse this smart home voice command into JSON actions.

Current time: {current_time} (Eastern)

Available lights: Eve (Bedroom), Adam (Living Room), Eden (Living Room)
Available actions: on, off, toggle, color, kelvin, breathe, pulse
Available colors: red, blue, green, purple, orange, pink, white, warm white
Kelvin range: 1500-9000 (1500=candle, 2700=warm, 5000=daylight)
Brightness: 0-100

Command: "{command}"

Return ONLY a JSON array of actions. Each action has:
- selector: "all", "Eve", "Adam", "Eden", "Bedroom", or "Living Room"
- action: "on", "off", "toggle", "color", "kelvin", "breathe", "pulse"
- color: color name (optional)
- brightness: 0-100 (optional)
- kelvin: 1500-9000 (optional)
- delay_seconds: seconds to wait before executing (optional, for "in X minutes/seconds")

Examples:
"turn lights purple at 50%" -> [{{"selector": "all", "action": "color", "color": "purple", "brightness": 50}}]
"make Eden red and Adam blue" -> [{{"selector": "Eden", "action": "color", "color": "red"}}, {{"selector": "Adam", "action": "color", "color": "blue"}}]
"turn off the lights in 5 minutes" -> [{{"selector": "all", "action": "off", "delay_seconds": 300}}]
"set Eve to blue in 30 seconds" -> [{{"selector": "Eve", "action": "color", "color": "blue", "delay_seconds": 30}}]

JSON only, no explanation:"""

            response = self.model.generate_content(parse_prompt)
            json_text = response.text.strip()
            
            # Clean up response - extract JSON
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            
            import json
            actions = json.loads(json_text)
            
            print(f"📋 Parsed {len(actions)} action(s)")
            
            # Execute each action
            from tools.lifx_tools import control_lights
            import threading
            results = []
            
            def execute_action(act):
                selector = act.get("selector", "all")
                action = act.get("action", "color")
                color = act.get("color")
                brightness = act.get("brightness")
                kelvin = act.get("kelvin")
                result = control_lights(action, selector, color, brightness=brightness, kelvin=kelvin)
                print(f"⏰ Timer fired: {action} {selector} → {result}")
            
            for act in actions:
                selector = act.get("selector", "all")
                action = act.get("action", "color")
                color = act.get("color")
                brightness = act.get("brightness")
                kelvin = act.get("kelvin")
                delay = act.get("delay_seconds", 0)
                
                if delay and delay > 0:
                    print(f"⏳ Scheduling: {action} {selector} in {delay}s")
                    timer = threading.Timer(delay, execute_action, args=[act])
                    timer.start()
                    results.append(f"{selector}: scheduled in {delay}s")
                else:
                    print(f"⚡ {action} {selector}: color={color}, brightness={brightness}, kelvin={kelvin}")
                    result = control_lights(action, selector, color, brightness=brightness, kelvin=kelvin)
                    results.append(f"{selector}: {result}")
            
            final = " | ".join(results)
            print(f"✅ {final}")
            return final
            
        except Exception as e:
            print(f"❌ Error: {e}")
            # Fallback to simple parsing
            return await self._simple_command(command)
    
    async def _simple_command(self, command: str) -> str:
        """Fallback simple command parsing."""
        cmd_lower = command.lower()
        from tools.lifx_tools import control_lights
        
        if "off" in cmd_lower:
            return control_lights("off", "all")
        elif "on" in cmd_lower:
            return control_lights("on", "all")
        else:
            return "Command not understood"
    
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
