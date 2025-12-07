"""
Visions AI - Rich Animations Module
Provides visual feedback for all loading operations
"""
import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.spinner import Spinner

console = Console()

# Animation frames for different states
BRAIN_FRAMES = ["🧠", "🧠💭", "🧠💭💡", "🧠💡", "🧠"]
ROCKET_FRAMES = ["🚀", "🚀✨", "🚀✨⚡", "🚀⚡", "🚀"]
SEARCH_FRAMES = ["🔍", "🔎", "🔍", "🔎"]
THINK_FRAMES = ["🤔", "💭", "💡", "✨"]

class CascadeAnimation:
    """Animated display for the model cascade"""
    
    def __init__(self):
        self.models = {
            "triage": ("🎯", "Triage", "Analyzing query...", False),
            "lite": ("⚡", "Flash-Lite", "Quick instinct...", False),
            "flash": ("🌐", "Flash", "Grounded search...", False),
            "pro": ("🔮", "Pro", "Deep thinking...", False),
            "rag": ("📚", "RAG", "Knowledge base...", False),
            "synth": ("🧠", "Gemini 3", "Synthesizing...", False),
        }
        self.status = {}
    
    def create_frame(self):
        """Create a single animation frame"""
        lines = []
        for key, (emoji, name, desc, done) in self.models.items():
            if key not in self.status:
                status = "[dim]⏸ Waiting[/dim]"
                style = "dim"
            elif self.status[key] == "running":
                status = "[yellow]▰▰▱▱ Running[/yellow]"
                style = "yellow"
            elif self.status[key] == "done":
                status = "[green]✓ Complete[/green]"
                style = "green"
            elif self.status[key] == "skipped":
                status = "[dim]⊘ Skipped[/dim]"
                style = "dim"
            else:
                status = "[red]✗ Error[/red]"
                style = "red"
            
            lines.append(f"   {emoji} [{style}]{name:12}[/{style}] {status}")
        
        return "\n".join(lines)


def animated_progress(description: str, steps: list, delay: float = 0.3):
    """
    Show animated progress through steps
    
    Args:
        description: Main task description
        steps: List of (step_text, duration) tuples
        delay: Base delay between updates
    """
    with Progress(
        SpinnerColumn("dots12", style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=20),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"[cyan]{description}", total=len(steps))
        
        for step_text, duration in steps:
            progress.update(task, description=f"[cyan]{step_text}")
            time.sleep(duration)
            progress.advance(task)


def cascade_animation(routing: dict = None):
    """
    Animated cascade showing which models are being invoked
    """
    if routing is None:
        routing = {}
    
    frames = []
    
    # Build animation sequence based on routing
    steps = [
        ("🎯", "Triage", "Analyzing query intent...", 0.3),
    ]
    
    if not routing.get("is_greeting"):
        if not routing.get("is_simple"):
            steps.append(("⚡", "Flash-Lite", "Quick instinct check...", 0.2))
        if routing.get("needs_realtime"):
            steps.append(("🌐", "Flash", "Searching real-time data...", 0.4))
        if routing.get("needs_deep_thinking"):
            steps.append(("🔮", "Pro", "Deep analysis (2048 tokens)...", 0.5))
        if routing.get("needs_knowledge"):
            steps.append(("📚", "RAG", "Searching knowledge base...", 0.3))
    
    steps.append(("🧠", "Gemini 3", "Synthesizing response...", 0.3))
    
    with Progress(
        SpinnerColumn("dots12", style="magenta"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        for emoji, name, desc, duration in steps:
            task_desc = f"{emoji} [bold]{name}[/bold]: {desc}"
            task = progress.add_task(task_desc, total=None)
            time.sleep(duration)
            progress.remove_task(task)


def thinking_animation(duration: float = 2.0):
    """Show animated thinking process"""
    frames = [
        "🧠 [cyan]●[/cyan]○○ Thinking...",
        "🧠 ○[cyan]●[/cyan]○ Processing...",
        "🧠 ○○[cyan]●[/cyan] Reasoning...",
        "🧠 ○[cyan]●[/cyan]○ Analyzing...",
        "🧠 [cyan]●[/cyan]○○ Formulating...",
    ]
    
    iterations = int(duration / 0.3)
    with Live(console=console, refresh_per_second=4, transient=True) as live:
        for i in range(iterations):
            frame = frames[i % len(frames)]
            live.update(Text.from_markup(f"   {frame}"))
            time.sleep(0.3)


def memory_save_animation():
    """Animated memory save indicator"""
    frames = [
        "💾 [cyan]●[/cyan] ○ ○ [dim]Recording to Memory...[/dim]",
        "💾 ○ [cyan]●[/cyan] ○ [dim]Processing...[/dim]",
        "💾 ○ ○ [cyan]●[/cyan] [dim]Saving...[/dim]",
        "💾 [green]✓[/green] [bold green]Memory Saved[/bold green]",
    ]
    
    with Live(console=console, refresh_per_second=4, transient=True) as live:
        for frame in frames:
            live.update(Align.center(Text.from_markup(frame)))
            time.sleep(0.2)


def search_animation(query: str, duration: float = 1.5):
    """Animated search indicator"""
    with console.status(
        f"[bold cyan]🔍 Searching: {query[:50]}...[/bold cyan]",
        spinner="dots12"
    ):
        time.sleep(duration)


def generation_animation(prompt: str):
    """Animated image generation indicator"""
    steps = [
        ("🎨 Parsing prompt...", 0.2),
        ("🖼️ Initializing generation...", 0.3),
        ("✨ Creating image...", 0.5),
        ("🔮 Applying enhancements...", 0.3),
    ]
    
    animated_progress(f"Generating: {prompt[:30]}...", steps)


def boot_sequence_animation():
    """Animated boot sequence"""
    steps = [
        ("🚀 Initializing Neural Link...", 0.3),
        ("🔑 Authenticating Identity...", 0.2),
        ("🧠 Loading Memory Systems...", 0.2),
        ("💾 Short-Term Memory... ✅", 0.15),
        ("☁️ Long-Term Database... ✅", 0.15),
        ("⚡ Cascade Router... ✅", 0.15),
        ("🎯 Query Triage... ✅", 0.15),
        ("🔥 System Ready!", 0.2),
    ]
    
    for step, delay in steps:
        console.print(f"[cyan]{step}[/cyan]")
        time.sleep(delay)


def model_cascade_live(routing: dict = None):
    """
    Live updating cascade display showing model status
    """
    if routing is None:
        routing = {"needs_realtime": True, "needs_deep_thinking": True, "needs_knowledge": True}
    
    def make_line(emoji, name, status, style="white"):
        status_icons = {
            "waiting": "[dim]⏳ Waiting[/dim]",
            "running": "[yellow]▰▰▱▱ Running[/yellow]",
            "done": "[green]✓ Done[/green]",
            "skipped": "[dim]⊘ Skipped[/dim]",
        }
        return f"   {emoji} [{style}]{name:14}[/{style}] {status_icons.get(status, status)}"
    
    table = Table.grid(padding=(0, 2))
    table.add_column()
    
    # Show cascade with live updates
    with Live(console=console, refresh_per_second=4, transient=True) as live:
        states = {}
        
        # Triage
        states["triage"] = "running"
        live.update(Panel(
            "\n".join([
                make_line("🎯", "Triage", states.get("triage", "waiting")),
                make_line("⚡", "Flash-Lite", states.get("lite", "waiting")),
                make_line("🌐", "Flash", states.get("flash", "waiting")),
                make_line("🔮", "Pro", states.get("pro", "waiting")),
                make_line("📚", "RAG", states.get("rag", "waiting")),
                make_line("🧠", "Gemini 3", states.get("synth", "waiting")),
            ]),
            title="[bold cyan]🧠 MODEL CASCADE[/bold cyan]",
            border_style="cyan"
        ))
        time.sleep(0.3)
        states["triage"] = "done"
        
        # Flash-Lite
        if not routing.get("is_simple"):
            states["lite"] = "running"
            live.update(Panel("\n".join([
                make_line("🎯", "Triage", states.get("triage", "waiting")),
                make_line("⚡", "Flash-Lite", states.get("lite", "waiting")),
                make_line("🌐", "Flash", states.get("flash", "waiting")),
                make_line("🔮", "Pro", states.get("pro", "waiting")),
                make_line("📚", "RAG", states.get("rag", "waiting")),
                make_line("🧠", "Gemini 3", states.get("synth", "waiting")),
            ]), title="[bold cyan]🧠 MODEL CASCADE[/bold cyan]", border_style="cyan"))
            time.sleep(0.2)
            states["lite"] = "done"
        else:
            states["lite"] = "skipped"


if __name__ == "__main__":
    # Demo the animations
    console.print("[bold cyan]Animation Demo[/bold cyan]\n")
    
    boot_sequence_animation()
    console.print()
    
    thinking_animation(1.5)
    console.print()
    
    memory_save_animation()
    console.print()
    
    cascade_animation({"needs_realtime": True, "needs_deep_thinking": True, "needs_knowledge": True})
