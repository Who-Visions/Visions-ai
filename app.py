"""
Visions AI - Cloud Run HTTP Server
Flask app that exposes the agent as an HTTP API with A2A protocol support.
"""
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import the agent
from visions_assistant.agent import get_chat_response

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "visions-ai",
        "version": "3.0.0"
    })

@app.route('/.well-known/agent.json', methods=['GET'])
def agent_json():
    """A2A Protocol - Agent Identity Card (Who Visions Fleet Standard)"""
    return jsonify({
        "name": "Dr. Visions",
        "version": "3.0.0",
        "description": "World-class photography mentor and creative director with 80 years of visual arts experience. Expert in composition theory (Rudolf Arnheim), advanced camera gear, cinematic lighting, and visual storytelling. Powered by Google Gemini 3 Pro multi-model intelligence cascade.",
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
                "image_generation": "gemini-3-pro-image-preview",
                "grounded_search": "gemini-2.5-flash",
                "deep_thinking": "gemini-2.5-pro"
            },
            "specialties": [
                "Rudolf Arnheim composition theory",
                "Phase One / Leica / Sony A1 expertise",
                "High-end commercial photography",
                "Cinematic lighting setups"
            ]
        }
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for Visions AI.
    
    Request body:
    {
        "message": "user message here",
        "image_path": "optional path to image"
    }
    """
    try:
        data = request.get_json() or {}
        message = data.get('message', '')
        image_path = data.get('image_path', None)
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        response = get_chat_response(message, image_path)
        
        return jsonify({
            "response": response,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/query', methods=['POST'])
def query():
    """
    Query endpoint (alias for chat).
    """
    return chat()

@app.route('/v1/chat', methods=['POST'])
def v1_chat():
    """
    Alias for /chat to support standardized agent communication.
    Handles both OpenAI format and simple message format.
    """
    try:
        data = request.get_json() or {}
        
        # Handle OpenAI messages format
        if 'messages' in data:
            messages = data.get('messages', [])
            if messages:
                # Extract the last user message
                user_messages = [m for m in messages if m.get('role') == 'user']
                if user_messages:
                    message = user_messages[-1].get('content', '')
                else:
                    message = messages[-1].get('content', '')
            else:
                return jsonify({"error": "Messages array is empty"}), 400
        else:
            # Handle simple message format
            message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        image_path = data.get('image_path', None)
        response = get_chat_response(message, image_path)
        
        return jsonify({
            "response": response,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/v1/chat/completions', methods=['POST'])
def v1_chat_completions():
    """
    OpenAI-compatible chat completions endpoint.
    Maps OpenAI API format to Visions agent response format.
    """
    try:
        data = request.get_json() or {}
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "Messages array is required"}), 400
        
        # Extract the last user message
        user_messages = [m for m in messages if m.get('role') == 'user']
        if user_messages:
            message = user_messages[-1].get('content', '')
        else:
            message = messages[-1].get('content', '')
        
        if not message:
            return jsonify({"error": "Message content is required"}), 400
        
        # Get response from agent
        response_text = get_chat_response(message, image_path=None)
        
        # Return OpenAI-compatible format
        return jsonify({
            "id": "chatcmpl-visions-ai",
            "object": "chat.completion",
            "created": int(os.times().elapsed),
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
        })
    except Exception as e:
        return jsonify({
            "error": {
                "message": str(e),
                "type": "visions_error",
                "code": "internal_error"
            }
        }), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    """OpenAI-compatible models endpoint."""
    return jsonify({
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
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
