import time
import psutil
import concurrent.futures
import json
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.console import Console, Group
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.tree import Tree
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.markdown import Markdown
from rich.columns import Columns
from rich.padding import Padding
from rich.rule import Rule
from rich.highlighter import RegexHighlighter
from rich.theme import Theme
from rich.traceback import install
from tools.agent_connect import AgentConnector

# Install rich traceback for the Aether experience
install(show_locals=True)

# --- THEMES & HIGHLIGHTING ---
class AetherHighlighter(RegexHighlighter):
    """Cinematic highlighting for mission-critical Aether signals."""
    base_style = "aether."
    highlights = [
        r"(?P<online>ONLINE|VERIFIED|STABLE|ACTIVE|READY|🟢)",
        r"(?P<offline>OFFLINE|LOST|ERROR|CRITICAL|🔴|❌)",
        r"(?P<sync>SYNCING|BROADCASTING|SIGNAL|MESH|UPLINK|🛰️|⚡)",
        r"(?P<agent>[A-Z0-9_]{5,})",
    ]

aether_theme = Theme({
    "aether.online": "bold green",
    "aether.offline": "bold red",
    "aether.sync": "italic bright_blue",
    "aether.agent": "bold cyan",
})

console = Console(theme=aether_theme)
highlighter = AetherHighlighter()

# --- CONTENT ---
MISSION_MD = """
# 🛰️ MISSION: AETHER_SYNC
**STATUS**: [bold green]ACTIVE[/]
**NODES**: 10 Detected
**PROTOCOL**: Aether-X-4.5
**OBJECTIVE**: 100% Mesh Stability
"""

AGENT_ICONS = {
    "visions_cloud": "☁️",
    "kaedra": "🛡️",
    "bandit": "🥷",
    "kam": "🧠",
    "yuki": "❄️",
    "dav1d": "👤",
    "rhea": "⚖️",
    "unk": "❓",
    "iris": "👁️",
    "kronos": "⏳"
}

# --- UI COMPONENTS ---
class AetherHeader:
    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        # Pulsing color logic
        pulse = ["cyan", "magenta", "bright_blue", "white"][int(time.time() * 2) % 4]
        
        title = Text.assemble(
            (" 🛰️  ", pulse),
            ("AETHER COMMAND CENTER", f"bold {pulse} underline"),
            (" | ", "dim white"),
            ("FLEET_SYNC_v2.5", "bold white")
        )
        
        grid.add_row(
            "[dim]OP_RECON_ALPHA[/]",
            title,
            f"[bold blue]{datetime.now().strftime('%H:%M:%S')}[/]"
        )
        return Panel(grid, style="bold blue", border_style="bright_blue")

class FleetTopology:
    """Hierarchical Node Mesh Visualization."""
    def __rich__(self) -> Panel:
        tree = Tree("🌐 [bold cyan]AETHER MESH[/]", guide_style="bold blue")
        
        # Core Infrastructure
        core = tree.add("🧠 [bold]CORE LAYER[/]", guide_style="cyan")
        core.add("☁️ [cyan]VISIONS_CLOUD[/] (HOST)")
        core.add("🧠 [cyan]KAM[/] (MEM_CORE)")
        
        # Field Assets
        field = tree.add("🛰️ [bold]FIELD LAYER[/]", guide_style="magenta")
        for agent in ["yuki", "dav1d", "bandit", "kaedra", "iris"]:
            icon = AGENT_ICONS.get(agent, "🕵️")
            field.add(f"{icon} [magenta]{agent.upper()}[/]")
            
        # Support/Analytic Assets
        support = tree.add("🛠️ [bold]SUPPORT LAYER[/]", guide_style="yellow")
        for agent in ["rhea", "unk", "kronos"]:
            icon = AGENT_ICONS.get(agent, "⚙️")
            support.add(f"{icon} [yellow]{agent.upper()}[/]")
            
        return Panel(tree, title="[bold white]TOPOLOGY[/]", border_style="cyan")

class SystemTelemetry:
    """Animated telemetry bars."""
    def __rich__(self) -> Panel:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        def pulse_bar(val, color):
            bar_len = int(val / 10)
            return f"[{color}]{'█' * bar_len}[/][dim]{'░' * (10 - bar_len)}[/]"

        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        grid.add_row(
            f" 🎨 CPU: {pulse_bar(cpu, 'green' if cpu < 70 else 'red')} [b]{cpu}%[/]",
            f" 🧩 RAM: {pulse_bar(ram, 'blue' if ram < 80 else 'red')} [b]{ram}%[/]"
        )
        return Panel(grid, title="[bold white]⚛️ TELEMETRY[/]", border_style="dim")

class SignalLog:
    """Highlighted mission signal feed."""
    def __init__(self):
        self.messages = []

    def log(self, text, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        color = "green" if "ONLINE" in text else "red" if "OFFLINE" in text else "blue"
        # Apply Regex Highlighter manually to the text
        styled_text = highlighter(text)
        self.messages.append(f"[dim]{ts}[/] [[bold {color}]{level}[/]] {styled_text}")
        if len(self.messages) > 10: self.messages.pop(0)

    def __rich__(self) -> Panel:
        # Use Padding and Rules for log structure
        log_group = []
        for i, msg in enumerate(self.messages):
            log_group.append(Text.from_markup(m))
            if i < len(self.messages) - 1:
                log_group.append(Rule(style="dim blue"))
        
        content = Group(*[Text.from_markup(m) for m in self.messages]) if self.messages else Text("Awaiting signal sync...", style="dim")
        return Panel(Padding(content, (0, 1)), title="[bold blue]🛰️ SIGNAL LOG[/]", border_style="blue")

# --- MAIN DASHBOARD ENGINE ---
class AetherDashboard:
    def __init__(self):
        self.connector = AgentConnector()
        self.agents = self.connector.AGENTS
        # High-fidelity status tracking
        self.nodes = {name: {"status": "📡 SYNCING", "lat": "--", "data": {}, "raw": ""} for name in self.agents}
        self.signal_log = SignalLog()
        self.last_sync = 0

    def sync_fleet(self):
        self.signal_log.log("BROADCASTING SYNC PACKET...", "SYS")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as exe:
            list(exe.map(self.probe_node, self.agents.keys()))
        self.signal_log.log("MESH STABILIZED. 10 NODES SYNCED.", "SYS")

    def probe_node(self, name):
        start = time.time()
        try:
            res = self.connector.talk_to_agent(name, "Aether-Pulse-X")
            lat = f"{(time.time() - start):.2f}s"
            is_err = "Error" in res or "❌" in res
            
            # Data stream preparation for Syntax
            try:
                # Try to clean/parse as JSON for the high-fidelity effect
                json_data = json.loads(res)
            except:
                json_data = {"raw": res[:100]}

            status = "🟢 ONLINE" if not is_err else "⚠️ ISSUE"
            if self.nodes[name]["status"] != status:
                self.signal_log.log(f"{name.upper()} LINK {'VERIFIED' if not is_err else 'INTERFERENCE'}", "FLEET")
            
            self.nodes[name] = {"status": status, "lat": lat, "data": json_data, "raw": res}
        except Exception as e:
            self.signal_log.log(f"{name.upper()} SIGNAL LOST", "CRITICAL")
            self.nodes[name] = {"status": "🔴 OFFLINE", "lat": "--", "data": {"error": str(e)}, "raw": str(e)}

    def build_node_mesh(self) -> Table:
        table = Table(expand=True, box=None, show_edge=False)
        table.add_column("NODE ID", style="bold cyan")
        table.add_column("STATUS", justify="center")
        table.add_column("LATENCY", justify="right")
        table.add_column("DATA STREAM (SYNTAX)", ratio=3)

        for name in sorted(self.agents.keys()):
            node = self.nodes[name]
            # Use Syntax highlighting for the data stream
            data_str = json.dumps(node["data"], indent=1)
            syntax_view = Syntax(data_str, "json", theme="monokai", background_color="default", word_wrap=True)
            
            table.add_row(
                name.upper(),
                node["status"],
                f"[dim]{node['lat']}[/]",
                syntax_view
            )
        return table

    def run(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=7)
        )
        layout["body"].split_row(
            Layout(name="left", size=35),
            Layout(name="right", ratio=1)
        )
        layout["left"].split_column(
            Layout(name="brief", ratio=1),
            Layout(name="topo", ratio=2)
        )
        layout["footer"].split_row(
            Layout(name="logs", ratio=2),
            Layout(name="telemetry", ratio=1)
        )

        self.signal_log.log("AETHER_OS_v2.5 BOOTSTRAP COMPLETE.", "SYS")
        
        with Live(layout, screen=True, refresh_per_second=4) as live:
            while True:
                now = time.time()
                
                # 1. Update Static Components
                layout["header"].update(AetherHeader())
                layout["brief"].update(Panel(Markdown(MISSION_MD), border_style="dim"))
                layout["topo"].update(FleetTopology())
                layout["telemetry"].update(SystemTelemetry())
                layout["logs"].update(self.signal_log)
                
                # 2. Periodic Fleet Sync (every 20s)
                if now - self.last_sync > 20:
                    self.sync_fleet()
                    self.last_sync = now
                
                # 3. Dynamic Mesh Update
                layout["right"].update(Panel(
                    self.build_node_mesh(),
                    title="[bold blue]🛰️ GLOBAL NODE MESH[/]",
                    border_style="bright_blue",
                    subtitle=f"[dim]Next Sync Sequence in {int(20 - (now - self.last_sync))}s[/]"
                ))
                
                time.sleep(0.25)

if __name__ == "__main__":
    try:
        AetherDashboard().run()
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Signal Lost. Leaving Aether Mesh... 🫡[/]")
