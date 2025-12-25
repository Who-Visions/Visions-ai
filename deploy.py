import vertexai
from vertexai.preview import reasoning_engines
from visions.core.agent import VisionsAgent
from google.cloud import storage
import os
import glob

# Configuration
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"
STAGING_BUCKET_URI = f"gs://{PROJECT_ID}-reasoning-artifacts"
STAGING_BUCKET_NAME = f"{PROJECT_ID}-reasoning-artifacts"

# Initialize SDK locally just for the build process
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET_URI)

def upload_directory_to_gcs(bucket_name, source_dir, destination_prefix):
    """Uploads a directory to GCS."""
    print(f"[UPLOAD] Uploading {source_dir} to gs://{bucket_name}/{destination_prefix}...")
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)

    files = glob.glob(f"{source_dir}/**", recursive=True)
    for file_path in files:
        if os.path.isfile(file_path):
            rel_path = os.path.relpath(file_path, source_dir)
            blob_path = os.path.join(destination_prefix, rel_path)
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(file_path)
            print(f"Uploaded {rel_path}")

# Upload Vector Store
if os.path.exists("vector_store"):
    upload_directory_to_gcs(STAGING_BUCKET_NAME, "vector_store", "vector_store")
else:
    print("[WARN] Warning: 'vector_store' directory not found.")

print(f"[DEPLOY] Deploying VisionsAgent to Vertex AI Reasoning Engine...")
print(f"Target Project: {PROJECT_ID}")

# Create the remote managed resource
remote_agent = reasoning_engines.ReasoningEngine.create(
    VisionsAgent(project=PROJECT_ID, location=LOCATION),
    requirements=[
        "google-cloud-aiplatform[reasoningengine,langchain]",
        "google-adk",
        "google-genai",
        "cloudpickle",
        "requests",
        "Pillow",
        "faiss-cpu",
        "langchain-community",
        "langchain-google-vertexai",
        "google-cloud-storage",
        "rich",
        # Memory System Dependencies
        "google-cloud-bigquery",
        "firebase-admin",
        "aiosqlite",  # SQLite fallback
    ],
    extra_packages=[
        "visions/core/agent.py", 
        "tools/", 
        "visions/modules/memory/memory_cloud.py", 
        "visions/core/config.py",
        "visions/core/visions_backend.py",
        "visions/modules/genai/genai_embeddings.py",
        "visions/modules/cost/cost_intelligence.py"
    ],
    display_name="Visions-AI-Reasoning-Agent",
    description="Visions AI Agent with Cloud Memory (Firestore + BigQuery)",
)

print("\n[SUCCESS] Deployment Complete!")
print(f"Resource Name: {remote_agent.resource_name}")
print("Agent is now live in Vertex AI Agent Builder > Reasoning Engine")
