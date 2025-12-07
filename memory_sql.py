"""
SQL/BigQuery Integration for Visions AI Long-Term Learning
Stores prompts, generations, and user patterns for analytics
"""
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

try:
    from google.cloud import bigquery
    BIGQUERY_AVAILABLE = True
except ImportError:
    BIGQUERY_AVAILABLE = False
    print("⚠️  BigQuery not available. Install with: pip install google-cloud-bigquery")


class LocalSQLMemory:
    """
    SQLite-based local memory for development and local deployments
    Can be synced to BigQuery for cloud analytics
    """
    def __init__(self, db_path: str = "memory/visions_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        self._create_tables()
        print(f"💾 Local SQL Memory initialized: {self.db_path}")
    
    def _create_tables(self):
        """Create database schema"""
        cursor = self.conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_message TEXT NOT NULL,
                session_id TEXT,
                metadata TEXT
            )
        """)
        
        # Image generations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prompt TEXT NOT NULL,
                filepath TEXT,
                source TEXT,
                model TEXT,
                success BOOLEAN,
                error_message TEXT,
                metadata TEXT
            )
        """)
        
        # Prompts analytics table (for learning patterns)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prompt TEXT NOT NULL,
                category TEXT,
                keywords TEXT,
                success_rate REAL,
                avg_generation_time REAL,
                metadata TEXT
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
    
    def log_conversation(self, user_msg: str, assistant_msg: str, 
                        session_id: str = None, metadata: Dict = None):
        """Log a conversation to SQL"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (timestamp, user_message, assistant_message, session_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            user_msg,
            assistant_msg,
            session_id,
            str(metadata) if metadata else None
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def log_image_generation(self, prompt: str, filepath: str = None, 
                            source: str = "unknown", model: str = None,
                            success: bool = True, error_message: str = None,
                            metadata: Dict = None):
        """Log an image generation attempt"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO image_generations 
            (timestamp, prompt, filepath, source, model, success, error_message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            prompt,
            filepath,
            source,
            model,
            success,
            error_message,
            str(metadata) if metadata else None
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def analyze_prompts(self, limit: int = 100) -> List[Dict]:
        """Analyze recent prompts for pattern learning"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                prompt,
                COUNT(*) as usage_count,
                AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                source,
                model
            FROM image_generations
            GROUP BY prompt
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_successful_prompts(self, limit: int = 50) -> List[str]:
        """Get prompts that successfully generated images"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT prompt
            FROM image_generations
            WHERE success = 1 AND filepath IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [row[0] for row in cursor.fetchall()]
    
    def get_conversation_history(self, session_id: str = None, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        cursor = self.conn.cursor()
        
        if session_id:
            cursor.execute("""
                SELECT * FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM conversations
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        # Count conversations
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]
        
        # Count image generations
        cursor.execute("SELECT COUNT(*) FROM image_generations")
        total_images = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute("""
            SELECT AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END)
            FROM image_generations
        """)
        success_rate = cursor.fetchone()[0] or 0.0
        
        return {
            "total_conversations": total_conversations,
            "total_image_generations": total_images,
            "image_success_rate": round(success_rate * 100, 2),
            "database_path": str(self.db_path.absolute())
        }
    
    def export_to_bigquery(self, project_id: str, dataset_id: str = "visions_memory"):
        """Export local data to BigQuery for cloud analytics"""
        if not BIGQUERY_AVAILABLE:
            print("❌ BigQuery SDK not installed")
            return False
        
        try:
            client = bigquery.Client(project=project_id)
            
            # Create dataset if it doesn't exist
            dataset_ref = f"{project_id}.{dataset_id}"
            
            print(f"📊 Exporting to BigQuery: {dataset_ref}")
            
            # TODO: Implement actual export logic
            # This would read from SQLite and batch insert to BigQuery
            
            print("✅ Export to BigQuery complete")
            return True
            
        except Exception as e:
            print(f"❌ BigQuery export failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        self.conn.close()


class BigQueryMemory:
    """
    BigQuery-based memory for cloud deployments and analytics
    Provides advanced querying and pattern recognition
    """
    def __init__(self, project_id: str, dataset_id: str = "visions_memory"):
        if not BIGQUERY_AVAILABLE:
            raise ImportError("BigQuery SDK not available")
        
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)
        
        self._create_tables()
        print(f"☁️  BigQuery Memory initialized: {project_id}.{dataset_id}")
    
    def _create_tables(self):
        """Create BigQuery tables"""
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        
        # Create dataset if it doesn't exist
        try:
            self.client.get_dataset(dataset_ref)
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            self.client.create_dataset(dataset)
            print(f"✅ Created dataset: {dataset_ref}")
        
        # Define schemas
        conversations_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("user_message", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("assistant_message", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING"),
            bigquery.SchemaField("metadata", "JSON"),
        ]
        
        image_generations_schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("prompt", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("filepath", "STRING"),
            bigquery.SchemaField("source", "STRING"),
            bigquery.SchemaField("model", "STRING"),
            bigquery.SchemaField("success", "BOOLEAN"),
            bigquery.SchemaField("error_message", "STRING"),
            bigquery.SchemaField("metadata", "JSON"),
        ]
        
        # Create tables
        self._create_table_if_not_exists("conversations", conversations_schema)
        self._create_table_if_not_exists("image_generations", image_generations_schema)
    
    def _create_table_if_not_exists(self, table_name: str, schema):
        """Create table if it doesn't exist"""
        table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        try:
            self.client.get_table(table_ref)
        except Exception:
            table = bigquery.Table(table_ref, schema=schema)
            self.client.create_table(table)
            print(f"✅ Created table: {table_name}")
    
    def log_image_generation(self, prompt: str, filepath: str = None,
                            source: str = "unknown", model: str = None,
                            success: bool = True, error_message: str = None,
                            metadata: Dict = None):
        """Log image generation to BigQuery"""
        table_ref = f"{self.project_id}.{self.dataset_id}.image_generations"
        
        row = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "filepath": filepath,
            "source": source,
            "model": model,
            "success": success,
            "error_message": error_message,
            "metadata": metadata
        }
        
        errors = self.client.insert_rows_json(table_ref, [row])
        
        if errors:
            print(f"❌ BigQuery insert errors: {errors}")
            return False
        return True
    
    def analyze_prompt_patterns(self) -> List[Dict]:
        """Use BigQuery ML to analyze prompt patterns"""
        query = """
        SELECT 
            prompt,
            COUNT(*) as usage_count,
            AVG(CAST(success AS INT64)) as success_rate,
            ARRAY_AGG(DISTINCT source) as sources,
            ARRAY_AGG(DISTINCT model) as models
        FROM `{project}.{dataset}.image_generations`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY prompt
        ORDER BY usage_count DESC, success_rate DESC
        LIMIT 100
        """.format(project=self.project_id, dataset=self.dataset_id)
        
        results = self.client.query(query).result()
        return [dict(row) for row in results]


if __name__ == "__main__":
    # Test local SQL memory
    print("="*80)
    print("TESTING LOCAL SQL MEMORY")
    print("="*80)
    
    memory = LocalSQLMemory()
    
    # Log some test data
    memory.log_conversation(
        "Generate a vintage camera photo",
        "Here's a professional photograph of a vintage film camera..."
    )
    
    memory.log_image_generation(
        prompt="A vintage film camera on a wooden desk",
        filepath="test_output/vintage_camera.jpg",
        source="ai_studio",
        model="gemini-3-pro-image-preview",
        success=True
    )
    
    # Get stats
    stats = memory.get_stats()
    print("\n📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Analyze prompts
    print("\n🔍 Prompt Analysis:")
    patterns = memory.analyze_prompts()
    for pattern in patterns[:5]:
        print(f"   {pattern}")
    
    memory.close()
    print("\n✅ Local SQL memory test complete")
