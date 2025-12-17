import os
import shutil
import time
from typing import Dict, Any, List
from .mcp_client import MCPClient

class BrowserTool:
    """
    Control a Chrome browser via Chrome DevTools MCP.
    Allows the agent to open pages, click elements, and extract data.
    """
    
    def __init__(self):
        self.client = None
        self._ensure_client()
        
    def _ensure_client(self):
        """Starts the MCP server if not already running."""
        if self.client:
            return

        # Ensure npx is available
        if not shutil.which("npx"):
            raise RuntimeError("npx is not installed or not in PATH")

        # Command to run the MCP server
        # We use -y to auto-accept installation if needed
        # On Windows, we need to explicitly find npx.cmd
        npx_path = shutil.which("npx")
        if not npx_path:
             raise RuntimeError("npx is not installed or not in PATH")
        
        command = npx_path
        # --browser-url is optional if we want to connect to existing, but let's let it launch its own or connect to default 9222
        args = ["-y", "chrome-devtools-mcp@latest"] 


        try:
            self.client = MCPClient(command, args)
            self.client.start()
            
            # Initialize connection
            # Give it a moment to spin up
            # time.sleep(2) 
            self.client.initialize()
            print("✅ Chrome DevTools MCP Connected", flush=True)
            if self.client:
                 print(f"DEBUG: Client initialized. Tools verify...", flush=True)

        except Exception as e:
            print(f"❌ Failed to start Chrome DevTools MCP: {e}")
            self.client = None

    def navigate(self, url: str) -> str:
        """
        Navigates to a specific URL.
        """
        if not self.client:
            return "Error: Browser tool not initialized."
            
        try:
            # Check available tools to find the right one
            # The tools are usually 'navigate_page' or similar
            result = self.client.call_tool("navigate_page", {"url": url})
            return f"Navigated to {url}. Result: {result}"
        except Exception as e:
            return f"Error navigating: {e}"

    def screenshot(self) -> str:
        """
        Takes a screenshot of the current page.
        Returns: Base64 encoded string or error.
        """
        if not self.client:
            return "Error: Browser tool not initialized."
        
        try:
            # Common tool name for screenshot
            result = self.client.call_tool("screenshot", {})
            # MCP results usually wrapped in content list
            if result and "content" in result:
                for item in result["content"]:
                    if item["type"] == "image":
                        return f"IMAGE_GENERATED:{item['data']}" # Match VisionTools format
            return "Error: No screenshot returned."
        except Exception as e:
            return f"Error taking screenshot: {e}"

    def click(self, selector: str) -> str:
        """
        Clicks an element identified by the CSS selector.
        """
        if not self.client:
            return "Error: Browser tool not initialized."
            
        try:
            self.client.call_tool("click", {"selector": selector})
            return f"Clicked element: {selector}"
        except Exception as e:
            return f"Error clicking {selector}: {e}"

    def type_text(self, selector: str, text: str) -> str:
        """
        Types text into an input field.
        """
        if not self.client:
            return "Error: Browser tool not initialized."
            
        try:
            self.client.call_tool("fill", {"selector": selector, "value": text})
            return f"Typed text into {selector}"
        except Exception as e:
            return f"Error typing in {selector}: {e}"

    def get_content(self) -> str:
        """
        Gets the text content of the current page.
        Note: The MCP might not have a direct 'get_content', often we use 'evaluate'
        or use accessibility tree.
        """
        # Based on typical MCP tools for chrome, might be 'run_script' or specific extract
        # Let's try evaluating document.body.innerText
        if not self.client:
            return "Error: Browser tool not initialized."

        try:
            # Some MCPs expose 'run_script' or 'evaluate'
            # Check tool list ideally, but assuming standard set
            result = self.client.call_tool("evaluate", {"expression": "document.body.innerText"})
            if result and "content" in result:
                 return result["content"][0]["text"]
            return "No content returned."
        except Exception as e:
            return f"Error getting content: {e}"

    def list_tools(self):
        """Debug function to list available tools from server."""
        if self.client:
            return self.client.list_tools()
        return []
