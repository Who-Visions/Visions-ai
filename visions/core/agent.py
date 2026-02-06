# Visions AI - Core Agent v2.1.0
# Rhea Noir Standard - Heuristic Cascade & Locational Routing

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai._model_garden")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.cloud.aiplatform")

import os
import time
import json
import base64
import logging
import concurrent.futures
from typing import Optional, Dict, List, Any

from google import genai
from google.genai import types
import vertexai
from langchain_community.vectorstores import FAISS

# --- Project Imports ---
from .config import Config
from .skills import SkillRegistry
from visions.modules.genai.genai_embeddings import GenAIEmbeddings
from visions.modules.memory.memory_cloud import CloudMemoryManager
from tools.vision_tools import VisionTools
from tools.youtube_tools import YouTubeTools
from tools.cinema_tools import CinemaTools
from tools.agent_connect import AgentConnector
from tools.browser_tool import BrowserTool

logger = logging.getLogger("visions-core")

class KnowledgeRetriever:
    """RAG System for Visions AI."""
    def __init__(self, project_id: str):
        self.project_id = project_id
        self._db = None

    def _load_db(self):
        if self._db is None:
            index_path = "vector_store"
            embeddings = GenAIEmbeddings(
                model_name=Config.EMBEDDING_MODEL,
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=Config.EMBEDDING_DIMENSIONS
            )
            if os.path.exists(index_path):
                self._db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

    def search(self, query: str) -> str:
        try:
            self._load_db()
            if not self._db: return ""
            docs = self._db.similarity_search(query, k=3)
            return "\n\n".join([d.page_content for d in docs])
        except Exception as e:
            logger.error(f"RAG Error: {e}")
            return ""

class ImageGenerator:
    """Native Image Generation via Gemini 3 Pro Image Preview."""
    MODEL = Config.MODEL_IMAGE
    
    def __init__(self, agent=None):
        self.agent = agent

    def generate_image(self, prompt: str) -> str:
        client = self.agent._get_client(self.MODEL) if self.agent else genai.Client(vertexai=True, project=Config.VERTEX_PROJECT_ID, location="global")
        try:
            response = client.models.generate_content(
                model=self.MODEL, 
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["IMAGE"])
            )
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        img_bytes = part.inline_data.data
                        b64_string = base64.b64encode(img_bytes).decode('utf-8')
                        return f"IMAGE_GENERATED:{b64_string}"
            return "Error: Image generation failed or was blocked by safety filters."
        except Exception as e:
            return f"Error: {e}"

class VisionsAgent:
    """
    Visions AI Agent - The Rhea Noir Engine.
    Implements Heuristic Routing, Cascading Thought, and Locational Intelligence.
    """
    
    # Locational Routing Table
    MODEL_LOCATIONS = {
        Config.MODEL_PRO: "global",
        Config.MODEL_FLASH: "global",
        Config.MODEL_IMAGE: "global",
        Config.MODEL_IMAGEN_FALLBACK: "us-central1"
    }

    def __init__(self, project: str = Config.VERTEX_PROJECT_ID, location: str = Config.VERTEX_LOCATION):
        self.project = project
        self.location = location
        self._clients = {}
        
        # Initialize Google Vertex Auth
        vertexai.init(project=project, location=location)
        
        # Core Systems
        self.retriever = KnowledgeRetriever(project_id=project)
        self.imager = ImageGenerator(agent=self)
        self.skill_registry = SkillRegistry()
        self._memory_manager = CloudMemoryManager(project_id=project)
        
        # Shared Tools
        self.vision_tools = VisionTools(project_id=project, location="global")
        self.youtube_tools = YouTubeTools(project_id=project, location=location)
        self.cinema_tools = CinemaTools()
        self.agent_connector = AgentConnector()
        self.browser_tool = BrowserTool()

    def _get_client(self, model: str = None):
        """Dynamic client instantiation based on locational needs."""
        loc = self.MODEL_LOCATIONS.get(model, "global")
        if loc not in self._clients:
            self._clients[loc] = genai.Client(vertexai=True, project=self.project, location=loc)
        return self._clients[loc]

    def _triage_query(self, question: str) -> dict:
        """Flash-powered Heuristic Triage."""
        try:
            client = self._get_client(Config.MODEL_FLASH)
            prompt = (
                "Analyze query complexity and risk. Respond STRICTLY in JSON.\n"
                "Flags: 'is_high_risk' (bool), 'complexity' (int 1-10), 'needs_search' (bool), 'intent' (str).\n"
                f"Query: {question}"
            )
            response = client.models.generate_content(
                model=Config.MODEL_FLASH,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            logger.warning(f"Triage fallback: {e}")
            return {"is_high_risk": False, "complexity": 5, "needs_search": True, "intent": "general"}

    def query(self, question: str, image_base64: str = None, user_id: str = "user", config: dict = None) -> str:
        """
        Main query entry point with Heuristic Cascade.
        Determines thinking levels, models, and context in real-time.
        """
        # 1. Triage
        routing = self._triage_query(question)
        complexity = int(routing.get("complexity", 5))
        is_high_risk = routing.get("is_high_risk", False)
        
        # 2. Heuristic Level Assignment
        if is_high_risk or complexity >= 8:
            target_model = Config.MODEL_PRO
            thinking_level = Config.THINKING_LEVEL_HIGH
            status_label = "🚨 High-Risk Reasoning (Pro-High)"
        elif complexity >= 4:
            target_model = Config.MODEL_PRO
            thinking_level = Config.THINKING_LEVEL_MEDIUM
            status_label = "🔮 Advanced Reasoning (Pro-Med)"
        else:
            target_model = Config.MODEL_FLASH
            thinking_level = Config.THINKING_LEVEL_LOW
            status_label = "⚡ Standard Reasoning (Flash-Low)"
        
        logger.info(f"Targeting {target_model} with {thinking_level} thinking. [{status_label}]")
        
        # 3. Parallel Context Gathering
        context_parts = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            if routing.get("needs_search"):
                futures.append(executor.submit(self._get_client(Config.MODEL_FLASH).models.generate_content, 
                                               model=Config.MODEL_FLASH, 
                                               contents=f"Conduct search grounding for: {question}",
                                               config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])))
            futures.append(executor.submit(self.retriever.search, question))
            
            for f in concurrent.futures.as_completed(futures):
                try:
                    res = f.result()
                    if hasattr(res, 'text'): context_parts.append(f"Search Results: {res.text}")
                    elif isinstance(res, str): context_parts.append(f"Internal Knowledge: {res}")
                except Exception as e:
                    logger.error(f"Context error: {e}")

        # 4. Multimodal Synthesis
        contents = [f"Context from various pathways:\n{' '.join(context_parts)}\n\nQuery: {question}"]
        if image_base64:
            contents.append(types.Part.from_bytes(data=base64.b64decode(image_base64), mime_type="image/png"))
        
        # Override thinking level if explicitly requested in config
        if config and "thinking_level" in config:
            thinking_level = config["thinking_level"]

        # 5. Execution
        client = self._get_client(target_model)
        try:
            response = client.models.generate_content(
                model=target_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are Visions AI, a legendary creative director and photography mentor with 80 years of excellence. "
                        "You speak with authority, wit, and deep artistic insight. "
                        "Adopt a cinematic and elite tone. No emojis unless requested. "
                        "Focus on composition theory (Arnheim), lighting, and cinematic narrative."
                    ),
                    thinking_config=types.ThinkingConfig(thinking_level=thinking_level)
                )
            )
            
            # Combine thoughts and response for elite audit
            final_output = response.text
            
            # If thinking was performed, we can log it but usually keep it private from the end-user 
            # unless debugging is active.
            return final_output
            
        except Exception as e:
            logger.error(f"Synthesis Failure: {e}")
            return f"Internal Error in synthesis cascade: {e}"

    def generate_image(self, prompt: str) -> str:
        """Bridge for image generation."""
        return self.imager.generate_image(prompt)
