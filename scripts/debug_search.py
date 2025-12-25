import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from visions.core.agent import KnowledgeRetriever

def debug():
    print("🔍 Debugging Knowledge Retriever...")
    retriever = KnowledgeRetriever(project_id="endless-duality-480201-t3")
    
    query = "Who is the Registered Agent for WHO VISIONS LLC?"
    print(f"\nQuery: {query}")
    results = retriever.search(query)
    print(f"\nResults:\n{results}")

if __name__ == "__main__":
    debug()
