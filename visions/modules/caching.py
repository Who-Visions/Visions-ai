
from google import genai
from google.genai import types
from visions.core.config import Config
import datetime

class CacheManager:
    """
    Manages Gemini Context Caching for cost optimization on large contexts.
    Implements Cookbook Pattern 14 (Caching.ipynb).
    """
    
    def __init__(self, project_id: str, location: str = "global"):
        self.client = genai.Client(vertexai=True, project=project_id, location=location)

    def create_cache(self, 
                     content_list: list, 
                     model_name: str, 
                     ttl_minutes: int = 60,
                     system_instruction: str = None) -> types.CachedContent:
        """
        Creates a new cached content object.
        
        Args:
            content_list: List of content parts (documents, text, files) to cache.
            model_name: The model this cache is intended for (caches are model-specific!).
            ttl_minutes: Time-to-live in minutes (default 60).
            system_instruction: Optional system instruction to bake into the cache.
            
        Returns:
            The created CachedContent object.
        """
        config = {
            'contents': content_list,
            'ttl': f"{ttl_minutes * 60}s"
        }
        
        if system_instruction:
            config['system_instruction'] = system_instruction
            
        print(f"📦 Creating cache for model {model_name} with TTL {ttl_minutes}m...")
        cache = self.client.caches.create(
            model=model_name,
            config=config
        )
        print(f"✅ Cache created: {cache.name} ({cache.usage_metadata.total_token_count} tokens)")
        return cache

    def get_cache(self, name: str) -> types.CachedContent:
        """Retrieves an existing cache by name."""
        return self.client.caches.get(name=name)

    def update_ttl(self, name: str, ttl_minutes: int):
        """Updates the TTL of an existing cache."""
        self.client.caches.update(
            name=name,
            config=types.UpdateCachedContentConfig(ttl=f"{ttl_minutes * 60}s")
        )
        print(f"🔄 Updated TTL for {name} to {ttl_minutes}m")

    def delete_cache(self, name: str):
        """Deletes a cache to stop billing."""
        self.client.caches.delete(name=name)
        print(f"🗑️ Deleted cache: {name}")

    def list_caches(self):
        """Lists all active caches."""
        return self.client.caches.list()
