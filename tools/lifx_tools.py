"""
LIFX Smart Light Control for Visions AI
Voice-controlled smart home integration via LIFX API.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional

# LIFX API Configuration
LIFX_API_URL = "https://api.lifx.com/v1"
LIFX_TOKEN = os.getenv("LIFX_API_TOKEN", "")


class LIFXController:
    """
    Controls LIFX smart lights via their REST API.
    Requires LIFX_API_TOKEN environment variable.
    """
    
    def __init__(self, token: str = None):
        self.token = token or LIFX_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to LIFX API."""
        url = f"{LIFX_API_URL}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            else:
                return {"error": f"Invalid method: {method}"}
            
            if response.status_code == 401:
                return {"error": "Authentication failed. Check LIFX_API_TOKEN."}
            elif response.status_code == 404:
                return {"error": "Light not found"}
            
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Request timed out"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def list_lights(self) -> List[Dict]:
        """Get all LIFX lights on the account."""
        result = self._request("GET", "lights/all")
        if isinstance(result, list):
            return [{"id": l.get("id"), "label": l.get("label"), "power": l.get("power"), 
                     "brightness": l.get("brightness"), "color": l.get("color", {}).get("hue")}
                    for l in result]
        return result
    
    def set_power(self, selector: str = "all", power: str = "on", duration: float = 1.0) -> Dict:
        """
        Turn lights on or off.
        
        Args:
            selector: Light selector (e.g., "all", "label:Living Room", or light ID)
            power: "on" or "off"
            duration: Fade duration in seconds
        """
        data = {"power": power, "duration": duration}
        return self._request("PUT", f"lights/{selector}/state", data)
    
    def set_color(self, selector: str = "all", color: str = "blue", 
                  brightness: float = 1.0, duration: float = 1.0) -> Dict:
        """
        Change light color and brightness.
        
        Args:
            selector: Light selector
            color: Color name ("red", "blue", "green", "warm white", etc.) or hex
            brightness: 0.0 to 1.0
            duration: Fade duration in seconds
        """
        data = {
            "color": color,
            "brightness": brightness,
            "duration": duration
        }
        return self._request("PUT", f"lights/{selector}/state", data)
    
    def toggle(self, selector: str = "all", duration: float = 1.0) -> Dict:
        """Toggle lights on/off."""
        return self._request("POST", f"lights/{selector}/toggle", {"duration": duration})
    
    def breathe(self, selector: str = "all", color: str = "blue", 
                period: float = 2.0, cycles: float = 3.0) -> Dict:
        """Perform breathe effect (pulse)."""
        data = {
            "color": color,
            "period": period,
            "cycles": cycles,
            "from_color": "black"
        }
        return self._request("POST", f"lights/{selector}/effects/breathe", data)
    
    def scene_activate(self, scene_name: str) -> Dict:
        """Activate a saved scene by name."""
        # First, get scenes
        scenes = self._request("GET", "scenes")
        if isinstance(scenes, list):
            for scene in scenes:
                if scene.get("name", "").lower() == scene_name.lower():
                    scene_uuid = scene.get("uuid")
                    return self._request("PUT", f"scenes/scene_id:{scene_uuid}/activate")
        return {"error": f"Scene '{scene_name}' not found"}


# Voice Tool Functions for Visions
def control_lights(action: str, selector: str = "all", color: str = None, 
                   brightness: float = None, kelvin: int = None) -> str:
    """
    Control LIFX smart lights via voice command.
    
    Args:
        action: Action to perform ("on", "off", "toggle", "color", "kelvin", "breathe", "list")
        selector: Which lights ("all", or light name like "Living Room")
        color: Color for color action (e.g., "blue", "red", "warm white")
        brightness: Brightness level 0-100
        kelvin: Color temperature in Kelvin (2500-9000, e.g., 2700 for warm, 5000 for daylight)
        
    Returns:
        Status message for voice response
    """
    controller = LIFXController()
    
    if not controller.token:
        return "LIFX API token not configured. Add LIFX_API_TOKEN to environment."
    
    # Build selector - default to "all" or use label:
    if selector and selector.lower() != "all":
        selector = f"label:{selector}"
    else:
        selector = "all"
    
    action = action.lower()
    
    if action == "on":
        result = controller.set_power(selector, "on")
        return f"Lights turned on." if "error" not in result else f"Error: {result['error']}"
        
    elif action == "off":
        result = controller.set_power(selector, "off")
        return f"Lights turned off." if "error" not in result else f"Error: {result['error']}"
        
    elif action == "toggle":
        result = controller.toggle(selector)
        return f"Lights toggled." if "error" not in result else f"Error: {result['error']}"
        
    elif action == "color" and color:
        bright = (brightness or 100) / 100.0
        result = controller.set_color(selector, color, bright)
        return f"Lights set to {color}." if "error" not in result else f"Error: {result['error']}"
    
    elif action == "kelvin" or (action == "color" and kelvin):
        # Set color temperature in Kelvin
        k = kelvin or 3000
        bright = (brightness or 100) / 100.0
        # LIFX API accepts kelvin as "kelvin:XXXX" in color field
        result = controller.set_color(selector, f"kelvin:{k}", bright)
        return f"Lights set to {k}K color temperature." if "error" not in result else f"Error: {result['error']}"
        
    elif action == "breathe":
        result = controller.breathe(selector, color or "blue")
        return f"Breathing effect activated." if "error" not in result else f"Error: {result['error']}"
        
    elif action == "list":
        lights = controller.list_lights()
        if isinstance(lights, list):
            names = [f"{l['label']} ({l['power']})" for l in lights]
            return f"Found {len(lights)} lights: " + ", ".join(names)
        return f"Error: {lights.get('error', 'Unknown error')}"
    
    else:
        return f"Unknown action: {action}. Use on, off, toggle, color, kelvin, breathe, or list."


# Function declaration for Gemini Live API
LIFX_FUNCTION_DECLARATION = {
    "name": "control_lights",
    "description": "Control LIFX smart lights. Turn on/off, change colors, set color temperature (Kelvin), or create effects. Use when user says 'turn on the lights', 'make the lights blue', 'set lights to 3000K', 'warm up the lights'.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["on", "off", "toggle", "color", "kelvin", "breathe", "list"],
                "description": "Action: on, off, toggle, color (change color), kelvin (set color temperature), breathe (pulse effect), list (show all lights)"
            },
            "selector": {
                "type": "string",
                "description": "Which light(s) to control: 'all' or room name like 'Living Room', 'Bedroom'"
            },
            "color": {
                "type": "string",
                "description": "Color name: blue, red, green, purple, orange, warm white, cool white, etc."
            },
            "brightness": {
                "type": "number",
                "description": "Brightness level 0-100"
            },
            "kelvin": {
                "type": "integer",
                "description": "Color temperature in Kelvin (2500-9000). 2700K=warm/cozy, 3000K=soft white, 4000K=neutral, 5000K=daylight, 6500K=cool daylight"
            }
        },
        "required": ["action"]
    }
}


if __name__ == "__main__":
    # Test
    print("Testing LIFX Controller...")
    controller = LIFXController()
    if controller.token:
        lights = controller.list_lights()
        print(f"Lights: {lights}")
    else:
        print("No LIFX_API_TOKEN set. Add to .env")
