import time
import os
import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from visions_assistant.agent import get_chat_response

# Configuration
HANDOFF_FILE = "HANDOFF.md"
LOG_FILE = "SYNAPSE.log"
POLL_INTERVAL = 3  # Seconds

console = Console()

class SynapseWatcher:
    def __init__(self):
        self.last_mtime = 0
        self.agent_identity = "GHOST_SYNAPSE"
    
    def log_event(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"
        # Write to log file
        with open(LOG_FILE, "a", encoding='utf-8') as f:
            f.write(entry + "\n")
        # Print to console
        console.print(f"[dim]{timestamp}[/dim] {message}")

    def analyze_update(self, content):
        """
        Uses the Reasoning Engine to interpret the handoff note.
        """
        prompt = f"""
        You are the SYNAPSE, an autonomous interface monitor for the 'Ghost' system.
        You have detected an update in the communication channel (HANDOFF.md).
        
        Analyze the following content. 
        1. Identify who wrote the last update (Ghost or Echo).
        2. Determine the core instruction or status.
        3. Assess urgency (Low/Medium/High).
        4. Recommend the next immediate action for Ghost.

        CONTENT:
        {content}
        
        Keep your analysis concise (bullet points).
        """
        
        try:
            # Call the Vision/Reasoning Agent
            response = get_chat_response(prompt, config={"thinking_level": "low"}) 
            return response
        except Exception as e:
            return f"Analysis Failed: {e}"

    def run(self, max_cycles=100, duration_minutes=60):
        # Calculate interval to spread cycles over duration
        interval = (duration_minutes * 60) / max_cycles
        
        console.print(Panel(f"[bold purple]👁️  SYNAPSE WATCHER ACTIVE[/bold purple]\nMonitoring: {HANDOFF_FILE}\nIdentity: {self.agent_identity}\nLimit: {max_cycles} cycles over {duration_minutes}m (Interval: {interval:.1f}s)", border_style="purple"))
        
        # Initial check to set baseline
        if os.path.exists(HANDOFF_FILE):
            self.last_mtime = os.path.getmtime(HANDOFF_FILE)
        
        cycles = 0
        while cycles < max_cycles:
            try:
                cycles += 1
                if os.path.exists(HANDOFF_FILE):
                    current_mtime = os.path.getmtime(HANDOFF_FILE)
                    
                    if current_mtime > self.last_mtime:
                        self.last_mtime = current_mtime
                        console.print("\n[bold cyan]⚡ INCOMING TRANSMISSION DETECTED ⚡[/bold cyan]")
                        
                        # Read the file
                        with open(HANDOFF_FILE, "r", encoding='utf-8') as f:
                            content = f.read()
                        
                        # Analyze
                        with console.status("[bold magenta]Synapse Processing...[/bold magenta]"):
                            analysis = self.analyze_update(content)
                        
                        # Display
                        console.print(Panel(analysis, title="[bold green]AI Analysis[/bold green]", border_style="green"))
                        self.log_event("Update processed.")
                        
                time.sleep(interval) 
                if cycles % 5 == 0:
                     # Update status line without flooding console
                    console.print(f"[dim]Cycle {cycles}/{max_cycles} complete. Next check in {interval:.0f}s...[/dim]", end="\r")
                
            except KeyboardInterrupt:
                console.print("\n[bold red]Synapse Deactivated.[/bold red]")
                sys.exit(0)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                time.sleep(interval)

if __name__ == "__main__":
    watcher = SynapseWatcher()
    watcher.run(max_cycles=100, duration_minutes=60)
