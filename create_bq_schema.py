
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, Conflict
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "endless-duality-480201-t3")
DATASET_ID = "visions_memory"
TABLE_ID = "interaction_logs"

def create_schema():
    client = bigquery.Client(project=PROJECT_ID)
    
    # 1. Create Dataset
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    
    try:
        client.create_dataset(dataset, timeout=30)
        print(f"✅ Created dataset {dataset_ref}")
    except Conflict:
        print(f"⚠️  Dataset {dataset_ref} already exists")
    except Exception as e:
        print(f"❌ Failed to create dataset: {e}")
        return

    # 2. Create Table
    table_ref = f"{dataset_ref}.{TABLE_ID}"
    schema = [
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("prompt", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("response", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    table = bigquery.Table(table_ref, schema=schema)
    
    try:
        client.create_table(table, timeout=30)
        print(f"✅ Created table {table_ref}")
    except Conflict:
        print(f"⚠️  Table {table_ref} already exists")
    except Exception as e:
        print(f"❌ Failed to create table: {e}")

if __name__ == "__main__":
    create_schema()
