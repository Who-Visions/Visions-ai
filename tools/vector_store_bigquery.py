import os
import json
import uuid
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

class BigQueryVectorStore:
    def __init__(self, project_id: str, location: str, dataset_id: str = "visions_memory"):
        self.project_id = project_id
        self.location = location
        self.dataset_id = dataset_id
        self.table_id = "embeddings"
        
        self.client = bigquery.Client(project=project_id)
        aiplatform.init(project=project_id, location=location)
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    def initialize_dataset(self):
        """Ensures the dataset and table exist."""
        dataset_ref = self.client.dataset(self.dataset_id)
        try:
            self.client.get_dataset(dataset_ref)
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = self.location
            self.client.create_dataset(dataset)
            print(f"Created dataset {self.dataset_id}.")

        table_ref = dataset_ref.table(self.table_id)
        try:
            self.client.get_table(table_ref)
        except Exception:
            schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="NULLABLE"),
            ]
            table = bigquery.Table(table_ref, schema=schema)
            self.client.create_table(table)
            print(f"Created table {self.table_id}.")

    def get_embedding(self, text: str) -> List[float]:
        """Generates embedding using Vertex AI."""
        embeddings = self.embedding_model.get_embeddings([text])
        return embeddings[0].values

    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        """Adds a text memory with its embedding to BigQuery."""
        embedding = self.get_embedding(text)
        
        row = {
            "id": str(uuid.uuid4()),
            "content": text,
            "metadata": json.dumps(metadata) if metadata else None,
            "embedding": embedding,
            "created_at": "CURRENT_TIMESTAMP()" # Let BQ handle timestamp or pass explicit
        }
        
        # Insert rows (using insert_rows_json avoids explicit SQL construction)
        # Note: CURRENT_TIMESTAMP() doesn't work in json insert, need actual time or rely on default?
        # Let's drop created_at from dict and handle it via SQL or just insert without it for now (v1)
        # Or better:
        from datetime import datetime
        row["created_at"] = datetime.utcnow().isoformat()

        errors = self.client.insert_rows_json(f"{self.project_id}.{self.dataset_id}.{self.table_id}", [row])
        if errors:
            raise Exception(f"BigQuery Insert Errors: {errors}")

    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches for similar memories using vector search."""
        query_embedding = self.get_embedding(query)
        
        # SQL for vector search using cosine distance
        sql = f"""
        SELECT
            id,
            content,
            metadata,
            1 - COSINE_DISTANCE(embedding, {query_embedding}) as similarity
        FROM
            `{self.project_id}.{self.dataset_id}.{self.table_id}`
        ORDER BY
            similarity DESC
        LIMIT {limit}
        """
        
        query_job = self.client.query(sql)
        results = []
        for row in query_job:
            try:
                meta = json.loads(row.metadata) if row.metadata else {}
            except:
                meta = {}
                
            results.append({
                "id": row.id,
                "content": row.content,
                "metadata": meta,
                "similarity": row.similarity
            })
        return results
