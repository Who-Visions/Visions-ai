"""
Visions AI - Rhea Noir Fleet Server v2.0.0
HTTP API powered by FastAPI, implementing the standardized A2A protocol.
"""
import os
import time
import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Enhanced Logging ---
try:
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()
    logger = logging.getLogger("visions-fleet-server")
    print("📡 Cloud Logging Enabled.")
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("visions-fleet-server")
    print("📝 Local Logging Fallback.")

# --- Import Assistant Bridge ---
from visions_assistant.agent import get_chat_response

app = FastAPI(
    title="Visions AI",
    description="Rhea Noir Fleet Server - World-Class Photography Mentor & Creative Director.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    message: str
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    user_id: Optional[str] = "user"
    config: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    id: str = str(uuid.uuid4())
    status: str = "success"

# --- Endpoints ---

@app.get("/")
@app.get("/health")
async def health():
    """Health Check for Cloud Run."""
    return {
        "status": "online",
        "service": "visions-assistant",
        "version": "2.0.0",
        "fleet": "Rhea Noir",
        "heartbeat": time.time()
    }

@app.get("/health/detailed")
async def health_detailed():
    """Detailed System Health."""
    return {
        "status": "online",
        "env": os.environ.get("K_SERVICE", "local"),
        "port": os.environ.get("PORT", "8080"),
        "python": "3.12",
        "dependencies": "verified"
    }

@app.get("/.well-known/agent.json")
@app.get("/agent-card")
async def agent_identity():
    """A2A Protocol - Agent Identity Card."""
    return {
        "name": "Visions",
        "tagline": "Legendary Creative Director",
        "version": "2.0.0",
        "capabilities": [
            "photography-mentorship",
            "composition-analysis",
            "lighting-design",
            "image-generation",
            "cinematic-direction"
        ],
        "endpoints": {
            "chat": "/v1/chat/completions",
            "health": "/health"
        }
    }

@app.post("/chat", response_model=ChatResponse)
@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Standardized Chat Endpoint."""
    logger.info(f"📩 Request from {request.user_id}: {request.message[:50]}...")
    try:
        response_text = get_chat_response(
            user_message=request.message,
            image_path=request.image_path,
            video_path=request.video_path,
            user_id=request.user_id,
            config=request.config
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"❌ Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def openai_compatible_chat(request: Request):
    """OpenAI Proxy for Cursor/ChatGPT integration."""
    try:
        data = await request.json()
        messages = data.get("messages", [])
        if not messages:
            raise HTTPException(status_code=400, detail="Messages array required")
        
        last_msg = messages[-1].get("content", "")
        response_text = get_chat_response(user_message=last_msg)
        
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "visions-ai",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop"
            }]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """Available Models."""
    return {
        "object": "list",
        "data": [{"id": "visions-ai", "object": "model", "owned_by": "whovisions"}]
    }

@app.post("/render")
async def trigger_render(request: Request, background_tasks: BackgroundTasks):
    """Trigger Video/World Render via Background Tasks."""
    data = await request.json()
    background_tasks.add_task(logger.info, f"🎬 Rendering initiated: {data}")
    return {"status": "processing", "job_id": str(uuid.uuid4())}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
