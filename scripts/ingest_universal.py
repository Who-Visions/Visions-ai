#!/usr/bin/env python3
"""
🌟 UNIVERSAL INGESTION SYSTEM 🌟
Synthesized from Dav1d's Wisdom (Video, RAG, Ecosystem, Docs).
Capabilities:
- YouTube: Structured Workflow JSONs
- Web: Recursive Documentation Crawling
- Local: Markdown Knowledge Base
- Features: Auto-Tagging, Adaptive Backoff, Rich UI
"""
import sys
import os
import time
import json
import re
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import shutil
import tempfile
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.vector_store_bigquery import BigQueryVectorStore
from config import Config

# Try importing rich
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Installing rich...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.table import Table

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 INTELLIGENCE: AUTO-TAGGING & CHUNKING
# ═══════════════════════════════════════════════════════════════════════════════

def extract_metadata(text: str, source_type: str) -> Dict[str, Any]:
    """Auto-tag content based on keywords."""
    tags = [source_type]
    
    # Simple keyword mapping (expandable)
    keywords = {
        "python": "python",
        "javascript": "javascript",
        "react": "react",
        "next.js": "nextjs",
        "api": "api",
        "vision": "ai-vision",
        "gemini": "llm",
        "vertex": "cloud",
        "docker": "devops"
    }
    
    content_lower = text.lower()
    for word, tag in keywords.items():
        if word in content_lower:
            tags.append(tag)
            
    return {
        "tags": list(set(tags)),
        "analyzed_at": datetime.utcnow().isoformat()
    }

def chunk_markdown(content: str, source_name: str) -> List[Dict]:
    """Smart Markdown Splitting (H2 Headers)."""
    parts = re.split(r'(^## .+$)', content, flags=re.MULTILINE)
    chunks = []
    current_header = "Overview"
    current_text = ""
    
    for part in parts:
        if part.startswith('## '):
            if current_text.strip():
                chunks.append({
                    "content": current_text.strip(),
                    "header": current_header,
                    "source": source_name
                })
            current_header = part.replace('## ', '').strip()
            current_text = part + "\n"
        else:
            current_text += part
            
    if current_text.strip():
        chunks.append({
            "content": current_text.strip(),
            "header": current_header,
            "source": source_name
        })
    return chunks

# ═══════════════════════════════════════════════════════════════════════════════
# 🌐 SOURCES
# ═══════════════════════════════════════════════════════════════════════════════

class Source:
    def yield_chunks(self):
        raise NotImplementedError

class YouTubeJSONSource(Source):
    """Ingests structured JSON transcripts from ingest_youtube.py."""
    def __init__(self, directory: Path):
        self.directory = directory
        
    def yield_chunks(self):
        files = list(self.directory.glob("*.json"))
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                
                # Check if valid structure
                if "steps" not in data:
                    continue
                    
                videoid = data.get("video_id", f.stem)
                title = data.get("title", f.name)
                
                # Yield summary
                if "summary" in data:
                    yield {
                        "content": f"Source: YouTube (Summary)\nVideo: {title}\nURL: {data.get('url','')}\n\nSummary:\n{data['summary']}",
                        "metadata": {"source": "youtube", "video_id": videoid, "type": "summary"}
                    }
                
                # Yield steps
                for step in data.get("steps", []):
                    timestamp = step.get("time", "")
                    action = step.get("action", "")
                    code = step.get("code", "")
                    
                    text = f"Source: YouTube (Step)\nVideo: {title}\nTimestamp: {timestamp}\n\nAction: {action}"
                    if code:
                        text += f"\nCode:\n{code}"
                        
                    yield {
                        "content": text,
                        "metadata": {"source": "youtube", "video_id": videoid, "type": "workflow_step", "timestamp": timestamp}
                    }
            except Exception as e:
                console.print(f"[red]Error parsing {f.name}: {e}[/red]")

class WebDocsSource(Source):
    """Recursively crawls documentation sites."""
    def __init__(self, start_url: str, max_pages: int = 50):
        self.start_url = start_url
        self.base_domain = urlparse(start_url).netloc
        self.max_pages = max_pages
        self.visited = set()
        
    def get_page(self, url):
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.text
        except:
            return None
            
    def parse_html(self, html, url):
        soup = BeautifulSoup(html, 'html.parser')
        main = soup.find('main') or soup.find('article') or soup.body
        
        # Remove navs
        for tag in main.find_all(['nav', 'aside', 'footer']):
            tag.decompose()
            
        text = main.get_text(separator='\n\n', strip=True)
        title = soup.title.string if soup.title else url
        
        links = []
        for a in main.find_all('a', href=True):
            full = urljoin(url, a['href'])
            if urlparse(full).netloc == self.base_domain and '#' not in a['href']:
                links.append(full)
                
        return {"title": title, "content": text, "url": url}, links

    def yield_chunks(self):
        queue = [self.start_url]
        count = 0
        
        while queue and count < self.max_pages:
            url = queue.pop(0)
            if url in self.visited:
                continue
            self.visited.add(url)
            count += 1
            
            console.print(f"[dim]Crawling: {url}[/dim]")
            html = self.get_page(url)
            if not html: continue
            
            data, next_links = self.parse_html(html, url)
            for link in next_links:
                if link not in self.visited:
                    queue.append(link)
            
            # Simple chunking for docs
            chunk_size = 2000
            content = data['content']
            for i in range(0, len(content), chunk_size):
                chunk_text = content[i:i+chunk_size]
                yield {
                    "content": f"Source: Web Documentation\nTitle: {data['title']}\nURL: {url}\n\n{chunk_text}",
                    "metadata": {"source": "web_docs", "url": url, "title": data['title']}
                }
            time.sleep(0.5) # Politeness

class LocalDirectorySource(Source):
    """Ingests local files (Markdown & Code) from a directory."""
    def __init__(self, path: str):
        self.path = Path(path)
        
    def yield_chunks(self):
        if self.path.is_file():
            files = [self.path]
            # If explicit file, assume we want it regardless of extension (within reason)
        else:
            # Extensions to look for
            extensions = {'.md', '.py', '.js', '.ts', '.tsx', '.json', '.html', '.css', '.txt'}
            files = [p for p in self.path.rglob("*") if p.suffix in extensions and ".git" not in p.parts]
            
        for f in files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                rel_path = f.relative_to(self.path) if self.path.is_dir() else f.name
                
                # Apply chunking strategy based on file type
                if f.suffix == '.md':
                    chunks = chunk_markdown(content, str(rel_path))
                    for chunk in chunks:
                        yield {
                            "content": f"Source: Local File\nFile: {rel_path}\nHeader: {chunk.get('header')}\n\n{chunk['content']}",
                            "metadata": {"source": "local_dir", "file": str(rel_path), "type": "markdown", "path": str(f)}
                        }
                else:
                    # Simple chunking for code
                    if len(content) > 10000:
                        lines = content.splitlines()
                        chunk_size = 200
                        for i in range(0, len(lines), chunk_size):
                            chunk_text = "\n".join(lines[i:i+chunk_size])
                            yield {
                                "content": f"Source: Local File\nFile: {rel_path}\nRange: {i}-{i+chunk_size}\n\n{chunk_text}",
                                "metadata": {"source": "local_dir", "file": str(rel_path), "type": "code", "path": str(f)}
                            }
                    else:
                        yield {
                            "content": f"Source: Local File\nFile: {rel_path}\n\n{content}",
                            "metadata": {"source": "local_dir", "file": str(rel_path), "type": "code", "path": str(f)}
                        }
            except Exception as e:
                console.print(f"[red]Error reading {f.name}: {e}[/red]")

class GitRepositorySource(Source):
    """Clones and ingests a Git repository."""
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
        self.temp_dir = Path(tempfile.mkdtemp(prefix="visions_ingest_"))
        
    def yield_chunks(self):
        try:
            console.print(f"[dim]Cloning {self.repo_url}...[/dim]")
            subprocess.check_call(["git", "clone", "--depth", "1", self.repo_url, str(self.temp_dir)])
            
            extensions = {'.md', '.py', '.js', '.ts', '.tsx', '.json', '.html', '.css'}
            
            for f in self.temp_dir.rglob("*"):
                if f.is_file() and f.suffix in extensions and ".git" not in f.parts:
                    try:
                        content = f.read_text(encoding='utf-8', errors='ignore')
                        rel_path = f.relative_to(self.temp_dir)
                        
                        # Apply chunking strategy based on file type
                        if f.suffix == '.md':
                            chunks = chunk_markdown(content, str(rel_path))
                            for chunk in chunks:
                                yield {
                                    "content": f"Source: Git Repo\nRepo: {self.repo_url}\nFile: {rel_path}\nHeader: {chunk.get('header')}\n\n{chunk['content']}",
                                    "metadata": {"source": "git_repo", "repo": self.repo_url, "file": str(rel_path), "type": "markdown"}
                                }
                        else:
                            # Simple chunking for code
                            # TODO: Use tree-sitter or similar for smarter code splitting?
                            # For now, just entire file or simple split if too large
                            if len(content) > 10000:
                                # Split by lines roughly
                                lines = content.splitlines()
                                chunk_size = 200
                                for i in range(0, len(lines), chunk_size):
                                    chunk_text = "\n".join(lines[i:i+chunk_size])
                                    yield {
                                        "content": f"Source: Git Repo\nRepo: {self.repo_url}\nFile: {rel_path}\nRange: {i}-{i+chunk_size}\n\n{chunk_text}",
                                        "metadata": {"source": "git_repo", "repo": self.repo_url, "file": str(rel_path), "type": "code"}
                                    }
                            else:
                                yield {
                                    "content": f"Source: Git Repo\nRepo: {self.repo_url}\nFile: {rel_path}\n\n{content}",
                                    "metadata": {"source": "git_repo", "repo": self.repo_url, "file": str(rel_path), "type": "code"}
                                }
                                
                    except Exception as e:
                        # console.print(f"[dim]Skipping {f.name}: {e}[/dim]")
                        pass
        finally:
            # Cleanup
             if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 INGESTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class UniversalIngestor:
    def __init__(self, project_id: str, location: str):
        self.store = BigQueryVectorStore(project_id, location)
        self.store.initialize_dataset()
        
    def ingest(self, source: Source):
        chunks = list(source.yield_chunks()) # Materialize for progress bar
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Ingesting {len(chunks)} chunks...[/cyan]", total=len(chunks))
            
            for chunk in chunks:
                try:
                    # Adaptive Backoff / Retry
                    retries = 3
                    for attempt in range(retries):
                        try:
                            # Enrich metadata
                            meta = chunk['metadata']
                            meta.update(extract_metadata(chunk['content'], meta['source']))
                            
                            self.store.add_memory(chunk['content'], meta)
                            break
                        except Exception as e:
                            if "429" in str(e) or "quota" in str(e).lower():
                                time.sleep(2 ** attempt) # Backoff
                            else:
                                raise e
                    
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]Failed chunk: {e}[/red]")

# ═══════════════════════════════════════════════════════════════════════════════
# 🏁 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Ingestion System")
    parser.add_argument("--mode", choices=["youtube", "web", "local", "git"], required=True)
    parser.add_argument("--target", help="Target path or URL")
    
    args = parser.parse_args()
    
    ingestor = UniversalIngestor(Config.VERTEX_PROJECT_ID, Config.VERTEX_LOCATION)
    
    if args.mode == "youtube":
        path = Path(args.target) if args.target else Path("knowledge_base/transcripts")
        source = YouTubeJSONSource(path)
        ingestor.ingest(source)
        
    elif args.mode == "web":
        if not args.target:
            print("Error: --target URL required for web mode")
            sys.exit(1)
        source = WebDocsSource(args.target)
        ingestor.ingest(source)
        
    elif args.mode == "local":
        if not args.target:
            print("Error: --target path required for local mode")
            sys.exit(1)
        source = LocalDirectorySource(args.target)
        ingestor.ingest(source)

    elif args.mode == "git":
        if not args.target:
            print("Error: --target Repository URL required for git mode")
            sys.exit(1)
        source = GitRepositorySource(args.target)
        ingestor.ingest(source)
        
    console.print("[bold green]Ingestion Complete! 🧠[/bold green]")
