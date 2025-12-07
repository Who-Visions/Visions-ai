import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import vertexai

# Config
PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"
# Index both the X drive and the local knowledge base (where key_facts.txt is)
SOURCE_DIRS = ["/mnt/x", "knowledge_base"]
INDEX_DIR = "vector_store"

def build_index():
    print(f"🚀 Initializing Vertex AI for project {PROJECT_ID}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    documents = []
    
    for directory in SOURCE_DIRS:
        print(f"📚 Loading documents from {directory}...")
        
        if not os.path.exists(directory):
            print(f"⚠️ Directory not found: {directory}")
            continue

        # Load .txt files
        try:
            loader_txt = DirectoryLoader(directory, glob="**/*.txt", loader_cls=TextLoader, show_progress=True)
            docs_txt = loader_txt.load()
            print(f"   - Found {len(docs_txt)} .txt files")
            documents.extend(docs_txt)
        except Exception as e:
            print(f"⚠️ Error loading .txt files from {directory}: {e}")

        # Load .md files
        try:
            loader_md = DirectoryLoader(directory, glob="**/*.md", loader_cls=TextLoader, show_progress=True)
            docs_md = loader_md.load()
            print(f"   - Found {len(docs_md)} .md files")
            documents.extend(docs_md)
        except Exception as e:
            print(f"⚠️ Error loading .md files from {directory}: {e}")
    
    if not documents:
        print("❌ No documents found!")
        return

    print(f"📄 Total Documents: {len(documents)}. Splitting...")
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    print(f"🧩 Created {len(texts)} text chunks.")

    print("🧠 Generating embeddings (this may take a moment)...")
    embedding_model = VertexAIEmbeddings(model_name="text-embedding-004")
    
    # Create FAISS index
    db = FAISS.from_documents(texts, embedding_model)
    
    print(f"💾 Saving index to {INDEX_DIR}...")
    db.save_local(INDEX_DIR)
    print("✅ Index built successfully!")

if __name__ == "__main__":
    build_index()
