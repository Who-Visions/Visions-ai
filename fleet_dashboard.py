import time
import psutil
import concurrent.futures
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.style import Style
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.markdown import Markdown
from tools.agent_connect import AgentConnector

console = Console()

# --- THEMES & EMOJIS ---
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

MISSION_MD = """
# 🛰️ MISSION: FLEET SYNC
**Status**: ACTIVE
**Objective**: Maintain 10/10 Node Integrity
**Protocol**: Aether-X-4
"""

class Header:
    """Animated Header with pulsing title."""
    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        # Pulsing color logic (simulated by time)
        colors = ["cyan", "bright_blue", "magenta", "bright_cyan"]
        color = colors[int(time.time()) % len(colors)]
        
        title = Text.assemble(
            (" 🛰️  ", "white"),
            ("VISIONS", f"bold {color} underline"),
            (" | ", "dim white"),
            ("AETHER COMMAND", "bold white"),
            (" ⚡ ", "bold yellow")
        )
        
        grid.add_row(
            "[dim]V_PRO_RECON[/]",
            title,
            f"[bold blue]{datetime.now().strftime('%H:%M:%S')}[/]",
        )
        return Panel(grid, style="bold blue", border_style="bright_blue")

class SystemHealth:
    """Animated system metrics."""
    def __rich__(self) -> Panel:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        
        def get_pulse(val):
            if val < 50: return "green"
            if val < 80: return "yellow"
            return "red"

        status_bar = "▆ " * 10
        cpu_pulse = f"[{get_pulse(cpu)}]{status_bar[:int(cpu/10)*2]}[/][dim]{status_bar[int(cpu/10)*2:][/]"
        ram_pulse = f"[{get_pulse(ram)}]{status_bar[:int(ram/10)*2]}[/][dim]{status_bar[int(ram/10)*2:][/]"

        content = Columns([
            Text.assemble(("  CPU ", "bold"), (f"{cpu}% ", f"bold {get_pulse(cpu)}"), cpu_pulse),
            Text.assemble(("  RAM ", "bold"), (f"{ram}% ", f"bold {get_pulse(ram)}"), ram_pulse),
            Text.assemble(("  LINK ", "bold"), ("STABLE ⚡", "bold green"))
        ], expand=True)

        return Panel(content, title="[bold white]CORE TELEMETRY[/]", border_style="dim")

class EventLog:
    """Scrolling mission log with icons."""
    def __init__(self):
        self.logs = []

    def add_log(self, message: str, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = "📡"
        if "ONLINE" in message: icon = "✅"
        elif "OFFLINE" in message: icon = "❌"
        elif "ISSUE" in message: icon = "⚠️"
        elif "SYS" in level: icon = "⚙️"
        
        color = "green" if "ONLINE" in message else "red" if "OFFLINE" in message else "cyan"
        self.logs.append(f"[dim]{timestamp}[/] {icon} [bold {color}]{message}[/]")
        if len(self.logs) > 10:
            self.logs.pop(0)

    def __rich__(self) -> Panel:
        return Panel("\n".join(self.logs) or "[dim]Waiting for signal...[/]", title="[bold cyan]MISSION LOG[/]", border_style="blue")

class FleetDashboard:
    def __init__(self):
        self.connector = AgentConnector()
        self.agents = self.connector.AGENTS
        self.data = {name: {"status": "📡 SCANNING", "latency": "--", "response": "--", "online": True} for name in self.agents}
        self.log = EventLog()
        self.spinner = Spinner("dots", text="Scanning Fleet...")

    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="upper", ratio=1),
            Layout(name="lower", size=15),
        )
        layout["upper"].split_row(
            Layout(name="brief", size=30),
            Layout(name="nodes", ratio=1),
        )
        layout["lower"].split_row(
            Layout(name="logs", ratio=2),
            Layout(name="system", ratio=1),
        )
        return layout

    def scan_agent(self, name):
        start = time.time()
        try:
            res = self.connector.talk_to_agent(name, "Dashboard Sync Pulse")
            lat = f"{(time.time() - start):.2f}s"
            
            is_err = "Error" in res or "❌" in res
            status = "[bold yellow]⚠️ ISSUE[/]" if is_err else "[bold green]🟢 ONLINE[/]"
            
            if self.data[name]["status"] != status:
                self.log.add_log(f"{name.upper()} { 'LINK STABILIZED' if not is_err else 'SIGNAL DRIFT'}")
            
            self.data[name] = {"status": status, "latency": lat, "response": res[:80], "online": not is_err}
        except Exception as e:
            lat = f"{(time.time() - start):.2f}s"
            if self.data[name]["online"]:
                self.log.add_log(f"{name.upper()} SIGNAL LOST", "CRITICAL")
            self.data[name] = {"status": "[bold red]🔴 OFFLINE[/]", "latency": lat, "response": str(e)[:80], "online": False}

    def update_fleet(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as exe:
            exe.map(self.scan_agent, self.agents.keys())

    def get_node_table(self) -> Table:
        table = Table(expand=True, box=None, show_edge=False)
        table.add_column("NODE", ratio=1)
        table.add_column("STRENGTH", ratio=1, justify="center")
        table.add_column("LATENCY", ratio=1, justify="right")
        table.add_column("DATA STREAM", ratio=3)

        for name in sorted(self.agents.keys()):
            info = self.data[name]
            icon = AGENT_ICONS.get(name, "🛰️")
            table.add_row(
                f"{icon} [bold cyan]{name.upper()}[/]",
                info["status"],
                f"[dim]{info['latency']}[/]",
                f"[italic]{info['response']}[/]"
            )
        return table

    def run(self):
        layout = self.make_layout()
        self.log.add_log("Aether OS Bootstrap Complete.", "SYS")
        self.log.add_log("Listening for fleet signals...", "SYS")

        with Live(layout, screen=True, refresh_per_second=4) as live:
            last_sync = 0
            while True:
                # 1. Update Layout Static Components
                layout["header"].update(Header())
                layout["brief"].update(Panel(Markdown(MISSION_MD), border_style="dim"))
                layout["system"].update(SystemHealth())
                layout["logs"].update(self.log)
                
                # 2. Sync Logic
                now = time.time()
                if now - last_sync > 15:
                    self.log.add_log("Broadcasting Sync Packet...")
                    self.update_fleet()
                    last_sync = now
                
                # 3. Update Dynamic Node View
                layout["nodes"].update(Panel(
                    self.get_node_table(),
                    title="[bold blue]🛰️ GLOBAL NODE MESH[/]",
                    border_style="bright_blue",
                    subtitle=f"[dim]Next Sync in {int(15 - (now - last_sync))}s[/]"
                ))
                
                time.sleep(0.25)

if __name__ == "__main__":
    try:
        FleetDashboard().run()
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Signal Termination Sequence Initiated. Goodbye, Operator. 🫡[/]")
