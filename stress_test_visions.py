import time
import sys
import collections
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich import box
from datetime import datetime

from visions_director_engine import DirectorEngine
from visions_assistant.agent import get_chat_response

# Data Structures
results = collections.defaultdict(lambda: {"success": 0, "fail": 0, "429": 0, "latencies": []})
test_logs = collections.deque(maxlen=8)
current_run = 0
total_runs = 20

def log_event(message, style="white"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    test_logs.append(f"[{timestamp}] [{style}]{message}[/{style}]")

def generate_dashboard():
    # 1. Main Table
    table = Table(title=f"Visions AI Stress Test ({current_run}/{total_runs})", box=box.ROUNDED, expand=True)
    table.add_column("Test Case", style="cyan", no_wrap=True)
    table.add_column("Success", justify="center", style="green")
    table.add_column("Fail", justify="center", style="bold red")
    table.add_column("429 (Rate Limit)", justify="center", style="yellow")
    table.add_column("Avg Latency", justify="right", style="magenta")
    table.add_column("Last Status", justify="left")

    for test_name, data in results.items():
        avg_lat = 0
        if data["latencies"]:
            avg_lat = sum(data["latencies"]) / len(data["latencies"])
        
        status_icon = "⚪"
        if data.get("last_result") == "success": status_icon = "🟢"
        elif data.get("last_result") == "fail": status_icon = "🔴"
        elif data.get("last_result") == "429": status_icon = "⚠️"
        
        table.add_row(
            test_name,
            str(data["success"]),
            str(data["fail"]),
            str(data["429"]),
            f"{avg_lat:.2f}s",
            status_icon
        )

    # 2. Log Panel
    log_content = "\n".join(test_logs)
    log_panel = Panel(log_content, title="Live Logs", border_style="dim", height=12)

    # Layout
    layout = Layout()
    layout.split_column(
        Layout(table, name="upper"),
        Layout(log_panel, name="lower")
    )
    return layout

def safe_execution_visual(test_name, func, *args, **kwargs):
    """
    Executes a function with visual updates and 429 handling.
    """
    global results
    try:
        start_time = time.time()
        log_event(f"Running {test_name}...", "dim")
        
        # Execute
        result = func(*args, **kwargs)
        
        duration = time.time() - start_time
        
        # Check simulated 429 in string
        if isinstance(result, str) and "429" in result:
             raise Exception("Simulated 429 detection in response string")

        results[test_name]["success"] += 1
        results[test_name]["latencies"].append(duration)
        results[test_name]["last_result"] = "success"
        log_event(f"{test_name} Completed ({duration:.2f}s)", "green")
        return result

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
            results[test_name]["429"] += 1
            results[test_name]["last_result"] = "429"
            log_event(f"⚠️ 429 Limit Hit: {test_name}", "yellow")
            
            # Backoff
            log_event("⏳ Cooling down for 45s...", "bold yellow")
            # We can't update while sleeping in this simple linear script, 
            # but usually time.sleep blocks.
            # To keep UI alive we'd need async, but let's just sleep.
            # The Live context might freeze but will refresh after.
            time.sleep(45) 
            
            # Retry
            try:
                log_event(f"🔄 Retrying {test_name}...", "cyan")
                start_retry = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_retry
                
                results[test_name]["success"] += 1
                results[test_name]["latencies"].append(duration)
                results[test_name]["last_result"] = "success"
                log_event(f"{test_name} Retry Success", "green")
                return result
            except Exception as retry_e:
                results[test_name]["fail"] += 1
                results[test_name]["last_result"] = "fail"
                log_event(f"❌ Retry Failed: {retry_e}", "red")
                return None
        else:
            results[test_name]["fail"] += 1
            results[test_name]["last_result"] = "fail"
            log_event(f"❌ Error {test_name}: {e}", "red")
            return None

def main():
    global current_run
    console = Console()
    
    # Initialize Engine
    log_event("Initializing DirectorEngine (Gemini 3 Pro)...", "magenta")
    director = DirectorEngine(lambda p, c=None: get_chat_response(p, config=c))
    
    with Live(generate_dashboard(), refresh_per_second=4, console=console) as live:
        for i in range(1, total_runs + 1):
            current_run = i
            live.update(generate_dashboard())
            
            log_event(f"--- Starting Run {i} ---", "bold white")
            
            # 1. Chat
            safe_execution_visual(
                "Chat (Baseline)", 
                get_chat_response, 
                "Identify yourself.",
                user_id=f"stress_user_{i}" # Unique user per run to avoid context bloat if desired, or same?
            )
            live.update(generate_dashboard())

            # 2. Act
            safe_execution_visual(
                "/act (Method Acting)",
                director.generate_performance,
                "Detective Stone", 
                "Interrogate suspect.", 
                "Interrogation Room"
            )
            live.update(generate_dashboard())

            # 3. Doctor
            safe_execution_visual(
                "/doctor (Script Doctor)",
                director.script_doctor,
                "INT. ROOM - DAY\nJOHN: Hi.\nMARY: Bye."
            )
            live.update(generate_dashboard())

            # 4. Evaluate
            safe_execution_visual(
                "/evaluate (Storybench)",
                director.evaluate_script,
                "INT. ROOM - DAY\nJOHN: Hi.\nMARY: Bye."
            )
            live.update(generate_dashboard())
            
            # 5. Constraints
            safe_execution_visual(
                "/check_constraints",
                director.check_constraints,
                "A story about a watch."
            )
            live.update(generate_dashboard())

            # 6. World
            safe_execution_visual(
                "/generate_world",
                director.generate_world_element,
                "Cyberpunk Shop", "Neon lights"
            )
            live.update(generate_dashboard())

            # 7. Novel
            safe_execution_visual(
                "/write_chapter (GPTAuthor)",
                director.write_novel_chapter,
                "Chapter 1: The End."
            )
            live.update(generate_dashboard())
            
            # Buffer
            time.sleep(1)

        log_event("🎉 Stress Test Complete!", "bold green")
        live.update(generate_dashboard())
        # Keep alive for a moment
        time.sleep(5)

if __name__ == "__main__":
    main()
