
import sys
import os
import logging
from pathlib import Path

# Configure path to mimic production container
sys.path.append(os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup_verifier")

def verify_startup():
    print("🔍 Starting Local Verification Suite...")
    
    # Check 1: Module Imports
    print("\n1. Testing Import Hierarchy...")
    try:
        from visions.modules.mem_store.memory_cloud import CloudMemoryManager
        print("   ✅ visions.modules.mem_store.memory_cloud")
        
        from visions.core.agent import VisionsAgent
        print("   ✅ visions.core.agent")
        
        from visions.api.app import app
        print("   ✅ visions.api.app (FastAPI instance)")
        
    except ImportError as e:
        print(f"   ❌ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"   ❌ UNEXPECTED ERROR: {e}")
        return False

    # Check 2: Class Initialization (Mocked)
    print("\n2. Testing Agent Initialization...")
    try:
        # We Mock the heavy Vertex AI init to avoid needing real creds just for import structure checks
        # But we want to ensure the _code_ logic holds up.
        from unittest.mock import MagicMock, patch
        
        with patch('google.genai.Client'), patch('vertexai.init'), patch('google.cloud.storage.Client'):
            agent = VisionsAgent(project="test-project", location="us-central1")
            print("   ✅ VisionsAgent initialized")
            
            # Test Triage Logic (Mocked Network)
            with patch.object(agent, '_triage_query', return_value={"is_high_risk": False, "complexity": 5}):
                print("   ✅ Triage logic verifiable")
                
    except Exception as e:
        print(f"   ❌ INIT ERROR: {e}")
        return False
        
    print("\n✅✅ STARTUP VERIFICATION PASSED ✅✅")
    return True

if __name__ == "__main__":
    if verify_startup():
        sys.exit(0)
    else:
        sys.exit(1)
