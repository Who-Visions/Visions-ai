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
        "kronos": "https://who-tester-agent-10579507338.us-central1.run.app",
        "dav1d": "https://dav1d-322812104986.us-central1.run.app",
        "rhea": "https://rhea-noir-145241643240.us-central1.run.app",
        "yuki": "https://yuki-ai-914641083224.us-central1.run.app",
        "bandit": "https://bandit-849984150802.us-central1.run.app",
        "kaedra": "https://kaedra-69017097813.us-central1.run.app",
        "visions_cloud": "https://visions-assistant-service-620633534056.us-central1.run.app",
        "unk": "https://unk-agent-574321322006.us-central1.run.app",
        "kam": "https://kam-api-587184277060.us-central1.run.app",
        "iris": "https://iris-agent-618147264860.us-central1.run.app"
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
        
        # KRONOS uses /generate endpoint, others use /chat
        is_kronos = "kronos" in agent_key
        # KRONOS uses /generate, KAEDRA might use root or /chat, others use /chat
        is_kronos = "kronos" in agent_key
        is_kaedra = "kaedra" in agent_key
        is_kam = "kam" in agent_key
        
        if is_kronos:
            endpoint = f"{target_url}/generate"
        elif is_kaedra:
            # Kaedra v0.0.6 seems to respond at root or has specific routing. 
            # We'll try /chat first, but add root as primary fallback.
            endpoint = f"{target_url}/chat" 
        elif is_kam:
            # Kam uses OpenAI-compatible /v1/chat/completions
            endpoint = f"{target_url}/v1/chat/completions"
        else:
            endpoint = f"{target_url}/chat"
        
        print(f"📡 Connecting to Agent {agent_name.title()} at {target_url}...")
        
        try:
            # Get Auth Token
            headers = {"Content-Type": "application/json"}
            token = self._get_id_token(target_url)
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # Payload - KRONOS and KAM use 'prompt', others use 'message'
            if is_kronos or is_kam:
                payload = {"prompt": message}
            else:
                payload = {"message": message}
            
            # Request
            response = requests.post(endpoint, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                # Try to extract the response text from various common formats
                return data.get("response") or data.get("text") or data.get("message") or data.get("content") or str(data)
            elif response.status_code == 404:
                # Try fallback endpoints
                fallbacks = ["/generate", "/query", "/chat"] if not is_kronos else ["/chat", "/query"]
                if "kaedra" in agent_key:
                     # Kaedra verified online at root "/"
                     fallbacks = ["/", "/v1/chat", "/api/chat"]
                for fallback in fallbacks:
                    fallback_endpoint = f"{target_url}{fallback}"
                    print(f"🔄 Retrying with fallback endpoint {fallback_endpoint}...")
                    # Adjust payload for fallback
                    fb_payload = {"prompt": message} if "/generate" in fallback else {"message": message}
                    response = requests.post(fallback_endpoint, json=fb_payload, headers=headers, timeout=60)
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("response") or data.get("text") or data.get("content") or str(data)
                return f"Error {response.status_code}: All endpoints failed"
            else:
                return f"Error {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"❌ Connection failed: {str(e)}"

    def list_available_agents(self) -> str:
        """Lists all agents available for collaboration."""
        return "Available Agents:\n" + "\n".join([f"- {k.title()}: {v}" for k, v in self.AGENTS.items()])
