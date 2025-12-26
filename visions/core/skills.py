
import os
import yaml
import glob
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class SkillMetadata:
    name: str
    description: str
    usage_trigger: str
    path: str
    programs: List[str] = None 

    def __post_init__(self):
        if self.programs is None:
            self.programs = []

class SkillRegistry:
    """
    Manages the discovery and loading of Visions Skills.
    Implements Progressive Disclosure:
    - Level 1: Metadata (System Prompt)
    - Level 2: Instructions (On-Demand Activation)
    - Level 3: Execution (Script capabilities)
    """

    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            # Default to visions/skills relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.skills_dir = os.path.join(base_dir, "skills")
        else:
            self.skills_dir = skills_dir
        
        self.skills: Dict[str, SkillMetadata] = {}
        self._scan_skills()

    def _scan_skills(self):
        """Scans the skills directory for valid SKILL.md files and programs."""
        self.skills = {}
        # Look for vision/skills/*/SKILL.md
        pattern = os.path.join(self.skills_dir, "*", "SKILL.md")
        skill_files = glob.glob(pattern)

        print(f"🔍 SkillRegistry: Scanning {self.skills_dir}...")
        
        for file_path in skill_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse Frontmatter (simple implementation)
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter_raw = parts[1]
                        meta = yaml.safe_load(frontmatter_raw)
                        
                        if meta and 'name' in meta and 'description' in meta:
                            # Check for programs directory
                            skill_dir = os.path.dirname(file_path)
                            programs_dir = os.path.join(skill_dir, "programs")
                            programs = []
                            if os.path.exists(programs_dir) and os.path.isdir(programs_dir):
                                # Find .py files
                                py_files = glob.glob(os.path.join(programs_dir, "*.py"))
                                programs = [os.path.basename(p) for p in py_files]

                            skill = SkillMetadata(
                                name=meta['name'],
                                description=meta['description'],
                                usage_trigger=meta.get('usage_trigger', ''),
                                path=file_path,
                                programs=programs
                            )
                            self.skills[skill.name] = skill
                            prog_msg = f" (Programs: {programs})" if programs else ""
                            print(f"   ✅ Loaded Skill: {skill.name}{prog_msg}")
                        else:
                            print(f"   ⚠️ Invalid frontmatter in {file_path}")
            except Exception as e:
                print(f"   ❌ Error loading skill from {file_path}: {e}")

        print(f"   Total Skills Loaded: {len(self.skills)}")

    def get_system_prompt_snippet(self) -> str:
        """Generates the 'Available Skills' section for the System Prompt."""
        if not self.skills:
            return ""

        snippet = "\n\n# 🛠️ AVAILABLE AGENT SKILLS\n"
        snippet += "You have access to the following domain-specific skills. "
        snippet += "Use the `activate_skill` tool to load their full instructions when needed.\n\n"
        
        for name, skill in self.skills.items():
            snippet += f"- **{name}**: {skill.description}\n"
            if skill.usage_trigger:
                snippet += f"  - *Trigger*: {skill.usage_trigger}\n"
        
        return snippet

    def get_skill_content(self, skill_name: str) -> str:
        """Reads the full content of a skill's SKILL.md and appends program info."""
        if skill_name not in self.skills:
            return f"Error: Skill '{skill_name}' not found."
        
        try:
            skill = self.skills[skill_name]
            with open(skill.path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Append Level 3 Info
            if skill.programs:
                content += "\n\n# 💻 LEVEL 3: EXECUTABLE PROGRAMS\n"
                content += "The following executable programs are available for this skill. "
                content += "Use the `run_skill_program` tool to execute them.\n\n"
                for prog in skill.programs:
                    content += f"- `{prog}`\n"
            
            return content
        except Exception as e:
            return f"Error reading skill file: {e}"

    def list_skills(self) -> List[str]:
        return list(self.skills.keys())
    
    def get_program_path(self, skill_name: str, program_name: str) -> Optional[str]:
        """Resolves the absolute path to a skill program."""
        if skill_name not in self.skills:
            return None
        
        skill = self.skills[skill_name]
        if program_name in skill.programs:
             skill_dir = os.path.dirname(skill.path)
             return os.path.join(skill_dir, "programs", program_name)
        return None
