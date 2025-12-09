# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*deprecated.*")
warnings.filterwarnings("ignore", message=".*google-cloud-storage.*")

import os
import sys
import time
import random
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn

# Ensure we can import from visions_assistant
sys.path.append(os.getcwd())
from visions_assistant.agent import get_chat_response

# Cost Intelligence System
try:
    from cost_intelligence import get_intelligence, route_query, log_query
    from usage_tracker import get_tracker
    COST_TRACKING_ENABLED = True
except ImportError:
    COST_TRACKING_ENABLED = False
    get_intelligence = None
    route_query = None
    get_tracker = None

console = Console()

# Initialize cost intelligence
cost_intel = get_intelligence() if COST_TRACKING_ENABLED else None

# --- Theme Constants ---
BORDER_STYLE = "bright_cyan"
TITLE_STYLE = "bold magenta"
USER_STYLE = "bold green"
AGENT_STYLE = "bold #af00ff" # Deep Purple
SYSTEM_STYLE = "italic cyan"

def print_header():
    console.clear()
    ascii_art = """
    ██╗   ██╗    ██╗    ███████╗    ██╗     ██████╗     ███╗   ██╗    ███████╗
    ██║   ██║    ██║    ██╔════╝    ██║    ██╔═══██╗    ████╗  ██║    ██╔════╝
    ██║   ██║    ██║    ███████╗    ██║    ██║   ██║    ██╔██╗ ██║    ███████╗
    ╚██╗ ██╔╝    ██║    ╚════██║    ██║    ██║   ██║    ██║╚██╗██║    ╚════██║
     ╚████╔╝     ██║    ███████║    ██║    ╚██████╔╝    ██║ ╚████║    ███████║
      ╚═══╝      ╚═╝    ╚══════╝    ╚═╝     ╚═════╝     ╚═╝  ╚═══╝    ╚══════╝
                                  A I   S Y S T E M S
    """
    
    grid = Layout()
    
    header_panel = Panel(
        Align.center(
            Text(ascii_art, style="bold blue") + 
            Text("\n\nConnected to: ", style="dim white") + Text("GEMINI 3 PRO IMAGE (Global)", style="bold yellow") +
            Text("\nKnowledge Base: ", style="dim white") + Text("ONLINE", style="bold green") +
            Text("\nRegion: ", style="dim white") + Text("us-central1", style="cyan"),
        ),
        border_style=BORDER_STYLE,
        title="[bold white]V I S I O N S   I N T E R F A C E[/bold white]",
        subtitle="[dim]v2.5.0 | Access Level: OWNER[/dim]",
        padding=(1, 2),
        expand=True
    )
    console.print(header_panel)

def simulate_boot_sequence():
    """Simulates a high-tech boot up sequence."""
    with Progress(
        SpinnerColumn("dots12", style="magenta"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
        expand=True
    ) as progress:
        t1 = progress.add_task("[cyan]Initializing Neural Link...", total=100)
        for i in range(20):
            time.sleep(0.02)
            progress.update(t1, advance=5)
        
        progress.update(t1, description="[blue]Authenticating Identity: Dave...")
        time.sleep(0.3)
        
        progress.update(t1, description="[magenta]Loading Cascade Router...")
        time.sleep(0.2)
        
        progress.update(t1, description="[yellow]Initializing Query Triage...")
        time.sleep(0.2)
        
        progress.update(t1, description="[green]System Ready.")
        time.sleep(0.2)

def show_cascade_animation():
    """Show animated cascade indicator using Live"""
    from rich.live import Live
    from rich.group import Group
    from rich.panel import Panel
    
    cascade_steps = [
        ("🎯 Triage", "routing query...", 0.15),
        ("⚡ Flash-Lite", "quick assessment...", 0.1),
        ("🌐 Flash", "grounded search...", 0.15),
        ("🔮 Pro", "deep thinking...", 0.2),
        ("📚 RAG", "knowledge lookup...", 0.1),
    ]
    
    step_visuals = []
    
    # render initial frame
    title = Text("\n🧠 Model Cascade Active", style="bold cyan")
    
    with Live(console=console, refresh_per_second=10, transient=True) as live:
        for step, desc, delay in cascade_steps:
            # Build the list of active steps
            step_visuals.append(Text(f"   {step} {desc}", style="dim"))
            
            # Create the group
            group = Group(
                title,
                *step_visuals
            )
            
            live.update(Panel(group, border_style="cyan", title="Routing", expand=False))
            time.sleep(delay)
            
            # Highlight the last added step
            step_visuals[-1].style = "bold white"
            live.update(Panel(Group(title, *step_visuals), border_style="cyan", title="Routing", expand=False))
            time.sleep(0.1)


def print_agent_response(text, image_path=None, show_thinking=False):
    """Streams the agent response with optional thinking display."""
    
    # Show cascade animation
    show_cascade_animation()
    
    status_msg = "[bold magenta]🧠 Gemini 3 Pro synthesizing...[/bold magenta]"
    if image_path:
        status_msg = "[bold cyan]🧠 Processing visual data...[/bold cyan]"

    # Get response with spinner
    with console.status(status_msg, spinner="dots12"):
        response = get_chat_response(text, image_path)
    
    # Parse JSON response
    import json
    try:
        data = json.loads(response)
        user_text = data.get("text", response)
        thinking = data.get("thinking", "")
        images = data.get("images", [])
    except json.JSONDecodeError:
        # Fallback for non-JSON response
        user_text = response
        thinking = ""
        images = []

    console.print()
    
    # Show thinking if enabled (debug mode)
    if thinking and show_thinking:
        console.print(f"[dim italic]🧠 Internal Thinking Process:[/dim italic]")
        thinking_md = Markdown(thinking)
        console.print(Panel(
            thinking_md,
            border_style="dim yellow",
            title="[dim yellow]Debug: Visions' Thoughts[/dim yellow]",
            padding=(1, 2),
            expand=True
        ))
        console.print()
    
    # Show user-facing response (clean)
    console.print(f"[{AGENT_STYLE}]VISIONS >[/{AGENT_STYLE}]")
    
    # Render Markdown nicely
    md = Markdown(user_text)
    console.print(Panel(
        md,
        border_style="purple",
        title="[dim]Response[/dim]",
        padding=(1, 2),
        expand=True
    ))
    
    # Show images if any
    if images:
        console.print(f"[cyan]📸 {len(images)} image(s) generated[/cyan]")

def main():
    print_header()
    simulate_boot_sequence()
    
    # Debug mode flag (toggle with /debug)
    debug_mode = False
    
    welcome_msg = "[bold white]Welcome, Dave. How can I assist your creative vision today?[/bold white]"
    if debug_mode:
        welcome_msg += "\n[dim yellow]Debug Mode: ON (thinking visible)[/dim yellow]"
    
    console.print(Panel(
        Align.center(welcome_msg),
        style="on #1a1a1a",
        border_style="dim",
        expand=True
    ))

    while True:
        # Get input nicely
        console.print() # Spacer
        user_input = Prompt.ask(f"[{USER_STYLE}]Input[/{USER_STYLE}]")
        
        if user_input.lower() in ["exit", "quit"]:
            console.print("\n[bold red]Terminating Session...[/bold red]")
            time.sleep(0.5)
            console.clear()
            break
        
        # Toggle debug mode
        if user_input.lower() == "/debug":
            debug_mode = not debug_mode
            status = "ON" if debug_mode else "OFF"
            color = "green" if debug_mode else "red"
            console.print(f"[bold {color}]🔧 Debug Mode: {status}[/bold {color}]")
            if debug_mode:
                console.print("[dim]Visions' internal thinking will now be visible[/dim]")
            else:
                console.print("[dim]Only user-facing responses will be shown[/dim]")
            continue
        
        if not user_input.strip():
            continue

        image_path = None
        prompt_text = user_input

        # Handle Image Command
        if user_input.startswith("/image"):
            parts = user_input.split(" ", 2)
            if len(parts) < 3:
                console.print("[bold red]Usage:[/bold red] /image <path_to_image> <your prompt>")
                continue
            image_path = parts[1].strip('"').strip("'") # Handle quotes
            prompt_text = parts[2]
            
            if not os.path.exists(image_path):
                console.print(f"[bold red]Error:[/bold red] Image not found at {image_path}")
                continue

            # Visual Feedback for Upload
            console.print(Panel(
                f"Target: {image_path}\nStatus: Encrypting & Uploading...",
                border_style="cyan",
                title="[bold cyan]VISUAL DATA UPLINK[/bold cyan]",
                expand=True
            ))

        # Clear the raw prompt line and render a nice User Panel instead to keep history clean
        # (Rich doesn't easily delete the last line, so we just render the panel after the input)
        console.print(Panel(
            prompt_text,
            border_style="green",
            title="[bold green]YOU[/bold green]",
            title_align="left",
            expand=True
        ))

        print_agent_response(prompt_text, image_path, show_thinking=debug_mode)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted.[/bold red]")