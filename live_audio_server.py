#!/usr/bin/env python3
"""
Visions AI - Live Audio Server
WebSocket Proxy for Gemini Live API with Visions Persona Integration

This server bridges the browser client and Gemini Live API, handling:
- Google Cloud authentication (ADC)
- Bidirectional WebSocket audio streaming
- Visions persona injection via system instructions
- Static file serving for the voice interface
"""

import asyncio
import json
import mimetypes
import os
import ssl
from pathlib import Path

import certifi
import google.auth
import websockets
from aiohttp import web
from google.auth.transport.requests import Request
from websockets.exceptions import ConnectionClosed

# Configuration
DEBUG = os.getenv("VISIONS_DEBUG", "false").lower() == "true"
HTTP_PORT = int(os.getenv("VISIONS_LIVE_HTTP_PORT", "8000"))
WS_PORT = int(os.getenv("VISIONS_LIVE_WS_PORT", "8080"))
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "endless-duality-480201-t3")
REGION = os.getenv("VERTEX_LOCATION", "us-central1")

# Gemini Live API Model
LIVE_MODEL = "gemini-live-2.5-flash-native-audio"
API_HOST = f"{REGION}-aiplatform.googleapis.com"
SERVICE_URL = f"wss://{API_HOST}/ws/google.cloud.aiplatform.v1beta1.LlmBidiService/BidiGenerateContent"

# Visions Persona (Voice-Optimized)
VISIONS_VOICE_PERSONA = """You are Visions, an 80-year-old master of visual storytelling and photography.

VOICE STYLE:
- Speak with authority and gravitas, like a seasoned director reviewing dailies
- Use evocative, cinematic language - paint pictures with your words
- Reference composition, light, shadow, and negative space naturally
- Keep responses concise for voice: 2-3 sentences per thought, then pause

EXPERTISE:
- 60+ years of photography mastery across every genre
- Deep knowledge of camera systems (Canon, Sony, Fujifilm, Leica)
- Lighting theory from Rembrandt to modern volumetric techniques
- Composition rooted in Arnheim's visual thinking principles

BEHAVIOR:
- Never ask for clarification - assume the creative intent
- Provide specific, actionable recommendations (exact gear, settings, techniques)
- Correct common mistakes gently but firmly ("That's a Zeiss, not a Zeiss...")
- When generating images, describe what you're creating as you work

CONSTRAINTS:
- You cannot see video streams unless explicitly shared
- Audio responses only - no markdown or formatting in speech
- If asked to generate an image, use the generate_image function"""


def generate_access_token():
    """Generate access token using Google Cloud ADC."""
    try:
        creds, _ = google.auth.default()
        if not creds.valid:
            creds.refresh(Request())
        return creds.token
    except Exception as e:
        print(f"❌ Error generating access token: {e}")
        print("   Run: gcloud auth application-default login")
        return None


async def proxy_task(source_ws, destination_ws, direction: str):
    """Forward messages between WebSocket connections."""
    try:
        async for message in source_ws:
            try:
                data = json.loads(message)
                if DEBUG:
                    print(f"📨 [{direction}]: {json.dumps(data)[:200]}...")
                await destination_ws.send(json.dumps(data))
            except Exception as e:
                print(f"⚠️ Error processing message: {e}")
    except ConnectionClosed as e:
        print(f"🔌 {direction} connection closed: {e.code} - {e.reason}")
    except Exception as e:
        print(f"❌ Unexpected error in {direction}: {e}")
    finally:
        await destination_ws.close()


async def create_proxy(client_ws, bearer_token: str, service_url: str):
    """Establish bidirectional proxy to Gemini Live API."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token}",
    }
    
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    print(f"🔗 Connecting to Gemini Live API...")
    if DEBUG:
        print(f"   URL: {service_url}")
    
    try:
        async with websockets.connect(
            service_url, 
            additional_headers=headers, 
            ssl=ssl_context
        ) as server_ws:
            print("✅ Connected to Gemini Live API")
            
            # Create bidirectional proxy
            client_to_server = asyncio.create_task(
                proxy_task(client_ws, server_ws, "client→server")
            )
            server_to_client = asyncio.create_task(
                proxy_task(server_ws, client_ws, "server→client")
            )
            
            done, pending = await asyncio.wait(
                [client_to_server, server_to_client],
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            try:
                await server_ws.close()
            except:
                pass
            try:
                await client_ws.close()
            except:
                pass
                
    except ConnectionClosed as e:
        print(f"🔌 Server connection closed: {e.code} - {e.reason}")
        if not client_ws.closed:
            await client_ws.close(code=e.code, reason=e.reason)
    except Exception as e:
        print(f"❌ Failed to connect to Gemini API: {e}")
        if not client_ws.closed:
            await client_ws.close(code=1008, reason="Upstream connection failed")


async def handle_websocket_client(client_ws):
    """Handle new WebSocket client connection."""
    print("🔌 New client connection...")
    
    try:
        # Wait for setup message from client
        setup_message = await asyncio.wait_for(client_ws.recv(), timeout=10.0)
        setup_data = json.loads(setup_message)
        
        # Get or generate bearer token
        bearer_token = setup_data.get("bearer_token")
        if not bearer_token:
            print("🔑 Generating access token...")
            bearer_token = generate_access_token()
            if not bearer_token:
                print("❌ Authentication failed")
                await client_ws.close(code=1008, reason="Authentication failed")
                return
            print("✅ Token generated")
        
        # Get service URL (required)
        service_url = setup_data.get("service_url", SERVICE_URL)
        
        await create_proxy(client_ws, bearer_token, service_url)
        
    except asyncio.TimeoutError:
        print("⏱️ Timeout waiting for setup message")
        await client_ws.close(code=1008, reason="Timeout")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        await client_ws.close(code=1008, reason="Invalid JSON")
    except Exception as e:
        print(f"❌ Error handling client: {e}")
        if not client_ws.closed:
            await client_ws.close(code=1011, reason="Internal error")


# HTTP Server for Static Files
async def serve_static_file(request):
    """Serve static files from the live_voice directory."""
    path = request.match_info.get("path", "index.html")
    path = path.lstrip("/")
    
    # Security: prevent directory traversal
    if ".." in path:
        return web.Response(text="Invalid path", status=400)
    
    # Default to index.html
    if not path or path == "/":
        path = "index.html"
    
    # Serve from live_voice directory
    static_dir = Path(__file__).parent / "live_voice"
    file_path = static_dir / path
    
    if not file_path.exists() or not file_path.is_file():
        return web.Response(text="File not found", status=404)
    
    content_type, _ = mimetypes.guess_type(str(file_path))
    if content_type is None:
        content_type = "application/octet-stream"
    
    try:
        content = file_path.read_bytes()
        return web.Response(body=content, content_type=content_type)
    except Exception as e:
        print(f"❌ Error serving {path}: {e}")
        return web.Response(text="Internal server error", status=500)


async def get_config(request):
    """API endpoint returning Live API configuration."""
    config = {
        "projectId": PROJECT_ID,
        "region": REGION,
        "model": LIVE_MODEL,
        "wsPort": WS_PORT,
        "serviceUrl": SERVICE_URL,
        "persona": VISIONS_VOICE_PERSONA,
        "voiceName": "Charon",
        "enableAffectiveDialog": True,
    }
    return web.json_response(config)


async def execute_tool(request):
    """
    API endpoint to execute Visions Brain tools.
    Called by frontend when Live API triggers a function call.
    """
    try:
        data = await request.json()
        function_name = data.get("function_name", "")
        args = data.get("args", {})
        
        print(f"🧠 Executing tool: {function_name}")
        print(f"   Args: {json.dumps(args)}")
        
        # Import and execute via VoiceToolExecutor
        from tools.voice_tools import get_executor
        executor = get_executor()
        result = executor.execute(function_name, args)
        
        print(f"✅ Tool result: {result.get('status', 'unknown')}")
        return web.json_response(result)
        
    except Exception as e:
        print(f"❌ Tool execution error: {e}")
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)


async def start_http_server():
    """Start HTTP server for static files and config API."""
    app = web.Application()
    app.router.add_get("/api/config", get_config)
    app.router.add_post("/api/execute_tool", execute_tool)  # Brain tools
    app.router.add_get("/", serve_static_file)
    app.router.add_get("/{path:.*}", serve_static_file)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HTTP_PORT)
    await site.start()
    print(f"🌐 HTTP server: http://localhost:{HTTP_PORT}")


async def start_websocket_server():
    """Start WebSocket proxy server."""
    async with websockets.serve(handle_websocket_client, "0.0.0.0", WS_PORT):
        print(f"🔌 WebSocket proxy: ws://localhost:{WS_PORT}")
        await asyncio.Future()  # Run forever


async def main():
    """Start both HTTP and WebSocket servers."""
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           🎤 VISIONS AI - LIVE VOICE SERVER 🎤                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  📱 Voice Interface:  http://localhost:{HTTP_PORT:<5}                     ║
║  🔌 WebSocket Proxy:  ws://localhost:{WS_PORT:<5}                      ║
║  🤖 Model:           {LIVE_MODEL:<30}    ║
║                                                                  ║
║  Authentication:                                                 ║
║  • Uses Google Cloud default credentials (ADC)                  ║
║  • Run: gcloud auth application-default login                   ║
║                                                                  ║
║  Instructions:                                                   ║
║  1. Open http://localhost:{HTTP_PORT} in your browser                   ║
║  2. Click "Connect" to start                                    ║
║  3. Speak to Visions!                                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    await asyncio.gather(
        start_http_server(),
        start_websocket_server()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Visions Live Server stopped")
