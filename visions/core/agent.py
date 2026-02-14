# Visions AI - Core Agent v3.0.0 (God Mode)
# Rhea Noir Standard - Heuristic Cascade, Locational Routing & Bucket Synchronization

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
from pathlib import Path

from google import genai
from google.genai import types
import vertexai
from langchain_community.vectorstores import FAISS
from google.cloud import storage

# --- Project Imports ---
from .config import Config
from .skills import SkillRegistry
from visions.modules.genai.genai_embeddings import GenAIEmbeddings
from visions.modules.mem_store.memory_cloud import CloudMemoryManager
from tools.vision_tools import VisionTools
from tools.youtube_tools import YouTubeTools
from tools.cinema_tools import CinemaTools
from tools.agent_connect import AgentConnector
from tools.browser_tool import BrowserTool
from tools.audio_tools import AudioGenerator
from tools.video_tools import VeoDirector
from .prompts import GOD_MODE

logger = logging.getLogger("visions-core")

class KnowledgeRetriever:
    """RAG System with GCS Bucket Synchronization."""
    def __init__(self, project_id: str):
        self.project_id = project_id
        self._db = None
        self.bucket_name = Config.GCS_BUCKET
        self.gcs_prefix = Config.VECTOR_STORE_PREFIX
        self.local_index = "vector_store"

    def _sync_from_gcs(self):
        """Standard GCS Sink - Ensuring vision is current."""
        if os.path.exists(self.local_index) and any(os.scandir(self.local_index)):
            return # Already synced or exists
            
        logger.info(f"⬇️ Syncing Knowledge Base from gs://{self.bucket_name}/{self.gcs_prefix}...")
        try:
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(self.bucket_name)
            blobs = bucket.list_blobs(prefix=self.gcs_prefix)
            
            os.makedirs(self.local_index, exist_ok=True)
            for blob in blobs:
                rel_path = os.path.relpath(blob.name, self.gcs_prefix)
                dest_path = os.path.join(self.local_index, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                blob.download_to_filename(dest_path)
        except Exception as e:
            logger.error(f"GCS Sync Failed: {e}")

    def _load_db(self):
        if self._db is None:
            self._sync_from_gcs()
            embeddings = GenAIEmbeddings(
                model_name=Config.EMBEDDING_MODEL,
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=Config.EMBEDDING_DIMENSIONS
            )
            if os.path.exists(self.local_index):
                try:
                    self._db = FAISS.load_local(self.local_index, embeddings, allow_dangerous_deserialization=True)
                    logger.info("✅ FAISS Knowledge Base Loaded.")
                except Exception as e:
                    logger.error(f"FAISS Load Error: {e}")

    def search(self, query: str) -> str:
        try:
            self._load_db()
            if not self._db: return ""
            docs = self._db.similarity_search(query, k=3)
            return "\n\n".join([d.page_content for d in docs])
        except Exception as e:
            logger.error(f"RAG Search Error: {e}")
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
            return "Error: Image generation failed (Safety or Capacity)."
        except Exception as e:
            return f"Error: {e}"

class VisionsAgent:
    """
    Visions AI Agent - Rhea Noir Engine v3.0.0 (God Mode).
    Heuristic Routing, Multi-Bucket Sync, Deep Thinking, and Advanced Safety.
    """
    
    MODEL_LOCATIONS = {
        Config.MODEL_PRO: "global",
        Config.MODEL_FLASH: "global",
        Config.MODEL_IMAGE: "global",
        "gemini-3-pro-image-preview": "global",
        Config.MODEL_IMAGEN_FALLBACK: "us-central1"
    }

    def __init__(self, project: str = Config.VERTEX_PROJECT_ID, location: str = Config.VERTEX_LOCATION):
        self.project = project
        self.location = location
        self._clients = {}
        
        # Init GCP
        vertexai.init(project=project, location=location)
        
        # Systems
        self.retriever = KnowledgeRetriever(project_id=project)
        self.imager = ImageGenerator(agent=self)
        self.skill_registry = SkillRegistry()
        self.memory = CloudMemoryManager(project_id=project)
        
        # Tools
        self.vision_tools = VisionTools(project_id=project, location="global")
        self.youtube_tools = YouTubeTools(project_id=project, location=location)
        self.cinema_tools = CinemaTools()
        self.agent_connector = AgentConnector()
        self.browser_tool = BrowserTool()
        self.audio_generator = AudioGenerator()
        self.video_director = VeoDirector()

    def _get_client(self, model: str = None) -> genai.Client:
        loc = self.MODEL_LOCATIONS.get(model, "global")
        if loc not in self._clients:
            self._clients[loc] = genai.Client(vertexai=True, project=self.project, location=loc)
        return self._clients[loc]

    def count_tokens(self, content: Any, model: str = Config.MODEL_FLASH) -> int:
        """Count tokens for usage optimization."""
        try:
            client = self._get_client(model)
            # Ensure proper content formatting for SDK
            response = client.models.count_tokens(model=model, contents=content)
            return response.total_tokens
        except Exception as e:
            logger.error(f"Token count failed: {e}")
            return 0

    def _triage_query(self, question: str) -> dict:
        """Route query by complexity/risk."""
        try:
            client = self._get_client(Config.MODEL_FLASH)
            prompt = f"Categorize query. Respond JSON: {{'is_high_risk': bool, 'complexity': 1-10, 'needs_search': bool}}. Query: {question}"
            response = client.models.generate_content(
                model=Config.MODEL_FLASH,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0 # Deterministic routing
                )
            )
            return json.loads(response.text)
        except Exception:
            return {"is_high_risk": False, "complexity": 5, "needs_search": True}

    def query(self, question: str, image_base64: str = None, user_id: str = "user", config: dict = None) -> str:
        """Standard Rhea Noir Cascade with God Mode Enhancements."""
        routing = self._triage_query(question)
        complexity = int(routing.get("complexity", 5))
        is_high_risk = routing.get("is_high_risk", False)
        
        # 6-Level Reasoning Heuristic Ladder
        logger.info(f"🤔 Smart Router Analysis - Complexity: {complexity}, Risk: {is_high_risk}")

        if is_high_risk or complexity >= 9:
            target_model = Config.MODEL_PRO
            thinking_level = Config.THINKING_LEVEL_HIGH
            routing_tier = "Tier 6: Pro / High (God Mode)"
        elif complexity >= 7:
            target_model = Config.MODEL_PRO
            thinking_level = Config.THINKING_LEVEL_LOW
            routing_tier = "Tier 5: Pro / Low"
        elif complexity >= 6:
            target_model = Config.MODEL_FLASH
            thinking_level = Config.THINKING_LEVEL_HIGH
            routing_tier = "Tier 4: Flash / High"
        elif complexity >= 4:
            target_model = Config.MODEL_FLASH
            thinking_level = Config.THINKING_LEVEL_MEDIUM
            routing_tier = "Tier 3: Flash / Medium"
        elif complexity >= 2:
            target_model = Config.MODEL_FLASH
            thinking_level = Config.THINKING_LEVEL_LOW
            routing_tier = "Tier 2: Flash / Low"
        else:
            target_model = Config.MODEL_FLASH
            thinking_level = Config.THINKING_LEVEL_MINIMAL
            routing_tier = "Tier 1: Flash / Minimal"
            
        logger.info(f"➡️ Routing Decision: {routing_tier}")
        
        # Parallel Intel
        context = ""
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            if routing.get("needs_search"):
                futures.append(executor.submit(self._get_client(Config.MODEL_FLASH).models.generate_content, 
                                               model=Config.MODEL_FLASH, 
                                               contents=f"Grounding search for: {question}",
                                               config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])))
            futures.append(executor.submit(self.retriever.search, question))
            
            for f in concurrent.futures.as_completed(futures):
                try:
                    res = f.result()
                    if hasattr(res, 'text'): context += f"\nSearch: {res.text}"
                    elif isinstance(res, str): context += f"\nKnowledge: {res}"
                except Exception: pass

        # Multimodal synthesis
        contents = [f"Intelligence Context: {context}\n\nInquiry: {question}"]
        if image_base64:
            contents.append(types.Part.from_bytes(data=base64.b64decode(image_base64), mime_type="image/png"))

        # Pre-flight Token Check
        token_count = self.count_tokens(contents, model=target_model)
        logger.info(f"🪙 Estimated Tokens: {token_count}")

        # Execute Synthesis
        client = self._get_client(target_model)
        
        # Robust Safety Settings (Allowing Creative Freedom)
        # Block only explicit high probability harm to allow artistic expression
        safety_settings = [
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
        ]

        try:
            response = client.models.generate_content(
                model=target_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=GOD_MODE,
                    thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
                    safety_settings=safety_settings,
                    temperature=1.0 # Default recommended for reasoning models
                )
            )
            final_response = response.text
            
            # 6. Persistent Memory (Fire-and-forget for speed)
            try:
                self.memory.save_interaction(user_id=user_id, prompt=question, response=final_response)
            except Exception as mem_e:
                logger.warning(f"Memory Save Failure: {mem_e}")
                
            return final_response
        except Exception as e:
            return f"Service interruption in synthesis: {e}"

    def generate_image(self, prompt: str) -> str:
        return self.imager.generate_image(prompt)

    def generate_speech(self, text: str, voice_name: str = "Kore") -> str:
        """Generate text-to-speech audio."""
        result = self.audio_generator.generate_speech(text, voice_name)
        if result:
            return f"AUDIO_GENERATED:{result}"
        return "Error: Speech generation failed."

    def generate_video(self, prompt: str) -> str:
        """Generate video from text using Veo."""
        result = self.video_director.generate_video(prompt)
        if result:
            return f"VIDEO_GENERATED:{result}"
        return "Error: Video generation failed."
