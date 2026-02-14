#!/usr/bin/env python3
"""
Vision Tools for Visions AI
Powered entirely by Gemini 3 Pro Image Preview - Google's flagship multimodal model.
"""

from visions.skills.visual import VisionService

# Facade class to maintain backward compatibility if needed, 
# or specific overrides.
class VisionTools(VisionService):
    pass

# Helper Functions
def quick_vqa(image_path: str, question: str, project_id: str = "endless-duality-480201-t3") -> str:
    tools = VisionTools(project_id=project_id)
    return tools.visual_question_answer(image_path, question)

def quick_generate(prompt: str, output_path: str = None, project_id: str = "endless-duality-480201-t3") -> str:
    tools = VisionTools(project_id=project_id)
    return tools.generate_image(prompt, output_path)

if __name__ == "__main__":
    import argparse
    # ... existing main block logic if needed for CLI ...
    # For now, just a placeholder as the skill is the main driver
    print("Use visions.skills.visual for core logic.")
