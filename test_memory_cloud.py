"""
Test script for Visions AI Cloud Memory System
Demonstrates Firestore + BigQuery memory integration
"""
import asyncio
from memory_cloud import CloudMemoryManager


async def test_memory_system():
    """Test the cloud memory system end-to-end."""
    print("="*80)
    print("🧪 TESTING VISIONS AI CLOUD MEMORY SYSTEM")
    print("="*80)
    
    # Initialize
    memory = CloudMemoryManager()
    await memory.initialize()
    
    # Test user
    user_id = "test_user_dave"
    
    print("\n📝 Testing Short-Term Memory (Firestore)...")
    print("-"*40)
    
    # Add some test messages
    await memory.remember_message(
        user_id=user_id,
        role="user",
        content="My name is Dave and I prefer dark mode for all my apps"
    )
    
    await memory.remember_message(
        user_id=user_id,
        role="assistant",
        content="Nice to meet you, Dave! I've noted your preference for dark mode."
    )
    
    await memory.remember_message(
        user_id=user_id,
        role="user",
        content="I work at Who Visions LLC as a developer"
    )
    
    # Wait for async operations
    await asyncio.sleep(2)
    
    print("\n🔍 Retrieving Memory Context...")
    print("-"*40)
    
    context = await memory.get_context_for_model(user_id)
    
    print(f"Session ID: {context.get('session_id')}")
    print(f"Conversation History: {len(context.get('conversation_history', []))} messages")
    print(f"Long-term Memories: {len(context.get('long_term_memories', []))} entries")
    
    if context.get('conversation_history'):
        print("\n📬 Recent Conversation:")
        for msg in context['conversation_history'][-3:]:
            print(f"  [{msg['role']}]: {msg['content'][:60]}...")
    
    if context.get('long_term_memories'):
        print("\n🧠 Long-term Memories:")
        for mem in context['long_term_memories']:
            print(f"  - {mem.get('memory_key', 'unknown')}: {mem.get('content', '')[:50]}...")
    
    print("\n📊 Testing Long-Term Memory (BigQuery)...")
    print("-"*40)
    
    # Store a memory directly
    await memory.long_term.store_memory(
        user_id=user_id,
        memory_key="preference:color_scheme",
        content="User prefers dark mode for all applications",
        importance=0.8,
        source="explicit"
    )
    
    await memory.long_term.store_memory(
        user_id=user_id,
        memory_key="user:occupation",
        content="Developer at Who Visions LLC",
        importance=0.9,
        source="conversation"
    )
    
    # Wait for BigQuery insertion
    await asyncio.sleep(3)
    
    # Retrieve memories
    memories = await memory.long_term.retrieve_memories(user_id, limit=5)
    print(f"\nRetrieved {len(memories)} memories from BigQuery:")
    for mem in memories:
        print(f"  - [{mem.get('importance', 0):.1f}] {mem.get('memory_key')}: {mem.get('content', '')[:50]}...")
    
    # Print status
    await memory.print_status()
    
    # End session
    await memory.end_session(user_id)
    
    print("\n✅ Cloud Memory System Test Complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_memory_system())
