"""
Visions Desktop - Brain / Command Processing
Uses Gemini to understand commands and execute actions.
"""

import os
import json
from datetime import datetime, timezone, timedelta


class VisionsBrain:
    """Process voice commands with Gemini and execute actions."""
    
    def __init__(self):
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel("gemini-2.0-flash")
    
    def process(self, command: str) -> str:
        """Process a voice command and return spoken response."""
        
        # Get current Eastern time
        eastern = timezone(timedelta(hours=-5))
        now = datetime.now(eastern)
        current_time = now.strftime("%I:%M %p on %A, %B %d, %Y")
        
        try:
            # Parse command with Gemini
            parse_prompt = f"""Parse this voice command into JSON actions.

Current time: {current_time} (Eastern)

**LIGHTS (type: "light")**:
- Lights: Eve (Bedroom), Adam (Living Room), Eden (Living Room)
- Actions: on, off, toggle, color, kelvin, breathe, pulse
- Colors: red, blue, green, purple, orange, pink, white, warm white
- Groups: Bedroom, Living Room

**SYSTEM (type: "system")**:
- Actions: mute, unmute, volume_up, volume_down, screenshot, lock, sleep, open_browser, open_terminal, time

Command: "{command}"

Return ONLY a JSON array. Each action has:
- type: "light" or "system"
- For lights: selector, action, color (optional), brightness (optional), kelvin (optional)
- For system: action, value (optional)

If no action needed, return empty array [].
If it's a question or conversation, return: {{"type": "chat", "message": "your response"}}

JSON only:"""

            response = self.model.generate_content(parse_prompt)
            json_text = response.text.strip()
            
            # Clean up response
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            
            actions = json.loads(json_text)
            
            # Handle single chat response
            if isinstance(actions, dict) and actions.get("type") == "chat":
                return actions.get("message", "I'm not sure how to respond.")
            
            # Execute actions
            results = []
            for act in actions:
                result = self._execute_action(act)
                results.append(result)
            
            if results:
                return ". ".join(results)
            else:
                return "I didn't understand that command."
                
        except Exception as e:
            print(f"❌ Brain error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _execute_action(self, action: dict) -> str:
        """Execute a single action."""
        act_type = action.get("type", "")
        
        if act_type == "light":
            return self._execute_light(action)
        elif act_type == "system":
            return self._execute_system(action)
        elif act_type == "chat":
            return action.get("message", "")
        else:
            return "Unknown action type."
    
    def _execute_light(self, action: dict) -> str:
        """Execute a light control action."""
        try:
            from tools.lifx_tools import control_lights
            
            selector = action.get("selector", "all")
            act = action.get("action", "color")
            color = action.get("color")
            brightness = action.get("brightness")
            kelvin = action.get("kelvin")
            
            result = control_lights(act, selector, color, brightness=brightness, kelvin=kelvin)
            return result
        except Exception as e:
            return f"Light control failed: {str(e)}"
    
    def _execute_system(self, action: dict) -> str:
        """Execute a system action."""
        try:
            from tools.system_tools import system_command
            
            act = action.get("action", "")
            value = action.get("value")
            
            result = system_command(act, value)
            return result
        except Exception as e:
            return f"System command failed: {str(e)}"
