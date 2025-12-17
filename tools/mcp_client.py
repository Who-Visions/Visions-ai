import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class MCPClient:
    """
    A generic Model Context Protocol (MCP) client.
    communicates with an MCP server via Stdio (Standard Input/Output).
    """

    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        """
        Initialize the MCP Client.

        Args:
            command: The command to run the MCP server (e.g., "npx").
            args: List of arguments for the command.
            env: Optional environment variables dictionary.
        """
        self.command = command
        self.args = args
        self.env = env or os.environ.copy()
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        
        # We need a loop to handle async IO
        self._loop = asyncio.new_event_loop()
        self._executor = ThreadPoolExecutor(max_workers=2)

    def start(self):
        """Starts the MCP server subprocess."""
        cmd_list = [self.command] + self.args
        logger.info(f"Starting MCP Server: {' '.join(cmd_list)}")
        
        # Use simple subprocess with pipes
        self.process = subprocess.Popen(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr, # Forward stderr to see logs
            env=self.env,
            text=True,
            bufsize=0 # Unbuffered
        )
        
        # Start reading stdout in a separate thread
        # self._executor.submit(self._read_stdout)
        import threading
        self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader_thread.start()

        # Send initialize request
        # This is strictly synchronous in this simple implementation for now,
        # but ideally should await the response.
        # For simplicity in this agent context, we might assume it's ready or wait a bit.

        
    def _read_stdout(self):
        """Continuously reads stdout and processes JSON-RPC messages."""
        if not self.process or not self.process.stdout:
            return

        for line in self.process.stdout:
            if not line:
                break
            try:
                # DEBUG: Print raw output from MCP server
                print(f"DEBUG_MCP_RAW: {line.strip()}", flush=True)
                message = json.loads(line)
                self._handle_message(message)
            except json.JSONDecodeError:
                print(f"DEBUG_MCP_JSON_ERROR: {line.strip()}", flush=True)
                pass
            except Exception as e:
                logger.error(f"MCP Client: Error handling message: {e}")

    def _handle_message(self, message: Dict[str, Any]):
        """Handles a JSON-RPC message."""
        msg_id = message.get("id")
        
        if msg_id is not None and msg_id in self._pending_requests:
            # It's a response to a request
            future = self._pending_requests.pop(msg_id)
            if "error" in message:
                error_msg = message["error"].get("message", "Unknown error")
                self._loop.call_soon_threadsafe(future.set_exception, Exception(error_msg))
            else:
                result = message.get("result")
                self._loop.call_soon_threadsafe(future.set_result, result)
        else:
            # It's a notification or request from server (not handled deeply here yet)
            pass

    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Sends a JSON-RPC request and awaits the response."""
        if not self.process or self.process.poll() is not None:
            raise RuntimeError("MCP server is not running")

        self._request_id += 1
        req_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }

        # Create future for response
        future = self._loop.create_future()
        self._pending_requests[req_id] = future

        # Send request
        json_str = json.dumps(request) + "\n"
        self.process.stdin.write(json_str)
        self.process.stdin.flush()

        # Wait for response
        # In a real async app we'd await future, but here we might need to bridge sync/async
        try:
             return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
             print(f"DEBUG_MCP: Request {req_id} timed out", flush=True)
             raise TimeoutError(f"Request {req_id} ({method}) timed out after 30s")

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Synchronous wrapper to call a tool. 
        Runs the async loop until complete.
        """
        return self._loop.run_until_complete(
            self._send_request("tools/call", {"name": tool_name, "arguments": arguments})
        )

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lists available tools."""
        result = self._loop.run_until_complete(self._send_request("tools/list"))
        return result.get("tools", [])

    def initialize(self):
        """Sends the initialize request."""
        # Capabilities
        caps = {
            "roots": {"listChanged": False},
            "sampling": {}
        }
        
        result = self._loop.run_until_complete(
            asyncio.wait_for(
                self._send_request("initialize", {
                    "protocolVersion": "2024-11-05",
                    "capabilities": caps,
                    "clientInfo": {"name": "VisionsAgent", "version": "1.0"}
                }),
                timeout=15.0
            )
        )
        
        # Must send initialized notification
        notify = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }

        self.process.stdin.write(json.dumps(notify) + "\n")
        self.process.stdin.flush()
        
        return result

    def close(self):
        """Stops the server."""
        if self.process:
            self.process.terminate()
            self.process.wait()
        self._executor.shutdown(wait=False)
