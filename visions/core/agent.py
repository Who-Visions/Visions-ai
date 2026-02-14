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
import datetime
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
from .prompts import GOD_MODE


logger = logging.getLogger("visions-core")

class KnowledgeRetriever:
    """RAG System with GCS Bucket Synchronization."""
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
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
            from visions.modules.genai.genai_embeddings import GenAIEmbeddings
            embeddings = GenAIEmbeddings(
                model_name=Config.EMBEDDING_MODEL,
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=Config.EMBEDDING_DIMENSIONS,
                project=self.project_id,
                location=self.location
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

    MAX_HISTORY: int = 10

    def __init__(self, project: str = Config.VERTEX_PROJECT_ID, location: str = Config.VERTEX_LOCATION):
        self.project = project
        self.location = location
        # Syncing instance variables to class-level Config for module-wide consistency
        Config.VERTEX_PROJECT_ID = project
        Config.VERTEX_LOCATION = location
        
        self._clients = {}
        self._tools_initialized = False


    def set_up(self):
        """Initialize resources. Called automatically by Reasoning Engine or manually."""
        if self._tools_initialized:
            return

        # CRITICAL: Prevent google-genai conflict between Vertex AI and API Key modes.
        # If running in Vertex AI mode, we must NOT have GOOGLE_API_KEY set in the environment.
        if "GOOGLE_API_KEY" in os.environ:
            logger.info("🧹 Clearing GOOGLE_API_KEY from environment to enable Vertex AI mode.")
            os.environ.pop("GOOGLE_API_KEY", None)
        if "GOOGLE_AI_STUDIO_API_KEY" in os.environ:
            os.environ.pop("GOOGLE_AI_STUDIO_API_KEY", None)

        logger.info("⚙️ Initializing Visions Agent Resources...")
        
        # Init GCP
        vertexai.init(project=self.project, location=self.location)
        
        # Lazy imports for stability and pickling
        from .skills import SkillRegistry
        from visions.modules.mem_store.memory_cloud import CloudMemoryManager
        from visions.modules.genai.genai_embeddings import GenAIEmbeddings
        from tools.vision_tools import VisionTools
        from tools.youtube_tools import YouTubeTools
        from tools.cinema_tools import CinemaTools
        from tools.agent_connect import AgentConnector
        from tools.browser_tool import BrowserTool
        from tools.audio_tools import AudioGenerator
        from tools.video_tools import VeoDirector


        # Systems
        self.retriever = KnowledgeRetriever(project_id=self.project, location=self.location)
        self.imager = ImageGenerator(agent=self)

        self.skill_registry = SkillRegistry()
        self.memory = CloudMemoryManager(project_id=self.project)
        
        # Tools
        self.vision_tools = VisionTools(project_id=self.project, location="global")
        self.youtube_tools = YouTubeTools(project_id=self.project, location=self.location)
        self.cinema_tools = CinemaTools()
        self.agent_connector = AgentConnector()
        try:
            self.browser_tool = BrowserTool()
        except Exception as e:
            logger.warning(f"⚠️ BrowserTool init failed (npx missing?): {e}")
            self.browser_tool = None

        self.audio_generator = AudioGenerator(project=self.project, location=self.location)
        self.video_director = VeoDirector(project=self.project, location=self.location)

        
        self._tools_initialized = True
        logger.info("✅ Visions Agent Resources Initialized.")


    def _ensure_initialized(self):
        if not self._tools_initialized:
            self.set_up()

    def _get_client(self, model: str = None) -> genai.Client:
        self._ensure_initialized()
        loc = self.MODEL_LOCATIONS.get(model, "global")
        # Clients are not picklable, so we don't store them in __init__
        # But we can cache them in the instance once running
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

        # 6. Context Clipping (Token Optimization)
        if len(context) > 150000:
            logger.warning(f"⚠️ Context exceeds safety threshold. Clipping for token optimization...")
            context = context[:150000] + "... [Context Truncated]"

        # Multimodal synthesis
        contents = [f"Intelligence Context: {context}\n\nInquiry: {question}"]
        if image_base64:
            contents.append(types.Part.from_bytes(data=base64.b64decode(image_base64), mime_type="image/png"))

        # Pre-flight Token Check
        token_count = self.count_tokens(contents, model=target_model)
        logger.info(f"🪙 Estimated Tokens: {token_count}")

        # Execute Synthesis with Tool Support
        client = self._get_client(target_model)
        
        # Define Tool Definitions for Multimodal Generation
        # We use explicit FunctionDeclarations for maximum compatibility with Vertex AI Global Endpoint
        creative_tools = [
            types.FunctionDeclaration(
                name="generate_image",
                description="Generate a high-quality cinematic image from a prompt using Gemini 3 Pro Vision.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "prompt": types.Schema(type=types.Type.STRING, description="Detailed visual prompt describing the scene.")
                    },
                    required=["prompt"]
                )
            ),
            types.FunctionDeclaration(
                name="generate_speech",
                description="Convert text to natural-sounding speech audio.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "text": types.Schema(type=types.Type.STRING, description="The exact text to convert to speech."),
                        "voice_name": types.Schema(type=types.Type.STRING, description="Optional voice name (e.g., 'Kore', 'Charon'). Default is 'Kore'.")
                    },
                    required=["text"]
                )
            ),
            types.FunctionDeclaration(
                name="generate_video",
                description="Generate a short, high-fidelity video from a text description using Veo.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "prompt": types.Schema(type=types.Type.STRING, description="Detailed video prompt describing motion and lighting.")
                    },
                    required=["prompt"]
                )
            )
        ]

        # Tool Configuration - Separate Tool objects per capability
        # CRITICAL: code_execution and function_declarations CANNOT share a Tool object.
        # gemini-3-pro-image-preview does NOT support function calling / code execution;
        # the agentic brain (flash/pro) is the one receiving these tools.
        generation_tools = [
             types.Tool(function_declarations=creative_tools),
        ]

        # Tool Mapping for dispatch
        tool_dispatch = {
            "generate_image": self.generate_image,
            "generate_speech": self.generate_speech,
            "generate_video": self.generate_video
        }

        # Robust Safety Settings (Allowing Creative Freedom)
        # Block only explicit high probability harm to allow artistic expression
        safety_settings = [
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
        ]

        # Multi-turn Tool Loop (Token Optimized TST-Loop)
        chat_contents = list(contents)  # Preserve original contents
        max_tool_turns = 3
        payload_store = {} # Side-channel to prevent token explosion
        final_response = None
        
        try:
            for turn in range(max_tool_turns):
                # Apply Thinking Config (Pro only)
                thinking_cfg = None
                if target_model == Config.MODEL_PRO:
                    thinking_cfg = types.ThinkingConfig(include_thoughts=True)

                logger.info(f"🚀 Turn {turn+1} | Model: {target_model}")
                
                response = client.models.generate_content(
                    model=target_model,
                    contents=chat_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=GOD_MODE,
                        tools=generation_tools,
                        thinking_config=thinking_cfg,
                        safety_settings=safety_settings,
                        temperature=1.0 
                    )
                )
                
                # Parse response parts for tool calls and text
                tool_calls = []
                text_parts = []
                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if part.function_call:
                            tool_calls.append(part.function_call)
                        elif part.text:
                            text_parts.append(part.text)
                
                if not tool_calls:
                    # No tools invoked — final text response
                    final_response = response.text or "\n".join(text_parts)
                    break
                
                # --- Append model's own response (with function_call parts) to history ---
                # This is required so the model sees: user → model(function_call) → user(function_response)
                chat_contents.append(response.candidates[0].content)
                
                # Execute calls with Token-Safe Interception (TST)
                tool_result_parts = []
                for tc in tool_calls:
                    if tc.name in tool_dispatch:
                        try:
                            args = {k: v for k, v in tc.args.items()}
                            result = tool_dispatch[tc.name](**args)
                            
                            # Token Optimization: Intercept massive results (base64)
                            if isinstance(result, str) and len(result) > 5000:
                                payload_id = f"PL_{int(time.time())}_{tc.name}"
                                payload_store[payload_id] = result
                                placeholder = f"SUCCESS. Payload stored as {payload_id}. Reference this ID in your response to the user."
                                logger.info(f"📥 Massive payload stored in side-channel: {payload_id}")
                                model_result = placeholder
                            else:
                                model_result = result
                                
                            tool_result_parts.append(
                                types.Part.from_function_response(
                                    name=tc.name,
                                    response={"result": model_result}
                                )
                            )
                        except Exception as tool_e:
                            logger.error(f"Tool {tc.name} error: {tool_e}")
                            tool_result_parts.append(
                                types.Part.from_function_response(
                                    name=tc.name,
                                    response={"error": str(tool_e)}
                                )
                            )
                    else:
                        tool_result_parts.append(
                            types.Part.from_function_response(
                                name=tc.name,
                                response={"error": f"Tool '{tc.name}' not available."}
                            )
                        )
                
                # Append tool results as user turn
                chat_contents.append(types.Content(parts=tool_result_parts, role="user"))
                
            else:
                # for/else: loop exhausted without break
                if final_response is None:
                    final_response = "Tool loop exceeded max turns. Please simplify your request."

            # 8. Post-Processing: Restore Payloads to Final Response
            for p_id, p_content in payload_store.items():
                final_response = final_response.replace(p_id, p_content)

            # 6. Persistent Memory (Fire-and-forget for speed)
            try:
                self.memory.save_interaction(user_id=user_id, prompt=question, response=final_response)
            except Exception as mem_e:
                logger.warning(f"Memory Save Failure: {mem_e}")
                
            return final_response
        except Exception as e:
            logger.error(f"Synthesis Loop Error: {e}")
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

    def get_live_token(self, model: str = None, expires_minutes: int = 30) -> str:
        """Provision an ephemeral token for Live API (v1alpha)."""
        client = self._get_client(model or Config.LIVE_AUDIO_MODEL)
        # Force v1alpha for auth tokens as per docs
        orig_version = client.http_options.api_version
        client.http_options.api_version = 'v1alpha'
        try:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            token = client.auth_tokens.create(
                config={
                    'uses': 1,
                    'expire_time': now + datetime.timedelta(minutes=expires_minutes),
                    'new_session_expire_time': now + datetime.timedelta(minutes=5)
                }
            )
            return token.name
        finally:
            client.http_options.api_version = orig_version
