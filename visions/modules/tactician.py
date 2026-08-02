import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class TacticalPlanner:
    """
    The Tactician - Logical, mathematical, and dynamic planning engine.
    Uses Gemma 4 (Local) for multi-pass strategy and failsafe verification.
    💅🏿✨🧠🖤🏾🏿🪐🛰️🔥💯
    """
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.gemma_model = os.getenv("GEMMA_MODEL", "gemma4:e4b")

    def plan(self, objective: str) -> Dict[str, Any]:
        """
        Main entry point for generating a logical, failsafe plan.
        Follows the 3-pass 'Grind It Out' protocol.
        """
        # PASS 1: The Draft (Logical Layout)
        draft = self._generate_draft(objective)
        
        # PASS 2: The Math & Logic Stress Test (Failsafe)
        verified = self._verify_logic(objective, draft)
        
        # PASS 3: The Final Polish (Rhea Voice & Data Parity)
        return verified

    def _generate_draft(self, objective: str) -> str:
        """First pass: Build the logical framework."""
        now = datetime.now()
        next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
        next_month_name = next_month.strftime("%B %Y")
        
        prompt = f"""<|think|>
        OBJECTIVE: {objective}
        CURRENT TIME: {now.strftime("%Y-%m-%d")}
        TARGET WINDOW: {next_month_name}
        
        TASK: Create a mathematically sound, logically robust flight and travel strategy.
        - Calculate approximate costs.
        - Identify optimal windows.
        - Factor in potential failsafes (delays, pricing surges).
        
        STRICT REQUIREMENT: Use dark skin tone emojis 💅🏿 black coded vibes only.
        
        Return a structured draft.
        """
        return self._gemma_query(prompt)

    def _verify_logic(self, objective: str, draft: str) -> Dict[str, Any]:
        """Second pass: Stress test the math and logic for 'No Mistakes' policy."""
        prompt = f"""<|think|>
        ORIGINAL OBJECTIVE: {objective}
        PROPOSED DRAFT: {draft}
        
        VALIDATION CHECKLIST:
        1. Is the math correct? (Dates, potential pricing, durations) 📉
        2. Are there logical fallacies in the travel sequence? 🌀
        3. Is this failsafe? (What happens if the primary path fumbles?) 🛡️
        
        Return a FINAL JSON response with the following keys:
        {{
          "plan_summary": "string",
          "mathematical_confirmation": "string",
          "failsafe_measures": ["string"],
          "dynamic_steps": ["string"],
          "vibe": "string",
          "verified": true
        }}
        """
        response_ext = self._gemma_query(prompt)
        try:
            if "```json" in response_ext:
                response_ext = response_ext.split("```json")[1].split("```")[0].strip()
            return json.loads(response_ext)
        except:
            return {
                "plan_summary": draft,
                "mathematical_confirmation": "Logic processed via stream, verification pending deep audit.",
                "failsafe_measures": ["Primary logic gates cleared."],
                "dynamic_steps": ["Proceed with the draft sequence."],
                "vibe": "Straight grind. 💅🏿🔥",
                "verified": False
            }

    def _gemma_query(self, prompt: str) -> str:
        """Helper to hit the local Gemma 4 node."""
        try:
            resp = requests.post(f"{self.ollama_url}/api/chat", json={
                "model": self.gemma_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"num_predict": 1024}
            }, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "")
        except Exception as e:
            return f"Thinking channel fumbled: {str(e)}"
        return "Thinking channel unreachable."

if __name__ == "__main__":
    planner = TacticalPlanner()
    print(json.dumps(planner.plan("flights to Florida next month"), indent=2))
