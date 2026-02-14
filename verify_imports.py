
import sys
import importlib.util

def check_import(module_name):
    try:
        if importlib.util.find_spec(module_name) is None:
            print(f"❌ {module_name}: Not Found")
        else:
            print(f"✅ {module_name}: Found")
    except ImportError:
         print(f"❌ {module_name}: ImportError")

print(f"Python Executable: {sys.executable}")
print("Checking Core Dependencies for Visions AI...")

modules = [
    "google.genai",
    "google.cloud.storage",
    "google.cloud.bigquery",
    "vertexai",
    "rich",
    "visions.core.agent" # Check local path resolution
]

# Ensure CWD is valid for local imports
import os
sys.path.append(os.getcwd())

for m in modules:
    check_import(m)
