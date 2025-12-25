"""
Visions AI - Cloud Run HTTP Server
FastAPI app that exposes the agent as an HTTP API with A2A protocol support.
"""
import os
import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the agent
from visions_assistant.agent import get_chat_response

app = FastAPI(
    title="Visions AI",
    description="World-class photography mentor and creative director. Powered by Gemini 3 multi-model cascade.",
    version="3.1.0"  # Updated for Gemini 3 integration
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response validation
class ChatRequest(BaseModel):
    message: str
    image_path: Optional[str] = None
    user_id: Optional[str] = "user"


class ChatResponse(BaseModel):
    response: str
    status: str = "success"


class Message(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "visions-ai"


class OpenAIChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


@app.get("/")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "visions-ai",
        "version": "3.0.0"
    }


@app.get("/.well-known/agent.json")
async def agent_json():
    """A2A Protocol - Agent Identity Card (Who Visions Fleet Standard)"""
    return {
        "name": "Visions",
        "version": "3.1.0",
        "description": "Legendary Creative Director with 80 years shaping visual culture. Oscar-winner. Pulitzer laureate. Powered by Gemini 3 multi-model cascade.",
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
            "models": {
                "synthesis": "gemini-3-pro-preview",
                "fast_synthesis": "gemini-3-flash-preview",  # FREE TIER available
                "image_generation": "gemini-3-pro-image-preview",
                "grounded_search": "gemini-3-flash-preview",
                "deep_thinking": "gemini-3-pro-preview",
                "embeddings": "gemini-embedding-001"
            },
            "gemini_3_features": {
                "thinking_levels": ["low", "medium", "high", "minimal"],
                "media_resolution": "medium",  # Optimal for PDFs
                "flash_free_tier": True
            },
            "specialties": [
                "Rudolf Arnheim composition theory",
                "Phase One / Leica / Sony A1 expertise",
                "High-end commercial photography",
                "Cinematic lighting setups",
                "Screenwriting & narrative structure"
            ]
        }
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for Visions AI.
    
    Request body:
    {
        "message": "user message here",
        "image_path": "optional path to image"
    }
    """
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        response = get_chat_response(request.message, request.image_path, request.user_id)
        
        return ChatResponse(
            response=response,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=ChatResponse)
async def query(request: ChatRequest):
    """
    Query endpoint (alias for chat).
    """
    return await chat(request)


@app.post("/v1/chat")
async def v1_chat(request: Request):
    """
    Alias for /chat to support standardized agent communication.
    Handles both OpenAI format and simple message format.
    """
    try:
        data = await request.json()
        
        # Handle OpenAI messages format
        if 'messages' in data:
            messages = data.get('messages', [])
            if not messages:
                raise HTTPException(status_code=400, detail="Messages array is empty")
            
            # Extract the last user message
            user_messages = [m for m in messages if m.get('role') == 'user']
            if user_messages:
                message = user_messages[-1].get('content', '')
            else:
                message = messages[-1].get('content', '')
        else:
            # Handle simple message format
            message = data.get('message', '')
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        image_path = data.get('image_path', None)
        user_id = data.get('user_id', 'user') or data.get('user', 'user')
        response = get_chat_response(message, image_path, user_id)
        
        return {
            "response": response,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat/completions")
async def v1_chat_completions(request: Request):
    """
    OpenAI-compatible chat completions endpoint.
    Maps OpenAI API format to Visions agent response format.
    """
    try:
        data = await request.json()
        messages = data.get('messages', [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="Messages array is required")
        
        # Extract the last user message
        user_messages = [m for m in messages if m.get('role') == 'user']
        if user_messages:
            message = user_messages[-1].get('content', '')
        else:
            message = messages[-1].get('content', '')
        
        if not message:
            raise HTTPException(status_code=400, detail="Message content is required")
        
        # Get response from agent
        response_text = get_chat_response(message, image_path=None)
        
        # Return OpenAI-compatible format
        return {
            "id": "chatcmpl-visions-ai",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "visions-ai",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(message.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(message.split()) + len(response_text.split())
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": str(e),
                "type": "visions_error",
                "code": "internal_error"
            }
        )


@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint."""
    return {
        "object": "list",
        "data": [
            {
                "id": "visions-ai",
                "object": "model",
                "created": 1702857600,
                "owned_by": "whovisions",
                "permission": [],
                "root": "visions-ai",
                "parent": None
            }
        ]
    }


if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    uvicorn.run(app, host='0.0.0.0', port=port)
