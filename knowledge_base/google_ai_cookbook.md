# Google AI Cookbook & Repository Map
**Source:** [GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai)
**Ingested:** 2025-12-17

## Overview
This cookbook consolidates key patterns, code snippets, and resources found in the official Google Cloud Generative AI repository, specifically tailored for the "Ai with Dav3" Google-First strategy.

## Vertex AI Workflow (Conceptual)
Based on [Vertex AI Overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/overview):
1.  **Prompt Design:** Use *Vertex AI Studio* for management.
2.  **Foundation Models:** Gemini (Multimodal), Imagen (Visual).
3.  **Customization:** *Model Tuning* to specialize behavior.
4.  **External Access:**
    *   **Grounding:** Validates against source of truth (Google Search/Data) to reduce hallucinations.
    *   **RAG:** Connects to private documents/databases.
    *   **Function Calling:** Real-time API interactions.
5.  **Safety & Citation:** Built-in citation checks and safety filters.

## Key Resources
The repository has been cloned to `knowledge_base/temp_repo` (temporary analysis).

### 1. Gemini 3.0 Essentials
The latest models are demonstrated in `gemini/getting-started/`.
*   **Gemini 3 Pro:** `gemini/getting-started/intro_gemini_3_pro.ipynb`
*   **Gemini 3 Image Gen:** `gemini/getting-started/intro_gemini_3_image_gen.ipynb`

### 2. Agents
Agent templates are located in `agents/`.
*   **Agent Engine:** `agents/agent_engine/`
*   **Data Analytics:** `agents/gemini_data_analytics/`

## Code Snippets

### Initializing Gemini 3.0 Pro (Python)
Requires `google-genai` SDK >= 1.51.0.

```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project="YOUR_PROJECT_ID", location="global")

MODEL_ID = "gemini-3-pro-preview"

# Thinking Level can be set to LOW (speed) or HIGH (reasoning)
response = client.models.generate_content(
    model=MODEL_ID,
    contents="Explain how AI works",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level=types.ThinkingLevel.LOW
        )
    ),
)
print(response.text)
```

### Media Resolution (Multimodality)
Gemini 3 allows granular control over token usage for images/video.

```python
response = client.models.generate_content(
    model=MODEL_ID,
    contents=[
        types.Part(
            file_data=types.FileData(file_uri="gs://...", mime_type="video/mp4"),
            media_resolution=types.PartMediaResolution(
                level=types.PartMediaResolutionLevel.MEDIA_RESOLUTION_LOW
            ),
        ),
        "What happens in this video?",
    ],
)
```

### Agents & Memory
For building autonomous agents, refer to the `agents/` directory templates:
- **Agent Engine:** `agents/agent_engine/` (Supports Memory Bank & MCP)
- **MCP Tutorial:** `agents/agent_engine/tutorial_mcp_on_agent_engine.ipynb` - *Critical for our Chrome Tool integration.*
