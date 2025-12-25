"""
Cinema Tools - Agent-facing wrapper for Visions Cinema
"""
import os
from pathlib import Path
# DON'T import VisionsCinema at module level - causes pickling issues
# from visions_cinema import VisionsCinema

class CinemaTools:
    """
    Agent-accessible tools for cinematic character and video generation.
    """
    def __init__(self):
        self._cinema = None
    
    @property
    def cinema(self):
        if self._cinema is None:
            # Lazy import to avoid pickling issues during deployment
            from visions.modules.cinema.visions_cinema import VisionsCinema
            self._cinema = VisionsCinema()
        return self._cinema
    
    def create_character(self, description: str, name: str = "Character") -> str:
        """
        Generate a base character image using Gemini 3 Pro Image.
        
        Args:
            description: Description of the character (e.g., "cyberpunk detective with neon hair")
            name: Name to save the character as
            
        Returns:
            Path to the generated character image
        """
        try:
            filepath = self.cinema.generate_character_base(description, name)
            return f"✅ Character created: {filepath}"
        except Exception as e:
            return f"Error creating character: {str(e)}"
    
    def generate_cinematic_shot(self, character_path: str, shot_type: str, scene_description: str, character_description: str) -> str:
        """
        Generate a cinematic shot of a character with camera angle control.
        
        Args:
            character_path: Path to the base character image
            shot_type: Type of shot (e.g., "Close Up", "Wide Shot", "Over Shoulder")
            scene_description: What's happening in the scene
            character_description: Description to maintain consistency
            
        Returns:
            Path to the generated shot
        """
        try:
            filepath = self.cinema.generate_shot(character_path, shot_type, scene_description, character_description)
            if filepath:
                return f"✅ Shot generated: {filepath}"
            else:
                return "Failed to generate shot"
        except Exception as e:
            return f"Error generating shot: {str(e)}"
    
    def animate_image(self, image_path: str, motion_description: str) -> str:
        """
        Animate a static image using Veo 3.1.
        
        Args:
            image_path: Path to the image to animate
            motion_description: Description of the motion/action
            
        Returns:
            Path to the generated video
        """
        try:
            video_path = self.cinema.animate_shot(image_path, motion_description)
            if video_path:
                return f"🎬 Video generated: {video_path}"
            else:
                return "Failed to generate video"
        except Exception as e:
            return f"Error animating image: {str(e)}"
