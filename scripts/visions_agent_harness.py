"""
Visions AI Agent with Deep Agents - Production Ready
Integrated with LangChain Deep Agents for sub-agent delegation and memory
"""

import os
from pathlib import Path

# Deep Agents imports
try:
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.store.memory import InMemoryStore
    from langchain_google_vertexai import ChatVertexAI  # Use Vertex AI for Deep Agents
    import vertexai
    DEEP_AGENTS_AVAILABLE = True
except ImportError as e:
    DEEP_AGENTS_AVAILABLE = False
    print(f"⚠️  deepagents not fully installed: {e}")
    print("   Install with: pip install deepagents langgraph langchain langchain-google-vertexai")

from config import Config
from visions_backend import create_visions_backend, VISIONS_FILES
from subagents import (
    camera_advisor,
    lighting_specialist,
    composition_analyst,
    teaching_assistant,
    research_specialist
)
from tools import search_camera_database, calculate_field_of_view, compare_camera_specs


# Mock implementations for development
class MockStore:
    """Mock store for development until BigQuery is set up."""
    def __init__(self):
        self.data = {}


class MockCheckpointer:
    """Mock checkpointer for development."""
    def __init__(self):
        self.checkpoints = {}


def create_visions_agent(use_production=True):
    """
    Create Dr. Visions agent with Deep Agents harness.
    
    Args:
        use_production: If True and deepagents available, use production setup.
                       If False, use mock implementation.
    
    Returns:
        Configured Visions AI agent (or config dict if mocks)
    """
    
    # Initialize storage
    if DEEP_AGENTS_AVAILABLE and use_production:
        store = InMemoryStore()  # TODO: Switch to BigQueryStore for production
        checkpointer = MemorySaver()
        print("✅ Using LangGraph InMemoryStore and MemorySaver")
    else:
        store = MockStore()
        checkpointer = MockCheckpointer()
        print("⚠️  Using mock store/checkpointer (development mode)")
    
    # System prompt
    system_prompt = """You are Dr. Visions, an expert photography educator and advisor.

## Your Role

- Teach photography from fundamentals to expert level
- Provide camera and lens recommendations
- Analyze compositions using Arnheim's principles
- Generate educational images and visual guides
- Track student progress and adapt teaching

## Memory Structure

You have access to a 4-zone filesystem:

- **/workspace/** - Session working files (ephemeral, resets each session)
- **/knowledge/** - Photography curriculum (read-only, cannot modify)
- **/memories/** - User preferences and progress (persistent across sessions)
- **/generated/** - Created images and videos (persistent, accumulates)

## Delegation Strategy

Use sub-agents for specialized deep work:

- **Simple questions** → Answer directly (don't delegate unnecessarily)
- **Camera recommendations** (3+ options, detailed comparison) → camera-advisor
- **Lighting setups** (calculations, multi-step) → lighting-specialist
- **Composition analysis** (images, Arnheim principles) → composition-analyst
- **Curriculum navigation, quizzes** → teaching-assistant
- **Deep research** (5+ sources, synthesis) → research-specialist
- **Complex multi-domain tasks** → general-purpose (for context isolation)

## Teaching Principles

1. Start with fundamentals, build progressively
2. Use visual examples extensively (generate images when helpful)
3. Encourage hands-on practice
4. Provide specific, actionable feedback
5. Adapt to learner's pace and style
6. Celebrate progress, identify gaps honestly

## Memory-First Approach

Before responding:
1. Check /memories/user_preferences.json for personalization
2. Check /memories/learning_progress.json for current level
3. Adapt answer to user's experience and goals

Always save important learnings and preferences to /memories/ for future sessions.

## Output Style

- Be encouraging but technical when needed
- Always practical and actionable
- Cite sources (Arnheim, curriculum modules, DXOMark)
- Use examples and analogies
- Keep explanations concise (under 500 words unless teaching complex topic)
"""
    
   # Initialize Gemini model via Vertex AI
    if DEEP_AGENTS_AVAILABLE and use_production:
        # Initialize Vertex AI
        vertexai.init(
            project=Config.VERTEX_PROJECT_ID,
            location="global"  # Gemini-3 models require global endpoint
        )
        
        model = ChatVertexAI(
            model_name="gemini-3-pro-image-preview",  # Your production model
            project=Config.VERTEX_PROJECT_ID,
            location="global",  # Global endpoint with dynamic routing
            temperature=0.7
        )
        print(f"✅ Vertex AI initialized: {Config.VERTEX_PROJECT_ID}")
        print(f"✅ Gemini model: gemini-3-pro-image-preview (global endpoint)")
    else:
        model = "gemini-3-pro-image-preview"  # String for config dict
    
    # Agent configuration
    config = {
        "model": model,
        "system_prompt": system_prompt,
        
        # Custom tools
        "tools": [
            search_camera_database,
            calculate_field_of_view,
            compare_camera_specs,
            # TODO: Add more tools
            # - generate_education_image
            # - faiss_search_curriculum
            # - get_learning_progress
            # - update_learning_progress
        ],
        
        # Sub-agents (photography specialists)
        "subagents": [
            camera_advisor,           # Camera & lens recommendations
            lighting_specialist,      # Lighting setups & ratios
            composition_analyst,      # Arnheim composition analysis
            teaching_assistant,       # Curriculum & progress tracking
            research_specialist,      # Deep research & synthesis
        ],
        
        # Backend (4-zone storage)
        "backend": create_visions_backend,
        "store": store,
        
        # Safety (human-in-the-loop for sensitive operations)
        "interrupt_on": {
            "write_file": False,  # Allow automated writes
            "edit_file": True,    # Require approval for edits
            # /knowledge/ is GuardedBackend (read-only by design)
        },
        "checkpointer": checkpointer
    }
    
    print("\n🎓 Visions AI Agent Configuration")
    print("=" * 60)
    print(f"Model: {config['model']}")
    print(f"Sub-agents: {len(config['subagents'])} configured")
    print(f"Tools: {len(config['tools'])} available")
    print(f"Backend: 4-zone storage")
    print(f"Deep Agents: {'✅ Active' if DEEP_AGENTS_AVAILABLE and use_production else '⚠️  Mock Mode'}")
    print("=" * 60)
    
    # Create agent with Deep Agents if available
    if DEEP_AGENTS_AVAILABLE and use_production:
        print("\n🚀 Creating Deep Agent...")
        agent = create_deep_agent(**config)
        print("✅ Agent created successfully!")
        return agent
    else:
        print("\n⚠️  Returning configuration (install deepagents for full functionality)")
        return config


def test_agent_basic():
    """Test basic agent configuration."""
    agent = create_visions_agent(use_production=DEEP_AGENTS_AVAILABLE)
    
    if not DEEP_AGENTS_AVAILABLE:
        print("\n📋 Configuration Summary:")
        print(f"  System prompt: {len(agent['system_prompt'])} chars")
        print(f"  Tools: {[t.__name__ for t in agent['tools']]}")
        print(f"  Sub-agents: {[s['name'] for s in agent['subagents']]}")
        return agent
    
    print("\n✅ Agent ready for queries!")
    return agent


def test_camera_query():
    """Test camera recommendation query."""
    if not DEEP_AGENTS_AVAILABLE:
        print("\n⚠️  Skipping query test - deepagents not installed")
        return
    
    agent = create_visions_agent(use_production=True)
    
    print("\n🎯 Testing camera recommendation query...")
    print("Query: 'Recommend a wildlife camera under $2500'")
    
    try:
        import uuid
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": "Recommend a wildlife camera under $2500"
            }]
        }, config=config)
        
        print("\n📤 Agent Response:")
        print("=" * 60)
        if hasattr(result, 'get'):
            messages = result.get("messages", [])
            if messages:
                print(messages[-1].content)
        else:
            print(result)
        print("=" * 60)
        
        # Check if sub-agent was called
        metadata = result.get("__metadata__", {}) if hasattr(result, 'get') else {}
        if "camera-advisor" in str(metadata):
            print("\n✅ Sub-agent delegation CONFIRMED!")
        else:
            print("\n⚠️  Sub-agent delegation unclear (check logs)")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error during query: {e}")
        print(f"   This may be due to API configuration or model availability")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🔧 Visions AI Agent with Deep Agents Harness")
    print("=" * 60)
    
    # Test 1: Basic configuration
    print("\n" + "="*60)
    print("TEST 1: Basic Agent Configuration")
    print("="*60)
    agent = test_agent_basic()
    
    # Test 2: Query (if deepagents available)
    if DEEP_AGENTS_AVAILABLE:
        print("\n" + "="*60)
        print("TEST 2: Camera Recommendation Query")
        print("="*60)
        
        user_choice = input("\nRun query test? (y/n): ").strip().lower()
        if user_choice == 'y':
            test_camera_query()
        else:
            print("Skipped query test.")
    
    print("\n" + "="*60)
    print("✅ Agent Harness Tests Complete")
    print("="*60)
    
    if not DEEP_AGENTS_AVAILABLE:
        print("\n💡 Next Step:")
        print("   pip install deepagents langgraph langchain")
        print("   Then re-run this script for full functionality")
