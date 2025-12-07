"""
Visions AI Memory System
Provides short-term (session) and long-term (persistent) memory
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import deque

@dataclass
class MemoryEntry:
    """Single memory entry"""
    timestamp: str
    type: str  # "conversation", "image_generation", "preference", "feedback"
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Dict = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class ShortTermMemory:
    """
    In-session memory for conversation context
    Uses a circular buffer to maintain recent history
    """
    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self.entries = deque(maxlen=max_entries)
        self.session_start = datetime.now().isoformat()
    
    def add(self, type: str, role: str, content: str, metadata: Dict = None):
        """Add entry to short-term memory"""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            type=type,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.entries.append(entry)
        return entry
    
    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent entries"""
        return list(self.entries)[-limit:]
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get conversation history in format suitable for model context"""
        history = []
        for entry in list(self.entries)[-limit:]:
            if entry.type == "conversation":
                history.append({
                    "role": entry.role,
                    "content": entry.content
                })
        return history
    
    def clear(self):
        """Clear short-term memory"""
        self.entries.clear()
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "session_start": self.session_start,
            "total_entries": len(self.entries),
            "max_entries": self.max_entries,
            "types": {
                entry_type: sum(1 for e in self.entries if e.type == entry_type)
                for entry_type in set(e.type for e in self.entries)
            }
        }


class LongTermMemory:
    """
    Persistent memory stored in JSON files
    Stores preferences, patterns, and important interactions
    """
    def __init__(self, storage_dir: str = "memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Memory files
        self.preferences_file = self.storage_dir / "preferences.json"
        self.history_file = self.storage_dir / "conversation_history.json"
        self.generated_images_file = self.storage_dir / "generated_images.json"
        
        # Load existing data
        self.preferences = self._load_json(self.preferences_file, default={
            "user_name": "Dave",
            "favorite_styles": [],
            "common_prompts": [],
            "safety_level": "default"
        })
        
        self.conversation_history = self._load_json(self.history_file, default=[])
        self.generated_images = self._load_json(self.generated_images_file, default=[])
    
    def _load_json(self, filepath: Path, default=None):
        """Load JSON file or return default"""
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading {filepath}: {e}")
                return default
        return default
    
    def _save_json(self, filepath: Path, data):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving {filepath}: {e}")
            return False
    
    def save_conversation(self, user_msg: str, assistant_msg: str, metadata: Dict = None):
        """Save a conversation exchange to long-term memory"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_msg,
            "assistant": assistant_msg,
            "metadata": metadata or {}
        }
        self.conversation_history.append(entry)
        
        # Keep only last 1000 conversations to avoid huge files
        if len(self.conversation_history) > 1000:
            self.conversation_history = self.conversation_history[-1000:]
        
        return self._save_json(self.history_file, self.conversation_history)
    
    def save_generated_image(self, prompt: str, filepath: str, metadata: Dict = None):
        """Record a generated image"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "filepath": filepath,
            "metadata": metadata or {}
        }
        self.generated_images.append(entry)
        
        # Keep only last 500 images
        if len(self.generated_images) > 500:
            self.generated_images = self.generated_images[-500:]
        
        return self._save_json(self.generated_images_file, self.generated_images)
    
    def set_preference(self, key: str, value):
        """Set a user preference"""
        self.preferences[key] = value
        return self._save_json(self.preferences_file, self.preferences)
    
    def get_preference(self, key: str, default=None):
        """Get a user preference"""
        return self.preferences.get(key, default)
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:]
    
    def get_recent_images(self, limit: int = 10) -> List[Dict]:
        """Get recently generated images"""
        return self.generated_images[-limit:]
    
    def search_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """Search conversation history"""
        results = []
        query_lower = query.lower()
        
        for conv in reversed(self.conversation_history):
            if (query_lower in conv['user'].lower() or 
                query_lower in conv['assistant'].lower()):
                results.append(conv)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_stats(self) -> Dict:
        """Get long-term memory statistics"""
        return {
            "total_conversations": len(self.conversation_history),
            "total_images_generated": len(self.generated_images),
            "preferences": self.preferences,
            "storage_location": str(self.storage_dir.absolute())
        }


class MemoryManager:
    """
    Unified memory manager combining short-term and long-term memory
    """
    def __init__(self, storage_dir: str = "memory", short_term_limit: int = 100):
        self.short_term = ShortTermMemory(max_entries=short_term_limit)
        self.long_term = LongTermMemory(storage_dir=storage_dir)
        
        print(f"🧠 Memory System Initialized")
        print(f"   Short-term: {short_term_limit} entries")
        print(f"   Long-term: {self.long_term.storage_dir.absolute()}")
    
    def remember_conversation(self, user_msg: str, assistant_msg: str, 
                              save_to_long_term: bool = True):
        """Remember a conversation exchange"""
        # Add to short-term
        self.short_term.add("conversation", "user", user_msg)
        self.short_term.add("conversation", "assistant", assistant_msg)
        
        # Optionally save to long-term
        if save_to_long_term:
            self.long_term.save_conversation(user_msg, assistant_msg)
    
    def remember_image_generation(self, prompt: str, filepath: str, 
                                  source: str = "unknown"):
        """Remember an image generation"""
        metadata = {"source": source}
        
        # Add to short-term
        self.short_term.add("image_generation", "system", prompt, metadata)
        
        # Save to long-term
        self.long_term.save_generated_image(prompt, filepath, metadata)
    
    def get_context_for_model(self, limit: int = 10) -> str:
        """Get recent context formatted for model input"""
        history = self.short_term.get_conversation_history(limit)
        
        if not history:
            return ""
        
        # Format as context
        context_parts = []
        for entry in history:
            role = entry['role'].upper()
            content = entry['content'][:200]  # Truncate to save tokens
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def print_status(self):
        """Print memory system status"""
        print("\n" + "="*80)
        print("MEMORY SYSTEM STATUS")
        print("="*80)
        
        short_stats = self.short_term.get_stats()
        print(f"\n📊 Short-Term Memory:")
        print(f"   Session started: {short_stats['session_start']}")
        print(f"   Entries: {short_stats['total_entries']}/{short_stats['max_entries']}")
        print(f"   Types: {short_stats['types']}")
        
        long_stats = self.long_term.get_stats()
        print(f"\n💾 Long-Term Memory:")
        print(f"   Total conversations: {long_stats['total_conversations']}")
        print(f"   Total images: {long_stats['total_images_generated']}")
        print(f"   Storage: {long_stats['storage_location']}")
        print(f"   User: {long_stats['preferences'].get('user_name', 'Unknown')}")
        
        print("="*80 + "\n")


if __name__ == "__main__":
    # Test the memory system
    memory = MemoryManager()
    
    # Simulate some interactions
    memory.remember_conversation(
        "What is aperture in photography?",
        "Aperture is the opening in a lens that controls how much light enters..."
    )
    
    memory.remember_image_generation(
        "A professional photograph of a vintage camera",
        "test_output/vintage_camera.jpg",
        source="ai_studio"
    )
    
    # Print status
    memory.print_status()
    
    # Show recent context
    print("Recent Context for Model:")
    print(memory.get_context_for_model())
