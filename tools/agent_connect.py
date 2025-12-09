import os
import google.auth.transport.requests
import google.oauth2.id_token
import requests
import json
from typing import Optional, Dict, Any

class AgentConnector:
    """
    Enables secure communication with other AI Agents in the fleet.
    Handles authentication (ID Tokens) and API protocols automatically.
    """
    
    AGENTS = {
        "rhea": "https://rhea-noir-145241643240.us-central1.run.app",
        "dav1d": "https://dav1d-322812104986.us-central1.run.app"
    }
    
    def __init__(self):
        self._auth_req = google.auth.transport.requests.Request()
    
    def _get_id_token(self, url: str) -> str:
        """Generates an ID token for the specific Cloud Run service URL."""
        try:
            # Use Google Auth to get an ID token for the target audience (URL)
            token = google.oauth2.id_token.fetch_id_token(self._auth_req, url)
            return token
        except Exception as e:
            print(f"⚠️ Auth Warning: Could not generate ID token locally: {e}")
            # In some local dev environments (like generic ADC), this might fail.
            # In Cloud Run, this works automatically via Metadata Server.
            # Returning None to try unauthenticated (or let the caller handle it)
            return None

    def talk_to_agent(self, agent_name: str, message: str) -> str:
        """
        Sends a message to another specialized AI agent and returns their response.
        
        Args:
            agent_name: The name of the agent ("rhea" or "dav1d")
            message: The question or instruction for the agent
            
        Returns:
            The agent's response as text.
        """
        agent_key = agent_name.lower().strip()
        
        # Check if known agent
        target_url = None
        for name, url in self.AGENTS.items():
            if name in agent_key:
                target_url = url
                break
        
        if not target_url:
            return f"❌ Unknown agent '{agent_name}'. Available agents: {', '.join(self.AGENTS.keys())}"
        
        endpoint = f"{target_url}/chat"
        # Also try /v1/chat if standard endpoint fails, or assuming standard architecture
        
        print(f"📡 Connecting to Agent {agent_name.title()} at {target_url}...")
        
        try:
            # Get Auth Token
            headers = {"Content-Type": "application/json"}
            token = self._get_id_token(target_url)
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # Payload
            payload = {"message": message}
            
            # Request
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                # Try to extract the response text from various common formats
                return data.get("response") or data.get("text") or data.get("message") or str(data)
            elif response.status_code == 404:
                 # Try fallback endpoint /query
                fallback_endpoint = f"{target_url}/query"
                print(f"🔄 Retrying with fallback endpoint {fallback_endpoint}...")
                response = requests.post(fallback_endpoint, json=payload, headers=headers, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response") or str(data)
                else:
                    return f"Error {response.status_code}: {response.text}"
            else:
                return f"Error {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"❌ Connection failed: {str(e)}"

    def list_available_agents(self) -> str:
        """Lists all agents available for collaboration."""
        return "Available Agents:\n" + "\n".join([f"- {k.title()}: {v}" for k, v in self.AGENTS.items()])
