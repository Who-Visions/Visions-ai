from rich import print
from rich.console import Console
from fleet_dashboard import AetherHeader, FleetTopology, SystemTelemetry, AetherDashboard, AGENT_ICONS

console = Console()

def test_components():
    print("[bold]Testing AetherHeader...[/bold]")
    try:
        header = AetherHeader()
        print(header)
        print("[green]OK[/green]")
    except Exception as e:
        print(f"[red]FAIL: {e}[/red]")

    print("\n[bold]Testing FleetTopology...[/bold]")
    try:
        topo = FleetTopology()
        print(topo)
        print("[green]OK[/green]")
    except Exception as e:
        print(f"[red]FAIL: {e}[/red]")

    print("\n[bold]Testing SystemTelemetry...[/bold]")
    try:
        telemetry = SystemTelemetry()
        print(telemetry)
        print("[green]OK[/green]")
    except Exception as e:
        print(f"[red]FAIL: {e}[/red]")

if __name__ == "__main__":
    test_components()
