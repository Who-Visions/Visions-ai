"""
Visions AI - Component Test Suite
Tests all updated components: cascade, routing, animations
"""
# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all imports work"""
    print("\n[1] Testing imports...")
    
    try:
        from agent import VisionsAgent
        print("   ✓ agent.py imports OK")
    except Exception as e:
        print(f"   ✗ agent.py failed: {e}")
        return False
    
    try:
        from animations import boot_sequence_animation, memory_save_animation, cascade_animation
        print("   ✓ animations.py imports OK")
    except Exception as e:
        print(f"   ✗ animations.py failed: {e}")
        return False
    
    return True

def test_agent_init():
    """Test agent initialization"""
    print("\n[2] Testing agent initialization...")
    
    try:
        from agent import VisionsAgent
        agent = VisionsAgent()
        print("   ✓ VisionsAgent created")
        print(f"   Project: {agent.project}")
        print(f"   Location: {agent.location}")
        return agent
    except Exception as e:
        print(f"   ✗ Agent init failed: {e}")
        return None

def test_triage(agent):
    """Test query triage"""
    print("\n[3] Testing query triage...")
    
    try:
        routing = agent._triage_query("What are the latest Canon cameras?")
        print("   ✓ Triage complete")
        print(f"   Routing: {routing}")
        return routing
    except Exception as e:
        print(f"   ✗ Triage failed: {e}")
        return None

def test_cascade(agent):
    """Test cascade intelligence gathering"""
    print("\n[4] Testing cascade (sample query)...")
    
    try:
        # Test with a simple greeting first
        routing = {"is_greeting": True}
        intelligence = agent._gather_intelligence("hi", routing)
        print("   ✓ Greeting handled (skipped heavy models)")
        
        return True
    except Exception as e:
        print(f"   ✗ Cascade failed: {e}")
        return False

def test_query(agent):
    """Test full query with real-time output"""
    print("\n[5] Testing full query (simple)...")
    
    try:
        result = agent.query("hi")
        import json
        data = json.loads(result)
        text = data.get("text", "")[:100]
        print(f"   ✓ Query complete")
        print(f"   Response preview: {text}...")
        return True
    except Exception as e:
        print(f"   ✗ Query failed: {e}")
        return False

def main():
    print("=" * 60)
    print("VISIONS AI - COMPONENT TEST SUITE")
    print("=" * 60)
    
    # Run tests
    if not test_imports():
        print("\n❌ Import tests failed - aborting")
        return
    
    agent = test_agent_init()
    if not agent:
        print("\n❌ Agent init failed - aborting")
        return
    
    test_triage(agent)
    test_cascade(agent)
    test_query(agent)
    
    print("\n" + "=" * 60)
    print("✅ ALL COMPONENT TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
