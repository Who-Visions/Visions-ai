
from pathlib import Path

content = """# Google AI Studio API Key (for fallback when Vertex AI quotas exhausted)
# Get your key from: https://aistudio.google.com/app/apikey
GOOGLE_AI_STUDIO_API_KEY=

# Vertex AI Configuration
VERTEX_PROJECT_ID=endless-duality-480201-t3
VERTEX_LOCATION=us-central1
VERTEX_GLOBAL_LOCATION=global

# Reasoning Engine
REASONING_ENGINE_ID=542433066447011840

# Feature Flags
ENABLE_AI_STUDIO_FALLBACK=false
"""

env_path = Path('.env')
env_path.write_text(content, encoding='utf-8')
print(f"Created .env at {env_path.absolute()}")
