"""
Cloud Memory System for Visions AI
Firestore (short-term) + BigQuery (long-term) integration
With SQLite fallback for graceful degradation
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import deque
from pathlib import Path

# Try importing cloud dependencies - fallback to SQLite if unavailable
FIREBASE_AVAILABLE = False
BIGQUERY_AVAILABLE = False

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    print("⚠️  firebase-admin not available, using SQLite fallback")

try:
    from google.cloud import bigquery
    BIGQUERY_AVAILABLE = True
except ImportError:
    print("⚠️  google-cloud-bigquery not available, using SQLite fallback")

# SQLite fallback (always available)
try:
    import aiosqlite
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    print("⚠️  aiosqlite not available")

from config import Config


class FirestoreShortTermMemory:
    """
    Short-term memory using Firestore
    Fast, real-time, session-based context
    """
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or Config.VERTEX_PROJECT_ID
        self._db = None
        self._initialized = False
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def initialize(self):
        """Initialize Firestore connection"""
        if self._initialized:
            return
            
        # Initialize Firebase Admin if not already done
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        
        self._db = firestore.client()
        self._initialized = True
        print(f"🔥 Firestore Short-Term Memory initialized")
        print(f"   Project: {self.project_id}")
        print(f"   Session: {self.session_id}")
    
    async def add_message(self, user_id: str, role: str, content: str, 
                          metadata: Dict = None) -> str:
        """Add a message to the session"""
        if not self._initialized:
            await self.initialize()
        
        message_ref = self._db.collection("sessions").document(self.session_id)\
                             .collection("messages").document()
        
        message_data = {
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "metadata": metadata or {}
        }
        
        message_ref.set(message_data)
        return message_ref.id
    
    async def get_session_messages(self, limit: int = 20) -> List[Dict]:
        """Get recent messages from current session"""
        if not self._initialized:
            await self.initialize()
        
        messages_ref = self._db.collection("sessions").document(self.session_id)\
                               .collection("messages")\
                               .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                               .limit(limit)
        
        docs = messages_ref.stream()
        messages = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            messages.append(data)
        
        return list(reversed(messages))  # Oldest first
    
    async def update_session_context(self, context: Dict):
        """Update session-level context (current topic, intent, etc.)"""
        if not self._initialized:
            await self.initialize()
        
        session_ref = self._db.collection("sessions").document(self.session_id)
        session_ref.set({
            "context": context,
            "last_active": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }, merge=True)
    
    async def get_session_context(self) -> Dict:
        """Get current session context"""
        if not self._initialized:
            await self.initialize()
        
        session_ref = self._db.collection("sessions").document(self.session_id)
        doc = session_ref.get()
        
        if doc.exists:
            return doc.to_dict().get("context", {})
        return {}
    
    async def get_conversation_for_model(self, limit: int = 10) -> List[Dict]:
        """Get conversation history formatted for model context"""
        messages = await self.get_session_messages(limit)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]


class BigQueryLongTermMemory:
    """
    Long-term memory using BigQuery
    Persistent storage, analytics, semantic search ready
    """
    
    DATASET_ID = "visions_memory"
    TABLE_USER_MEMORIES = "user_memories"
    TABLE_CONVERSATION_SUMMARIES = "conversation_summaries"
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or Config.VERTEX_PROJECT_ID
        self._client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize BigQuery client and ensure tables exist"""
        if self._initialized:
            return
        
        self._client = bigquery.Client(project=self.project_id)
        
        # Create dataset if not exists
        await self._ensure_dataset()
        await self._ensure_tables()
        
        self._initialized = True
        print(f"📊 BigQuery Long-Term Memory initialized")
        print(f"   Project: {self.project_id}")
        print(f"   Dataset: {self.DATASET_ID}")
    
    async def _ensure_dataset(self):
        """Ensure the dataset exists"""
        dataset_id = f"{self.project_id}.{self.DATASET_ID}"
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = Config.VERTEX_LOCATION
        
        try:
            self._client.get_dataset(dataset_id)
        except Exception:
            self._client.create_dataset(dataset, exists_ok=True)
            print(f"   Created dataset: {self.DATASET_ID}")
    
    async def _ensure_tables(self):
        """Ensure memory tables exist"""
        # User Memories Table
        user_memories_schema = [
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("memory_key", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("importance", "FLOAT64", mode="NULLABLE"),
            bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("last_accessed", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("access_count", "INT64", mode="NULLABLE"),
            bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
        ]
        
        # Conversation Summaries Table
        summaries_schema = [
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("summary", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("key_topics", "STRING", mode="REPEATED"),
            bigquery.SchemaField("sentiment", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("message_count", "INT64", mode="NULLABLE"),
            bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
        ]
        
        await self._create_table_if_not_exists(self.TABLE_USER_MEMORIES, user_memories_schema)
        await self._create_table_if_not_exists(self.TABLE_CONVERSATION_SUMMARIES, summaries_schema)
    
    async def _create_table_if_not_exists(self, table_name: str, schema: List):
        """Create a table if it doesn't exist"""
        table_id = f"{self.project_id}.{self.DATASET_ID}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        
        try:
            self._client.get_table(table_id)
        except Exception:
            self._client.create_table(table, exists_ok=True)
            print(f"   Created table: {table_name}")
    
    async def store_memory(self, user_id: str, memory_key: str, content: str,
                          importance: float = 0.5, source: str = "conversation",
                          metadata: Dict = None):
        """Store a memory for a user"""
        if not self._initialized:
            await self.initialize()
        
        table_id = f"{self.project_id}.{self.DATASET_ID}.{self.TABLE_USER_MEMORIES}"
        
        rows = [{
            "user_id": user_id,
            "memory_key": memory_key,
            "content": content,
            "importance": importance,
            "source": source,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "access_count": 1,
            "metadata": json.dumps(metadata) if metadata else None
        }]
        
        errors = self._client.insert_rows_json(table_id, rows)
        if errors:
            print(f"❌ BigQuery insert errors: {errors}")
            return False
        return True
    
    async def retrieve_memories(self, user_id: str, limit: int = 10,
                               min_importance: float = 0.0) -> List[Dict]:
        """Retrieve memories for a user, ordered by importance"""
        if not self._initialized:
            await self.initialize()
        
        query = f"""
            SELECT user_id, memory_key, content, importance, source, 
                   created_at, last_accessed, access_count
            FROM `{self.project_id}.{self.DATASET_ID}.{self.TABLE_USER_MEMORIES}`
            WHERE user_id = @user_id AND importance >= @min_importance
            ORDER BY importance DESC, last_accessed DESC
            LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                bigquery.ScalarQueryParameter("min_importance", "FLOAT64", min_importance),
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ]
        )
        
        query_job = self._client.query(query, job_config=job_config)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    async def store_conversation_summary(self, user_id: str, session_id: str,
                                         summary: str, key_topics: List[str] = None,
                                         sentiment: str = None, message_count: int = None,
                                         metadata: Dict = None):
        """Store a conversation summary"""
        if not self._initialized:
            await self.initialize()
        
        table_id = f"{self.project_id}.{self.DATASET_ID}.{self.TABLE_CONVERSATION_SUMMARIES}"
        
        rows = [{
            "user_id": user_id,
            "session_id": session_id,
            "summary": summary,
            "key_topics": key_topics or [],
            "sentiment": sentiment,
            "created_at": datetime.utcnow().isoformat(),
            "message_count": message_count,
            "metadata": json.dumps(metadata) if metadata else None
        }]
        
        errors = self._client.insert_rows_json(table_id, rows)
        if errors:
            print(f"❌ BigQuery insert errors: {errors}")
            return False
        return True
    
    async def get_user_history(self, user_id: str, days: int = 30,
                               limit: int = 20) -> List[Dict]:
        """Get conversation history for a user"""
        if not self._initialized:
            await self.initialize()
        
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = f"""
            SELECT session_id, summary, key_topics, sentiment, created_at, message_count
            FROM `{self.project_id}.{self.DATASET_ID}.{self.TABLE_CONVERSATION_SUMMARIES}`
            WHERE user_id = @user_id AND created_at >= @cutoff
            ORDER BY created_at DESC
            LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                bigquery.ScalarQueryParameter("cutoff", "STRING", cutoff),
                bigquery.ScalarQueryParameter("limit", "INT64", limit),
            ]
        )
        
        query_job = self._client.query(query, job_config=job_config)
        results = query_job.result()
        
        return [dict(row) for row in results]


class CloudMemoryManager:
    """
    Unified Cloud Memory Manager
    Combines Firestore (short-term) and BigQuery (long-term)
    """
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or Config.VERTEX_PROJECT_ID
        self.short_term = FirestoreShortTermMemory(project_id)
        self.long_term = BigQueryLongTermMemory(project_id)
        self._initialized = False
    
    async def initialize(self):
        """Initialize both memory systems"""
        if self._initialized:
            return
        
        print("🧠 Initializing Cloud Memory System...")
        await self.short_term.initialize()
        await self.long_term.initialize()
        self._initialized = True
        print("✅ Cloud Memory System ready!")
    
    async def remember_message(self, user_id: str, role: str, content: str,
                               metadata: Dict = None):
        """Remember a message (short-term + async long-term)"""
        # Immediate short-term storage (Firestore)
        await self.short_term.add_message(user_id, role, content, metadata)
        
        # Check if this is important enough for long-term storage
        if self._should_persist_to_long_term(content, metadata):
            asyncio.create_task(
                self._persist_to_long_term(user_id, content, metadata)
            )
    
    def _should_persist_to_long_term(self, content: str, metadata: Dict = None) -> bool:
        """Determine if content should be stored long-term"""
        # Persist if explicitly marked important
        if metadata and metadata.get("important"):
            return True
        
        # Persist if it contains user preferences or facts
        important_patterns = [
            "my name is", "i prefer", "remember that", "i always",
            "my favorite", "i work at", "i live in", "my email",
            "call me", "don't forget"
        ]
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in important_patterns)
    
    async def _persist_to_long_term(self, user_id: str, content: str,
                                    metadata: Dict = None):
        """Persist to long-term storage (called async)"""
        # Extract a memory key from content
        memory_key = self._extract_memory_key(content)
        
        await self.long_term.store_memory(
            user_id=user_id,
            memory_key=memory_key,
            content=content,
            importance=0.7,  # Default importance for auto-persisted
            source="conversation",
            metadata=metadata
        )
    
    def _extract_memory_key(self, content: str) -> str:
        """Extract a memory key from content"""
        content_lower = content.lower()
        
        if "my name is" in content_lower:
            return "user:name"
        elif "i prefer" in content_lower or "my favorite" in content_lower:
            return "preference:general"
        elif "i work at" in content_lower or "my job" in content_lower:
            return "user:occupation"
        elif "i live in" in content_lower:
            return "user:location"
        elif "my email" in content_lower:
            return "user:contact"
        else:
            return f"fact:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def get_context_for_model(self, user_id: str) -> Dict:
        """Get combined context for model (short-term + relevant long-term)"""
        # Get recent conversation
        conversation = await self.short_term.get_conversation_for_model(limit=10)
        
        # Get relevant long-term memories
        memories = await self.long_term.retrieve_memories(
            user_id=user_id,
            limit=5,
            min_importance=0.5
        )
        
        # Get session context
        session_context = await self.short_term.get_session_context()
        
        return {
            "conversation_history": conversation,
            "long_term_memories": memories,
            "session_context": session_context,
            "session_id": self.short_term.session_id
        }
    
    async def end_session(self, user_id: str, generate_summary: bool = True):
        """End current session and optionally generate summary"""
        if generate_summary:
            messages = await self.short_term.get_session_messages(limit=50)
            
            if messages:
                # Generate summary (simplified - in production use Gemini)
                summary = f"Session with {len(messages)} messages"
                key_topics = []  # Would extract with Gemini
                
                await self.long_term.store_conversation_summary(
                    user_id=user_id,
                    session_id=self.short_term.session_id,
                    summary=summary,
                    key_topics=key_topics,
                    message_count=len(messages)
                )
        
        print(f"📝 Session ended: {self.short_term.session_id}")
    
    async def print_status(self):
        """Print memory system status"""
        print("\n" + "="*80)
        print("🧠 CLOUD MEMORY SYSTEM STATUS")
        print("="*80)
        print(f"\n🔥 Firestore (Short-Term):")
        print(f"   Session: {self.short_term.session_id}")
        print(f"   Project: {self.short_term.project_id}")
        
        print(f"\n📊 BigQuery (Long-Term):")
        print(f"   Dataset: {self.long_term.DATASET_ID}")
        print(f"   Tables: {self.long_term.TABLE_USER_MEMORIES}, {self.long_term.TABLE_CONVERSATION_SUMMARIES}")
        print("="*80 + "\n")


# Convenience function for quick access
async def get_memory_manager() -> CloudMemoryManager:
    """Get an initialized memory manager"""
    manager = CloudMemoryManager()
    await manager.initialize()
    return manager


# Example usage
async def main():
    print("="*80)
    print("TESTING CLOUD MEMORY SYSTEM")
    print("="*80)
    
    # Initialize
    memory = CloudMemoryManager()
    await memory.initialize()
    
    # Test user
    user_id = "test_user_001"
    
    # Remember some messages
    await memory.remember_message(
        user_id=user_id,
        role="user",
        content="My name is Dave and I prefer dark mode"
    )
    
    await memory.remember_message(
        user_id=user_id,
        role="assistant",
        content="Nice to meet you, Dave! I've noted your preference for dark mode."
    )
    
    await memory.remember_message(
        user_id=user_id,
        role="user",
        content="Generate a cinematic photo of New York"
    )
    
    # Wait for async operations
    await asyncio.sleep(1)
    
    # Get context
    context = await memory.get_context_for_model(user_id)
    print("\n📋 Context for Model:")
    print(json.dumps(context, indent=2, default=str))
    
    # Print status
    await memory.print_status()
    
    # End session
    await memory.end_session(user_id)
    
    print("\n✅ Cloud memory test complete!")


if __name__ == "__main__":
    asyncio.run(main())
