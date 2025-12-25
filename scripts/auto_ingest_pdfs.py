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

# Gemini Configuration - Strictly Gemini 3!
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1" # Changed to us-central1 for Gemini 3
MODEL_ID = "gemini-3-flash-preview"

# Rate limiting
MAX_RETRIES = 5
BASE_BACKOFF_SECONDS = 30

# Console
console = Console() if RICH_AVAILABLE else None

# Prompt for extracting insights (Visions Persona)
EXTRACTION_PROMPT = """You are VISIONS — the legendary Creative Director. 
Analyze this PDF and extract the KEY INSIGHTS in your signature authoritative, technical, and visionary style.

Output format (use this EXACTLY):
--------------------------------------------------------------------------------

TITLE: [Book/Document Title from the PDF]
AUTHOR: [Author Name from the PDF]
SOURCE: PDF Masterclass ([Brief 2-3 word description])
KEY_INSIGHTS:
- **[Concept Name]**: [1-2 sentence explanation using director lexicon: volumetric, hierarchy, gradients, etc.]
- **[Concept Name]**: [1-2 sentence explanation]
(Continue for 5-10 key concepts - focus on the MOST IMPORTANT teachings)

TRANSCRIPT EXCERPT:
[2-4 of the most impactful quotes directly from the text, each on its own line]

Be sharp. Be decisive. Capture the visual poetry and technical precision of the work."""


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
    """Use Gemini 3's Files API and Native Vision - Handles up to 50MB/1000 pages!"""
    for attempt in range(MAX_RETRIES):
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(
                vertexai=True,
                project=PROJECT_ID,
                location=LOCATION
            )
            
            # Step 1: Upload the file using Gemini Files API
            STATE.status = f"Uploading to Gemini Files API..."
            uploaded_file = client.files.upload(
                file=Path(filepath),
                config={"display_name": filename}
            )
            
            # Step 2: Poll for ACTIVE state
            STATE.status = f"Waiting for file to be processed..."
            while True:
                file_info = client.files.get(name=uploaded_file.name)
                if file_info.state == "ACTIVE":
                    break
                elif file_info.state == "FAILED":
                    log_error(f"Gemini File API failed for {filename}")
                    return ""
                time.sleep(2)
            
            # Step 3: Synthesis with Gemini 3 Flash
            STATE.status = f"Synthesizing with Gemini 3 Flash..."
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[
                    EXTRACTION_PROMPT,
                    uploaded_file
                ],
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    max_output_tokens=3000,
                    # Optimal for document understanding per Gemini 3 docs
                    media_resolution="media_resolution_medium"
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
            
            log_error(f"Native PDF synthesis error for {filename}: {e}")
            break
    
    return ""


def append_to_knowledge_base(insights: str):
    """Append the synthesized insights to the knowledge base file."""
    try:
        with open(KNOWLEDGE_BASE_FILE, 'a', encoding='utf-8') as f:
            f.write("\n\n" + insights)
    except Exception as e:
        log_error(f"Append to knowledge base error: {e}")


def sync_to_gcs():
    """Sync the knowledge base and processed log to GCS."""
    try:
        from google.cloud import storage
        STATE.status = "Syncing to GCS..."
        client = storage.Client(project=PROJECT_ID)
        
        # Ensure buckets exist
        buckets = [Config.GCS_BUCKET, Config.GCS_MEMORY_BUCKET]
        for b_name in buckets:
            try:
                client.get_bucket(b_name)
            except:
                print(f"🪣 Creating bucket: {b_name}")
                client.create_bucket(b_name, location=Config.VERTEX_LOCATION)
        
        bucket = client.bucket(Config.GCS_BUCKET)
            
        # Upload knowledge_base/writing_masterclass.txt
        kb_blob = bucket.blob("writing_masterclass.txt")
        kb_blob.upload_from_filename(KNOWLEDGE_BASE_FILE)
        
        # Upload knowledge_base/processed_pdfs.json
        log_blob = bucket.blob("processed_pdfs.json")
        log_blob.upload_from_filename(PROCESSED_LOG)
        
        return True
    except Exception as e:
        log_error(f"GCS Sync error: {e}")
        return False


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
            # Sync to GCS after successful rebuild
            sync_to_gcs()
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
