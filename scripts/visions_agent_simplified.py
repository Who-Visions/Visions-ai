"""
Visions AI Agent - Simplified with Direct Gemini Integration
Uses your approved Gemini models: gemini-3-pro-image-preview, gemini-2.5-flash-image
"""

import os
import uuid
from typing import Dict, List, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from visions_backend import create_visions_backend, VISIONS_FILES
from subagents.camera_advisor import camera_advisor
from tools import search_camera_database, calculate_field_of_view, compare_camera_specs


class VisionsAgentSimplified:
    """
    Visions AI Agent using direct Gemini models.
    Implements sub-agent delegation manually without Deep Agents dependency.
    """
    
    def __init__(self):
        # Initialize main model (vision + generation)
        self.main_model = ChatGoogleGenerativeAI(
            model="gemini-3-pro-image-preview",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        # Initialize sub-agent model (fast)
        self.subagent_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-image",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        # Tools
        self.tools = {
            "search_camera_database": search_camera_database,
            "calculate_field_of_view": calculate_field_of_view,
            "compare_camera_specs": compare_camera_specs,
        }
        
        # Sub-agents
        self.subagents = {
            "camera-advisor": camera_advisor
        }
        
        # Session memory
        self.conversations = {}  # thread_id -> messages
        
        print("✅ Visions AI Agent Initialized (Simplified)")
        print(f"   Main Model: gemini-3-pro-image-preview")
        print(f"   Sub-agent Model: gemini-2.5-flash-image")
        print(f"   Tools: {len(self.tools)}")
        print(f"   Sub-agents: {len(self.subagents)}")
    
    def should_delegate(self, query: str) -> str | None:
        """Determine if query should be delegated to sub-agent."""
        query_lower = query.lower()
        
        # Camera advisor triggers
        if any(trigger in query_lower for trigger in [
            "camera", "lens", "recommend", "compare", "should i buy",
            "wildlife", "landscape", "portrait", "body", "sensor"
        ]):
            # Check if it's complex enough for delegation
            if any(word in query_lower for word in ["recommend", "compare", "vs", "which", "best"]):
                return "camera-advisor"
        
        return None
    
    def call_subagent(self, subagent_name: str, query: str) -> str:
        """Call a sub-agent specialist."""
        if subagent_name not in self.subagents:
            return f"Sub-agent {subagent_name} not found."
        
        subagent = self.subagents[subagent_name]
        
        # Build sub-agent prompt
        messages = [
            SystemMessage(content=subagent["system_prompt"]),
            HumanMessage(content=query)
        ]
        
        print(f"   🔄 Delegating to {subagent_name}...")
        
        # Call sub-agent model
        response = self.subagent_model.invoke(messages)
        
        return response.content
    
    def invoke(self, query: str, thread_id: str = None) -> Dict[str, Any]:
        """
        Process a query.
        
        Args:
            query: User question
            thread_id: Session identifier
            
        Returns:
            Response dict with content and metadata
        """
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        # Get or create conversation
        if thread_id not in self.conversations:
            self.conversations[thread_id] = []
        
        messages = self.conversations[thread_id]
        
        # Check for delegation
        delegate_to = self.should_delegate(query)
        
        if delegate_to:
            # Delegate to sub-agent
            subagent_response = self.call_subagent(delegate_to, query)
            
            # Main agent synthesizes
            synthesis_prompt = f"""User asked: {query}

The {delegate_to} specialist provided this response:
{subagent_response}

Please present this information to the user in a clear, encouraging way. Add any relevant context or follow-up suggestions."""
            
            messages.append(HumanMessage(content=synthesis_prompt))
            final_response = self.main_model.invoke(messages)
            
            result = {
                "content": final_response.content,
                "delegated_to": delegate_to,
                "thread_id": thread_id
            }
        else:
            # Direct response from main model
            messages.append(HumanMessage(content=query))
            response = self.main_model.invoke(messages)
            
            result = {
                "content": response.content,
                "delegated_to": None,
                "thread_id": thread_id
            }
        
        # Update conversation
        messages.append(AIMessage(content=result["content"]))
        self.conversations[thread_id] = messages[-10:]  # Keep last 10 for context
        
        return result


def test_agent():
    """Test the simplified agent."""
    print("\n" + "="*60)
    print("TESTING VISIONS AI AGENT (SIMPLIFIED)")
    print("="*60)
    
    agent = VisionsAgentSimplified()
    
    # Test 1: Simple query (no delegation)
    print("\n📝 Test 1: Simple Question")
    print("Query: 'What is the exposure triangle?'")
    result1 = agent.invoke("What is the exposure triangle?")
    print(f"Delegated: {result1['delegated_to']}")
    print(f"Response: {result1['content'][:200]}...")
    
    # Test 2: Camera recommendation (should delegate)
    print("\n📝 Test 2: Camera Recommendation")
    print("Query: 'Recommend a wildlife camera under $2500'")
    result2 = agent.invoke("Recommend a wildlife camera under $2500")
    print(f"Delegated: {result2['delegated_to']}")
    print(f"Response: {result2['content'][:200]}...")
    
    print("\n" + "="*60)
    print("✅ Tests Complete!")
    print("="*60)
    
    return agent


if __name__ == "__main__":
    agent = test_agent()
    
    # Interactive mode
    print("\n💡 Agent ready for queries!")
    print("   Type your question or 'quit' to exit")
    
    while True:
        user_input = input("\n🎯 You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_input:
            continue
        
        result = agent.invoke(user_input)
        print(f"\n🎓 Dr. Visions: {result['content']}")
        if result['delegated_to']:
            print(f"   (via {result['delegated_to']})")
