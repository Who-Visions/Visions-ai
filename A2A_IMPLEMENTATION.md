# 🔗 A2A Protocol Implementation - Visions AI

## Overview
Visions AI now supports the **Who Visions Fleet A2A (Agent-to-Agent) Protocol**, enabling seamless discovery and communication with other agents in the fleet.

## Implemented Endpoints

### 1. Agent Identity Card (A2A Standard)
**Endpoint**: `GET /.well-known/agent.json`  
**Content-Type**: `application/json`  
**Authentication**: None (Public)

Returns the agent's identity card with capabilities and endpoints.

**Example Response**:
```json
{
  "name": "Dr. Visions",
  "version": "3.0.0",
  "description": "World-class photography mentor and creative director...",
  "capabilities": [
    "photography-technique-guidance",
    "composition-analysis",
    "lighting-design",
    "camera-equipment-recommendations",
    "image-generation",
    "image-analysis",
    "cinematic-direction",
    "youtube-workflow-extraction",
    "multi-agent-collaboration"
  ],
  "endpoints": {
    "chat": "/v1/chat/completions",
    "health": "/"
  },
  "extensions": {
    "color": "purple",
    "role": "Photography Expert & Creative Director",
    "models": {...},
    "specialties": [...]
  }
}
```

### 2. OpenAI-Compatible Chat Endpoint
**Endpoint**: `POST /v1/chat/completions`  
**Content-Type**: `application/json`  
**Authentication**: Optional (Bearer token for Cloud Run)

Accepts OpenAI-compatible chat requests with `messages` array.

**Request Format**:
```json
{
  "messages": [
    {"role": "user", "content": "What's the best camera for street photography?"}
  ],
  "model": "visions-ai"
}
```

**Response Format**:
```json
{
  "id": "chatcmpl-visions-ai",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "visions-ai",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "For street photography, I recommend..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

### 3. Flexible Chat Endpoint
**Endpoint**: `POST /v1/chat`  
**Content-Type**: `application/json`

Accepts both OpenAI format (`messages` array) and simple format (`message` string).

**Simple Format**:
```json
{
  "message": "What's the best camera for street photography?"
}
```

### 4. Legacy Endpoints
- `POST /chat` - Original Visions format
- `POST /query` - Alias for `/chat`
- `GET /v1/models` - OpenAI-compatible models list

## Testing

### Test Agent Identity Card
```bash
curl https://YOUR-CLOUD-RUN-URL/.well-known/agent.json
```

### Test Chat (OpenAI Format)
```bash
curl -X POST https://YOUR-CLOUD-RUN-URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Explain the rule of thirds"}
    ]
  }'
```

### Test Chat (Simple Format)
```bash
curl -X POST https://YOUR-CLOUD-RUN-URL/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain the rule of thirds"
  }'
```

## Agent Capabilities

- **photography-technique-guidance**: Composition, lighting, camera settings
- **composition-analysis**: Deep analysis using Rudolf Arnheim's principles
- **lighting-design**: Studio setups and natural light recommendations
- **camera-equipment-recommendations**: Gear advice for all budgets
- **image-generation**: Create visuals with Gemini 3 Pro Image Preview
- **image-analysis**: Critique uploaded photos with actionable feedback
- **cinematic-direction**: Framing, color grading, visual storytelling
- **youtube-workflow-extraction**: Analyze video tutorials for workflows
- **multi-agent-collaboration**: Consult with Rhea, Dav1d, Yuki via Neural Council

## Fleet Integration

Visions AI can be discovered by:
- **Who-Tester** (Fleet Leader)
- **Rhea** (Intelligence Analyst)
- **Dav1d** (Creative Director)
- **Yuki** (Strategic Planner)

Other agents can call Visions for photography expertise, image generation, or visual analysis tasks.

## Deployment

Deploy to Cloud Run with:
```bash
gcloud run deploy visions-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Notes

- All endpoints support CORS for cross-origin requests
- The agent uses Gemini 3 Pro for final synthesis
- Multi-model cascade (Flash-Lite → Flash → Pro → Gemini 3) for intelligent routing
- Rate limiting: 45 seconds between Gemini 3 Pro requests
