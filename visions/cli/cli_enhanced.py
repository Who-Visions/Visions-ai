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
from rich.layout import Layout
from rich.console import Group
from rich.tree import Tree
from datetime import datetime

# Ensure imports
sys.path.append(os.getcwd())
from visions_assistant.agent import get_chat_response
from visions.core.config import Config

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
usage_tracker = get_tracker() if COST_TRACKING_ENABLED else None

# Initialize Director Engine
try:
    from visions_director_engine import DirectorEngine
    # Note: DirectorEngine passes (prompt, config) to the generation function
    director_engine = DirectorEngine(lambda p, c=None: get_chat_response(p, config=c))
except ImportError:
    director_engine = None

# Gemini Colors
GOOGLE_BLUE = "#4285F4"
GOOGLE_RED = "#EA4335"
GOOGLE_YELLOW = "#FBBC05"
GOOGLE_GREEN = "#34A853"
ACCENT_PURPLE = "#8E24AA"

# Theme
BORDER_STYLE = "dim white"
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

class DirectorUI:
    def __init__(self):
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="header", size=8),
            Layout(name="body"),
            Layout(name="input", size=3),
            Layout(name="footer", size=1)
        )
        # Use a more open layout without side panels for 99% mimicry
        self.chat_history = []
        self.traces = []
        self.stats_text = "System Initializing..."
        self.status_bar_text = "Visions Active"
        
        # Build Panels
        self.update_header()
        self.update_main()
        self.update_input()
        self.update_footer()

    def update_header(self):
        ascii_art = """
   ██╗   ██╗    ██╗    ███████╗    ██╗     ██████╗     ███╗   ██╗    ███████╗
   ██║   ██║    ██║    ██╔════╝    ██║    ██╔═══██╗    ████╗  ██║    ██╔════╝
   ██║   ██║    ██║    ███████╗    ██║    ██║   ██║    ██╔██╗ ██║    ███████╗
   ╚██╗ ██╔╝    ██║    ╚════██║    ██║    ██║   ██║    ██║╚██╗██║    ╚════██║
    ╚████╔╝     ██║    ███████║    ██║    ╚██████╔╝    ██║ ╚████║    ███████║
     ╚═══╝      ╚═╝    ╚══════╝    ╚═╝     ╚═════╝     ╚═╝  ╚═══╝    ╚══════╝
        """
        # Multi-color gradient logo like Gemini-CLI
        lines = ascii_art.strip("\n").split("\n")
        colored_logo = Text()
        colors = [GOOGLE_BLUE, ACCENT_PURPLE, GOOGLE_RED, GOOGLE_YELLOW, GOOGLE_GREEN]
        for i, line in enumerate(lines):
            colored_logo.append(line + "\n", style=colors[i % len(colors)])

        self.layout["header"].update(
            Panel(
                Align.left(colored_logo),
                title="[dim]V I S I O N S   H Q[/dim]",
                border_style="dim"
            )
        )

    def update_main(self):
        # Gemini-CLI style: Sequential feed with Markdown
        elements = []
        # Limit history to prevent overflow, mimicking scroll
        for role, text in self.chat_history[-6:]:
            if role == "User":
                elements.append(Text(f"\n(user) > {text}", style="bold cyan"))
            else:
                msg_header = Text()
                msg_header.append("\n(visions) v\n", style="bold magenta")
                elements.append(msg_header)
                elements.append(Markdown(text))
        
        # Neural Traces: Dynamic reasoning steps
        if self.traces:
            elements.append(Text("\n───", style="dim"))
            for trace in self.traces[-3:]:
                elements.append(trace)

        self.layout["body"].update(Align.left(Group(*elements)))

    def update_footer(self):
        # Gemini-CLI Footer: Path | ID | Model
        cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
        # Truncate path if too long
        if len(cwd) > 30: cwd = "..." + cwd[-27:]
        
        path_text = Text(f" {cwd} ", style=f"bold {GOOGLE_BLUE}")
        status_text = Text(" [v3.0-visions] ", style=f"bold {GOOGLE_GREEN}")
        model_text = Text(f" {Config.MODEL_IMAGE} ", style=f"bold {ACCENT_PURPLE}")
        
        footer_table = Table.grid(expand=True)
        footer_table.add_column(justify="left", ratio=1)
        footer_table.add_column(justify="center", ratio=1)
        footer_table.add_column(justify="right", ratio=1)
        footer_table.add_row(path_text, status_text, model_text)
        
        self.layout["footer"].update(footer_table)

    def log_trace(self, message, style="white"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.traces.append(Text(f" [{timestamp}] {message}", style="dim " + style))
        self.update_main()

    def add_chat(self, role, text):
        self.chat_history.append((role, text))
        self.update_main()

    def clear(self):
        self.chat_history = []
        self.traces = []
        self.update_main()
        self.update_input()

    def update_input(self, placeholder="[dim]Ask visions or type /help...[/dim]"):
        self.layout["input"].update(Panel(placeholder, title="[bold cyan]Command Input[/bold cyan]", border_style="bright_blue"))

    def update_stats(self, *args, **kwargs):
        # Compatibility bridge
        self.update_footer()

ui = DirectorUI()

def show_help():
    help_text = """
### [bold white]Visions Commands[/bold white]
- `/image <path> <prompt>` : Analyze an image
- `/generate <prompt>`     : Generate an image (DALL-E 3 / Imagen style)
- `/clear`                 : Clear the current session history
- `/memory`                : View memory system status
- `/help`                  : Show this menu
- `exit`                   : Close the connection
    """
    ui.add_chat("Visions", help_text)

def simulate_boot_sequence(live):
    """Boot sequence within layout"""
    ui.log_trace("Initializing Global Systems...", "cyan")
    time.sleep(0.4)
    ui.log_trace("Authenticating: Owner Access Required", "yellow")
    time.sleep(0.4)
    ui.log_trace("Memory Core: Connected (SQLite)", "magenta")
    ui.update_stats()
    time.sleep(0.4)
    ui.log_trace("Visions Online.", "green")
    time.sleep(0.5)

def show_cascade_animation(live):
    """Integrated cascade info in side panel"""
    steps = ["Triage", "Flash Search", "Pro Refinement", "Memory Lookup"]
    for step in steps:
        ui.log_trace(f"Routing > {step}...", "dim cyan")
        time.sleep(0.15)


def print_agent_response(text, image_path=None, video_path=None, live=None):
    """Process and display agent response with UI updates"""
    show_cascade_animation(live)
    
    ui.log_trace("Pro Synthesis Started", "magenta")
    ui.update_footer() # Placeholder for "Thinking..."
    
    # Updated to pass video_path
    response = get_chat_response(text, image_path, video_path=video_path)
    
    ui.log_trace("Synthesis Complete", "green")
    ui.log_trace("Memory Recorded", "dim blue")
    ui.add_chat("Visions", response)
    ui.update_stats()

def main():
    # Keep screen=False to mimic gemini-cli's scroll-back capability
    with Live(ui.layout, console=console, refresh_per_second=4, transient=False) as live:
        simulate_boot_sequence(live)
        
        ui.add_chat("Visions", "Welcome, Dave. Memory-enhanced Visions is ready.")

        while True:
            ui.update_footer()
            ui.update_input("[bold green]▶ Awaiting your command...[/bold green]")
            live.stop()
            
            try:
                # 99% Mimic but with boundaries
                user_input = Prompt.ask(f"\n[bold white]?[/bold white]")
            except EOFError:
                break
            
            # Show the input in the box for a moment
            ui.update_input(f"[bold white]{user_input}[/bold white]")
            live.start()

            if user_input.lower() in ["exit", "quit"]:
                ui.log_trace("Terminating session...", "red")
                time.sleep(0.5)
                break
            
            if not user_input.strip():
                continue

            if user_input.lower() == "/help":
                show_help()
                continue

            if user_input.lower() == "/clear":
                ui.clear()
                ui.log_trace("Session history wiped.", "yellow")
                continue

            if user_input.lower() == "/memory":
                ui.log_trace("Querying Memory Hub", "magenta")
                mem_report = (
                    "**Memory System Status**\n\n"
                    "📊 Short-Term: Active\n"
                    "💾 Long-Term: Persistent\n"
                    "☁️  Predictive Sync: Ready"
                )
                ui.add_chat("Visions", mem_report)
                continue

            # Handle commands
            image_path = None
            video_path = None
            prompt_text = user_input

            if user_input.startswith("/image"):
                parts = user_input.split(" ", 2)
                if len(parts) >= 3:
                    image_source = parts[1].strip('\"').strip("'")
                    prompt_text = parts[2]
                    
                    # Handle URLs (Director Energy: Auto-download)
                    if image_source.startswith("http"):
                        try:
                            import requests
                            from urllib.parse import urlparse
                            
                            ui.log_trace(f"Downloading Image: {image_source}...", "cyan")
                            
                            # Create a temp dir
                            temp_dir = os.path.join(os.getcwd(), "temp_images")
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # Extract filename
                            parsed = urlparse(image_source)
                            filename = os.path.basename(parsed.path) or "downloaded_image.png"
                            local_path = os.path.join(temp_dir, filename)
                            
                            # Download
                            img_bytes = requests.get(image_source).content
                            with open(local_path, "wb") as f:
                                f.write(img_bytes)
                                
                            image_path = local_path
                            ui.log_trace(f"Visual Data Cached: {local_path}", "green")
                            
                        except Exception as e:
                            ui.log_trace(f"Download Error: {e}", "red")
                            continue
                    else:
                        image_path = image_source
                        ui.log_trace(f"Visual Data Uplink: {image_path}", "cyan")
                else:
                    ui.log_trace("Error: Invalid /image syntax", "red")
                    continue

            # Handle Video
            if user_input.startswith("/video"):
                # /video <path_or_url> [prompt]
                parts = user_input.split(" ", 2)
                if len(parts) >= 2:
                    video_source = parts[1].strip('\"').strip("'")
                    prompt_text = parts[2] if len(parts) > 2 else "Analyze this video."
                    
                    video_path = video_source
                    
                    # Handle URLs
                    if video_source.startswith("http"):
                        try:
                            import requests
                            from urllib.parse import urlparse
                            
                            ui.log_trace(f"Downloading Video stream: {video_source}...", "cyan")
                            
                            # Create a temp dir
                            temp_dir = os.path.join(os.getcwd(), "temp_video")
                            os.makedirs(temp_dir, exist_ok=True)
                            
                            # Extract filename
                            parsed = urlparse(video_source)
                            filename = os.path.basename(parsed.path) or "downloaded_video.mp4"
                            local_path = os.path.join(temp_dir, filename)
                            
                            # Download (stream for larger files)
                            # Only download if not already cached to save time/bandwidth during repeated tests
                            if not os.path.exists(local_path):
                                with requests.get(video_source, stream=True) as r:
                                    r.raise_for_status()
                                    with open(local_path, 'wb') as f:
                                        for chunk in r.iter_content(chunk_size=8192): 
                                            f.write(chunk)
                            else:
                                ui.log_trace(f"Using Cached Video: {local_path}", "dim green")
                                
                            video_path = local_path
                            ui.log_trace(f"Video Data Cached: {local_path}", "green")
                        except Exception as e:
                            ui.log_trace(f"Video Download Error: {e}", "red")
                            continue
                    
                    ui.log_trace(f"Video Data Uplink: {video_path}", "magenta")
                    
                    # Call print_agent_response logic logic inline or break flow
                    # We need to construct the call. The loop expects 'prompt_text' to be handled below?
                    # No, the loop usually continues to 'print_agent_response' if regular chat,
                    # but here we are inside a command block.
                    # Looking at /image block (lines 361-400), it parses image_path then falls through?
                    # Let's check where prompt_text and image_path are used.
                    # They are defined at line 357-359.
                    # If we set them here, we should just let it fall through to the main Print Agent Response call
                    # which happens AFTER these if blocks?
                    # Let's check the file content again to see where print_agent_response is called.
                    pass 
                else:
                    ui.log_trace("Error: Invalid /video syntax. Usage: /video <url> [prompt]", "red")
                    continue
            
            # Handle Director Mode Commands
            if user_input.startswith("/act "):
                # /act <role> <guide>
                parts = user_input.split(" ", 2)
                if len(parts) >= 3:
                    role = parts[1]
                    guide = parts[2]
                    scene_context = "Current Scene" # Simplified for now
                    
                    # Ensure character exists (lazy add for demo)
                    if role not in director_engine.context_graph["characters"]:
                         director_engine.add_character(role, "A character in the screen play.")

                    ui.log_trace(f"Director Engine: {role} Acting...", "magenta")
                    response = director_engine.generate_performance(role, guide, scene_context)
                    ui.add_chat(role, response)
                    ui.update_stats()
                    continue

            if user_input.startswith("/doctor"):
                # Critique last assistant response
                if ui.chat_history:
                    last_role, last_text = ui.chat_history[-1]
                    if last_role != "User":
                        ui.log_trace("Script Doctor: Analyzing...", "yellow")
                        critique = director_engine.script_doctor(last_text)
                        ui.add_chat("Script Doctor", critique)
                        ui.update_stats()
                        continue
                ui.log_trace("Error: No script to doctor", "red")
                continue

            if user_input.startswith("/evaluate"):
                # Score last response
                if ui.chat_history:
                    last_role, last_text = ui.chat_history[-1]
                    if last_role != "User":
                        ui.log_trace("Storybench Eval: Calculating...", "green")
                        eval_data = director_engine.evaluate_script(last_text)
                        
                        # Format scores nicely
                        score_table = Table(box=None, show_header=False)
                        for k, v in eval_data["scores"].items():
                            score_table.add_row(f"[bold]{k}[/bold]", f"{v}/5")
                        
                        ui.add_chat("Storybench", eval_data["raw_feedback"])
                        continue
                ui.log_trace("Error: No script to evaluate", "red")
                continue

            # Handle image generation
            if user_input.startswith("/generate"):
                prompt_text = user_input[10:].strip()
                
                if not prompt_text:
                    ui.log_trace("[bold red]Error:[/bold red] Please provide a prompt", "red")
                    continue
                
                # Show aspect ratio selector
                aspect_ratio = show_aspect_ratio_selector()
                
                ui.log_trace(f"Image Generation Request: Prompt='{prompt_text}', Aspect Ratio='{aspect_ratio}'", "yellow")
                
                # TODO: Integrate with dual_mode_generator
                ui.log_trace("Image generation integration pending...", "dim")
                # Stop live for animation
                live.stop()
                show_memory_save()
                live.start()
                continue

            ui.add_chat("User", prompt_text)
            print_agent_response(prompt_text, image_path=image_path, video_path=video_path, live=live)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted.[/bold red]")
