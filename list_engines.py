
import vertexai
from vertexai.preview import reasoning_engines
import os

PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

def list_engines():
    print(f"Listing Reasoning Engines in {PROJECT_ID} at {LOCATION}...")
    try:
        engines = reasoning_engines.ReasoningEngine.list()
        for engine in engines:
            print(f"Engine: {engine.display_name}")
            print(f"  Resource Name: {engine.resource_name}")
            print("-" * 20)
    except Exception as e:
        print(f"Error listing engines: {e}")

if __name__ == "__main__":
    list_engines()
