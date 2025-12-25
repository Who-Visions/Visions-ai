import time
import concurrent.futures
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from tools.agent_connect import AgentConnector

console = Console()

class FleetDashboard:
    def __init__(self):
        self.connector = AgentConnector()
        self.agents = self.connector.AGENTS
        self.statuses = {name: {"status": "📡 PENDING", "latency": "--", "response": "--"} for name in self.agents}
        self.last_update = "Never"

    def check_agent(self, agent_key):
        start_time = time.time()
        try:
            # Use a quick ping message
            response = self.connector.talk_to_agent(agent_key, "Ping")
            latency = f"{(time.time() - start_time):.2f}s"
            
            if "Error" in response or "❌" in response:
                return agent_key, {"status": "[bold yellow]⚠️ ISSUE[/]", "latency": latency, "response": response[:50] + "..."}
            else:
                return agent_key, {"status": "[bold green]🟢 ONLINE[/]", "latency": latency, "response": response[:50] + "..."}
        except Exception as e:
            latency = f"{(time.time() - start_time):.2f}s"
            return agent_key, {"status": "[bold red]🔴 OFFLINE[/]", "latency": latency, "response": str(e)[:50]}

    def update_all_statuses(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            future_to_agent = {executor.submit(self.check_agent, name): name for name in self.agents}
            for future in concurrent.futures.as_completed(future_to_agent):
                name, result = future.result()
                self.statuses[name] = result
        self.last_update = datetime.now().strftime("%H:%M:%S")

    def generate_table(self) -> Table:
        table = Table(title=f"Visions Fleet Dashboard | Last Update: {self.last_update}", title_style="bold magenta")
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Latency", justify="right", style="dim")
        table.add_column("Last Response", style="white")

        # Sort by status (Green first) then name
        sorted_agents = sorted(self.statuses.items(), key=lambda x: (x[1]["status"], x[0]))
        
        for name, info in sorted_agents:
            table.add_row(name.upper(), info["status"], info["latency"], info["response"])
        
        return table

    def run(self):
        console.clear()
        with Live(self.generate_table(), refresh_per_second=1, console=console) as live:
            while True:
                self.update_all_statuses()
                live.update(self.generate_table())
                time.sleep(30) # Refresh every 30 seconds

if __name__ == "__main__":
    dash = FleetDashboard()
    try:
        dash.run()
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Dashboard closed. Stay frosty. 🫡[/]")
