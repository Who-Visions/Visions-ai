import vertexai
from vertexai.preview import reasoning_engines
import os

PROJECT_ID = "endless-duality-480201-t3"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

try:
    engines = reasoning_engines.ReasoningEngine.list()
    if not engines:
        print("No reasoning engines found.")
    else:
        # Sort by creation time (latest first)
        engines.sort(key=lambda x: x.create_time, reverse=True)
        print(f"Top 10 Reasoning Engines in {LOCATION}:")
        for engine in engines[:10]:
            print(f"ID: {engine.resource_name}")
            print(f"  Display Name: {engine.display_name}")
            print(f"  Created: {engine.create_time}")
            print("-" * 40)
except Exception as e:
    print(f"❌ Failed to list reasoning engines: {e}")
