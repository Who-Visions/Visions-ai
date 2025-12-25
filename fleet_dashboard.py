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
from rich.columns import Columns
from tools.agent_connect import AgentConnector

console = Console()

class Header:
    """Display header with clock and title."""
    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        grid.add_row(
            "[b]VISIONS[/b] FLEET",
            "[bold magenta]Aether Command Center[/]",
            datetime.now().ctime(),
        )
        return Panel(grid, style="bold cyan")

class FleetMetrics:
    """Display real-time system metrics."""
    def __rich__(self) -> Panel:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        metrics_text = Text.assemble(
            ("CPU: ", "bold white"), (f"{cpu}%", "bold green" if cpu < 70 else "bold red"),
            "  ",
            ("RAM: ", "bold white"), (f"{ram}%", "bold green" if ram < 80 else "bold red"),
            "  ",
            ("NET: ", "bold white"), ("OPTIMAL", "bold green")
        )
        return Panel(Align.center(metrics_text), title="System Health", border_style="dim")

class EventLog:
    """A scrolling log of fleet events."""
    def __init__(self):
        self.logs = []

    def add_log(self, message: str, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = "green" if "ONLINE" in message else "yellow" if "ISSUE" in message else "cyan"
        if "OFFLINE" in message: color = "red"
        self.logs.append(f"[{timestamp}] [[bold {color}]{level}[/]] {message}")
        if len(self.logs) > 10:
            self.logs.pop(0)

    def __rich__(self) -> Panel:
        log_content = "\n".join(self.logs) if self.logs else "No events recorded..."
        return Panel(log_content, title="Live Event Feed", border_style="blue")

class FleetDashboard:
    def __init__(self):
        self.connector = AgentConnector()
        self.agents = self.connector.AGENTS
        self.statuses = {name: {"status": "📡 PENDING", "latency": "--", "response": "--"} for name in self.agents}
        self.event_log = EventLog()
        self.last_update = "---"

    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )
        layout["main"].split_row(
            Layout(name="body", ratio=3),
            Layout(name="side", ratio=1),
        )
        return layout

    def check_agent(self, agent_key):
        start_time = time.time()
        try:
            response = self.connector.talk_to_agent(agent_key, "Ping")
            latency = f"{(time.time() - start_time):.2f}s"
            
            if "Error" in response or "❌" in response:
                status_str = "[bold yellow]⚠️ ISSUE[/]"
                msg = f"{agent_key.upper()} encountered an issue."
            else:
                status_str = "[bold green]🟢 ONLINE[/]"
                msg = f"{agent_key.upper()} is active."
            
            # Simple check if status changed
            old_status = self.statuses.get(agent_key, {}).get("status")
            if old_status and old_status != status_str:
                self.event_log.add_log(msg, "FLEET")

            return agent_key, {"status": status_str, "latency": latency, "response": response[:60] + "..."}
        except Exception as e:
            latency = f"{(time.time() - start_time):.2f}s"
            status_str = "[bold red]🔴 OFFLINE[/]"
            self.event_log.add_log(f"{agent_key.upper()} went offline.", "CRITICAL")
            return agent_key, {"status": status_str, "latency": latency, "response": str(e)[:60]}

    def update_all_statuses(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            future_to_agent = {executor.submit(self.check_agent, name): name for name in self.agents}
            for future in concurrent.futures.as_completed(future_to_agent):
                name, result = future.result()
                self.statuses[name] = result
        self.last_update = datetime.now().strftime("%H:%M:%S")

    def generate_table(self) -> Table:
        table = Table(expand=True, box=None)
        table.add_column("Agent ID", style="bold cyan", ratio=1)
        table.add_column("Status", justify="center", ratio=1)
        table.add_column("Latency", justify="right", style="dim", ratio=1)
        table.add_column("Signal Data", style="italic", ratio=3)

        sorted_agents = sorted(self.statuses.items(), key=lambda x: (x[1]["status"], x[0]))
        for name, info in sorted_agents:
            table.add_row(name.upper(), info["status"], info["latency"], info["response"])
        
        return table

    def run(self):
        layout = self.make_layout()
        layout["header"].update(Header())
        layout["footer"].update(FleetMetrics())
        layout["side"].update(Panel(self.event_log, title="Events"))
        
        self.event_log.add_log("Aether Link established.", "SYS")
        self.event_log.add_log("Syncing with 10 agents...", "SYS")

        with Live(layout, refresh_per_second=4, screen=True) as live:
            while True:
                # Update Header/Footer time and metrics
                layout["header"].update(Header())
                layout["footer"].update(FleetMetrics())
                
                # Update Table
                self.update_all_statuses()
                layout["body"].update(Panel(self.generate_table(), title="Active Fleet", border_style="cyan"))
                layout["side"].update(self.event_log)
                
                time.sleep(15) 

if __name__ == "__main__":
    dash = FleetDashboard()
    try:
        dash.run()
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Signal lost. Closing gateway... 🫡[/]")
