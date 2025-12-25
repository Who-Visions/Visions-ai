"""Quick visual demo of the new CLI"""
from cli_visual import *

print("\n" + "="*80)
print("VISIONS AI - VISUAL DEMO")
print("="*80 + "\n")

# Show header
console.print(create_visual_header())
time.sleep(1)

# Show boot
console.print(f"\n{EMOJI['rocket']} [bold cyan]Booting...[/bold cyan]\n")
create_boot_visuals()
time.sleep(0.5)

# Show aspect ratios
console.print(create_aspect_ratio_table())
time.sleep(0.5)

# Show stats
console.print(create_stats_panel())
time.sleep(0.5)

# Show memory animation
console.print(f"\n{EMOJI['brain']} [bold]Memory Save Demo:[/bold]\n")
create_memory_animation()

console.print(f"\n{EMOJI['sparkles']} [bold green]Visual demo complete![/bold green] {EMOJI['sparkles']}\n")
