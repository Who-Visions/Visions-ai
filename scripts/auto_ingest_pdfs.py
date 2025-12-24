#!/usr/bin/env python3
"""
Auto-Ingestor: Watches a folder for new PDFs and ingests them into Visions' knowledge base.
Runs every 10 minutes to continuously "teach" Visions new screenwriting knowledge.

Features:
- Rich Live CLI with beautiful progress display
- Uses Gemini 3 Flash NATIVE PDF reading (no extraction needed!)
- Failsafe error handling (no crashes, errors logged to file)
- 429 Rate limit respect with exponential backoff
- Automatic vector store rebuild

Usage:
    python scripts/auto_ingest_pdfs.py
    or
    run_ingestor.bat
"""

import os
import sys
import time
import json
import hashlib
import base64
from datetime import datetime
from pathlib import Path

# Suppress all warnings and info logs
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Configuration
WATCH_FOLDER = r"C:\Users\super\Watchtower\HQ_WhoArt\pdfs"
KNOWLEDGE_BASE_FILE = r"C:\Users\super\Watchtower\HQ_WhoArt\Visions-ai\knowledge_base\writing_masterclass.txt"
PROCESSED_LOG = r"C:\Users\super\Watchtower\HQ_WhoArt\Visions-ai\knowledge_base\processed_pdfs.json"
ERROR_LOG = r"C:\Users\super\Watchtower\HQ_WhoArt\Visions-ai\knowledge_base\ingestor_errors.log"
BUILD_INDEX_SCRIPT = r"C:\Users\super\Watchtower\HQ_WhoArt\Visions-ai\build_index.py"
POLL_INTERVAL_SECONDS = 600  # 10 minutes

# Gemini Configuration - Using native PDF reading!
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "global"
MODEL_ID = "gemini-2.0-flash"  # Flash handles PDFs natively and fast

# Rate limiting
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 30

# Console
console = Console() if RICH_AVAILABLE else None

# Prompt for extracting insights
EXTRACTION_PROMPT = """You are Visions, a master screenwriting and creative writing teacher. 
Analyze this PDF and extract the KEY INSIGHTS in a structured format.

Output format (use this EXACTLY):
--------------------------------------------------------------------------------

TITLE: [Book/Document Title from the PDF]
AUTHOR: [Author Name from the PDF]
SOURCE: PDF Masterclass ([Brief 2-3 word description])
KEY_INSIGHTS:
- **[Concept Name]**: [1-2 sentence explanation]
- **[Concept Name]**: [1-2 sentence explanation]
(Continue for 5-10 key concepts - focus on the MOST IMPORTANT teachings)

TRANSCRIPT EXCERPT:
[2-4 of the most impactful quotes directly from the text, each on its own line]

Be concise but capture the ESSENTIAL teachings. Focus on:
- Structure concepts (3-act, sequences, beats)
- Character development techniques
- Dialogue and scene craft
- Visual storytelling principles
- Any unique frameworks or methods this author introduces"""


class IngestorState:
    """Track the state of the ingestor for live display."""
    def __init__(self):
        self.status = "Initializing..."
        self.current_file = None
        self.files_processed = 0
        self.files_pending = 0
        self.last_scan = None
        self.next_scan = None
        self.errors_count = 0
        self.recent_ingestions = []


STATE = IngestorState()


def log_error(message: str):
    """Log errors to file silently."""
    try:
        STATE.errors_count += 1
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(ERROR_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass


def get_file_hash(filepath: str) -> str:
    """Generate a hash of the file for tracking."""
    try:
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception as e:
        log_error(f"Hash error for {filepath}: {e}")
        return ""


def load_processed_log() -> dict:
    """Load the log of already-processed files."""
    try:
        if os.path.exists(PROCESSED_LOG):
            with open(PROCESSED_LOG, 'r') as f:
                return json.load(f)
    except Exception as e:
        log_error(f"Load processed log error: {e}")
    return {}


def save_processed_log(log: dict):
    """Save the processed files log."""
    try:
        with open(PROCESSED_LOG, 'w') as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        log_error(f"Save processed log error: {e}")


def synthesize_with_native_pdf(filepath: str, filename: str) -> str:
    """Use Gemini's NATIVE PDF reading capability - no extraction needed!"""
    for attempt in range(MAX_RETRIES):
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(
                vertexai=True,
                project=PROJECT_ID,
                location=LOCATION
            )
            
            # Read PDF as bytes and send directly to Gemini
            with open(filepath, 'rb') as f:
                pdf_bytes = f.read()
            
            # Gemini can handle PDFs up to 100MB natively
            # For very large PDFs, we truncate to 20MB
            MAX_PDF_SIZE = 20 * 1024 * 1024  # 20MB
            if len(pdf_bytes) > MAX_PDF_SIZE:
                log_error(f"PDF too large ({len(pdf_bytes) / 1024 / 1024:.1f}MB), truncating: {filename}")
                pdf_bytes = pdf_bytes[:MAX_PDF_SIZE]
            
            # Create the PDF part for multimodal input
            pdf_part = types.Part.from_bytes(
                data=pdf_bytes,
                mime_type="application/pdf"
            )
            
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    EXTRACTION_PROMPT,
                    pdf_part
                ],
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2500
                )
            )
            
            return response.text.strip() if response.text else ""
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for rate limit (429)
            if "429" in error_str or "rate" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                backoff = BASE_BACKOFF_SECONDS * (2 ** attempt)
                STATE.status = f"Rate limited. Waiting {backoff}s..."
                log_error(f"Rate limit hit for {filename}, backing off {backoff}s")
                time.sleep(backoff)
                continue
            
            log_error(f"Native PDF error for {filename}: {e}")
            break
    
    return ""


def append_to_knowledge_base(insights: str):
    """Append the synthesized insights to the knowledge base file."""
    try:
        with open(KNOWLEDGE_BASE_FILE, 'a', encoding='utf-8') as f:
            f.write("\n\n" + insights)
    except Exception as e:
        log_error(f"Append to knowledge base error: {e}")


def rebuild_vector_store():
    """Run the build_index.py script to rebuild the vector store."""
    try:
        STATE.status = "Rebuilding vector store..."
        import subprocess
        result = subprocess.run(
            [sys.executable, BUILD_INDEX_SCRIPT],
            cwd=str(Path(BUILD_INDEX_SCRIPT).parent),
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0
    except Exception as e:
        log_error(f"Vector store rebuild error: {e}")
        return False


def build_dashboard() -> Panel:
    """Build the Rich dashboard panel."""
    if not RICH_AVAILABLE:
        return None
    
    table = Table(box=box.ROUNDED, show_header=False, expand=True)
    table.add_column("Key", style="cyan", width=20)
    table.add_column("Value", style="white")
    
    table.add_row("Status", f"[bold green]{STATE.status}[/]")
    table.add_row("Current File", STATE.current_file or "[dim]None[/]")
    table.add_row("Files Processed", f"[bold]{STATE.files_processed}[/]")
    table.add_row("Pending", f"{STATE.files_pending}")
    table.add_row("Errors Logged", f"[dim]{STATE.errors_count}[/]")
    table.add_row("Last Scan", STATE.last_scan or "[dim]Never[/]")
    table.add_row("Next Scan", STATE.next_scan or "[dim]--[/]")
    
    if STATE.recent_ingestions:
        table.add_row("", "")
        table.add_row("[bold]Recent:[/]", "")
        for item in STATE.recent_ingestions[-3:]:
            table.add_row("  ✅", f"[green]{item}[/]")
    
    return Panel(
        table,
        title="[bold magenta]🎓 VISIONS AUTO-INGESTOR (Native PDF)[/]",
        subtitle=f"[dim]Watching: {WATCH_FOLDER[:40]}...[/]",
        border_style="magenta"
    )


def get_pending_files() -> list:
    """Get list of pending PDF files."""
    try:
        processed_log = load_processed_log()
        pending = []
        
        for filename in os.listdir(WATCH_FOLDER):
            if not filename.lower().endswith('.pdf'):
                continue
            if 'KDP' in filename.upper() or 'TEMPLATE' in filename.upper():
                continue
            
            filepath = os.path.join(WATCH_FOLDER, filename)
            file_hash = get_file_hash(filepath)
            
            if file_hash and file_hash not in processed_log:
                pending.append((filename, filepath, file_hash))
        
        return pending
    except Exception as e:
        log_error(f"Get pending files error: {e}")
        return []


def process_new_pdfs():
    """Scan for new PDFs and process them."""
    STATE.status = "Scanning for new PDFs..."
    STATE.last_scan = datetime.now().strftime('%H:%M:%S')
    
    processed_log = load_processed_log()
    pending_files = get_pending_files()
    STATE.files_pending = len(pending_files)
    
    if not pending_files:
        STATE.status = "All caught up! Waiting..."
        return False
    
    new_files_processed = False
    
    for filename, filepath, file_hash in pending_files:
        STATE.current_file = filename[:40] + "..." if len(filename) > 40 else filename
        STATE.status = f"Reading PDF with Gemini..."
        
        # Use native PDF reading - no extraction step!
        insights = synthesize_with_native_pdf(filepath, filename)
        
        if insights:
            append_to_knowledge_base(insights)
            processed_log[file_hash] = {
                "filename": filename,
                "processed_at": datetime.now().isoformat(),
                "status": "success"
            }
            new_files_processed = True
            STATE.files_processed += 1
            STATE.recent_ingestions.append(filename[:30])
            if len(STATE.recent_ingestions) > 5:
                STATE.recent_ingestions.pop(0)
        else:
            processed_log[file_hash] = {
                "filename": filename,
                "processed_at": datetime.now().isoformat(),
                "status": "failed_synthesis"
            }
        
        save_processed_log(processed_log)
        STATE.files_pending -= 1
        
        # Delay between files to respect rate limits
        time.sleep(5)
    
    STATE.current_file = None
    
    # Rebuild vector store if we processed any new files
    if new_files_processed:
        if rebuild_vector_store():
            STATE.status = "Vector store updated!"
        else:
            STATE.status = "Vector store rebuild had issues (see error log)"
    else:
        STATE.status = "No new content extracted"
    
    return new_files_processed


def run_with_live_display():
    """Run the main loop with Rich Live display."""
    if RICH_AVAILABLE:
        with Live(build_dashboard(), console=console, refresh_per_second=2) as live:
            try:
                while True:
                    live.update(build_dashboard())
                    process_new_pdfs()
                    
                    for remaining in range(POLL_INTERVAL_SECONDS, 0, -1):
                        STATE.next_scan = f"{remaining // 60}m {remaining % 60}s"
                        STATE.status = "Waiting for next scan..."
                        live.update(build_dashboard())
                        time.sleep(1)
                        
            except KeyboardInterrupt:
                STATE.status = "Stopped by user"
                live.update(build_dashboard())
    else:
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning...")
                process_new_pdfs()
                print(f"Next scan in {POLL_INTERVAL_SECONDS // 60} minutes...")
                time.sleep(POLL_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nStopped.")


def main():
    """Main entry point."""
    try:
        os.makedirs(os.path.dirname(KNOWLEDGE_BASE_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
    except:
        pass
    
    log_error("=== INGESTOR STARTED (Native PDF Mode) ===")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        process_new_pdfs()
    else:
        run_with_live_display()


if __name__ == "__main__":
    main()
