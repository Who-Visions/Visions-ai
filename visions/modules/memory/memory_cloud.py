# Visions AI - Memory Cloud Module
# Rhea Noir Standard - Persistent Memory via GCS Buckets

import os
import json
import logging
import time
from typing import Optional, Dict, List, Any
from google.cloud import storage
from visions.core.config import Config

logger = logging.getLogger("visions-memory")

class CloudMemoryManager:
    """Manages persistent memory using GCS Buckets for interaction logs and states."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.bucket_name = Config.GCS_MEMORY_BUCKET
        self._client = None
        self._bucket = None
        self._initialized = False

    def _get_client(self):
        if self._client is None:
            self._client = storage.Client(project=self.project_id)
        return self._client

    def _get_bucket(self):
        if self._bucket is None:
            client = self._get_client()
            try:
                self._bucket = client.bucket(self.bucket_name)
            except Exception as e:
                logger.error(f"Failed to access memory bucket {self.bucket_name}: {e}")
        return self._bucket

    async def initialize(self):
        """Verify bucket access."""
        if not self._initialized:
            bucket = self._get_bucket()
            if bucket and bucket.exists():
                logger.info(f"🧠 Memory System Live: gs://{self.bucket_name}")
                self._initialized = True
            else:
                logger.warning(f"⚠️ Memory bucket {self.bucket_name} not found or inaccessible.")
                
    def save_interaction(self, user_id: str, prompt: str, response: str):
        """Saves a JSON interaction log to the memory bucket."""
        bucket = self._get_bucket()
        if not bucket: return
        
        timestamp = int(time.time())
        filename = f"interactions/{user_id}/{timestamp}.json"
        
        data = {
            "timestamp": timestamp,
            "user_id": user_id,
            "prompt": prompt,
            "response": response
        }
        
        try:
            blob = bucket.blob(filename)
            blob.upload_from_string(
                data=json.dumps(data),
                content_type='application/json'
            )
            logger.info(f"💾 Interaction cached: {filename}")
        except Exception as e:
            logger.error(f"Failed to save interaction to GCS: {e}")

    def get_history(self, user_id: str, limit: int = 5) -> List[Dict[str, str]]:
        """Retrieves recent history from the bucket."""
        bucket = self._get_bucket()
        if not bucket: return []
        
        prefix = f"interactions/{user_id}/"
        try:
            blobs = list(bucket.list_blobs(prefix=prefix, max_results=limit))
            # Sort by Name (Timestamp) descending
            blobs.sort(key=lambda b: b.name, reverse=True)
            
            history = []
            for blob in blobs[:limit]:
                content = blob.download_as_text()
                history.append(json.loads(content))
            return history
        except Exception as e:
            logger.error(f"Error retrieving history from GCS: {e}")
            return []
