"""
Enhanced CLI with Memory Animation and Aspect Ratio Support
"""
# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*deprecated.*")
warnings.filterwarnings("ignore", message=".*google-cloud-storage.*")

import os
import sys
import time
import asyncio
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.align import Align
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.table import Table

# Ensure imports
sys.path.append(os.getcwd())
from visions_assistant.agent import get_chat_response

console = Console()

# Theme
BORDER_STYLE = "bright_cyan"
MEMORY_STYLE = "bold magenta"

# Aspect Ratios for Image Generation
ASPECT_RATIOS = {
    "1": "1:1 (Square)",
    "2": "16:9 (Landscape/Widescreen)",
    "3": "9:16 (Portrait)",
    "4": "4:3 (Traditional/Medium)",
    "5": "3:4 (Portrait Traditional)",
    "6": "21:9 (Ultra-Wide/Cinema)",
}

def create_memory_animation():
    """Visual animation showing memory being recorded"""
    table = Table.grid(expand=True)
    table.add_column(justify="center")
    
    frames = [
        "🧠 [cyan]●[/cyan] ○ ○ [dim]Recording to Memory...[/dim]",
        "🧠 ○ [cyan]●[/cyan] ○ [dim]Recording to Memory...[/dim]",
        "🧠 ○ ○ [cyan]●[/cyan] [dim]Recording to Memory...[/dim]",
        "🧠 [green]✓[/green] Memory Saved",
    ]
    
    return frames

def show_memory_save():
    """Show memory save animation"""
    frames = create_memory_animation()
    
    with Live(console=console, refresh_per_second=4, transient=True) as live:
        for frame in frames:
            live.update(Align.center(Text.from_markup(frame)))
            time.sleep(0.15)

def print_header():
    console.clear()
    ascii_art = """
    ██╗   ██╗    ██╗    ███████╗    ██╗     ██████╗     ███╗   ██╗    ███████╗
    ██║   ██║    ██║    ██╔════╝    ██║    ██╔═══██╗    ████╗  ██║    ██╔════╝
    ██║   ██║    ██║    ███████╗    ██║    ██║   ██║    ██╔██╗ ██║    ███████╗
    ╚██╗ ██╔╝    ██║    ╚════██║    ██║    ██║   ██║    ██║╚██╗██║    ╚════██║
     ╚████╔╝     ██║    ███████║    ██║    ╚██████╔╝    ██║ ╚████║    ███████║
      ╚═══╝      ╚═╝    ╚══════╝    ╚═╝     ╚═════╝     ╚═╝  ╚═══╝    ╚══════╝
                              A I   S Y S T E M S   +   M E M O R Y
    """
    
    header_panel = Panel(
        Align.center(
            Text(ascii_art, style="bold blue") + 
            Text("\n\nConnected to: ", style="dim white") + Text("GEMINI 3 PRO IMAGE (Global)", style="bold yellow") +
            Text("\nFallback: ", style="dim white") + Text("AI Studio API", style="bold green") +
            Text("\nMemory: ", style="dim white") + Text("ACTIVE (Async)", style=MEMORY_STYLE) +
            Text("\nRegion: ", style="dim white") + Text("us-central1", style="cyan"),
        ),
        border_style=BORDER_STYLE,
        title="[bold white]V I S I O N S   I N T E R F A C E   v3.0[/bold white]",
        subtitle="[dim]Dual-Mode | Memory-Enhanced | Access: OWNER[/dim]",
        padding=(1, 2),
        expand=True
    )
    console.print(header_panel)

def simulate_boot_sequence():
    """Boot sequence with memory initialization"""
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
        
        progress.update(t1, description="[magenta]Loading Memory Systems...")
        time.sleep(0.3)
        
        progress.update(t1, description="[yellow]Initializing Short-Term Memory...")
        time.sleep(0.2)
        
        progress.update(t1, description="[yellow]Connecting to Long-Term SQL...")
        time.sleep(0.2)
        
        progress.update(t1, description="[green]Memory Online. System Ready.")
        time.sleep(0.2)

def show_aspect_ratio_selector():
    """Show aspect ratio selection menu"""
    console.print("\n[bold cyan]📐 Select Aspect Ratio:[/bold cyan]")
    table = Table(show_header=False, box=None, expand=False)
    table.add_column("Key", style="cyan")
    table.add_column("Ratio", style="white")
    
    for key, value in ASPECT_RATIOS.items():
        table.add_row(key, value)
    
    console.print(table)
    
    choice = Prompt.ask(
        "[cyan]Choice[/cyan]",
        choices=list(ASPECT_RATIOS.keys()),
        default="1"
    )
    
    return ASPECT_RATIOS[choice]

def show_cascade_animation():
    """Show animated cascade indicator"""
    cascade_steps = [
        ("🎯 Triage", "routing query...", 0.15),
        ("⚡ Flash-Lite", "quick assessment...", 0.1),
        ("🌐 Flash", "grounded search...", 0.15),
        ("🔮 Pro", "deep thinking...", 0.2),
        ("📚 RAG", "knowledge lookup...", 0.1),
    ]
    
    console.print("\n[bold cyan]🧠 Model Cascade Active[/bold cyan]")
    for step, desc, delay in cascade_steps:
        console.print(f"   {step} [dim]{desc}[/dim]")
        time.sleep(delay)

def print_agent_response(text, image_path=None):
    """Print agent response with cascade animation and memory save"""
    
    # Show cascade animation
    show_cascade_animation()
    
    status_msg = "[bold magenta]🧠 Gemini 3 Pro synthesizing...[/bold magenta]"
    if image_path:
        status_msg = "[bold cyan]🧠 Processing visual data...[/bold cyan]"

    with console.status(status_msg, spinner="dots12"):
        response = get_chat_response(text, image_path)
    
    # Show memory being saved
    show_memory_save()
    
    console.print()
    console.print(f"[bold #af00ff]VISIONS >[/bold #af00ff]")
    
    md = Markdown(response)
    console.print(Panel(
        md, 
        border_style="purple", 
        title="[dim]Response[/dim]", 
        padding=(1, 2), 
        expand=True
    ))

def main():
    print_header()
    simulate_boot_sequence()
    
    console.print(Panel(
        Align.center(
            "[bold white]Welcome, Dave.[/bold white]\n" +
            "Memory-enhanced Visions is ready.\n\n" +
            "[dim]Commands:[/dim]\n" +
            "  [cyan]/image <path> <prompt>[/cyan] - Analyze image\n" +
            "  [cyan]/generate <prompt>[/cyan] - Generate image (with aspect ratio selector)\n" +
            "  [cyan]/memory[/cyan] - Show memory stats\n" +
            "  [cyan]exit[/cyan] - Terminate session"
        ),
        style="on #1a1a1a",
        border_style="dim",
        expand=True
    ))

    while True:
        console.print()
        user_input = Prompt.ask(f"[bold green]Input[/bold green]")
        
        if user_input.lower() in ["exit", "quit"]:
            console.print("\n[bold red]Terminating Session...[/bold red]")
            show_memory_save()
            time.sleep(0.5)
            console.clear()
            break
        
        if not user_input.strip():
            continue
        
        # Handle memory command
        if user_input.lower() == "/memory":
            console.print(Panel(
                "[cyan]Memory System Status:[/cyan]\n\n" +
                "📊 Short-Term: In-session buffer (100 entries)\n" +
                "💾 Long-Term: SQLite database (persistent)\n" +
                "☁️  Future: BigQuery analytics sync\n\n" +
                "[dim]All conversations are automatically saved.[/dim]",
                title="[bold magenta]MEMORY STATS[/bold magenta]",
                border_style=MEMORY_STYLE,
                expand=True
            ))
            continue
        
        # Handle image generation
        if user_input.startswith("/generate"):
            prompt_text = user_input[10:].strip()
            
            if not prompt_text:
                console.print("[bold red]Error:[/bold red] Please provide a prompt")
                continue
            
            # Show aspect ratio selector
            aspect_ratio = show_aspect_ratio_selector()
            
            console.print(Panel(
                f"📐 Aspect Ratio: [cyan]{aspect_ratio}[/cyan]\n" +
                f"🎨 Prompt: {prompt_text}\n\n" +
                "[dim]Generating...[/dim]",
                title="[bold yellow]IMAGE GENERATION REQUEST[/bold yellow]",
                border_style="yellow",
                expand=True
            ))
            
            # TODO: Integrate with dual_mode_generator
            console.print("[dim]Image generation integration pending...[/dim]")
            show_memory_save()
            continue
        
        image_path = None
        prompt_text = user_input

        # Handle image analysis
        if user_input.startswith("/image"):
            parts = user_input.split(" ", 2)
            if len(parts) < 3:
                console.print("[bold red]Usage:[/bold red] /image <path> <prompt>")
                continue
            image_path = parts[1].strip('\"').strip("'")
            prompt_text = parts[2]
            
            if not os.path.exists(image_path):
                console.print(f"[bold red]Error:[/bold red] Image not found at {image_path}")
                continue

            console.print(Panel(
                f"Target: {image_path}\nStatus: Encrypting & Uploading...",
                border_style="cyan",
                title="[bold cyan]VISUAL DATA UPLINK[/bold cyan]",
                expand=True
            ))

        # Show user input panel
        console.print(Panel(
            prompt_text,
            border_style="green",
            title="[bold green]YOU[/bold green]",
            title_align="left",
            expand=True
        ))

        print_agent_response(prompt_text, image_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted.[/bold red]")
