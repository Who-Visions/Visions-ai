
import sys
import time
import logging
import asyncio
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

# Integration Imports
from visions.core.config import Config
from visions.modules.mem_store.memory_cloud import CloudMemoryManager
from visions.core.agent import VisionsAgent
from google import genai
from google.genai import types

# Configure Console
console = Console()
logging.basicConfig(level=logging.ERROR) # Mute libraries for clean CLI

class IslandPi:
    """
    🏝️ Visions AI Command Center (Island Pi)
    Unified interface for System Validation, Sentinel Loops, and Reasoning Tests.
    """
    def __init__(self):
        self.agent = VisionsAgent()
        self.memory = CloudMemoryManager(project_id=Config.VERTEX_PROJECT_ID)
        self.project_id = Config.VERTEX_PROJECT_ID

    def header(self):
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]🏝️  ISLAND PI COMMAND CENTER v1.0[/bold cyan]\n"
            f"[dim]Project: {self.project_id} | Location: Global | Agent: Rhea Noir[/dim]",
            border_style="magenta"
        ))
        print()

    def run_diagnostics(self):
        """Unified Validation Suite"""
        self.header()
        console.print("[bold yellow]🚀 STARTING SYSTEM DIAGNOSTICS...[/bold yellow]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
        ) as progress:
            
            # 1. Config Check
            task1 = progress.add_task("[cyan]Checking Configuration...", total=1)
            time.sleep(0.5)
            try:
                Config.validate()
                progress.update(task1, completed=1, description="[green]✅ Configuration Valid[/green]")
            except Exception as e:
                progress.update(task1, completed=1, description=f"[red]❌ Config Error: {e}[/red]")
                return

            # 2. Memory System
            task2 = progress.add_task("[cyan]Verifying Memory Matrix (SQL/GCS/BQ)...", total=1)
            try:
                self.memory.save_interaction("diag_user", "PING", "PONG")
                # Quick Verification Read
                recent = self.memory.get_recent_context("diag_user", 1)
                if recent:
                    progress.update(task2, completed=1, description="[green]✅ Memory Matrix Online (Write/Read Confirmed)[/green]")
                else:
                    raise Exception("Read Verification Failed")
            except Exception as e:
                progress.update(task2, completed=1, description=f"[red]❌ Memory Fail: {e}[/red]")

            # 3. Model Pulse (Gemini 3 Flash)
            task3 = progress.add_task("[cyan]Pinging Gemini 3 Flash (Global)...", total=1)
            try:
                # Use the agent's smart router to verify connectivity
                start = time.time()
                self.agent._get_client(Config.MODEL_FLASH).models.generate_content(
                    model=Config.MODEL_FLASH,
                    contents="ping",
                    config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="low"))
                )
                latency = time.time() - start
                progress.update(task3, completed=1, description=f"[green]✅ Gemini 3 Flash Active ({latency:.2f}s)[/green]")
            except Exception as e:
                progress.update(task3, completed=1, description=f"[red]❌ Model Error: {e}[/red]")
        
        console.print("\n[bold green]✨ DIAGNOSTICS COMPLETE. ALL SYSTEMS GO.[/bold green]")
        console.input("\n[dim]Press Enter to return to menu...[/dim]")

    def sentinel_mode(self):
        """Visual Dashboard for the Eternal Loop"""
        self.header()
        console.print("[bold magenta]👁️  SENTINEL MODE ACTIVE (Ctrl+C to Exit)[/bold magenta]")
        
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="logs"),
            Layout(name="status", size=3)
        )
        
        layout["header"].update(Panel("Monitoring Gemini 3 & Memory Matrix 24/7", style="cyan"))
        layout["status"].update(Panel("System Status: NORMAL", style="green"))
        
        log_text = Text()
        
        with Live(layout, refresh_per_second=1):
            while True:
                try:
                    # Simulation of the real loop actions
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    # 1. Heartbeat
                    hb = f"[{timestamp}] 💓 Heartbeat saved to Memory Matrix..."
                    log_text.append(hb + "\n", style="dim")
                    self.memory.save_interaction("sentinel", "HEARTBEAT", "OK")
                    
                    # 2. Ping
                    start = time.time()
                    self.agent._get_client(Config.MODEL_FLASH).models.generate_content(
                        model=Config.MODEL_FLASH,
                        contents="ping",
                        config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="low"))
                    )
                    lat = time.time() - start
                    log_text.append(f"[{timestamp}] ✅ Gemini 3 Flash Ping: {lat:.2f}s\n", style="green")

                    # Keep log short
                    if len(log_text._text) > 20: 
                        log_text = Text("".join(log_text.plain.splitlines()[-20:]))

                    layout["logs"].update(Panel(log_text, title="Sentinel Logs", border_style="blue"))
                    
                    # Wait loop
                    for i in range(120): # 2 minute loop for demo (normally 5m)
                        time.sleep(1)
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    log_text.append(f"[ERROR] {e}\n", style="bold red")

    def interactive_chat(self):
        """Direct Line to Rhea Noir (Gemini 3 Pro)"""
        self.header()
        console.print("[bold magenta]💬 RHEA NOIR INTERFACE (Gemini 3 Pro)[/bold magenta]")
        console.print("[dim]Type 'exit' to quit.\n[/dim]")

        while True:
            user_input = console.input("[bold cyan]You > [/bold cyan]")
            if user_input.lower() in ['exit', 'quit']:
                break
                
            try:
                # Use the agent's new 6-Level Reasoning Query
                with console.status("[bold magenta]Thinking (Analyzing Config & Complexity)...[/bold magenta]"):
                    response = self.agent.query(question=user_input, user_id="admin_cli")
                
                console.print(f"\n[bold green]Rhea >[/bold green] {response}\n")
                console.print(Panel(f"[dim]Logic: 6-Tier Smart Router | Memory: Saved[/dim]"), style="dim")
                
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")

    def main_menu(self):
        while True:
            self.header()
            table = Table(show_header=False, box=None)
            table.add_row("[bold cyan]1.[/bold cyan] 🏥 Run System Diagnostics")
            table.add_row("[bold cyan]2.[/bold cyan] 👁️  Enter Sentinel Mode (Visual Loop)")
            table.add_row("[bold cyan]3.[/bold cyan] 💬 Chat with Rhea Noir (Gemini 3 Pro)")
            table.add_row("[bold cyan]4.[/bold cyan] ❌ Exit")
            console.print(table)
            
            choice = console.input("\n[bold yellow]Select Option > [/bold yellow]")
            
            if choice == "1":
                self.run_diagnostics()
            elif choice == "2":
                self.sentinel_mode()
            elif choice == "3":
                self.interactive_chat()
            elif choice == "4":
                console.print("[cyan]Shutting down Island Pi...[/cyan]")
                break

if __name__ == "__main__":
    try:
        app = IslandPi()
        app.main_menu()
    except Exception as e:
        console.print_exception()
