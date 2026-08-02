
import vertexai
from vertexai.preview import reasoning_engines
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "endless-duality-480201-t3")
LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")

vertexai.init(project=PROJECT_ID, location=LOCATION)

def test_remote_agent(resource_name):
    print(f"Testing remote agent: {resource_name}")
    try:
        remote_agent = reasoning_engines.ReasoningEngine(resource_name)
        
        # Test Query 1: General
        query1 = "Who are you?"
        print(f"\nQuery: {query1}")
        response1 = remote_agent.query(question=query1)
        print(f"Response: {response1}")

        # Test Query 2: Image Generation (Global Endpoint)
        query2 = "Generate an image of a futuristic city with flying cars."
        print(f"\nQuery: {query2}")
        response2 = remote_agent.query(question=query2)
        print(f"Response: {response2}")
        
    except Exception as e:
        print(f"Error testing agent: {e}")

if __name__ == "__main__":
    resource_name = input("Enter the Reasoning Engine Resource Name (e.g., projects/.../reasoningEngines/...): ")
    if resource_name:
        test_remote_agent(resource_name.strip())
    else:
        print("Resource name is required.")
