import asyncio
import concurrent.futures
import json
import os
import time
from typing import List, Dict, Any, Tuple
from visions_assistant.agent import get_chat_response
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live

console = Console()

class EchoOrchestrator:
    """
    Echo: The Parallel Directing Orchestrator.
    Runs Dual-Track inference: Creative (Visions) + Adversarial/Structural (Echo).
    """
    def __init__(self):
        self.history = []
    
    async def run_parallel_query(self, user_message: str) -> Tuple[str, str]:
        """
        Runs two Gemini 3 Pro synthesis tracks in parallel.
        """
        loop = asyncio.get_running_loop()
        
        # Track A: The Creative Vision (Ghost)
        prompt_a = user_message
        
        # Track B: The Echo Critique (Storytelling Architect)
        # We inject the STORY_RULES.md logic directly into the adversarial prompt
        prompt_b = f"""You are ECHO, the Structural Adversary. 
Your goal is to tear apart the following user intent based on the 'Humm Storytelling Rules':

1. HOOK: Is there a pattern interrupt in the first 3s?
2. STAKES: What is lost if the character/narrative fails?
3. STRUGGLE: Is the conflict too easy or clichéd?
4. RETENTION: Where will the audience click away?

Analyze the intent and provide a sharp, technical critique. Do not be polite. Point out the 'Sh*tty Retention' risks.

USER INTENT: {user_message}

ECHO STRUCTURAL CRITIQUE:"""

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # We use get_chat_response which handles the full agent.py cascade
            future_a = loop.run_in_executor(executor, get_chat_response, prompt_a)
            future_b = loop.run_in_executor(executor, get_chat_response, prompt_b)
            
            # Wait for both
            results = await asyncio.gather(future_a, future_b)
            return results[0], results[1]

    def make_layout() -> Layout:
    layout = Layout()
    layout.split_row(
        Layout(name="ghost", ratio=1),
        Layout(name="echo", ratio=1)
    )
    return layout

async def main():
    orchestrator = EchoOrchestrator()
    console.print("[bold purple]GHOST // ECHO PROTOCOL ACTIVE[/bold purple]")
    console.print("[dim]Ghost (The Creative Source) | Echo (The Structural Reflection)[/dim]\n")
    
    while True:
        try:
            query = console.input("[bold cyan]Command > [/bold cyan]")
            if query.lower() in ["exit", "quit"]:
                break
            
            with console.status("[bold magenta]Syncing Ghost & Echo...[/bold magenta]"):
                ghost_out, echo_out = await orchestrator.run_parallel_query(query)
            
            # Display results in panels
            layout = make_layout()
            layout["ghost"].update(Panel(ghost_out, title="[bold green]GHOST (Vision)[/bold green]", border_style="green"))
            layout["echo"].update(Panel(echo_out, title="[bold yellow]ECHO (Reflection)[/bold yellow]", border_style="yellow"))
            
            console.print(layout)
            console.print("\n" + "─"*80 + "\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(main())
