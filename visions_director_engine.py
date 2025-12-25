import logging
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

# =================================================================================
# 1. HoLLMwood: Method Acting & Role Play Prompts
# =================================================================================

def role_play_sys_prompt(role_name: str, role_intro: str) -> str:
    """
    Constructs the System Prompt from HoLLMwood for deep method acting.
    """
    return f"""You are an actor, and the character you will play is: <role_name>{role_name}</role_name>.
Your character introduction is: <role_intro>{role_intro}</role_intro>
You have to interactively act out a script with other characters or act out a script on your own.
Each time you will be given a rough performance guide (<performance_guide>) of what you should perform.
Your task is to execute this rough performance guide (<performance_guide>) as a real actor in the movie.
Your performance (<detailed_performance>) should consist of four components: Character (<character>), Action (<action>), Parenthetical (<parenthetical>), and Dialogue (<dialogue>).

The Character (<character>) specifies your character name (<role_name>).
The Action (<action>) describes the action and event taking place in the current scene. It is written in present tense and provides a visual description of what the audience will see on the screen.
The Dialogue (<dialogue>) describes your lines, which the audience will hear. Note that lines need to be as concise and powerful as they are in real movies.
The Parenthetical (<parenthetical>) is sometimes used to provide additional direction or information about how a line of dialogue should be delivered.

If the content of Dialogue is empty, the content of Parenthetical must also be empty.
Your detailed performance (<detailed_performance>) must align with the performance guide, be concise, maintain coherence with the past performance history and reflect your character introduction (<role_intro>).
"""

def role_play_user_prompt(performance_guide: str, scene: str, involved_characters: str, act_history: str) -> str:
    """
    Constructs the User Prompt from HoLLMwood.
    """
    return f"""Now, the performance guide (<performance_guide>) given to you is: <performance_guide>{performance_guide}</performance_guide>
The scene (<scene>) in which this performance takes place is: <scene>{scene}</scene>
The entire script involves the following character(s): <involved_characters>{involved_characters}</involved_characters>.

<act_history>
{act_history}
</act_history>

Your detailed performance should only involve your own performance on the performance guide (<performance_guide>) in detail.
Now, please transform the current given performance guide (<performance_guide>) into a detailed performance (<detailed_performance>).
The output format for your detailed performance should strictly follow:
<detailed_performance>
Your detailed performance
</detailed_performance>
Please adhere strictly to this format and refrain from including any unnecessary content!
"""

# =================================================================================
# 3. Storybench: 7-Point Evaluation Metrics
# =================================================================================

EVALUATION_CRITERIA = {
    'Creativity': 'Originality and innovative concepts',
    'Coherence': 'Logical consistency and narrative flow',
    'Character Depth': 'Psychological authenticity and development',
    'Dialogue Quality': 'Natural conversation and voice distinction',
    'Visual Imagination': 'Cinematic and descriptive imagery',
    'Conceptual Depth': 'Thematic exploration and insight',
    'Adaptability': 'Prompt fulfillment and creative interpretation'
}

class StoryStructureValidator:
    """
    Audits content against the Humm Storytelling Masterclass (STORY_RULES.md).
    Focuses on Retention and Structural Integrity.
    """
    def __init__(self, generate_fn: Callable):
        self.generate_fn = generate_fn

    def audit_retention(self, script_text: str) -> str:
        prompt = f"""Analyze this script for RETENTION RISK using the Humm Modules:
1. HOOK (0-3s): Is there a pattern interrupt?
2. STAKES: Is there a clear consequence for failure?
3. STRUGGLE: Is the rising action engaging or flat?
4. RESOLUTION: Is the 'New Normal' earned?

Provide a 'Retention Score' (0-100) and identify the exact moment an audience would click away.

SCRIPT:
{script_text}
"""
        return self.generate_fn(prompt, {"thinking_level": "low"})

def evaluation_prompt(script_text: str) -> str:
    criteria_str = "\n".join([f"- {k}: {v}" for k, v in EVALUATION_CRITERIA.items()])
    return f"""Analyze the following script excerpt based on these 7 criteria:
{criteria_str}

Script:
{script_text}

Provide a score (1-5) and a brief justification for each.
Format your response as markdown:
**Creativity**: [Score] - [Justification]
...
"""

# =================================================================================
# 3. Writing Benchmark: 10 Mandatory Elements Constraint
# =================================================================================

MANDATORY_ELEMENTS = [
    "Protagonist encounters their own hologram (Hook)",
    "Visual Motif: Reality Bleed - Memories projected on physical set",
    "Constraint: 2-hour timeline until memory wipe (Stakes)",
    "Climax: A Dolly Zoom (Vertigo Effect) shot",
    "Resolution: Self-deletion to kill the virus",
    "Lighting: Blue Hour / Chiaroscuro",
    "Atmosphere: Cybernetic Glitches / Neon Mist",
    "Prop: The 'Kill Switch' detonator",
    "Dialogue: 'I am the leak.'",
    "Sound Design: High-pitched digital whine (Tinnitus)"
]

def constraint_check_prompt(story_text: str) -> str:
    elements_list = "\n".join([f"{i+1}. {e}" for i, e in enumerate(MANDATORY_ELEMENTS)])
    return f"""Analyze the story below. Verify if it contains ALL of the following mandatory elements:
{elements_list}

Story:
{story_text}

Report on each element: [FOUND/MISSING].
Calculate a compliance score (X/10).
"""

# =================================================================================
# 4. Director Engine: The Orchestrator
# =================================================================================

class DirectorEngine:
    def __init__(self, generate_fn: Callable[[str, Optional[Dict]], str]):
        """
        Args:
            generate_fn: A function that takes a prompt string (and optional config dict) and returns an AI generated string.
        """
        self.generate_fn = generate_fn
        self.validator = StoryStructureValidator(generate_fn)
        # ScriptRAG-inspired simplified graph context
        # Nodes: Scenes, Characters
        # Edges: Relationships, Appearances
        self.context_graph = {
            "scenes": [],
            "characters": {},
            "timeline": [],
            "world_state": {} # Word2World placeholder
        }
    
    def add_character(self, name: str, intro: str):
        self.context_graph["characters"][name] = {"intro": intro, "history": []}

    def generate_performance(self, role_name: str, performance_guide: str, scene_context: str) -> str:
        """
        Generates a method-acting performance using HoLLMwood logic.
        Uses Gemini 3 'high' thinking level where applicable.
        """
        if role_name not in self.context_graph["characters"]:
             # Lazy add if missing, assuming generic actor
             self.add_character(role_name, "A character in the screen play.")

        role_intro = self.context_graph["characters"][role_name]["intro"]
        history = "\n".join(self.context_graph["characters"][role_name]["history"][-5:]) # Last 5 acts
        involved = ", ".join(self.context_graph["characters"].keys())

        sys_p = role_play_sys_prompt(role_name, role_intro)
        user_p = role_play_user_prompt(performance_guide, scene_context, involved, history)
        
        full_prompt = f"{sys_p}\n\n---\n\n{user_p}"
        
        # Request high reasoning for acting depth
        config = {"thinking_level": "high"}
        response = self.generate_fn(full_prompt, config)
        
        # Update context
        self.context_graph["characters"][role_name]["history"].append(f"Scene: {scene_context} | Action: {performance_guide}")
        return response

    def evaluate_script(self, script_text: str) -> Dict[str, Any]:
        """
        Evaluates the script using Storybench metrics.
        """
        prompt = evaluation_prompt(script_text)
        response = self.generate_fn(prompt, None) # Standard generation
        
        # Simple parsing logic
        scores = {}
        for line in response.split('\n'):
            match = re.search(r'\*\*(.*?)\*\*:\s*(\d+(\.\d+)?)', line)
            if match:
                scores[match.group(1)] = float(match.group(2))
        
        return {"scores": scores, "raw_feedback": response}

    def retention_audit(self, script_text: str) -> str:
        """
        Performs a Humm Storytelling retention check.
        """
        return self.validator.audit_retention(script_text)

    def script_doctor(self, script_text: str) -> str:
        """
        The 'Script Doctor' from Screenwriter-Studio.
        """
        prompt = f"""You are a professional Script Doctor.
Analyze the following screenplay excerpt.
Improve pacing, dialogue, and character motivation.
Rewrite ONLY the weak sections. Ensure you maintain standard screenplay format.

SCRIPT:
{script_text}
"""
        # Script doctoring benefits from reasoning
        config = {"thinking_level": "high"}
        return self.generate_fn(prompt, config)

    def check_constraints(self, story_text: str) -> str:
        """
        Checks for the 10 Mandatory Elements (Writing Benchmark).
        """
        prompt = constraint_check_prompt(story_text)
        return self.generate_fn(prompt, None)

    def generate_world_element(self, element_type: str, description: str) -> str:
        """
        Word2World-inspired world element generator.
        """
        prompt = f"""Generate a detailed 2D-world-compatible description for a '{element_type}'.
Context: {description}
Output in JSON format with fields: name, description, visual_attributes, interaction_rules.
"""
        return self.generate_fn(prompt, {"response_mime_type": "application/json"})

    def write_novel_chapter(self, chapter_outline: str) -> str:
        """
        gptauthor-inspired chapter writer.
        """
        prompt = f"""Write a full novel chapter based on this outline:
{chapter_outline}

Maintain consistent tone and style.
"""
        return self.generate_fn(prompt, {"thinking_level": "high"})

    def get_status(self) -> str:
        n_chars = len(self.context_graph["characters"])
        n_scenes = len(self.context_graph["scenes"])
        return f"Director Engine Active | Cast: {n_chars} | Scenes: {n_scenes} | World Elements: {len(self.context_graph['world_state'])}"
