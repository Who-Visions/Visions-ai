#!/usr/bin/env python3
"""
Visions AI Server
Production-ready HTTP server powered by Gemini 3 multi-model cascade.

Usage:
    python server.py                    # Run on port 8080
    python server.py --port 3000        # Custom port
    python server.py --dev              # Development mode (auto-reload)
"""

import os
import argparse
import uvicorn

# Import the FastAPI app
from app import app


def main():
    parser = argparse.ArgumentParser(description="🎬 Visions AI Server")
    parser.add_argument("--port", "-p", type=int, default=int(os.getenv("PORT", 8080)),
                        help="Port to run on (default: 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--dev", "-d", action="store_true",
                        help="Development mode with auto-reload")
    parser.add_argument("--workers", "-w", type=int, default=1,
                        help="Number of worker processes (production)")
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🎬 VISIONS AI SERVER                       ║
╠══════════════════════════════════════════════════════════════╣
║  Version: 3.1.0                                               ║
║  Models:  Gemini 3 Pro/Flash (Global Endpoint)               ║
║  Port:    {args.port:<48} ║
║  Mode:    {"Development (auto-reload)" if args.dev else "Production":<42} ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if args.dev:
        # Development: single worker with auto-reload
        uvicorn.run(
            "app:app",
            host=args.host,
            port=args.port,
            reload=True,
            reload_dirs=[".", "tools", "visions_assistant"]
        )
    else:
        # Production: multiple workers, no reload
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level="info"
        )


if __name__ == "__main__":
    main()
