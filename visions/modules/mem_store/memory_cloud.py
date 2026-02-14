
import json
import logging
import sqlite3
import time
import datetime
from pathlib import Path
from google.cloud import storage
from google.cloud import bigquery
from visions.core.config import Config

logger = logging.getLogger("visions-memory")

class CloudMemoryManager:
    """
    Hybrid Memory Manager:
    1. Local SQLite (Short-term, Fast)
    2. GCS Bucket (Raw Logs, Backup)
    3. BigQuery (Structured, Analytical)
    """
    def __init__(self, project_id: str):
        self.project_id = project_id
        
        # 1. GCS Setup
        self.bucket_name = Config.GCS_MEMORY_BUCKET
        self._gcs_client = None
        self._bucket = None
        
        # 2. BigQuery Setup
        self._bq_client = None
        self.bq_dataset = Config.BIGQUERY_DATASET
        self.bq_table = Config.BIGQUERY_TABLE
        
        # Local SQL Setup
        self.local_db = Config.LOCAL_MEMORY_DB
        self._init_local_sql()
        
        # 4. Markdown Journaling
        self.log_file = Path("docs/logs/CURRENT_SESSION.md")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _init_local_sql(self):
        """Initialize local SQLite for short-term memory."""
        try:
            conn = sqlite3.connect(self.local_db)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS interactions
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          user_id TEXT,
                          prompt TEXT,
                          response TEXT,
                          timestamp REAL)''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Local SQL Init Failed: {e}")

    def _get_gcs(self):
        if not self._gcs_client:
            self._gcs_client = storage.Client(project=self.project_id)
            self._bucket = self._gcs_client.bucket(self.bucket_name)
        return self._bucket

    def _get_bq(self):
        if not self._bq_client:
            self._bq_client = bigquery.Client(project=self.project_id)
        return self._bq_client
        
    def _log_to_markdown(self, user_id: str, prompt: str, response: str, timestamp: float):
        """Appends interaction to a local Markdown log."""
        try:
            timestamp_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            entry = f"\n## 🕒 {timestamp_str}\n\n"
            entry += f"**User ({user_id})**:\n{prompt}\n\n"
            entry += f"**Visions AI**:\n{response}\n\n"
            entry += "---\n"
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
                
        except Exception as e:
            logger.warning(f"Markdown Logging Failed: {e}")

    def save_interaction(self, user_id: str, prompt: str, response: str):
        """Save interaction to all three memory tiers + Markdown Log."""
        timestamp = time.time()
        
        # A. Local SQL (Immediate)
        try:
            conn = sqlite3.connect(self.local_db)
            c = conn.cursor()
            c.execute("INSERT INTO interactions (user_id, prompt, response, timestamp) VALUES (?, ?, ?, ?)",
                      (user_id, prompt, response, timestamp))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Local Memory Save Failed: {e}")
            
        # D. Markdown Log (User Visibility)
        self._log_to_markdown(user_id, prompt, response, timestamp)

        # B. GCS (Blob Persistence)
        try:
            bucket = self._get_gcs()
            blob_name = f"logs/{user_id}/{int(timestamp)}.json"
            blob = bucket.blob(blob_name)
            
            data = {
                "user_id": user_id,
                "timestamp": timestamp,
                "prompt": prompt,
                "response": response,
                "iso_time": datetime.datetime.now().isoformat()
            }
            blob.upload_from_string(json.dumps(data), content_type="application/json")
        except Exception as e:
            logger.warning(f"GCS Memory Save Failed: {e}")
            
        # C. BigQuery (Structured Storage)
        try:
            bq = self._get_bq()
            table_id = f"{self.project_id}.{self.bq_dataset}.{self.bq_table}"
            
            rows_to_insert = [{
                "user_id": user_id,
                "prompt": prompt,
                "response": response,
                "timestamp": datetime.datetime.now().isoformat()
            }]
            
            # Note: In production, you would check if table exists or stream. 
            # This assumes the dataset/table structure exists or BQ auto-creates if configured.
            # For robustness, we catch the error if table doesn't exist.
            errors = bq.insert_rows_json(table_id, rows_to_insert)
            if errors:
                logger.warning(f"BigQuery Insert Errors: {errors}")
                
        except Exception as e:
            # Common error: Table or Dataset not found. 
            # Not blocking the agent flow.
            logger.warning(f"BigQuery Memory Save Failed: {e}")

    def get_recent_context(self, user_id: str, limit: int = 5):
        """Retrieve recent context primarily from Local SQL (fast)."""
        try:
            conn = sqlite3.connect(self.local_db)
            c = conn.cursor()
            c.execute("SELECT prompt, response FROM interactions WHERE user_id=? ORDER BY id DESC LIMIT ?", 
                      (user_id, limit))
            rows = c.fetchall()
            conn.close()
            # Reverse to chronological
            return [{"role": "user", "content": r[0], "assistant": r[1]} for r in reversed(rows)]
        except Exception as e:
            logger.error(f"Local Context Retrieval Failed: {e}")
            return []
