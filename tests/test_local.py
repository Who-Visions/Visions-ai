import sys
import os

# Ensure the current directory is in the python path so we can import visions_assistant
sys.path.append(os.getcwd())

from visions_assistant.agent import get_chat_response

def main():
    print("🤖 Testing connection to Remote Reasoning Engine via visions_assistant...")
    user_query = "Generate an image of a professional photography studio with dramatic lighting, a camera on a tripod, and softboxes."
    
    print(f"📝 Query: {user_query}")
    response = get_chat_response(user_query)
    
    print("\n💬 Response:")
    print(response)

if __name__ == "__main__":
    main()

