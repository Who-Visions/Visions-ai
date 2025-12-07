"""
Visions GCP Memory Persistence
================================
Syncs Visions' learned knowledge to Google Cloud Platform:
- Long-term memory → Cloud Storage (JSON backup)
- Concept mastery → BigQuery (queryable knowledge base)
- Brain evolution → Cloud Storage (historical tracking)

This ensures Visions' hard-earned knowledge persists across sessions.
"""

from google.cloud import storage, bigquery
from datetime import datetime
import json
import os
from pathlib import Path

class VisionsMemorySync:
    """
    Syncs Visions' knowledge to GCP for persistence.
    """
    
    def __init__(self, project_id: str = "who-visions-dav1d"):
        """Initialize GCP clients"""
        self.project_id = project_id
        self.storage_client = storage.Client(project=project_id)
        self.bq_client = bigquery.Client(project=project_id)
        
        # GCS bucket for knowledge storage
        self.bucket_name = "visions-arnheim-knowledge"
        self.bucket = self._ensure_bucket()
        
        # BigQuery dataset for queryable knowledge
        self.dataset_id = "visions_knowledge"
        self.table_id = "concept_mastery"
        self._ensure_bigquery_schema()
    
    def _ensure_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            bucket = self.storage_client.get_bucket(self.bucket_name)
            print(f"✓ Using existing bucket: {self.bucket_name}")
        except:
            bucket = self.storage_client.create_bucket(
                self.bucket_name,
                location="us-east4"
            )
            print(f"✓ Created new bucket: {self.bucket_name}")
        return bucket
    
    def _ensure_bigquery_schema(self):
        """Create BigQuery table if it doesn't exist"""
        dataset_ref = self.bq_client.dataset(self.dataset_id)
        
        # Create dataset if needed
        try:
            self.bq_client.get_dataset(dataset_ref)
        except:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "us-east4"
            self.bq_client.create_dataset(dataset)
            print(f"✓ Created BigQuery dataset: {self.dataset_id}")
        
        # Define schema for concept mastery
        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("concept", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("classical_score", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("modern_application", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("synthesis_level", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("mastery", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("academic_year", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("course_attempt", "INTEGER", mode="REQUIRED"),
        ]
        
        table_ref = dataset_ref.table(self.table_id)
        try:
            self.bq_client.get_table(table_ref)
            print(f"✓ Using existing table: {self.table_id}")
        except:
            table = bigquery.Table(table_ref, schema=schema)
            self.bq_client.create_table(table)
            print(f"✓ Created BigQuery table: {self.table_id}")
    
    def sync_memory(self, brain):
        """
        Sync Visions' complete memory state to GCP
        
        Args:
            brain: VisionsArtBrain instance
        """
        timestamp = datetime.utcnow().isoformat()
        
        print("\n" + "="*60)
        print("☁️  SYNCING VISIONS' MEMORY TO GCP")
        print("="*60)
        
        # 1. Sync long-term memory to Cloud Storage (JSON backup)
        memory_data = {
            "timestamp": timestamp,
            "course_attempts": brain.course_attempts,
            "memory_strength": brain.memory_strength,
            "long_term_memory": {
                concept.value: score 
                for concept, score in brain.long_term_memory.items()
            },
            "brain_evolution": [
                {
                    "year": state.year.name,
                    "pattern_recognition": state.pattern_recognition,
                    "abstraction": state.abstraction,
                    "modern_translation": state.modern_translation,
                    "creative_synthesis": state.creative_synthesis,
                    "evolution_score": state.evolution_score
                }
                for state in brain.brain_states
            ]
        }
        
        blob = self.bucket.blob(f"memory_snapshots/{timestamp}_memory.json")
        blob.upload_from_string(
            json.dumps(memory_data, indent=2),
            content_type="application/json"
        )
        print(f"   ✓ Uploaded memory snapshot to GCS")
        
        # 2. Sync concept mastery to BigQuery (queryable)
        if brain.learning_outcomes:
            rows_to_insert = []
            for concept, outcome in brain.learning_outcomes.items():
                rows_to_insert.append({
                    "timestamp": datetime.utcnow(),
                    "concept": concept.value,
                    "classical_score": outcome.classical_score,
                    "modern_application": outcome.modern_application,
                    "synthesis_level": outcome.synthesis_level,
                    "mastery": outcome.mastery,
                    "academic_year": outcome.year.name,
                    "course_attempt": brain.course_attempts,
                })
            
            table_ref = self.bq_client.dataset(self.dataset_id).table(self.table_id)
            errors = self.bq_client.insert_rows_json(table_ref, rows_to_insert)
            
            if errors:
                print(f"   ⚠️  BigQuery insert errors: {errors}")
            else:
                print(f"   ✓ Synced {len(rows_to_insert)} concept masteries to BigQuery")
        
        # 3. Upload current transcript
        transcript = brain.generate_transcript()
        blob = self.bucket.blob(f"transcripts/{timestamp}_transcript.json")
        blob.upload_from_string(
            json.dumps(transcript, indent=2),
            content_type="application/json"
        )
        print(f"   ✓ Uploaded transcript to GCS")
        
        print(f"\n   📊 Memory Stats:")
        print(f"      Course Attempts: {brain.course_attempts}")
        print(f"      Memory Strength: {brain.memory_strength:.2%}")
        print(f"      GCS Bucket: gs://{self.bucket_name}/")
        print(f"      BigQuery: {self.project_id}.{self.dataset_id}.{self.table_id}")
        print("="*60 + "\n")
    
    def load_latest_memory(self, brain):
        """
        Load Visions' most recent memory state from GCP
        
        Args:
            brain: VisionsArtBrain instance to populate
        """
        print("\n" + "="*60)
        print("☁️  LOADING VISIONS' MEMORY FROM GCP")
        print("="*60)
        
        # List all memory snapshots
        blobs = list(self.bucket.list_blobs(prefix="memory_snapshots/"))
        
        if not blobs:
            print("   ⚠️  No previous memory found in GCP")
            print("="*60 + "\n")
            return False
        
        # Get most recent snapshot
        latest_blob = max(blobs, key=lambda b: b.time_created)
        memory_data = json.loads(latest_blob.download_as_string())
        
        # Restore memory state
        brain.course_attempts = memory_data["course_attempts"]
        brain.memory_strength = memory_data["memory_strength"]
        
        # Restore long-term memory
        from test_visions_arnheim_curriculum import Concept
        brain.long_term_memory = {
            Concept(concept_name): score
            for concept_name, score in memory_data["long_term_memory"].items()
        }
        
        print(f"   ✓ Loaded memory from {latest_blob.name}")
        print(f"   📊 Restored State:")
        print(f"      Course Attempts: {brain.course_attempts}")
        print(f"      Memory Strength: {brain.memory_strength:.2%}")
        print(f"      Concepts in Memory: {len(brain.long_term_memory)}")
        print("="*60 + "\n")
        
        return True


def demo_sync():
    """Demo the GCP sync functionality"""
    import sys
    sys.path.insert(0, 'tests')
    from test_visions_arnheim_curriculum import VisionsArtBrain, CURRICULUM, AcademicYear
    
    print("\n🌟 VISIONS MEMORY PERSISTENCE DEMO\n")
    
    # Create a brain with some learning
    brain = VisionsArtBrain()
    brain.enroll(AcademicYear.FRESHMAN)
    
    # Study a few concepts
    for concept_data in CURRICULUM[AcademicYear.FRESHMAN]["concepts"][:2]:
        brain.study(concept_data["concept"], concept_data["material"])
    
    brain.evolve_brain()
    brain.consolidate_memory()
    
    # Sync to GCP
    syncer = VisionsMemorySync()
    syncer.sync_memory(brain)
    
    print("✅ Demo complete! Visions' knowledge is now persisted in GCP.")
    print(f"   View in console: https://console.cloud.google.com/storage/browser/visions-arnheim-knowledge")


if __name__ == "__main__":
    demo_sync()
