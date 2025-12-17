import os
import time
from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import vertexai
from config import Config

# Config
PROJECT_ID = Config.VERTEX_PROJECT_ID
LOCATION = Config.VERTEX_LOCATION
# Index both the X drive, local knowledge base, and transcripts
SOURCE_DIRS = ["/mnt/x", "knowledge_base", "knowledge_base/transcripts"]
INDEX_DIR = Config.VECTOR_STORE_PREFIX
BATCH_SIZE = 50  # Process documents in batches of 50 to manage memory

def load_documents_batch(source_dirs: List[str], batch_size: int):
    """
    Generator that yields batches of documents.
    """
    all_files = []
    
    # Gather all file paths first
    for directory in source_dirs:
        if not os.path.exists(directory):
            print(f"⚠️ Directory not found: {directory}")
            continue
            
        print(f"📂 Scanning {directory}...")
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".txt") or file.endswith(".md"):
                    all_files.append(os.path.join(root, file))
    
    print(f"📄 Found total {len(all_files)} files to index.")
    
    # Yield batches
    current_batch = []
    for file_path in all_files:
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            docs = loader.load()
            current_batch.extend(docs)
            
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []
        except Exception as e:
            print(f"⚠️ Error loading {file_path}: {e}")
            
    if current_batch:
        yield current_batch

def build_index():
    print(f"🚀 Initializing Vertex AI for project {PROJECT_ID}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # Initialize embeddings
    print("🧠 Initializing Embeddings model (text-embedding-004)...")
    embedding_model = VertexAIEmbeddings(model_name="text-embedding-004")
    
    # Initialize splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    vector_store = None
    total_chunks = 0
    batc_num = 0
    
    # Process in batches
    for batch_docs in load_documents_batch(SOURCE_DIRS, BATCH_SIZE):
        batc_num += 1
        print(f"\n📦 Processing Batch {batc_num} ({len(batch_docs)} docs)...")
        
        # Split
        splits = text_splitter.split_documents(batch_docs)
        if not splits:
            continue
            
        print(f"   🧩 Generated {len(splits)} chunks.")
        
        # Embed and Add to Index
        if vector_store is None:
            # First batch determines the store
            vector_store = FAISS.from_documents(splits, embedding_model)
        else:
            # Subsequent batches are added
            vector_store.add_documents(splits)
            
        total_chunks += len(splits)
        print(f"   ✅ Batch {batc_num} added. Total chunks: {total_chunks}")
        
        # Optional: Save intermediate result?
        # vector_store.save_local(INDEX_DIR + "_temp")
    
    if vector_store:
        print(f"\n💾 Saving final index to {INDEX_DIR}...")
        vector_store.save_local(INDEX_DIR)
        print(f"✅ Index built successfully! Total Documents: {total_chunks}")
    else:
        print("❌ No documents were successfully processed.")

if __name__ == "__main__":
    build_index()
