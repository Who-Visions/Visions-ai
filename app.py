"""
Visions AI - Cloud Run HTTP Server
Flask app that exposes the agent as an HTTP API.
"""
import os
from flask import Flask, request, jsonify
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
