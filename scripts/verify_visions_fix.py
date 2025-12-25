import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from visions_assistant.agent import get_chat_response

def test_fix():
    print("🧪 Testing get_chat_response with correct keyword arguments...")
    
    # Simulate the call exactly as it is now in app.py
    # response = get_chat_response(user_message=..., image_path=..., user_id=...)
    
    try:
        # We expect this to fail deeper in the stack (e.g. connecting to remote agent)
        # BUT NOT with "No such file or directory: 'user'"
        response = get_chat_response(
            user_message="Ping", 
            image_path=None, 
            user_id="user"
        )
        print("✅ Function called successfully (no immediate crash).")
        print(f"Response: {response}")
        
    except FileNotFoundError as fnf:
        if "user" in str(fnf):
            print("❌ FAILURE: Caught 'No such file or directory: user'")
            print("The fix didn't work or wasn't applied correctly.")
            sys.exit(1)
        else:
            print(f"⚠️ Caught unrelated FileNotFoundError: {fnf}")
            
    except Exception as e:
        if "No such file" in str(e) and "user" in str(e):
             print("❌ FAILURE: Caught 'No such file or directory: user'")
             sys.exit(1)
        
        print(f"✅ Pass: Caught expected downstream error (since we are local): {e}")
        # If we get here, it means we passed the video_path check!

if __name__ == "__main__":
    test_fix()
