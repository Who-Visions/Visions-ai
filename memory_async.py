"""
Async Memory System for Visions AI
Non-blocking memory operations using asyncio and aiosqlite
"""
import asyncio
import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import deque

class AsyncShortTermMemory:
    """
    Async in-session memory
    Uses deque for O(1) operations
    """
    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self.entries = deque(maxlen=max_entries)
        self.session_id = datetime.now().isoformat()
        self._lock = asyncio.Lock()
    
    async def add(self, type: str, role: str, content: str, metadata: Dict = None):
        """Add entry (non-blocking)"""
        async with self._lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": type,
                "role": role,
                "content": content,
                "metadata": metadata or {}
            }
            self.entries.append(entry)
            return entry
    
    async def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get recent entries"""
        async with self._lock:
            return list(self.entries)[-limit:]
    
    async def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get conversation history for model context"""
        async with self._lock:
            history = []
            for entry in list(self.entries)[-limit:]:
                if entry['type'] == "conversation":
                    history.append({
                        "role": entry['role'],
                        "content": entry['content']
                    })
            return history
    
    async def clear(self):
        """Clear memory"""
        async with self._lock:
            self.entries.clear()


class AsyncSQLMemory:
    """
    Async SQLite-based long-term memory
    Non-blocking database operations using aiosqlite
    """
    def __init__(self, db_path: str = "memory/visions_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.db = None
        self._initialized = False
    
    async def initialize(self):
        """Async initialization"""
        if self._initialized:
            return
        
        self.db = await aiosqlite.connect(str(self.db_path))
        self.db.row_factory = aiosqlite.Row
        
        await self._create_tables()
        self._initialized = True
        print(f"💾 Async SQL Memory initialized: {self.db_path}")
    
    async def _create_tables(self):
        """Create database schema"""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_message TEXT NOT NULL,
                session_id TEXT,
                metadata TEXT
            )
        """)
        
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS image_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prompt TEXT NOT NULL,
                filepath TEXT,
                source TEXT,
                model TEXT,
                success BOOLEAN,
                generation_time REAL,
                error_message TEXT,
                metadata TEXT
            )
        """)
        
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS prompt_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prompt TEXT NOT NULL,
                category TEXT,
                keywords TEXT,
                usage_count INTEGER DEFAULT 1,
                success_rate REAL,
                avg_generation_time REAL
            )
        """)
        
        await self.db.commit()
    
    async def log_conversation(self, user_msg: str, assistant_msg: str,
                               session_id: str = None, metadata: Dict = None):
        """Log conversation asynchronously"""
        if not self._initialized:
            await self.initialize()
        
        await self.db.execute("""
            INSERT INTO conversations (timestamp, user_message, assistant_message, session_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            user_msg,
            assistant_msg,
            session_id,
            json.dumps(metadata) if metadata else None
        ))
        await self.db.commit()
    
    async def log_image_generation(self, prompt: str, filepath: str = None,
                                   source: str = "unknown", model: str = None,
                                   success: bool = True, generation_time: float = None,
                                   error_message: str = None, metadata: Dict = None):
        """Log image generation asynchronously"""
        if not self._initialized:
            await self.initialize()
        
        await self.db.execute("""
            INSERT INTO image_generations 
            (timestamp, prompt, filepath, source, model, success, generation_time, error_message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            prompt,
            filepath,
            source,
            model,
            success,
            generation_time,
            error_message,
            json.dumps(metadata) if metadata else None
        ))
        await self.db.commit()
    
    async def get_successful_prompts(self, limit: int = 50) -> List[str]:
        """Get successful prompts for learning"""
        if not self._initialized:
            await self.initialize()
        
        async with self.db.execute("""
            SELECT DISTINCT prompt
            FROM image_generations
            WHERE success = 1 AND filepath IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def analyze_prompts(self, limit: int = 100) -> List[Dict]:
        """Analyze prompts for pattern learning"""
        if not self._initialized:
            await self.initialize()
        
        async with self.db.execute("""
            SELECT 
                prompt,
                COUNT(*) as usage_count,
                AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(generation_time) as avg_time,
                source,
                model
            FROM image_generations
            GROUP BY prompt
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT ?
        """, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_stats(self) -> Dict:
        """Get database statistics"""
        if not self._initialized:
            await self.initialize()
        
        async with self.db.execute("SELECT COUNT(*) FROM conversations") as cursor:
            total_conversations = (await cursor.fetchone())[0]
        
        async with self.db.execute("SELECT COUNT(*) FROM image_generations") as cursor:
            total_images = (await cursor.fetchone())[0]
        
        async with self.db.execute("""
            SELECT AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END)
            FROM image_generations
        """) as cursor:
            success_rate = (await cursor.fetchone())[0] or 0.0
        
        return {
            "total_conversations": total_conversations,
            "total_image_generations": total_images,
            "image_success_rate": round(success_rate * 100, 2),
            "database_path": str(self.db_path.absolute())
        }
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()


class AsyncMemoryManager:
    """
    Unified async memory manager
    Combines short-term (session) and long-term (persistent SQL)
    """
    def __init__(self, db_path: str = "memory/visions_memory.db", 
                 short_term_limit: int = 100):
        self.short_term = AsyncShortTermMemory(max_entries=short_term_limit)
        self.long_term = AsyncSQLMemory(db_path=db_path)
        self._initialized = False
    
    async def initialize(self):
        """Async initialization"""
        if self._initialized:
            return
        
        await self.long_term.initialize()
        self._initialized = True
        
        print(f"🧠 Async Memory System Initialized")
        print(f"   Session ID: {self.short_term.session_id}")
        print(f"   Short-term: {self.short_term.max_entries} entries (in-memory)")
        print(f"   Long-term: {self.long_term.db_path} (SQLite)")
    
    async def remember_conversation(self, user_msg: str, assistant_msg: str):
        """Remember conversation (non-blocking)"""
        # Add to short-term (fast, in-memory)
        await self.short_term.add("conversation", "user", user_msg)
        await self.short_term.add("conversation", "assistant", assistant_msg)
        
        # Save to long-term (async, non-blocking)
        asyncio.create_task(
            self.long_term.log_conversation(
                user_msg, assistant_msg, 
                session_id=self.short_term.session_id
            )
        )
    
    async def remember_image_generation(self, prompt: str, filepath: str = None,
                                       source: str = "unknown", model: str = None,
                                       success: bool = True, generation_time: float = None,
                                       error_message: str = None):
        """Remember image generation (non-blocking)"""
        # Add to short-term
        metadata = {
            "source": source,
            "model": model,
            "success": success,
            "filepath": filepath
        }
        await self.short_term.add("image_generation", "system", prompt, metadata)
        
        # Save to long-term (async)
        asyncio.create_task(
            self.long_term.log_image_generation(
                prompt, filepath, source, model, success, 
                generation_time, error_message
            )
        )
    
    async def get_context_for_model(self, limit: int = 10) -> str:
        """Get recent context for model"""
        history = await self.short_term.get_conversation_history(limit)
        
        if not history:
            return ""
        
        context_parts = []
        for entry in history:
            role = entry['role'].upper()
            content = entry['content'][:200]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    async def print_status(self):
        """Print memory status"""
        stats = await self.long_term.get_stats()
        recent = await self.short_term.get_recent(limit=5)
        
        print("\n" + "="*80)
        print("ASYNC MEMORY SYSTEM STATUS")
        print("="*80)
        print(f"\n📊 Short-Term (Session: {self.short_term.session_id[:19]}):")
        print(f"   Entries: {len(self.short_term.entries)}/{self.short_term.max_entries}")
        print(f"   Recent: {len(recent)} items")
        
        print(f"\n💾 Long-Term (SQL):")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("="*80 + "\n")
    
    async def close(self):
        """Cleanup"""
        await self.long_term.close()


# Example usage
async def main():
    print("="*80)
    print("TESTING ASYNC MEMORY SYSTEM")
    print("="*80)
    
    # Initialize
    memory = AsyncMemoryManager()
    await memory.initialize()
    
    # Simulate some interactions (non-blocking!)
    await memory.remember_conversation(
        "Generate a cinematic photo of the Empire State Building",
        "Here's a professional cinematic photograph..."
    )
    
    await memory.remember_image_generation(
        prompt="Cinematic Empire State Building at sunset",
        filepath="test_output/empire_state.jpg",
        source="ai_studio",
        model="gemini-3-pro-image-preview",
        success=True,
        generation_time=3.5
    )
    
    # Wait a moment for async operations to complete
    await asyncio.sleep(0.5)
    
    # Print status
    await memory.print_status()
    
    # Get context
    context = await memory.get_context_for_model()
    print("Recent Context:")
    print(context)
    
    # Analyze prompts
    print("\n🔍 Analyzing prompts...")
    patterns = await memory.long_term.analyze_prompts()
    for pattern in patterns:
        print(f"   {pattern}")
    
    # Cleanup
    await memory.close()
    
    print("\n✅ Async memory test complete")


if __name__ == "__main__":
    # Check if aiosqlite is installed
    try:
        import aiosqlite
        asyncio.run(main())
    except ImportError:
        print("❌ aiosqlite not installed")
        print("Install with: pip install aiosqlite")
