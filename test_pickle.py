import cloudpickle
from visions.core.agent import VisionsAgent
import os

try:
    print("Combined pickle check...")
    agent = VisionsAgent(project="test-project", location="global")
    print("Agent init successful.")
    
    dumped = cloudpickle.dumps(agent)
    print(f"Pickle successful. Size: {len(dumped)} bytes")
    
    loaded = cloudpickle.loads(dumped)
    print("Unpickle successful.")
    
except Exception as e:
    print(f"Pickle Error: {e}")
    import traceback
    traceback.print_exc()
