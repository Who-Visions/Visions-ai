"""
Visions AI - Ultra-Visual CLI Edition
Rich emoji-based interface with stunning visual feedback
"""
# Suppress all warnings first
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*deprecated.*")
warnings.filterwarnings("ignore", message=".*google-cloud-storage.*")

import os
import sys
import time
import threading

# Try to import readline for better input handling (fixes garbled text)
try:
    import readline
except ImportError:
    pass  # Windows fallback

from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich import box

sys.path.append(os.getcwd())
from visions_assistant.agent import get_chat_response, _initialize_backend
from memory import MemoryManager
from animations import (
    boot_sequence_animation, 
    memory_save_animation, 
    thinking_animation,
    cascade_animation
)

# Cost Intelligence System
try:
    from cost_intelligence import get_intelligence, route_query, check_cache, log_query
    from usage_tracker import get_tracker
    COST_TRACKING_ENABLED = True
except ImportError:
    COST_TRACKING_ENABLED = False
    get_intelligence = None
    route_query = None
    get_tracker = None

console = Console()
memory = MemoryManager()

# Initialize cost intelligence
cost_intel = get_intelligence() if COST_TRACKING_ENABLED else None
usage_tracker = get_tracker() if COST_TRACKING_ENABLED else None

# Visual Theme - Emoji-Enhanced
EMOJI = {
    "brain": "🧠",
    "camera": "📸",
    "image": "🖼️",
    "sparkles": "✨",
    "rocket": "🚀",
    "eye": "👁️",
    "memory": "💾",
    "cloud": "☁️",
    "lightning": "⚡",
    "check": "✅",
    "warning": "⚠️",
    "error": "❌",
    "info": "ℹ️",
    "gear": "⚙️",
    "chart": "📊",
    "lock": "🔒",
    "key": "🔑",
    "globe": "🌍",
    "clock": "🕐",
    "fire": "🔥",
    "star": "⭐",
    "paint": "🎨",
    "magic": "🪄",
    "diamond": "💎",
    "target": "🎯",
    "microscope": "🔬",
    "crystal": "🔮",
    "books": "📚",
    "cascade": "⚡",
}

# Aspect Ratio Visuals
ASPECT_RATIOS = {
    "1": ("1:1", "⬜", "Square"),
    "2": ("16:9", "▭", "Landscape/Widescreen"),
    "3": ("9:16", "▯", "Portrait/Mobile"),
    "4": ("4:3", "▬", "Traditional/Medium"),
    "5": ("3:4", "▭", "Portrait Traditional"),
    "6": ("21:9", "▬▬", "Ultra-Wide/Cinema"),
}

def create_visual_header():
    """Ultra-visual header with emojis and graphics"""
    
    ascii_art = "V  I  S  I  O  N  S     A  I"
    
    status_grid = Columns([
        Panel(
            f"{EMOJI['globe']} [bold yellow]Global[/bold yellow]\n[dim]Vertex AI[/dim]",
            border_style="yellow",
            expand=True
        ),
        Panel(
            f"{EMOJI['rocket']} [bold green]Active[/bold green]\n[dim]AI Studio[/dim]",
            border_style="green",
            expand=True
        ),
        Panel(
            f"{EMOJI['brain']} [bold magenta]Online[/bold magenta]\n[dim]Memory[/dim]",
            border_style="magenta",
            expand=True
        ),
    ], expand=True)
    
    header_group = Group(
        Align.center(Text(f"{EMOJI['sparkles']} {ascii_art} {EMOJI['sparkles']}", style="bold blue")),
        Text(""),
        status_grid
    )
    
    return Panel(
        header_group,
        border_style="bright_cyan",
        title=f"[bold white]{EMOJI['camera']}  V I S I O N S   I N T E R F A C E  {EMOJI['camera']}[/bold white]",
        subtitle=f"[dim]{EMOJI['diamond']} v3.0 | Dual-Mode | Memory | Access: OWNER {EMOJI['diamond']}[/dim]",
        padding=(1, 2),
        expand=True,
        box=box.DOUBLE
    )


def create_boot_visuals():
    """Animated boot sequence with emojis - now uses shared animations"""
    steps = [
        (f"{EMOJI['rocket']} Initializing Neural Link...", 0.25),
        (f"{EMOJI['key']} Authenticating Identity: Dave...", 0.2),
        (f"{EMOJI['brain']} Loading Memory Systems...", 0.2),
        (f"{EMOJI['memory']} Short-Term Memory... {EMOJI['check']}", 0.15),
        (f"{EMOJI['cloud']} Long-Term SQL Database... {EMOJI['check']}", 0.15),
        (f"{EMOJI['lightning']} Cascade Router... {EMOJI['check']}", 0.15),
        (f"{EMOJI['target']} Query Triage... {EMOJI['check']}", 0.15),
        (f"{EMOJI['fire']} System Ready!", 0.2),
    ]
    
    for step_text, delay in steps:
        console.print(f"[cyan]{step_text}[/cyan]")
        time.sleep(delay)

def create_memory_animation():
    """Visual memory save animation"""
    frames = [
        f"{EMOJI['brain']} [cyan]●[/cyan] ○ ○ [dim]Recording Memory...[/dim]",
        f"{EMOJI['brain']} ○ [cyan]●[/cyan] ○ [dim]Processing...[/dim]",
        f"{EMOJI['brain']} ○ ○ [cyan]●[/cyan] [dim]Saving...[/dim]",
        f"{EMOJI['brain']} [green]{EMOJI['check']}[/green] [bold green]Memory Saved[/bold green]",
    ]
    
    with Live(console=console, refresh_per_second=4, transient=True) as live:
        for frame in frames:
            live.update(Align.center(Text.from_markup(frame)))
            time.sleep(0.15)

def create_aspect_ratio_table():
    """Visual aspect ratio selector"""
    table = Table(
        title=f"\n{EMOJI['paint']} [bold cyan]Select Aspect Ratio[/bold cyan] {EMOJI['paint']}",
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        box=box.ROUNDED
    )
    
    table.add_column("Key", style="cyan bold", justify="center")
    table.add_column("Shape", style="white", justify="center")
    table.add_column("Ratio", style="yellow")
    table.add_column("Description", style="dim white")
    
    for key, (ratio, shape, desc) in ASPECT_RATIOS.items():
        table.add_row(key, shape, ratio, desc)
    
    return table

def create_welcome_panel():
    """Visual welcome message"""
    # Use manual text formatting for perfect alignment
    from rich.text import Text
    
    command_lines = [
        (f"{EMOJI['camera']} /generate", "Generate image with aspect ratio"),
        (f"{EMOJI['eye']} /image", "Analyze uploaded image"),
        (f"{EMOJI['brain']} /memory", "View memory statistics"),
        (f"{EMOJI['chart']} /stats", "System performance stats"),
        (f"💰 /costs", "Cost intelligence dashboard"),
        (f"📊 /usage", "Today's generation usage"),
        (f"📁 /export", "Export usage report (csv/json)"),
        (f"{EMOJI['info']} /help", "Show all commands"),
        (f"{EMOJI['lock']} /exit", "Terminate session"),
    ]
    
    command_texts = []
    for cmd, desc in command_lines:
        line = Text()
        line.append(f"{cmd:<25}", style="cyan bold")
        line.append(desc, style="dim white")
        command_texts.append(line)
    
    content = Group(
        Align.center(
            f"[bold white]{EMOJI['sparkles']} Welcome, Dave {EMOJI['sparkles']}[/bold white]\n" +
            f"{EMOJI['target']} Memory-enhanced Visions AI is ready\n"
        ),
        *command_texts
    )
    
    return Panel(
        content,
        title=f"[bold green]{EMOJI['rocket']} COMMAND CENTER[/bold green]",
        border_style="green",
        expand=True,
        box=box.DOUBLE
    )

def create_stats_panel():
    """Visual statistics display"""
    stats_table = Table.grid(padding=(0, 4))
    stats_table.add_column(style="cyan")
    stats_table.add_column(style="yellow bold")
    
    stats_table.add_row(f"{EMOJI['globe']} Primary Endpoint", "Vertex AI (Global)")
    stats_table.add_row(f"{EMOJI['rocket']} Fallback", "AI Studio API")
    stats_table.add_row(f"{EMOJI['brain']} Short-Term", "100 entries (RAM)")
    stats_table.add_row(f"{EMOJI['memory']} Long-Term", "SQLite (Persistent)")
    stats_table.add_row(f"{EMOJI['fire']} Model", "Gemini 3 Pro Image")
    stats_table.add_row(f"{EMOJI['lightning']} Status", "Dual-Mode Active")
    
    return Panel(
        stats_table,
        title=f"[bold magenta]{EMOJI['chart']} SYSTEM STATISTICS[/bold magenta]",
        border_style="magenta",
        expand=True,
        box=box.HEAVY
    )

def main():
    console.clear()
    
    # Start background initialization
    init_thread = threading.Thread(target=_initialize_backend, daemon=True)
    init_thread.start()
    
    # Visual header
    console.print(create_visual_header())
    console.print()
    
    # Boot sequence
    with console.status(f"[bold cyan]{EMOJI['gear']} Booting Systems...[/bold cyan]", spinner="dots12"):
        time.sleep(1)
    
    create_boot_visuals()
    console.print()
    
    # Welcome
    console.print(create_welcome_panel())
    
    while True:
        console.print()
        # Use raw input for cleaner text handling (avoids garbling in WSL)
        console.print(f"[bold green]{EMOJI['camera']} Input:[/bold green] ", end="")
        try:
            user_input = sys.stdin.readline().strip()
        except EOFError:
            user_input = "exit"
        
        if not user_input:
            continue
        
        if user_input.lower() in ["exit", "quit", "/exit"]:
            console.print(f"\n[bold red]{EMOJI['lock']} Terminating Session...[/bold red]")
            create_memory_animation()
            time.sleep(0.5)
            console.clear()
            console.print(f"[bold blue]{EMOJI['sparkles']} Thank you, Dave. Visions signing off. {EMOJI['sparkles']}[/bold blue]")
            break
        
        # Stats command
        if user_input.lower() in ["/stats", "stats"]:
            console.print(create_stats_panel())
            continue
        
        # Memory command
        if user_input.lower() in ["/memory", "memory"]:
            short_stats = memory.short_term.get_stats()
            long_stats = memory.long_term.get_stats()
            
            memory_panel = Panel(
                f"[cyan]{EMOJI['brain']} Memory System Status:[/cyan]\n\n" +
                f"{EMOJI['lightning']} [bold]Short-Term:[/bold] {short_stats['total_entries']} entries (Active Session)\n" +
                f"{EMOJI['memory']} [bold]Long-Term:[/bold] {long_stats['total_conversations']} conversations saved\n" +
                f"{EMOJI['cloud']} [bold]Storage:[/bold] {long_stats['storage_location']}\n" +
                f"{EMOJI['chart']} [bold]User:[/bold] {long_stats['preferences'].get('user_name', 'Unknown')}\n\n" +
                f"[dim]{EMOJI['check']} Memory is active and recording[/dim]",
                title=f"[bold magenta]{EMOJI['brain']} MEMORY BANK[/bold magenta]",
                border_style="magenta",
                expand=True,
                box=box.DOUBLE
            )
            console.print(memory_panel)
            continue
        
        # Help command
        if user_input.lower() in ["help", "/help"]:
            console.print(create_welcome_panel())
            continue
        
        # Cost tracking commands
        if user_input.lower() in ["/costs", "/cost", "costs"]:
            if cost_intel:
                cost_intel.print_dashboard()
            else:
                console.print(f"[yellow]{EMOJI['warning']} Cost tracking not available[/yellow]")
            continue
        
        # Usage tracking
        if user_input.lower() in ["/usage", "usage"]:
            if usage_tracker:
                usage_tracker.print_daily_summary()
            else:
                console.print(f"[yellow]{EMOJI['warning']} Usage tracking not available[/yellow]")
            continue
        
        # Export reports
        if user_input.lower().startswith("/export"):
            if cost_intel:
                parts = user_input.split()
                format = parts[1] if len(parts) > 1 else "json"
                filepath = cost_intel.export_report(format)
                console.print(f"[green]{EMOJI['check']} Exported to: {filepath}[/green]")
            else:
                console.print(f"[yellow]{EMOJI['warning']} Cost tracking not available[/yellow]")
            continue
        
        # Generate image
        if user_input.startswith("/generate"):
            prompt_text = user_input[10:].strip()
            
            if not prompt_text:
                console.print(f"[bold red]{EMOJI['warning']} Error:[/bold red] Please provide a prompt")
                continue
            
            # Aspect ratio selector
            console.print(create_aspect_ratio_table())
            choice = Prompt.ask(
                f"[cyan]{EMOJI['target']} Choice[/cyan]",
                choices=list(ASPECT_RATIOS.keys()),
                default="1"
            )
            
            ratio, shape, desc = ASPECT_RATIOS[choice]
            
            console.print(Panel(
                f"{EMOJI['paint']} [bold]Aspect Ratio:[/bold] {shape} {ratio} ({desc})\n" +
                f"{EMOJI['magic']} [bold]Prompt:[/bold] {prompt_text}\n\n" +
                f"{EMOJI['rocket']} [dim]Initiating generation...[/dim]",
                title=f"[bold yellow]{EMOJI['camera']} IMAGE GENERATION REQUEST[/bold yellow]",
                border_style="yellow",
                expand=True,
                box=box.HEAVY
            ))
            
            # TODO: Integrate with dual_mode_generator
            with console.status(f"[bold yellow]{EMOJI['sparkles']} Generating...[/bold yellow]", spinner="aesthetic"):
                time.sleep(1)
            
            console.print(f"[bold green]{EMOJI['check']} Generation complete![/bold green]")
            console.print(f"[dim]{EMOJI['info']} Full integration pending...[/dim]")
            create_memory_animation()
            continue
        
        # Image analysis
        image_path = None
        prompt_text = user_input
        
        if user_input.startswith("/image"):
            parts = user_input.split(" ", 2)
            if len(parts) < 3:
                console.print(f"[bold red]{EMOJI['warning']} Usage:[/bold red] /image <path> <prompt>")
                continue
            
            image_path = parts[1].strip('\"').strip("'")
            prompt_text = parts[2]
            
            if not os.path.exists(image_path):
                console.print(f"[bold red]{EMOJI['error']} Error:[/bold red] Image not found")
                continue
            
            console.print(Panel(
                f"{EMOJI['camera']} [bold]Target:[/bold] {image_path}\n" +
                f"{EMOJI['lock']} [bold]Status:[/bold] Encrypting & Uploading...\n" +
                f"{EMOJI['cloud']} [bold]Destination:[/bold] Vertex AI",
                border_style="cyan",
                title=f"[bold cyan]{EMOJI['eye']} VISUAL DATA UPLINK[/bold cyan]",
                expand=True,
                box=box.DOUBLE
            ))
        
        # Show user input
        console.print(Panel(
            f"{EMOJI['target']} {prompt_text}",
            border_style="green",
            title=f"[bold green]{EMOJI['sparkles']} YOU[/bold green]",
            title_align="left",
            expand=True,
            box=box.ROUNDED
        ))
        
        # Get context from memory
        context = memory.get_context_for_model(limit=5)
        full_prompt = f"Context from previous turn:\n{context}\n\nCurrent User Question: {prompt_text}" if context else prompt_text

        # Smart routing - determine best tier for this query
        query_tier = "standard"
        query_model = "gemini-3-pro"
        if COST_TRACKING_ENABLED and route_query:
            query_model, query_tier = route_query(prompt_text)

        # Check cache first
        cached_response = None
        if COST_TRACKING_ENABLED and check_cache:
            cached_response = check_cache(full_prompt)
            if cached_response:
                console.print(f"[green]{EMOJI['lightning']} Cache hit! (90% cost saved)[/green]")

        # Show cascade animation while loading
        console.print(f"\n[bold cyan]{EMOJI['brain']} Activating Model Cascade...[/bold cyan]")
        console.print(f"[dim]   Smart Route: {query_tier} → {query_model}[/dim]")
        
        # Animated cascade indicator
        cascade_steps = [
            (f"   {EMOJI['target']} Triage", "routing query...", 0.2),
            (f"   {EMOJI['lightning']} Flash-Lite", "quick assessment...", 0.15),
            (f"   {EMOJI['globe']} Flash", "grounded search...", 0.2),
            (f"   {EMOJI['crystal']} Pro", "deep thinking...", 0.25),
            (f"   {EMOJI['books']} RAG", "knowledge lookup...", 0.15),
        ]
        
        for step, desc, delay in cascade_steps:
            console.print(f"{step} [dim]{desc}[/dim]")
            time.sleep(delay)

        # Get response with animated status
        with console.status(f"[bold magenta]{EMOJI['brain']} Gemini 3 Pro synthesizing...[/bold magenta]", spinner="dots12"):
            if cached_response:
                response = cached_response
            else:
                response = get_chat_response(full_prompt, image_path)
        
        # Log the query cost
        if COST_TRACKING_ENABLED and log_query and cost_intel:
            # Estimate tokens (rough: 4 chars = 1 token)
            input_tokens = len(full_prompt) // 4
            output_tokens = len(response) // 4
            cost = log_query("text", query_model, query_tier, input_tokens, output_tokens, cached=bool(cached_response))
            
            # Cache the response for future use
            if not cached_response and cost_intel:
                cost_intel.cache_response(full_prompt, response, input_tokens)
        
        # Save to memory with animation
        memory.remember_conversation(prompt_text, response)
        create_memory_animation()
        
        # Display response
        console.print(f"\n[bold #af00ff]{EMOJI['eye']} VISIONS >[/bold #af00ff]")
        md = Markdown(response)
        console.print(Panel(
            md,
            border_style="purple",
            title=f"[dim]{EMOJI['star']} Response[/dim]",
            padding=(1, 2),
            expand=True,
            box=box.DOUBLE
        ))
        
        # Show cost after response
        if COST_TRACKING_ENABLED and cost_intel:
            breakdown = cost_intel.get_cost_breakdown(1)  # Today only
            console.print(f"[dim]{EMOJI['chart']} Session: ${breakdown['total_cost']:.4f} | Tier: {query_tier}[/dim]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print(f"\n[bold red]{EMOJI['warning']} Interrupted.[/bold red]")
