"""
Voice Tools for Gemini Live API
Bridges Live API function calling to existing Visions agent tools.
"""

from typing import Dict, Any, List
import json


class VoiceToolsRegistry:
    """
    Registry of function declarations for Gemini Live API.
    Maps voice commands to agent tool execution.
    """
    
    @staticmethod
    def get_function_declarations() -> List[Dict]:
        """
        Returns function declarations for Gemini Live API.
        These enable voice-triggered tool execution.
        """
        return [
            {
                "name": "search_knowledge_base",
                "description": "Search the Visions knowledge base for photography info, composition theory, Arnheim principles, camera specs, and Doctor Who lore. Use when the user asks about photography techniques, visual theory, or needs expert knowledge.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query - topic or question to look up"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "generate_image",
                "description": "Generate an image based on a text description. Use when the user asks to create, generate, draw, or visualize something. Returns the image which you should describe to the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Detailed description of the image to generate"
                        }
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "recommend_camera",
                "description": "Recommend cameras based on budget and experience. Use when user asks for camera buying advice or gear recommendations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "budget": {
                            "type": "string",
                            "description": "Budget range (e.g. 'under $1000', '$1000-$3000', '$5000+')"
                        },
                        "experience_level": {
                            "type": "string",
                            "enum": ["beginner", "enthusiast", "professional"],
                            "description": "User's photography experience level"
                        },
                        "photography_type": {
                            "type": "string",
                            "description": "Type of photography (landscape, portrait, street, wildlife, etc)"
                        }
                    },
                    "required": ["budget", "experience_level", "photography_type"]
                }
            },
            {
                "name": "analyze_composition",
                "description": "Provide composition guidelines for a subject and style. Use when user asks about framing, composition techniques, or visual arrangement.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "Main subject (portrait, landscape, architecture, street, macro)"
                        },
                        "style": {
                            "type": "string",
                            "description": "Desired style (minimalist, dramatic, documentary, fine_art)"
                        }
                    },
                    "required": ["subject", "style"]
                }
            },
            {
                "name": "recommend_lighting",
                "description": "Recommend lighting setups for photography scenarios. Use when user asks about lighting equipment or how to light a scene.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scenario": {
                            "type": "string",
                            "description": "Photography scenario (portrait, product, headshot, studio, outdoor)"
                        },
                        "budget": {
                            "type": "string",
                            "enum": ["budget", "moderate", "professional"],
                            "description": "Budget level for equipment"
                        }
                    },
                    "required": ["scenario"]
                }
            },
            {
                "name": "control_lights",
                "description": "Control LIFX smart lights. Turn on/off, change colors, set color temperature (Kelvin). Use when user says 'turn on the lights', 'make the lights blue', 'set lights to 3000K', 'warm up the lights'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["on", "off", "toggle", "color", "kelvin", "breathe", "list"],
                            "description": "Action: on, off, toggle, color, kelvin (set color temperature), breathe (pulse), or list"
                        },
                        "selector": {
                            "type": "string",
                            "description": "Which lights: 'all' or room name like 'Living Room'"
                        },
                        "color": {
                            "type": "string",
                            "description": "Color: blue, red, green, purple, warm white, etc."
                        },
                        "brightness": {
                            "type": "number",
                            "description": "Brightness 0-100"
                        },
                        "kelvin": {
                            "type": "integer",
                            "description": "Color temperature in Kelvin (2500-9000). 2700K=warm, 3000K=soft, 4000K=neutral, 5000K=daylight"
                        }
                    },
                    "required": ["action"]
                }
            }
        ]


class VoiceToolExecutor:
    """
    Executes tool calls received from Gemini Live API.
    Bridges to actual agent tool implementations.
    """
    
    def __init__(self):
        # Lazy-load tools to avoid import overhead
        self._retriever = None
        self._imager = None
        self._camera_advisor = None
        self._lighting_advisor = None
        self._composition_advisor = None
    
    def _get_retriever(self):
        if self._retriever is None:
            from agent import KnowledgeRetriever
            self._retriever = KnowledgeRetriever(project_id="endless-duality-480201-t3")
        return self._retriever
    
    def _get_imager(self):
        if self._imager is None:
            from agent import ImageGenerator
            self._imager = ImageGenerator()
        return self._imager
    
    def _get_camera_advisor(self):
        if self._camera_advisor is None:
            from agent import CameraAdvisor
            self._camera_advisor = CameraAdvisor()
        return self._camera_advisor
    
    def _get_lighting_advisor(self):
        if self._lighting_advisor is None:
            from agent import LightingAdvisor
            self._lighting_advisor = LightingAdvisor()
        return self._lighting_advisor
    
    def _get_composition_advisor(self):
        if self._composition_advisor is None:
            from agent import CompositionAdvisor
            self._composition_advisor = CompositionAdvisor()
        return self._composition_advisor
    
    def execute(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a function call and return the result.
        
        Args:
            function_name: Name of the function to execute
            args: Arguments dictionary
            
        Returns:
            Result dictionary to send back to Live API
        """
        print(f"🛠️ Executing voice tool: {function_name}")
        print(f"   Args: {json.dumps(args, indent=2)}")
        
        try:
            if function_name == "search_knowledge_base":
                result = self._get_retriever().search(args.get("query", ""))
                # Return simple string for Live API
                return f"Knowledge found: {result[:1500]}" if len(str(result)) > 1500 else f"Knowledge found: {result}"
            
            elif function_name == "generate_image":
                result = self._get_imager().generate_image(args.get("prompt", ""))
                if result.startswith("IMAGE_GENERATED:"):
                    return "Image generated successfully. Describe what you created to the user."
                else:
                    return f"Image generation failed: {result}"
            
            elif function_name == "recommend_camera":
                result = self._get_camera_advisor().recommend_camera(
                    budget=args.get("budget", "$1000-$3000"),
                    experience_level=args.get("experience_level", "enthusiast"),
                    photography_type=args.get("photography_type", "general")
                )
                return f"Camera recommendation: {result}"
            
            elif function_name == "analyze_composition":
                result = self._get_composition_advisor().analyze_composition(
                    subject=args.get("subject", "general"),
                    style=args.get("style", "natural")
                )
                return f"Composition advice: {result}"
            
            elif function_name == "recommend_lighting":
                result = self._get_lighting_advisor().recommend_lighting_setup(
                    scenario=args.get("scenario", "portrait"),
                    budget=args.get("budget", "moderate")
                )
                return f"Lighting recommendation: {result}"
            
            elif function_name == "control_lights":
                # LIFX Smart Home Control
                from tools.lifx_tools import control_lights
                result = control_lights(
                    action=args.get("action", "list"),
                    selector=args.get("selector", "all"),
                    color=args.get("color"),
                    brightness=args.get("brightness"),
                    kelvin=args.get("kelvin")
                )
                # Clear completion message to prevent model loops
                return f"DONE. {result}"
            
            else:
                return f"Unknown function: {function_name}"
                
        except Exception as e:
            print(f"❌ Tool execution error: {e}")
            return f"Error: {str(e)}"


# Singleton instance
_executor = None

def get_executor() -> VoiceToolExecutor:
    """Get the singleton voice tool executor."""
    global _executor
    if _executor is None:
        _executor = VoiceToolExecutor()
    return _executor


def get_function_declarations() -> List[Dict]:
    """Get function declarations for Live API setup."""
    return VoiceToolsRegistry.get_function_declarations()
