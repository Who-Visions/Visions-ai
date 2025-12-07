#!/usr/bin/env python3
"""
Quick local test of image generation through the CLI flow
"""
import sys
sys.path.insert(0, 'visions_assistant')

from dual_mode_generator import DualModeImageGenerator
from config import Config

print("🧪 LOCAL IMAGE GENERATION TEST")
print("="*80)

# Initialize generator
generator = DualModeImageGenerator(
    project_id=Config.VERTEX_PROJECT_ID,
    ai_studio_key=Config.GOOGLE_AI_STUDIO_API_KEY
)

# Test with a simple prompt
prompt = "A minimalist photograph of a vintage film camera"

print(f"\n📝 Prompt: {prompt}\n")

# Generate
result = generator.generate_image(prompt)

print("\n" + "="*80)
print("RESULT")
print("="*80)
print(f"✅ Success: {result['success']}")
print(f"📍 Source: {result['source']}")

if result['success']:
    import os
    os.makedirs("test_output", exist_ok=True)
    
    # Determine extension
    ext = "png" if "png" in result['mime_type'] else "jpg"
    filename = f"test_output/local_test.{ext}"
    
    with open(filename, "wb") as f:
        f.write(result['data'])
    
    print(f"💾 Saved to: {filename}")
    print(f"📊 Size: {len(result['data']):,} bytes")
    print(f"\n🎉 Local image generation working via {result['source'].upper()}!")
else:
    print(f"❌ Error: {result['error']}")

print("="*80)
