"""
Visions AI - Neural Agent Council
A council of specialized AI agents that collaborate to provide comprehensive answers.
Inspired by Karpathy's LLM Council, adapted for the Visions agent ecosystem.

Council Members:
- Visions (Photography Expert)
- Rhea (Intelligence Analyst)
- Dav1d (Creative Director)
- Yuki (Strategic Planner)

The Chairman (Visions) synthesizes all perspectives into a final answer.
"""

import asyncio
import aiohttp
import google.auth.transport.requests
import google.oauth2.id_token
from typing import List, Dict, Any, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.console import Group

console = Console()

# Agent Registry - The Who Visions Fleet
COUNCIL_AGENTS = {
    "kronos": {
        "url": "https://who-tester-agent-10579507338.us-central1.run.app",
        "name": "KRONOS",
        "specialty": "Lead Orchestrator & Council Coordinator",
        "emoji": "⚡"
    },
    "visions": {
        "url": None,  # Local - uses internal agent
        "name": "Dr. Visions",
        "specialty": "Photography & Visual Arts Expert",
        "emoji": "🎨"
    },
    "dav1d": {
        "url": "https://dav1d-322812104986.us-central1.run.app",
        "name": "DAV1D",
        "specialty": "Digital Avatar & Voice Intelligence Director",
        "emoji": "🎭"
    },
    "rhea": {
        "url": "https://rhea-noir-145241643240.us-central1.run.app",
        "name": "Rhea Noir",
        "specialty": "VTuber Mentor & Caribbean Vibes",
        "emoji": "🌙"
    },
    "yuki": {
        "url": "https://yuki-ai-914641083224.us-central1.run.app",
        "name": "Yuki",
        "specialty": "Cosplay Architect & Anime Database",
        "emoji": "🦊"
    },
    "bandit": {
        "url": "https://bandit-849984150802.us-central1.run.app",
        "name": "Bandit",
        "specialty": "Snow's Agent & 4-Year Training Complete",
        "emoji": "🦝"
    },
    "kaedra": {
        "url": "https://kaedra-69017097813.us-central1.run.app",
        "name": "Kaedra",
        "specialty": "Shadow Tactician & Strategic Intelligence",
        "emoji": "🌑"
    },
    "unk": {
        "url": "https://unk-agent-574321322006.us-central1.run.app",
        "name": "UNK",
        "specialty": "Cognitive Orchestrator & 6-Tier Model Routing",
        "emoji": "🧠"
    },
    "kam": {
        "url": "https://kam-api-587184277060.us-central1.run.app",
        "name": "K.A.M",
        "specialty": "Kindness Alignment & Emotional Intelligence",
        "emoji": "💛"
    },
    "iris": {
        "url": "https://iris-agent-618147264860.us-central1.run.app",
        "name": "IRIS",
        "specialty": "Multimodal Agent, RAG & Embeddings",
        "emoji": "👁️"
    }
}

CHAIRMAN = "visions"


class AgentCouncil:
    """
    Orchestrates a council of AI agents to collaboratively answer questions.
    Implements a 3-stage deliberation process:
    1. Individual opinions from each agent
    2. Peer review and ranking (optional)
    3. Chairman synthesis of final answer
    """
    
    def __init__(self, include_ranking: bool = False):
        """
        Initialize the council.
        
        Args:
            include_ranking: If True, includes Stage 2 peer ranking (slower but more thorough)
        """
        self.include_ranking = include_ranking
        self._auth_req = google.auth.transport.requests.Request()
        
    def _get_id_token(self, url: str) -> Optional[str]:
        """Get ID token for authenticated Cloud Run requests."""
        try:
            return google.oauth2.id_token.fetch_id_token(self._auth_req, url)
        except Exception:
            return None
    
    async def _query_remote_agent(
        self, 
        agent_key: str, 
        message: str,
        session: aiohttp.ClientSession
    ) -> Dict[str, Any]:
        """Query a remote agent via HTTP."""
        agent = COUNCIL_AGENTS[agent_key]
        url = agent["url"]
        
        if not url:
            return {"agent": agent_key, "response": None, "error": "Local agent - use internal call"}
        
        try:
            headers = {"Content-Type": "application/json"}
            token = self._get_id_token(url)
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            payload = {"message": message}
            
            async with session.post(f"{url}/chat", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "agent": agent_key,
                        "name": agent["name"],
                        "specialty": agent["specialty"],
                        "emoji": agent["emoji"],
                        "response": data.get("response") or data.get("text") or str(data)
                    }
                else:
                    return {
                        "agent": agent_key,
                        "name": agent["name"],
                        "response": None,
                        "error": f"HTTP {resp.status}"
                    }
        except Exception as e:
            return {
                "agent": agent_key,
                "name": agent["name"],
                "response": None,
                "error": str(e)
            }
    
    async def _query_local_visions(self, message: str) -> Dict[str, Any]:
        """Query the local Visions agent."""
        try:
            # Import here to avoid circular imports
            from visions_assistant.agent import get_chat_response
            response = get_chat_response(message)
            return {
                "agent": "visions",
                "name": "Dr. Visions",
                "specialty": "Photography & Visual Arts Expert",
                "emoji": "📸",
                "response": response
            }
        except Exception as e:
            return {
                "agent": "visions",
                "name": "Dr. Visions",
                "response": None,
                "error": str(e)
            }
    
    async def stage1_collect_opinions(self, query: str) -> List[Dict[str, Any]]:
        """
        Stage 1: Collect individual opinions from all council members.
        
        Args:
            query: The user's question
            
        Returns:
            List of agent responses
        """
        results = []
        
        # Prepare remote agent queries
        remote_agents = [k for k, v in COUNCIL_AGENTS.items() if v["url"] is not None]
        
        async with aiohttp.ClientSession() as session:
            # Query remote agents in parallel
            tasks = [self._query_remote_agent(agent, query, session) for agent in remote_agents]
            remote_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in remote_results:
                if isinstance(result, dict):
                    results.append(result)
                    
        # Query local Visions agent
        visions_result = await self._query_local_visions(query)
        results.append(visions_result)
        
        return results
    
    async def stage3_synthesize(
        self, 
        query: str, 
        stage1_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Stage 3: Chairman synthesizes all opinions into a final answer.
        
        Args:
            query: Original user query
            stage1_results: Results from Stage 1
            
        Returns:
            Final synthesized answer
        """
        # Build context from all opinions
        opinions_text = "\n\n".join([
            f"**{r['name']} ({r['specialty']})**:\n{r['response']}"
            for r in stage1_results if r.get('response')
        ])
        
        synthesis_prompt = f"""You are the Chairman of the Neural Agent Council. Multiple specialized AI agents have provided their perspectives on a user's question.

**Original Question:** {query}

**Agent Opinions:**
{opinions_text}

**Your Task as Chairman:**
Synthesize all perspectives into a single, comprehensive answer. Consider:
- Each agent's unique expertise and perspective
- Areas of agreement (these are likely accurate)
- Any contradictions (resolve them logically)
- Missing information that you can add

Provide a clear, authoritative final answer that represents the council's collective wisdom."""

        # Use local Visions as chairman
        result = await self._query_local_visions(synthesis_prompt)
        result["role"] = "Chairman"
        return result
    
    async def convene(self, query: str, show_progress: bool = True) -> Dict[str, Any]:
        """
        Convene the full council to answer a query.
        
        Args:
            query: The user's question
            show_progress: If True, shows animated progress in console
            
        Returns:
            Dict with stage1, stage3, and metadata
        """
        if show_progress:
            console.print(Panel(
                f"🔗 [bold]Neural Agent Council Convening[/bold]\n\n"
                f"Query: {query[:100]}...\n\n"
                f"Council Members:\n" +
                "\n".join([f"  {v['emoji']} {v['name']}" for v in COUNCIL_AGENTS.values()]),
                title="Council Session",
                border_style="cyan"
            ))
        
        # Stage 1: Collect opinions
        if show_progress:
            console.print("\n[cyan]Stage 1: Collecting Individual Opinions...[/cyan]")
        
        stage1_results = await self.stage1_collect_opinions(query)
        
        if show_progress:
            successful = len([r for r in stage1_results if r.get('response')])
            console.print(f"[green]✓ Received {successful}/{len(COUNCIL_AGENTS)} opinions[/green]")
            
            # Show individual opinions
            for result in stage1_results:
                if result.get('response'):
                    console.print(Panel(
                        result['response'][:500] + "..." if len(result.get('response', '')) > 500 else result.get('response', ''),
                        title=f"{result.get('emoji', '🤖')} {result['name']}",
                        border_style="dim"
                    ))
        
        # Stage 3: Synthesize
        if show_progress:
            console.print("\n[cyan]Stage 3: Chairman Synthesizing Final Answer...[/cyan]")
        
        stage3_result = await self.stage3_synthesize(query, stage1_results)
        
        if show_progress:
            console.print(Panel(
                stage3_result.get('response', 'No response'),
                title="[bold green]📜 Council's Final Answer[/bold green]",
                border_style="green"
            ))
        
        return {
            "stage1": stage1_results,
            "stage3": stage3_result,
            "query": query,
            "council_members": list(COUNCIL_AGENTS.keys())
        }


# CLI Tool for agent.py
def convene_council(query: str) -> str:
    """
    Convene the Neural Agent Council to collaboratively answer a complex question.
    
    Use this tool when the user asks a question that would benefit from multiple expert perspectives,
    such as complex photography decisions, creative projects, or strategic planning.
    
    Args:
        query: The question to present to the council
        
    Returns:
        The council's synthesized answer
    """
    council = AgentCouncil()
    
    # Run the async council in a sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(council.convene(query, show_progress=False))
    
    # Format response
    individual_opinions = "\n\n".join([
        f"**{r['name']}**: {r['response'][:200]}..."
        for r in result['stage1'] if r.get('response')
    ])
    
    final_answer = result['stage3'].get('response', 'Council failed to synthesize.')
    
    return f"""🔗 **Neural Agent Council Report**

**Individual Perspectives:**
{individual_opinions}

---

**Council's Final Answer:**
{final_answer}
"""


# Test function
async def test_council():
    """Quick test of the council."""
    council = AgentCouncil()
    result = await council.convene("What are the best practices for portrait photography lighting?")
    return result


if __name__ == "__main__":
    asyncio.run(test_council())
