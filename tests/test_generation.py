#!/usr/bin/env python3
"""
Test script to verify image generation works with gemini-3-pro-image-preview
"""
import sys
import os

# Add the visions_assistant to the path
sys.path.insert(0, 'visions_assistant')

from visions_assistant.agent import get_chat_response

def main():
    print("🎨 Testing Image Generation with gemini-3-pro-image-preview...")
    query = "Generate a hyper-realistic photograph of a professional photography studio with dramatic lighting, a DSLR camera on a tripod, and two softboxes positioned at 45-degree angles."
    
    print(f"📝 Query: {query}")
    print("\n🔄 Sending request to Visions Agent...\n")
    
    response = get_chat_response(query)
    
    print("\n" + "="*80)
    print("💬 RESPONSE:")
    print("="*80)
    print(response)
    print("="*80)
    
    # Save to file
    with open("last_generation_test.txt", "w", encoding="utf-8") as f:
        f.write(f"Query: {query}\n\n")
        f.write("="*80 + "\n")
        f.write(response)
    
    print("\n✅ Response saved to: last_generation_test.txt")

if __name__ == "__main__":
    main()
