"""
Test Deep Agents with Gemini - Simple validation
"""

import os
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

# Try creating a minimal agent with Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    # Initialize Gemini model
    model = ChatGoogleGenerativeAI(
        model="gemini-3-pro-image-preview",
        google_api_key=os.environ.get("GOOGLE_API_KEY")
    )
    
    print("✅ Gemini model initialized")
    
    # Create minimal agent
    agent = create_deep_agent(
        model=model,
        system_prompt="You are a helpful assistant.",
        store=InMemoryStore(),
        checkpointer=MemorySaver()
    )
    
    print("✅ Deep agent created successfully!")
    print(f"Agent type: {type(agent)}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   You may need: pip install langchain-google-genai")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
