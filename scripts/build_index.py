import os
import time
import vertexai
from config import Config
from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from genai_embeddings import GenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google.cloud import storage
import hashlib
import json
from rich.console import Console, Group, RenderableType
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.pretty import Pretty
from datetime import datetime

console = Console()

# Config
PROJECT_ID = Config.VERTEX_PROJECT_ID
LOCATION = Config.VERTEX_LOCATION
# Index both the X drive, local knowledge base, and transcripts
SOURCE_DIRS = ["/mnt/x", "knowledge_base", "knowledge_base/transcripts"]
INDEX_DIR = Config.VECTOR_STORE_PREFIX
BATCH_SIZE = 5  # Reduced for gemini-embedding-001 quotas
BATCH_DELAY = 5 # Seconds to wait between batches (User: "take a break")
CACHE_FILE = "indexing_cache.json"

def get_file_hash(file_path: str) -> str:
    """Returns MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=4)

def load_documents_batch(source_dirs: List[str], batch_size: int):
    """
    Generator that yields batches of documents.
    """
    all_files = []
    
    # Gather all file paths first
    for directory in source_dirs:
        if not os.path.exists(directory):
            print(f"⚠️ Directory not found: {directory}")
            continue
            
        print(f"📂 Scanning {directory}...")
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".txt") or file.endswith(".md"):
                    all_files.append(os.path.join(root, file))
    
    # Filter by cache
    cache = load_cache()
    to_index = []
    skipped = 0
    for f in all_files:
        f_hash = get_file_hash(f)
        if cache.get(f) == f_hash:
            skipped += 1
        else:
            to_index.append(f)
            
    print(f"📄 Total files found: {len(all_files)}")
    print(f"⏩ Skipped (already indexed): {skipped}")
    print(f"👷 New/Changed files to process: {len(to_index)}")
    
    # Yield batches
    current_batch = []
    for file_path in to_index:
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            docs = loader.load()
            current_batch.extend(docs)
            
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []
        except Exception as e:
            print(f"⚠️ Error loading {file_path}: {e}")
            
    if current_batch:
        yield current_batch

def build_index():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3)
    )
    layout["body"].split_row(
        Layout(name="main", ratio=2),
        Layout(name="side", ratio=1)
    )
    
    header_table = Table.grid(expand=True)
    header_table.add_column(justify="center", ratio=1)
    header_table.add_row("[bold cyan]VISIONS AI - KNOWLEDGE INDEXER[/bold cyan]")
    header_table.add_row(f"[dim]{PROJECT_ID} | {Config.EMBEDDING_MODEL}[/dim]")
    layout["header"].update(Panel(header_table, border_style="blue"))
    
    status_table = Table(show_header=True, header_style="bold magenta", expand=True, box=None)
    status_table.add_column("ID", width=4, justify="right")
    status_table.add_column("State", width=12)
    status_table.add_column("Source", ratio=1)
    status_table.add_column("Chunks", width=8, justify="right")

    overall_progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        console=console
    )
    
    layout["footer"].update(Panel(overall_progress, title="Overall Progress", border_style="cyan"))
    layout["main"].update(Panel(status_table, title="Pipeline Status", border_style="green"))
    
    log_messages = []
    
    def update_logs(message: str, style: str = "white"):
        line = Text()
        line.append(f"[{datetime.now().strftime('%H:%M:%S')}] ", style="dim")
        line.append(message, style=style)
        log_messages.append(line)
        if len(log_messages) > 18:
            log_messages.pop(0)
        layout["side"].update(Panel(Group(*log_messages), title="Execution Status", border_style="yellow"))

    with Live(layout, refresh_per_second=4, screen=True) as live:
        update_logs("Initializing Vertex AI...", "dim")
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        embeddings = GenAIEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=Config.EMBEDDING_DIMENSIONS
        )
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        vector_store = None
        total_chunks_session = 0
        
        update_logs("Scanning source directories...", "cyan")
        batches = list(load_documents_batch(SOURCE_DIRS, BATCH_SIZE))
        
        if not batches:
            update_logs("Knowledge base is already synchronized.", "green")
            layout["main"].update(Panel(Align.center("[bold green]Sync Status: Up to Date[/bold green]\n\nAll Knowledge is Indexed.", vertical="middle"), title="System Status"))
            if os.path.exists(INDEX_DIR):
                update_logs("Running auxiliary GCS sync...", "dim")
                sync_to_gcs(INDEX_DIR, update_logs)
            time.sleep(3)
            return

        task_id = overall_progress.add_task("Indexing...", total=len(batches))
        
        for idx, batch_docs in enumerate(batches, start=1):
            file_names = ", ".join([os.path.basename(d.metadata['source']) for d in batch_docs])
            status_table.add_row(f"{idx}", "[blue]WAITING[/blue]", file_names, "-")
            
            # Split
            update_logs(f"Processing Batch {idx}...", "magenta")
            splits = text_splitter.split_documents(batch_docs)
            if not splits:
                status_table.columns[1]._cells[-1] = "[dim]SKIP[/dim]"
                overall_progress.advance(task_id)
                continue
            
            status_table.columns[1]._cells[-1] = "[yellow]EMBEDDING[/yellow]"
            status_table.columns[3]._cells[-1] = f"{len(splits)}"
            
            try:
                if vector_store is None:
                    if os.path.exists(INDEX_DIR):
                        update_logs("Loading existing local index...", "dim")
                        vector_store = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
                        update_logs("Adding docs to index...", "dim")
                        vector_store.add_documents(splits)
                    else:
                        update_logs("Creating new local index...", "dim")
                        vector_store = FAISS.from_documents(splits, embeddings)
                else:
                    vector_store.add_documents(splits)
                
                total_chunks_session += len(splits)
                vector_store.save_local(INDEX_DIR)
                
                # Cache
                cache = load_cache()
                for d in batch_docs:
                    cache[d.metadata['source']] = get_file_hash(d.metadata['source'])
                save_cache(cache)
                
                status_table.columns[1]._cells[-1] = "[green]DONE[/green]"
                update_logs(f"Batch {idx} complete. ({len(splits)} chunks)", "green")
            except Exception as e:
                status_table.columns[1]._cells[-1] = "[red]ERROR[/red]"
                update_logs(f"Error in Batch {idx}: {e}", "red")
                
            overall_progress.advance(task_id)
            
            if idx < len(batches):
                update_logs(f"Waiting {BATCH_DELAY}s (breaker penalty)...", "dim")
                time.sleep(BATCH_DELAY)

        summary = Panel(Pretty({
            "Session": "Complete",
            "Files": len(batches) * BATCH_SIZE,
            "Chunks": total_chunks_session,
            "Sync": "gs://reasoning-artifacts"
        }), title="Build Summary", border_style="bold green")
        layout["main"].update(summary)
        
        update_logs("Starting GCS Synchronization...", "cyan")
        sync_to_gcs(INDEX_DIR, update_logs)
        update_logs("Indexing and Sync Complete.", "bold green")
        time.sleep(3)

def sync_to_gcs(local_dir: str, log_fn=None):
    """Uploads the local vector store directory to GCS."""
    def printer(msg, style="white"):
        if log_fn:
            log_fn(msg, style)
        else:
            console.print(msg, style=style)

    printer(f"☁️  Syncing {local_dir} to GCS...", "cyan")
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket_name = Config.GCS_BUCKET
        memory_bucket = Config.GCS_MEMORY_BUCKET
        
        for b_name in [bucket_name, memory_bucket]:
            try:
                client.get_bucket(b_name)
            except:
                printer(f"🪣 Creating bucket: {b_name}", "yellow")
                client.create_bucket(b_name, location=LOCATION)
            
        for root, _, files in os.walk(local_dir):
            for file in files:
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, os.path.dirname(local_dir))
                blob_path = rel_path.replace("\\", "/") 
                
                blob = client.bucket(bucket_name).blob(blob_path)
                blob.upload_from_filename(local_path)
                printer(f"   ✅ {blob_path}", "dim")
        
        printer("✅ GCS Sync Complete.", "green")
    except Exception as e:
        printer(f"❌ GCS Sync Failed: {e}", "red")

if __name__ == "__main__":
    build_index()
