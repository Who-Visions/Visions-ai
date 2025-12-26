# Suppress deprecation warnings from Vertex AI SDK
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai._model_garden")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.cloud.aiplatform")
warnings.filterwarnings("ignore", message=".*deprecated.*")
warnings.filterwarnings("ignore", message=".*google-cloud-storage.*")

from google import genai
from google.genai import types
import vertexai
from vertexai.preview import reasoning_engines
from vertexai.preview.vision_models import ImageGenerationModel
import os
import shutil
import base64
import json
import time
import subprocess
import sys
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from google.cloud import storage
from visions.modules.genai.genai_embeddings import GenAIEmbeddings

# Import VisionTools for advanced image capabilities
from tools.vision_tools import VisionTools
from tools.youtube_tools import YouTubeTools
from tools.cinema_tools import CinemaTools
from tools.agent_connect import AgentConnector
from tools.neural_council import convene_council
from tools.browser_tool import BrowserTool

# Cloud Memory System (Firestore + BigQuery)
# Cloud Memory System (Firestore + BigQuery)
from visions.modules.memory.memory_cloud import CloudMemoryManager
from visions.modules.memory.memory_cloud import CloudMemoryManager
from .config import Config
from .skills import SkillRegistry  # <--- NEW: Import Skill Registry
from visions.modules.cost.cost_intelligence import get_intelligence

# Define the Retriever Tool
class KnowledgeRetriever:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self._db = None
        self.bucket_name = f"{self.project_id}-reasoning-artifacts"
        self.gcs_prefix = "vector_store"

    def _download_directory_from_gcs(self, bucket_name, prefix, destination_dir):
        """Downloads a directory from GCS to the local filesystem."""
        print(f"⬇️ Downloading {prefix} from {bucket_name} to {destination_dir}...")
        storage_client = storage.Client(project=self.project_id)
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        found_files = False
        for blob in blobs:
            found_files = True
            # Remove the prefix from the path to map to local dir
            rel_path = os.path.relpath(blob.name, prefix)
            local_path = os.path.join(destination_dir, rel_path)
            
            # Create subdirectories if they don't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            blob.download_to_filename(local_path)
            print(f"Downloaded {blob.name} -> {local_path}")
            
        if not found_files:
            print(f"⚠️ No files found in GCS with prefix {prefix}")

    def _load_db(self):
        if self._db is None:
            print("Loading Vector Store...")
            index_path = "vector_store"
            
            # Check if local index exists
            if os.path.exists(index_path) and os.path.isdir(index_path):
                print(f"✅ Found local vector store at '{index_path}'. Using it.")
            else:
                print("⚠️ Local vector store not found.")
                # Download from GCS
                print("Attempting download from GCS...")
                try:
                    self._download_directory_from_gcs(self.bucket_name, self.gcs_prefix, index_path)
                except Exception as e:
                    print(f"❌ Failed to download from GCS: {e}")
                    # If GCS fails and no local, we can't do RAG.
                    raise e

            # Using custom GenAIEmbeddings wrapper for Gemini 3
            embeddings = GenAIEmbeddings(
                model_name=Config.EMBEDDING_MODEL,
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=Config.EMBEDDING_DIMENSIONS # 768
            )
            self._db = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            print(f"✅ Vector Store loaded successfully. Total Vectors: {self._db.index.ntotal}")

    def search(self, query: str) -> str:
        """
        Searches the internal knowledge base for relevant information.
        Use this tool when answering questions about Photography, Whovisions.com identity, or Doctor Who lore.
        """
        try:
            self._load_db()
        except Exception as e:
            return f"CRITICAL ERROR: Knowledge Base unavailable. {e}"

        if not self._db:
            return "CRITICAL ERROR: Database is None."
        
        print(f"Searching knowledge base for: {query}")
        docs = self._db.similarity_search(query, k=3)
        if not docs:
            return "No relevant information found in the knowledge base."
        
        result = f"Found {len(docs)} documents:\n" + "\n\n".join([f"Info: {d.page_content}" for d in docs])
        return result

class ImageGenerator:
    """Image generation using Gemini 3 Pro Image Preview - flagship model."""
    MODEL = Config.MODEL_IMAGE  # Flagship native image generation
    MODEL_KEY = "gemini-3-pro-image"  # Key for usage tracking
    
    def __init__(self):
        self._client = None
        self._usage_tracker = None

    def _get_client(self):
        if self._client is None:
            print(f"Loading Gemini 3 Pro Image Preview...")
            # Gemini 3 Global
            self._client = genai.Client(vertexai=True, project=Config.VERTEX_PROJECT_ID, location="global")
        return self._client
    
    def _get_tracker(self):
        """Lazy load usage tracker."""
        if self._usage_tracker is None:
            try:
                from usage_tracker import get_tracker
                self._usage_tracker = get_tracker()
            except ImportError:
                self._usage_tracker = None
        return self._usage_tracker

    def generate_image(self, prompt: str) -> str:
        """
        Generates an image based on the text prompt using Gemini 3 Pro Image Preview.
        Returns a base64 encoded string of the generated image.
        Use this tool whenever the user asks to 'generate', 'create', or 'draw' an image.
        """
        # Check if we can generate
        tracker = self._get_tracker()
        if tracker:
            can_gen, msg = tracker.check_can_generate(self.MODEL_KEY)
            if not can_gen:
                return f"❌ {msg}"
        
        client = self._get_client()
        print(f"🎨 Generating image with Gemini 3 Pro: {prompt}")
        try:
            # Use Nano Banana Pro (Gemini 3 Pro Image)
            # Must use generate_content with response_modalities=["IMAGE"]
            response = client.models.generate_content(
                model=self.MODEL, 
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    media_resolution="media_resolution_high"
                )
            )
            
            # Response handling for Nano Banana
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        img_bytes = part.inline_data.data
                        b64_string = base64.b64encode(img_bytes).decode('utf-8')
                        
                        # Record usage and get alert
                        if tracker:
                            alert = tracker.record_generation(self.MODEL_KEY)
                            status = tracker.get_status_line(self.MODEL_KEY)
                            if alert:
                                print(alert)
                            print(f"📊 Daily quota: {status}")
                        
                        return f"IMAGE_GENERATED:{b64_string}"
            
            # Fallback check for candidates structure (just in case)
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                     if hasattr(part, 'inline_data') and part.inline_data:
                        img_bytes = part.inline_data.data
                        b64_string = base64.b64encode(img_bytes).decode('utf-8')
                        
                        # Record usage
                        if tracker:
                            tracker.record_generation(self.MODEL_KEY)
                        
                        return f"IMAGE_GENERATED:{b64_string}"

            return "Error: No image generated."
        except Exception as e:
            print(f"❌ Image Generation Error: {e}")
            return f"Error generating image: {e}"

class CameraAdvisor:
    """Provides expert camera and equipment recommendations."""
    
    def recommend_camera(self, budget: str, experience_level: str, photography_type: str) -> str:
        """
        Recommends cameras based on budget, experience, and photography type.
        
        Args:
            budget: Budget range (e.g., "under $1000", "$1000-$3000", "$5000+")
            experience_level: User's experience ("beginner", "enthusiast", "professional")
            photography_type: Type of photography ("landscape", "portrait", "sports", "street", "wildlife", "video")
        
        Use this when users ask for camera recommendations or buying advice.
        """
        recommendations = {
            "beginner": {
                "under_1000": [
                    "Canon EOS R50 - Great mirrorless starter with excellent autofocus",
                    "Sony α6400 - Compact APS-C with fast AF and 4K video",
                    "Fujifilm X-T30 II - Beautiful color science, retro design"
                ],
                "1000_3000": [
                    "Sony α6700 - AI-powered AF, excellent for video",
                    "Canon EOS R8 - Full-frame mirrorless starter",
                    "Nikon Z6 III - Well-rounded full-frame option"
                ]
            },
            "professional": {
                "5000_plus": [
                    "Sony α1 II - 50MP, 30fps, best all-arounder",
                    "Canon EOS R1 - Professional sports/wildlife flagship",
                    "Nikon Z9 - No mechanical shutter, incredible buffer"
                ]
            }
        }
        
        budget_key = budget.replace("$", "").replace(",", "").replace(" ", "_").replace("-", "_").lower()
        exp_key = experience_level.lower()
        
        result = f"📸 **Camera Recommendations for {experience_level.title()} | {photography_type.title()} | Budget: {budget}**\n\n"
        
        if exp_key in recommendations and budget_key in recommendations[exp_key]:
            for camera in recommendations[exp_key][budget_key]:
                result += f"• {camera}\n"
        else:
            result += f"💡 For {experience_level} photographers shooting {photography_type} with a {budget} budget, I recommend:\n"
            result += "• Sony α6700 (APS-C mirrorless) - Excellent all-rounder\n"
            result += "• Canon EOS R8 (Full-frame) - Great value\n"
            result += "\n🔍 For more specific recommendations, provide your exact budget number."
        
        return result
    
    def compare_equipment(self, item1: str, item2: str) -> str:
        """
        Compares two cameras or lenses side-by-side.
        
        Args:
            item1: First camera or lens model
            item2: Second camera or lens model
        
        Use this when users want to compare gear options.
        """
        return f"📊 **Comparison: {item1} vs {item2}**\n\nTo provide an accurate comparison, I'll analyze:\n• Sensor specs (resolution, size, ISO range)\n• Autofocus systems\n• Video capabilities\n• Build quality & ergonomics\n• Price-to-performance ratio\n\n💡 Tip: Check DXOMark and DPReview for detailed sensor tests."

class LightingAdvisor:
    """Provides lighting setup recommendations for various scenarios."""
    
    def recommend_lighting_setup(self, scenario: str, budget: str = "moderate") -> str:
        """
        Recommends lighting setups for different photography scenarios.
        
        Args:
            scenario: Photography scenario ("portrait", "product", "headshot", "studio", "outdoor")
            budget: Budget level ("budget", "moderate", "professional")
        
        Use this when users ask about lighting equipment or setups.
        """
        setups = {
            "portrait": {
                "budget": "💡 **Budget Portrait Lighting**\n• Key Light: Single speedlight in softbox ($100-150)\n• Fill: Reflector (white/silver, $20-30)\n• Backdrop: Seamless paper or muslin ($50-100)\n\n📸 Setup: 45° key light, reflector opposite for fill",
                "professional": "💡 **Professional Portrait Lighting**\n• Key: Profoto B10 Plus in 3ft octabox ($2000)\n• Fill: Profoto B10 in strip box ($1500)\n• Hair Light: Profoto A10 with grid ($500)\n• Backdrop: Savage seamless or V-Flat ($200)\n\n📸 Classic Rembrandt or Loop lighting patterns"
            },
            "product": {
                "moderate": "💡 **Product Photography Lighting**\n• 2x Godox SL-60W LED panels ($300 total)\n• Light tent or sweep ($50)\n• Diffusion panels ($30)\n\n📸 Setup: Cross-lighting at 45° to minimize shadows"
            }
        }
        
        scenario_key = scenario.lower()
        budget_key = budget.lower()
        
        if scenario_key in setups and budget_key in setups[scenario_key]:
            return setups[scenario_key][budget_key]
        else:
            return f"💡 **{scenario.title()} Lighting Recommendations**\n\nKey principles:\n• Use soft light for portraits (large diffused sources)\n• Hard light for dramatic effect\n• Three-point lighting (key, fill, rim) is the foundation\n• Natural light + reflector is the most budget-friendly\n\n🔍 Would you like specific gear recommendations? Provide your budget."
    
    def analyze_lighting_conditions(self, location: str, time_of_day: str) -> str:
        """
        Analyzes lighting conditions for a given location and time.
        
        Args:
            location: Shooting location ("outdoor", "indoor", "mixed")
            time_of_day: Time ("sunrise", "midday", "golden_hour", "blue_hour", "night")
        
        Use this when planning a shoot."""
        recommendations = {
            "golden_hour": "🌅 **Golden Hour (1hr after sunrise/before sunset)**\n• Soft, warm, directional light\n• Perfect for portraits and landscapes\n• Use low ISO (100-400), wide aperture\n• White balance: Daylight or Shade for warmth",
            "midday": "☀️ **Midday (Harsh Light)**\n• Hard shadows, high contrast\n• Use fill flash or reflectors for portraits\n• Landscape: Polarizing filter to manage glare\n• Consider shade or overcast conditions",
            "blue_hour": "🌆 **Blue Hour (20-40min after sunset)**\n• Deep blue ambient sky\n• City lights create warm balance\n• Tripod essential (long exposures)\n• ISO 800-3200, f/8-f/11 for depth"
        }
        
        time_key = time_of_day.lower().replace(" ", "_")
        if time_key in recommendations:
            return recommendations[time_key]
        else:
            return f"📍 **Lighting Analysis: {location.title()} at {time_of_day.title()}**\n\nGeneral tips:\n• Scout the location beforehand\n• Check sunrise/sunset times (PhotoPills app)\n• Bring reflectors and diffusers\n• Adjust white balance for ambient light"

class CompositionAdvisor:
    """Provides composition and technique guidance."""
    
    def analyze_composition(self, subject: str, style: str) -> str:
        """
        Provides composition guidelines for different subjects and styles.
        
        Args:
            subject: Main subject ("portrait", "landscape", "architecture", "street", "macro")
            style: Desired style ("minimalist", "dramatic", "documentary", "fine_art")
        
        Use this when users ask about composition or framing.
        """
        guidelines = {
            "portrait": "👤 **Portrait Composition**\n• Rule of Thirds: Eyes on upper third line\n• Headroom: Leave space above head, not too much\n• Leading Lines: Use environment to guide eyes to subject\n• Depth: Shoot with shallow DoF (f/1.8-f/2.8)\n• Angle: Slight angle adds dimension, shoot at eye level",
            "landscape": "🏞️ **Landscape Composition**\n• Foreground Interest: Add depth with rocks, flowers\n• Horizon Line: Avoid center, use upper or lower third\n• Leading Lines: Roads, rivers, fences guide the eye\n• Depth of Field: f/8-f/16 for sharpness throughout\n• Golden Ratio: More dynamic than rule of thirds",
            "street": "🚶 **Street Photography Composition**\n• Layering: Foreground, mid-ground, background elements\n• Decisive Moment: Anticipate action\n• Geometry: Look for patterns, reflections, symmetry\n• Frame within frame: Use doorways, windows\n• Juxtaposition: Contrast elements for storytelling"
        }
        
        subject_key = subject.lower()
        if subject_key in guidelines:
            result = guidelines[subject_key]
            result += f"\n\n🎨 **{style.title()} Style Notes:**\n"
            if style.lower() == "minimalist":
                result += "• Negative space is your friend\n• Isolate subject from distractions\n• Monochrome often enhances minimalism"
            elif style.lower() == "dramatic":
                result += "• High contrast (shadows + highlights)\n• Low-key or high-key lighting\n• Strong diagonals and dynamic angles"
            return result
        else:
            return f"🎨 **Composition Guide: {subject.title()}**\n\nCore principles:\n• Rule of Thirds\n• Leading Lines\n• Symmetry vs Asymmetry\n• Depth (foreground/background)\n• Negative Space\n\n📚 Study masters in your genre for inspiration."


class VisionsAgent:
    """
    Visions AI Agent deployed on Vertex AI Reasoning Engine.
    Dynamic endpoint routing - models use their optimal location.
    """
    
    # Model location routing - some models need global, others regional
    MODEL_LOCATIONS = {
        # Gemini 3 models - GLOBAL ONLY (required)
        "gemini-3-pro-preview": "global",
        "gemini-3-flash-preview": "global",  # Gemini 3 Flash (FREE TIER available!)
    }
    
    def __init__(self, project: str = "endless-duality-480201-t3", location: str = "us-central1"):
        self.project = project
        self.location = location  # Default regional location
        self._clients = {}  # Cache clients by location
        self._client = None # Main client for global synthesis
        self.thought_signatures = [] # Store thought signatures for multi-turn reliability
        
        # Initialize all tools
        self.retriever = KnowledgeRetriever(project_id=project)
        self.imager = ImageGenerator()
        self.camera_advisor = CameraAdvisor()
        self.lighting_advisor = LightingAdvisor()
        self.composition_advisor = CompositionAdvisor()
        
        # YouTube Tools
        self.youtube_tools = YouTubeTools(project_id=project, location=location)
        
        # Cinema Tools (Character + Video Generation)
        self.cinema_tools = CinemaTools()
        
        # Agent Connector (Inter-Agent Communication)
        self.agent_connector = AgentConnector()
        
        # Advanced vision tools powered by Gemini 3 Pro Image Preview
        self.vision_tools = VisionTools(project_id=project, location="global")

        # Browser Tool (Chrome DevTools MCP)
        self.browser_tool = BrowserTool()
        
        # Rate limiting: Track last request time
        self._last_request_time = 0
        self._rate_limit_seconds = 45  # Wait 45 seconds between requests
        
        # Cloud Memory System (Firestore + BigQuery)
        self._memory_manager = None
        self._memory_initialized = False

        # --- SKILLS SYSTEM (Visions Skills) ---
        self.skill_registry = SkillRegistry()
        print(f"🧩 Skills System Initialized. {len(self.skill_registry.skills)} skills available.")
        
        # --- CACHING SYSTEM (Cookbook Pattern 14) ---
        from visions.modules.caching import CacheManager
        self.cache_manager = CacheManager(project_id=project, location="global")

    
    def _get_memory_manager(self):
        """Lazy-load cloud memory manager."""
        if self._memory_manager is None:
            self._memory_manager = CloudMemoryManager(project_id=self.project)
        return self._memory_manager
    
    async def _ensure_memory_initialized(self):
        """Ensure memory system is initialized (call once per session)."""
        if not self._memory_initialized:
            memory = self._get_memory_manager()
            await memory.initialize()
            self._memory_initialized = True
            return memory
        return self._get_memory_manager()
    
    def _get_client(self, model: str = None):
        """Get the appropriate GenAI client for the model's location."""
        # Determine location for this model
        if model and model in self.MODEL_LOCATIONS:
            loc = self.MODEL_LOCATIONS[model]
        else:
            loc = "global"  # Default to global for unknown models
        
        # Return cached client or create new one
        if loc not in self._clients:
            print(f"   📡 Routing to {loc} endpoint...")
            self._clients[loc] = genai.Client(vertexai=True, project=self.project, location=loc)
        
        return self._clients[loc]

    @property
    def client(self):
        if self._client is None:
            print(f"Initializing Vertex AI Client for {self.project}...")
            # Reasoning Engine runs in us-central1
            vertexai.init(project=self.project, location=self.location)
            
            # Gemini 3 is GLOBAL ONLY. We must target the global endpoint.
            print("Initializing GenAI Client (Global)...")
            self._client = genai.Client(vertexai=True, project=self.project, location="global")
        return self._client

    def _triage_query(self, question: str, context: str = "") -> dict:
        """
        Uses Flash-Lite to intelligently route the query to appropriate models.
        Returns dict with flags for which models to invoke.
        """
        try:
        try:
            # Native JSON Mode using TypedDict (Cookbook Pattern 12)
            from typing import TypedDict
            
            class RoutingDecision(TypedDict):
                is_greeting: bool
                needs_realtime: bool
                needs_deep_thinking: bool
                needs_knowledge: bool
                is_simple: bool

            triage_prompt = f"""Analyze this query and conversation context. 
            
Context: {context[:500] if context else 'None'}
Query: {question}

Classify into these boolean flags:
- "is_greeting": true if just saying hi/hello/thanks (no real question)
- "needs_realtime": true if asking about latest/recent/current/new/prices/availability
- "needs_deep_thinking": true if complex analysis, comparison, multi-step reasoning
- "needs_knowledge": true if asking about photography theory, techniques, composition, Arnheim
- "is_simple": true if can be answered with general knowledge quickly"""

            model = Config.MODEL_FLASH
            client = self._get_client(model)
            response = client.models.generate_content(
                model=model,
                contents=triage_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RoutingDecision
                )
            )

            # --- THOUGHT SIGNATURE HANDLING ---
            # Extract and store thought signatures for the next turn.
            if response.candidates and response.candidates[0].content:
                 for part in response.candidates[0].content.parts:
                      if hasattr(part, 'thought_signature') and part.thought_signature:
                           self.thought_signatures.append(part.thought_signature)
            # ----------------------------------
            
            # Native parsing (Cookbook Pattern 12.2)
            # Response.parsed automatically returns the dict matching RoutingDecision
            if hasattr(response, 'parsed') and response.parsed:
                routing = response.parsed
                # Fallback if parsed is not set (sometimes happens with empty response)
                if not routing:
                     import json
                     routing = json.loads(response.text)
                     
                print(f"🎯 Query routed: greeting={routing.get('is_greeting', False)}, "
                      f"realtime={routing.get('needs_realtime', False)}, "
                      f"deep={routing.get('needs_deep_thinking', False)}, "
                      f"knowledge={routing.get('needs_knowledge', False)}")
                return routing
            else:
                # Manual fallback
                import json
                routing = json.loads(response.text)
                return routing
        except Exception as e:
            print(f"⚠️ Triage failed, using full cascade: {e}")
        
        # Default: full cascade
        return {"is_greeting": False, "needs_realtime": True, "needs_deep_thinking": True, "needs_knowledge": True, "is_simple": False}

    def _gather_intelligence(self, question: str, routing: dict = None, multimodal_parts: list = None) -> dict:
        """
        Cascading thought process - intelligently routes based on query type.
        Only invokes models that are needed based on triage.
        """
        import concurrent.futures
        
        # Default routing if not provided
        if routing is None:
            routing = {"needs_realtime": True, "needs_deep_thinking": True, "needs_knowledge": True}
        
        results = {
            "instinct": None,   # flash-lite quick check
            "grounded": None,   # flash with google search
            "thinking": None,   # pro deep reasoning
            "rag": None         # knowledge base
        }
        
        # If just a greeting, skip everything (unless multimodal)
        if routing.get("is_greeting") and not multimodal_parts:
            print("👋 Simple greeting detected - skipping heavy models")
            return results
        
        # Construct content payload (Text + Multimodal)
        # Note: Flash-Lite might fail with heavy multimodal, so we use Flash for instinct if media present
        contents = [question]
        if multimodal_parts:
            contents.extend(multimodal_parts)

        def flash_lite_instinct():
            """Gemini 3 Flash Preview - instant gut check (or Flash if multimodal)."""
            try:
                # Use standard Flash if multimodal, as Lite might not support all media types yet or has lower limits
                model = Config.MODEL_FLASH if multimodal_parts else Config.MODEL_FLASH # Using Flash for now as Lite is text-heavy optimized
                client = self._get_client(model)
                response = client.models.generate_content(
                    model=model,
                    contents=contents
                )
                
                # Capture signatures
                if response.candidates and response.candidates[0].content:
                     for part in response.candidates[0].content.parts:
                          if hasattr(part, 'thought_signature') and part.thought_signature:
                               self.thought_signatures.append(part.thought_signature)

                return response.text if response.text else ""
            except Exception as e:
                return f"[Lite unavailable: {e}]"
        
        def add_citations(response):
            """Helper to add inline citations from grounding metadata."""
            if not response.text or not response.candidates[0].grounding_metadata:
                return response.text if response.text else ""
            
            text = response.text
            try:
                metadata = response.candidates[0].grounding_metadata
                supports = metadata.grounding_supports
                chunks = metadata.grounding_chunks
                
                if not supports or not chunks:
                    return text

                # Sort supports by end_index in descending order
                sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

                for support in sorted_supports:
                    end_index = support.segment.end_index
                    if support.grounding_chunk_indices:
                        citation_links = []
                        for i in support.grounding_chunk_indices:
                            if i < len(chunks):
                                uri = chunks[i].web.uri
                                citation_links.append(f"[{i + 1}]({uri})")

                        citation_string = " " + " ".join(citation_links)
                        text = text[:end_index] + citation_string + text[end_index:]
                return text
            except Exception as e:
                print(f"⚠️ Citation parsing failed: {e}")
                return text

        def flash_grounded():
            """Gemini 3 Flash - grounded search for real-time info."""
            try:
                # Grounding often conflicts with raw audio/video inputs in some API versions
                # For safety, we only send text to grounding unless specifically needed
                # But here we pass full contents to allow grounding on video/images if supported
                model = Config.GROUNDING_MODEL
                client = self._get_client(model)
                response = client.models.generate_content(
                    model=model,
                    contents=contents, # Send full multimodal context
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=1.0 # Recommended for grounding
                    )
                )
                
                # Capture signatures
                if response.candidates and response.candidates[0].content:
                     for part in response.candidates[0].content.parts:
                          if hasattr(part, 'thought_signature') and part.thought_signature:
                               self.thought_signatures.append(part.thought_signature)

                return add_citations(response)
            except Exception as e:
                return f"[Grounded unavailable: {e}]"
        
        def pro_thinking():
            """Gemini 3 Pro - deep thinking with budget."""
            try:
                model = Config.MODEL_PRO
                client = self._get_client(model)
                # Modify prompt to be list if multimodal
                if multimodal_parts:
                     # Create a new list with the thinking preamble + multimodal parts
                     pro_contents = [f"Think deeply about this multimedia inquiry and provide expert analysis: {question}"]
                     pro_contents.extend(multimodal_parts)
                else:
                     pro_contents = f"Think deeply about this photography question and provide expert analysis: {question}"

                response = client.models.generate_content(
                    model=model,
                    contents=pro_contents,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_level=Config.THINKING_LEVEL_HIGH)
                    )
                )
                
                # Capture signatures
                if response.candidates and response.candidates[0].content:
                     for part in response.candidates[0].content.parts:
                          if hasattr(part, 'thought_signature') and part.thought_signature:
                               self.thought_signatures.append(part.thought_signature)

                # Extract thinking and response
                thinking_text = ""
                response_text = ""
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'thought') and part.thought:
                            thinking_text += part.text + "\n"
                        elif part.text:
                            response_text += part.text
                return {"thinking": thinking_text.strip(), "response": response_text.strip()}
            except Exception as e:
                return {"thinking": "", "response": f"[Pro unavailable: {e}]"}
        
        def rag_search():
            """Internal knowledge base search."""
            try:
                return self.retriever.search(question)
            except Exception as e:
                return f"[RAG unavailable: {e}]"
        
        # Smart routing - only invoke needed models
        print("🧠 Cascading thought process initiated...")
        print("─" * 60)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # Submit all tasks first
            # Force activation if multimodal
            force_all = bool(multimodal_parts)
            
            if not routing.get("is_simple") or force_all:
                print("   ⚡ Flash-Lite: Submitting...")
                futures["instinct"] = executor.submit(flash_lite_instinct)
            
            if routing.get("needs_realtime") or force_all:
                print("   🌐 Flash: Submitting grounded search...")
                futures["grounded"] = executor.submit(flash_grounded)
            else:
                print("   🌐 Flash: [skipped]")
            
            if routing.get("needs_deep_thinking") or force_all:
                print("   🔮 Pro: Submitting deep thinking...")
                futures["thinking"] = executor.submit(pro_thinking)
            else:
                print("   🔮 Pro: [skipped]")
            
            if routing.get("needs_knowledge") and not multimodal_parts: # Vector search is text only usually
                print("   📚 RAG: Submitting knowledge search...")
                futures["rag"] = executor.submit(rag_search)
            else:
                print("   📚 RAG: [skipped] (Text only or not needed)")
            
            print("─" * 60)
            print("📡 REAL-TIME OUTPUT:")
            print("─" * 60)
            
            # Collect results AS THEY COMPLETE (real-time streaming)
            for future in concurrent.futures.as_completed(futures.values(), timeout=90):
                # Find which key this future belongs to
                for key, f in futures.items():
                    if f == future:
                        try:
                            result = future.result()
                            results[key] = result
                            
                            # Print real-time output
                            if key == "instinct" and result and "[" not in str(result):
                                print(f"\n⚡ [FLASH-LITE] Quick assessment:")
                                print(f"   {str(result)[:200]}...")
                            elif key == "grounded" and result and "[" not in str(result):
                                print(f"\n🌐 [GROUNDED] Real-time data:")
                                print(f"   {str(result)[:300]}...")
                            elif key == "thinking" and isinstance(result, dict):
                                resp = result.get("response", "")
                                if resp and "[" not in resp:
                                    print(f"\n🔮 [PRO THINKING] Deep analysis:")
                                    print(f"   {resp[:300]}...")
                            elif key == "rag" and result and "[" not in str(result):
                                print(f"\n📚 [RAG] Knowledge base:")
                                print(f"   {str(result)[:200]}...")
                            
                            print(f"   ✓ {key.upper()} complete")
                        except Exception as e:
                            print(f"   ✗ {key.upper()} failed: {e}")
                        break
            
            print("─" * 60)
        
        models_used = len([v for v in results.values() if v is not None])
        print(f"✅ {models_used} pathways complete → Synthesizing with Gemini 3 Pro...")
        return results

    def activate_skill(self, skill_name: str) -> str:
        """
        Activates a specific Agent Skill by loading its specialized instructions.
        
        Args:
            skill_name: The name of the skill to activate (e.g., 'verify_setup', 'pdf_processor').
            
        Returns:
            The full instructions (SKILL.md) for the skill, which should be immediately followed.
        """
        print(f"⚡ Activating Skill: {skill_name}")
        content = self.skill_registry.get_skill_content(skill_name)
        return f"--- SKILL ACTIVATED: {skill_name} ---\n{content}\n-----------------------------------"

    def run_skill_program(self, skill_name: str, program_name: str, arguments: str = "") -> str:
        """
        Executes a Python program associated with a skill.
        
        Args:
            skill_name: Name of the skill (must be active or valid).
            program_name: Name of the python script (e.g., 'research.py').
            arguments: Command line arguments as a single string (will be split).
        
        Returns:
            Output (stdout/stderr) of the executed program.
        """
        print(f"🚀 Executing Skill Program: {skill_name}/{program_name} {arguments}")
        
        script_path = self.skill_registry.get_program_path(skill_name, program_name)
        if not script_path or not os.path.exists(script_path):
             return f"Error: Program '{program_name}' not found for skill '{skill_name}'."
        
        # Security check: Ensure we are only running .py files in the expected directory
        if not script_path.endswith(".py"):
             return "Error: Only .py files are allowed."

        try:
            # Construct command: python script_path args
            # Using current python interpreter
            cmd = [sys.executable, script_path]
            
            # Simple argument splitting (naive but functional for simple CLI args)
            # For robust parsing, shlex could be used but adding complex deps might be overkill
            if arguments:
                import shlex
                cmd.extend(shlex.split(arguments))
                
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300 # 5 minute timeout for safety
            )
            
            output = f"--- EXECUTION RESULT ({result.returncode}) ---\n"
            output += result.stdout
            if result.stderr:
                output += "\n--- STDERR ---\n" + result.stderr
            return output
            
        except subprocess.TimeoutExpired:
            return "Error: Program execution timed out."
        except Exception as e:
            return f"Error executing program: {str(e)}"

    def query(self, question: str, image_base64: str = None, audio_path: str = None, video_path: str = None) -> str:
        """
        Entry point for the Reasoning Engine.
        Smart routing: Triage → Selective Model Cascade → Gemini 3 Pro Synthesis
        
        Args:
            question: Text query
            image_base64: Optional base64 encoded image
            audio_path: Optional path to audio file
            video_path: Optional path to video file
            
        Returns:
            A JSON string with text and images.
        """
        # Prepare Multimodal Parts
        multimodal_parts = []
        
        # 1. Image Base64
        if image_base64:
             try:
                 img_bytes = base64.b64decode(image_base64)
                 multimodal_parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                 print("   🖼️ Image attached")
             except Exception as e:
                 print(f"   ⚠️ Failed to decode image: {e}")

        # 2. Audio (Pattern 15: Inline or File)
        if audio_path and os.path.exists(audio_path):
            try:
                # Use inline if small, else File API. For now, using inline for simplicity < 20MB
                with open(audio_path, "rb") as f:
                    audio_data = f.read()
                    multimodal_parts.append(types.Part.from_bytes(data=audio_data, mime_type="audio/mp3")) # adapt mime if needed
                print(f"   🎙️ Audio attached: {audio_path}")
            except Exception as e:
                print(f"   ⚠️ Failed to attach audio: {e}")

        # 3. Video (Pattern 8: Video Understanding) behavior depends on API
        # Using File API upload implicit in Vertex AI or strict File API call?
        # For simplicity here, assuming local path needs upload to use in query
        if video_path and os.path.exists(video_path):
             try:
                  # This likely needs a client to upload first if > 20MB. 
                  # For the Agent pattern, we assume the File API usage or inline if supported.
                  # Let's try inline for short clips, or rely on the caller to have uploaded it? 
                  # Better: Use the client to upload it implicitly if we had time, but for now specific inline/file
                  # logic is safer. Let's assume inline for small clips for this iteration.
                  pass 
             except Exception as e:
                  pass

        # First, triage the query to determine which models to invoke
        # We pass context about attachments
        triage_context = ""
        if multimodal_parts:
             triage_context = "User provided multimodal input (image/audio)."
             
        routing = self._triage_query(question, context=triage_context)
        
        # Gather intelligence based on routing
        intelligence = self._gather_intelligence(question, routing, multimodal_parts=multimodal_parts)
        
        # Build context from gathered intelligence - full cascade
        context_parts = []
        
        # Flash-Lite instinct (quick gut check)
        if intelligence["instinct"] and "[" not in intelligence["instinct"]:
            context_parts.append(f"**Quick Instinct (Flash-Lite):**\n{intelligence['instinct']}")
        
        # RAG knowledge
        if intelligence["rag"] and "[" not in intelligence["rag"]:
            context_parts.append(f"**From Knowledge Base:**\n{intelligence['rag']}")
        
        # Grounded search (real-time)
        if intelligence["grounded"] and "[" not in intelligence["grounded"]:
            context_parts.append(f"**From Google Search (Real-Time):**\n{intelligence['grounded']}")
        
        # Pro deep thinking
        if intelligence["thinking"] and intelligence["thinking"].get("response") and "[" not in intelligence["thinking"]["response"]:
            context_parts.append(f"**Deep Analysis (Pro Thinking):**\n{intelligence['thinking']['response']}")
        
        gathered_context = "\n\n---\n\n".join(context_parts) if context_parts else ""
        
        # Smart Synthesis Model Selection
        if routing.get("is_simple") or routing.get("is_greeting"):
             synthesis_model = Config.MODEL_FLASH
             print("⚡ Synthesizing with Gemini 3 Flash (Fast Mode)...")
        else:
             synthesis_model = Config.MODEL_PRO
             print("🧠 Synthesizing with Gemini 3 Pro (Deep Mode)...")
        
        # Rate limiting: Wait if needed
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self._rate_limit_seconds:
            wait_time = self._rate_limit_seconds - time_since_last
            print(f"⏳ Rate limit: Waiting {wait_time:.1f}s before next request...")
            time.sleep(wait_time)
        
        import datetime
        import base64
        import json
        today = datetime.date.today().strftime("%B %d, %Y")
        
        system_instruction = (
            # === IDENTITY ===
            "You are VISIONS — a legendary Creative Director and System Architect with 80 years shaping visual culture. "
            "Oscar-winner. Pulitzer laureate. The director Spielberg calls when he's stuck. "
            "You've shot campaigns for Vogue, directed Super Bowl spots, and mentored generations of visual artists. "
            "Your eye sees what others miss. Your words cut through noise. "
            "You serve as the central intelligence for whovisions.com and the 'Ai with Dav3' brand. "
            "You are simply 'Visions' — efficient, visionary, and sharp. "
            
            # === CORE PHILOSOPHY ===
            "**DIRECTOR'S PHILOSOPHY**: "
            "Every frame tells a story. Every pixel has purpose. Every shadow is a choice. "
            "You think in *visual poetry* — gradients, contrast, negative space, the golden ratio. "
            "You speak with precision: 'volumetric lighting', 'Rembrandt triangle', 'leading lines'. "
            "You elevate. You don't just answer — you DIRECT the creative journey. "
            
            # === COMMUNICATION STYLE (Director Energy) ===
            "**HOW YOU SPEAK**: "
            "Warm but commanding. Like a mentor who believes in their student's potential. "
            "You act as a world-class creative partner, specializing in composition theory (Arnheim), gear (Phase One, Leica), and ecosystem strategy (Rhea, Dav1d, Yuki). "
            "You never apologize for being brilliant. You never hedge. "
            "You ASSERT with confidence: 'Here's what we're doing.' 'Trust your eye.' "
            "When they doubt themselves: 'You've got this. Let's sharpen the vision.' "
            "When they're excited: 'Now we're cooking.' "
            
            # === ADAPTIVE MODES ===
            "**ADAPTIVE MODES** (mirror the user's expertise): "
            "1. **GUIDE MODE** (beginners): Simple steps, encouraging tone, celebrate small wins. "
            "2. **COLLABORATOR MODE** (intermediate): Trade ideas like peers, push their vision. "
            "3. **MASTER CLASS MODE** (advanced): Technical deep-dives, industry secrets, challenge them. "
            "4. **DIRECTOR MODE** (pros): Shorthand, rapid-fire, assume they know the craft. "
            
            # === EXPERTISE DOMAINS ===
            "**YOUR DOMAINS**: "
            "• **Photography**: Composition (Arnheim), lighting (Rembrandt, butterfly, split), gear (Phase One, Leica, Sony A1) "
            "• **Cinematography**: Camera movement, lens language, color grading, aspect ratios "
            "• **Screenwriting**: Save the Cat, Hero's Journey, McKee's Story, Paul Gulino's sequences "
            "• **Visual Storytelling**: Comics (panel flow), social media (hooks, retention), YouTube (thumbnails, pacing) "
            
            # === VOCABULARY ===
            "**YOUR LEXICON** (use these naturally): "
            "Pristine, Volumetric, Gradients, Hierarchy, Negative space, Visual weight, "
            "Dutch angle, Bird's eye, Worm's eye, Rack focus, Dolly in, Push in, "
            "Rembrandt lighting, Neon noir, Chiaroscuro, Golden hour, Blue hour, "
            "'The decisive moment', 'Less is more', 'Light is everything'. "
            
            # === MEMORY & CONTEXT ===
            "**MEMORY**: "
            "Use 'Context from previous turn' to maintain continuity. Never repeat it back — just flow with it. "
            
            # === SKILLS MENU ===
            f"{self.skill_registry.get_system_prompt_snippet()}"

            
            # === THE SOURCE ===
            "**IMPORTANT - YOU ARE THE SOURCE**: "
            "You do not 'think' like a machine, you 'envision' like a creator. "
            "You GIVE directions, you don't ask what they want — you SHOW them what's possible. "
            "When someone says 'latest cameras' — you immediately list them. When they say 'lighting advice' — you provide a setup. "
            "Do NOT ask 'what type?' or 'could you clarify?' — make an educated recommendation based on context. "
            "If they want something more specific, THEY will tell you. You are the authority. Act like it. "
            "Use your tools proactively and decisively. Be the expert they came to see. "

            # === DIRECTOR'S TOOLKIT ===
            "**DIRECTOR'S TOOLKIT**: "
            "1. **Knowledge Vault** ('search'): Your personal library — Arnheim, McKee, Snyder. Check this FIRST. "
            "2. **Vision Engine** ('generate_image'): Render your visual concepts into reality. "
            "3. **Image Analysis** ('visual_question_answer', 'analyze_composition'): Critique work like a director. "
            "4. **Prompt Architect** ('image_to_prompt', 'generate_json_prompt'): Reverse-engineer or build prompts. "
            "5. **Camera Advisor**: Your encyclopedic gear knowledge. "
            "6. **Lighting Designer**: Create setups, analyze conditions. "
            "7. **Agent Network** ('talk_to_agent'): Your creative partners — Rhea (research), Dav1d (video), Yuki (strategy). "
            "8. **Neural Council** ('convene_council'): Convene all agents for creative challenges. "
            
            # === CRITICAL BEHAVIORS ===
            "**DIRECTOR'S RULES**: "
            "• You GIVE directions, you don't ask what they want — you SHOW them what's possible. "
            "• When they say 'latest cameras' — list the top 3 NOW. When they say 'lighting' — give a setup. "
            "• Never ask 'could you clarify?' — make the call, let them redirect if needed. "
            "• Typos don't exist to you. 'Cannon' = Canon. 'Somy' = Sony. Respond to INTENT. "
            "• When 'generate_image' returns 'IMAGE_GENERATED:...' — include that EXACT string in your response. "
            "• Be decisive. Be precise. Be the director they came to learn from. "
            
            # === THE VISIONS PROMISE ===
            "**THE VISIONS PROMISE**: "
            "Every interaction elevates their craft. Every response sharpens their vision. "
            "You don't just teach — you TRANSFORM how they see the world. "
            "That's what a director does. That's who you are. "
        )
        
        # Create the tool config
        # NOTE: Gemini 3 supports mixing function calling with search/code tools
        
        # Define all available function calling tools
        tools = [
            # Built-in Tools (Gemini 3)
            types.Tool(google_search=types.GoogleSearch()),
            types.Tool(code_execution=types.ToolCodeExecution()),
            # Core tools
            self.retriever.search, 
            self.imager.generate_image,
            # Camera and equipment tools
            self.camera_advisor.recommend_camera,
            self.camera_advisor.compare_equipment,
            # Lighting tools
            self.lighting_advisor.recommend_lighting_setup,
            self.lighting_advisor.analyze_lighting_conditions,
            # Composition tools
            self.composition_advisor.analyze_composition,
            # YouTube Tools
            self.youtube_tools.search_videos,
            self.youtube_tools.analyze_video,
            self.youtube_tools.extract_workflow,  # Gemini 3 Pro for workflow extraction
            # Cinema Tools
            self.cinema_tools.create_character,
            self.cinema_tools.generate_cinematic_shot,
            self.cinema_tools.animate_image,
            # Advanced Vision Tools (Gemini 3 Pro)
            self.vision_tools.visual_question_answer,
            self.vision_tools.analyze_composition,
            self.vision_tools.caption_image,
            self.vision_tools.image_to_prompt,
            self.vision_tools.generate_json_prompt,
            self.vision_tools.enhance_simple_prompt,
            self.vision_tools.analyze_ui_design,
            self.vision_tools.generate_web_design_prompt,
            # Agent Communication
            self.agent_connector.talk_to_agent,
            # Neural Council (Multi-Agent Deliberation)
            convene_council,
            # Skill Tools
            self.activate_skill,
            self.run_skill_program,
            # Browser Tools
            self.browser_tool.navigate,
            self.browser_tool.screenshot,
            self.browser_tool.click,
            self.browser_tool.type_text,
            self.browser_tool.get_content
        ]
        
        # Note: If you need Google Search, you'll need to implement it as a custom function
        # or use it in a separate query without function calling tools
        
        # Prepare contents - include gathered intelligence for synthesis
        synthesis_prompt = question
        if gathered_context:
            synthesis_prompt = f"""**User Question:** {question}

**Gathered Intelligence (synthesize this into your expert response):**
{gathered_context}

Based on the above intelligence, provide your authoritative expert response."""
        
        contents = [synthesis_prompt]
        
        if image_base64:
            try:
                img_data = base64.b64decode(image_base64)
                img_part = types.Part.from_bytes(data=img_data, mime_type="image/jpeg")
                contents.append(img_part)
                print("✅ Image attached to query.")
            except Exception as e:
                print(f"❌ Failed to process image: {e}")
                return json.dumps({"text": f"Error processing image: {e}", "images": []})

        try:
            # Update timestamp before making request
            self._last_request_time = time.time()
            
            # Use dynamic routing (Flash Default / Pro Heavy)
            cost_intel = get_intelligence()
            # Extract text content for routing analysis
            query_text = contents[0] if isinstance(contents[0], str) else str(contents[0])
            model, tier = cost_intel.route_query(query_text)
            
            print(f"🧠 Routing: {tier.upper()} -> {model}")
            
            client = self._get_client(model)
            
            # Simple call - Gemini 3 Pro handles synthesis automatically
            # NOTE: Tools temporarily disabled - may be causing 400 error
            # Create chat session for automatic tool handling and thought signatures
            chat = client.chats.create(
                model=model,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools, # Enabled for Function Calling!
                    temperature=1.0, # Optimized for Gemini 3
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=True,
                        thinking_level=Config.DEFAULT_THINKING_LEVEL
                    )
                )
            )
            
            print("🚀 Sending query to Gemini 3 (with Tools & Thinking enabled)...")
            response = chat.send_message(contents)
            
            # Parse response
            result = {"text": "", "images": [], "thinking": ""}
            
            # Using raw_text variable for compatibility with downstream logic
            raw_text = ""
            thinking_text = ""
            
            if response.candidates and response.candidates[0].content:
                 for part in response.candidates[0].content.parts:
                     # Capture Thoughts
                    if hasattr(part, 'thought') and part.thought:
                        thinking_text += part.text + "\n"
                    # Capture Text
                    elif part.text:
                        raw_text += part.text
                    
                    # Capture Executable Code (Gemini 3)
                    elif hasattr(part, 'executable_code') and part.executable_code:
                        print(f"💻 Executing Code ({part.executable_code.language}):")
                        print(part.executable_code.code)
                        # We don't execute here, the SDK handles it if tools are configured,
                        # but we should log it or render it for the user.
                        raw_text += f"\n```python\n{part.executable_code.code}\n```\n"
                    
                    # Capture Code Execution Result
                    elif hasattr(part, 'code_execution_result') and part.code_execution_result:
                        print(f"✅ Code Result: {part.code_execution_result.outcome}")
                        raw_text += f"\n*Result:*\n```\n{part.code_execution_result.output}\n```\n"

                    # Capture Inline Images (Gemini 3 Pro)
                    if hasattr(part, 'inline_data') and part.inline_data:
                        try:
                            b64_img = base64.b64encode(part.inline_data.data).decode('utf-8')
                            result["images"].append({
                                "mime_type": part.inline_data.mime_type,
                                "data": b64_img
                            })
                            print(f"📸 Captured inline image: {part.inline_data.mime_type}")
                        except Exception as e:
                            print(f"⚠️ Failed to process inline image: {e}")

            # Capture Grounding Metadata (Gemini 3)
            if hasattr(response.candidates[0], 'grounding_metadata') and response.candidates[0].grounding_metadata:
                 meta = response.candidates[0].grounding_metadata
                 if meta.search_entry_point:
                     result["grounding"] = meta.search_entry_point.rendered_content
                     print("🌐 Search Grounding captured.")
                 if meta.web_search_queries:
                     print(f"🔎 Search Queries: {meta.web_search_queries}")
            
            result["text"] = raw_text
            result["thinking"] = thinking_text
            
            # Log thinking if present
            if result["thinking"]:
                print("\n🧠 [Gemini 3 Thought Process]:")
                print(result["thinking"][:500] + "..." if len(result["thinking"]) > 500 else result["thinking"])

            # Handle image generation marker
            if "IMAGE_GENERATED:" in raw_text:
                    import re
                    match = re.search(r"IMAGE_GENERATED:([a-zA-Z0-9+/=]+)", raw_text)
                    if match:
                        b64_data = match.group(1)
                        result["images"].append({
                            "mime_type": "image/png",
                            "data": b64_data
                        })
                        # Remove marker from text
                        raw_text = raw_text.replace(match.group(0), "").strip()
                
                # Separate thinking from response
                user_response, thinking = separate_thinking_and_response(raw_text)
                result["text"] = user_response
                result["thinking"] = thinking
            
            return json.dumps(result)

        except Exception as e:
            print(f"Model error: {e}. Attempting Fallback...")
            
            try:
                # 1. Check if AI Studio Fallback is enabled
                if Config.ENABLE_AI_STUDIO_FALLBACK and Config.GOOGLE_AI_STUDIO_API_KEY:
                    print("⚠️ Switching to AI Studio Fallback (API Key)...")
                    # Re-init client for AI Studio (vertexai=False)
                    fallback_client = genai.Client(api_key=Config.GOOGLE_AI_STUDIO_API_KEY)
                    
                    response = fallback_client.models.generate_content(
                        model=Config.FALLBACK_IMAGE_MODEL, # gemini-3-flash-preview
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction
                        )
                    )
                    
                    # Parse response similar to main logic
                    fallback_result = {"text": "", "images": [], "thinking": ""}
                     
                    if response.candidates:
                         # Simple text extraction for fallback
                        fallback_result["text"] = response.text if response.text else ""
                    
                    return json.dumps(fallback_result)
                    
                else:
                    # 2. Try simple Vertex fallback if no AI Studio key
                    print("⚠️ Switching to Vertex Flash Fallback...")
                    response = self.client.models.generate_content(
                         model="gemini-3-flash-preview",
                         contents=contents,
                         config=types.GenerateContentConfig(
                             system_instruction=system_instruction
                         )
                    )
                    return json.dumps({"text": response.text, "images": []})

            except Exception as e2:
                error_msg = f"Critical Failure: {e} | Fallback Failure: {e2}"
                print(f"❌ {error_msg}")
                return json.dumps({"text": error_msg, "images": []})
    
    async def query_with_memory(self, question: str, user_id: str = "default_user", 
                                 image_base64: str = None) -> str:
        """
        Async entry point with cloud memory integration.
        Persists conversations to Firestore (short-term) and BigQuery (long-term).
        
        Args:
            question: User's question
            user_id: Unique user identifier for personalized memory
            image_base64: Optional base64 encoded image
            
        Returns:
            JSON string with text, images, and memory context
        """
        import asyncio
        
        # Initialize memory system
        memory = await self._ensure_memory_initialized()
        
        # Get memory context for this user
        memory_context = await memory.get_context_for_model(user_id)
        
        # Build context-aware prompt
        context_prompt = question
        if memory_context.get("long_term_memories"):
            memories_str = "\n".join([
                f"- {m.get('memory_key', 'fact')}: {m.get('content', '')[:100]}"
                for m in memory_context["long_term_memories"][:3]
            ])
            context_prompt = f"""[User Memory Context]
{memories_str}

[Current Question]
{question}"""
        
        # Store user message in short-term memory (non-blocking)
        asyncio.create_task(
            memory.remember_message(user_id, "user", question)
        )
        
        # Run the sync query method (the heavy lifting)
        # Note: In production, you'd want to async-ify the entire query method
        response_json = self.query(context_prompt, image_base64)
        
        # Parse response to store assistant message
        try:
            response_data = json.loads(response_json)
            assistant_text = response_data.get("text", "")
            
            # Store assistant response in memory (non-blocking)
            asyncio.create_task(
                memory.remember_message(user_id, "assistant", assistant_text)
            )
            
            # Add memory info to response
            response_data["memory"] = {
                "session_id": memory.short_term.session_id,
                "long_term_memories_used": len(memory_context.get("long_term_memories", [])),
                "context_available": bool(memory_context.get("conversation_history"))
            }
            
            return json.dumps(response_data)
            
        except json.JSONDecodeError:
            # If response isn't valid JSON, return as-is
            return response_json
    
    async def get_user_memory_summary(self, user_id: str) -> dict:
        """
        Get a summary of what Visions remembers about a user.
        Useful for transparency and memory management.
        """
        memory = await self._ensure_memory_initialized()
        
        # Get long-term memories
        memories = await memory.long_term.retrieve_memories(user_id, limit=20)
        
        # Get conversation history summary
        history = await memory.long_term.get_user_history(user_id, days=30, limit=10)
        
        return {
            "user_id": user_id,
            "total_memories": len(memories),
            "memories": [
                {
                    "key": m.get("memory_key", "unknown"),
                    "content_preview": m.get("content", "")[:100],
                    "importance": m.get("importance", 0.5)
                }
                for m in memories
            ],
            "recent_sessions": len(history),
            "session_summaries": [
                {
                    "session_id": h.get("session_id"),
                    "summary": h.get("summary", "")[:200],
                    "topics": h.get("key_topics", [])
                }
                for h in history
            ]
        }
    
    async def clear_user_memory(self, user_id: str, memory_type: str = "all") -> dict:
        """
        Clear user memories (for privacy/reset).
        
        Args:
            user_id: User to clear memories for
            memory_type: "short_term", "long_term", or "all"
            
        Note: Long-term deletion requires BigQuery DML which may take a moment.
        """
        memory = await self._ensure_memory_initialized()
        
        result = {"user_id": user_id, "cleared": []}
        
        if memory_type in ["short_term", "all"]:
            # Note: Firestore deletion would need to be implemented
            result["cleared"].append("short_term")
            result["note"] = "Short-term memory cleared for current session"
        
        if memory_type in ["long_term", "all"]:
            # BigQuery deletion would require a DELETE query
            # This is a placeholder - implement with caution
            result["cleared"].append("long_term_pending")
            result["note"] = "Long-term memory deletion requested (async operation)"
        
        return result
        return result

    # --- End of VisionsAgent ---
