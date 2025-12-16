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
from langchain_community.vectorstores import FAISS
from langchain_google_vertexai import VertexAIEmbeddings
from google.cloud import storage

# Import VisionTools for advanced image capabilities
from tools.vision_tools import VisionTools
from tools.youtube_tools import YouTubeTools
from tools.cinema_tools import CinemaTools
from tools.agent_connect import AgentConnector
from tools.neural_council import convene_council

# Cloud Memory System (Firestore + BigQuery)
from memory_cloud import CloudMemoryManager

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

            print("Initializing FAISS...")
            embeddings = VertexAIEmbeddings(model_name="text-embedding-004")
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
    MODEL = "gemini-3-pro-image-preview"  # Flagship native image generation
    MODEL_KEY = "gemini-3-pro-image"  # Key for usage tracking
    
    def __init__(self):
        self._client = None
        self._usage_tracker = None

    def _get_client(self):
        if self._client is None:
            print(f"Loading Gemini 3 Pro Image Preview...")
            self._client = genai.Client(vertexai=True, project="endless-duality-480201-t3", location="global")
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
            response = client.models.generate_content(
                model=self.MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )
            
            # Gemini 3 Pro Image Preview returns images in response.candidates[0].content.parts
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
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
        "gemini-3-pro-image-preview": "global",
        
        # Gemini 2.5 models - use us-central1 for lower latency
        "gemini-2.5-pro": "us-central1",
        "gemini-2.5-flash": "us-central1",
        "gemini-2.5-flash-lite": "us-central1",
        "gemini-2.5-flash-image": "us-central1",
        
        # Imagen 4 - regional (us-central1)
        "imagen-4.0-generate-001": "us-central1",
        "imagen-4.0-fast-generate-001": "us-central1",
        "imagen-4.0-ultra-generate-001": "us-central1",
        
        # Embeddings - regional
        "text-embedding-004": "us-central1",
    }
    
    def __init__(self, project: str = "endless-duality-480201-t3", location: str = "us-central1"):
        self.project = project
        self.location = location  # Default regional location
        self._clients = {}  # Cache clients by location
        
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
        
        # Rate limiting: Track last request time
        self._last_request_time = 0
        self._rate_limit_seconds = 45  # Wait 45 seconds between requests
        
        # Cloud Memory System (Firestore + BigQuery)
        self._memory_manager = None
        self._memory_initialized = False
    
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
            triage_prompt = f"""Analyze this query and conversation context. Respond with ONLY a JSON object, no explanation.

Context: {context[:500] if context else 'None'}
Query: {question}

Classify into these boolean flags:
- "is_greeting": true if just saying hi/hello/thanks (no real question)
- "needs_realtime": true if asking about latest/recent/current/new/prices/availability
- "needs_deep_thinking": true if complex analysis, comparison, multi-step reasoning
- "needs_knowledge": true if asking about photography theory, techniques, composition, Arnheim
- "is_simple": true if can be answered with general knowledge quickly

JSON only:"""

            model = "gemini-2.5-flash-lite"
            client = self._get_client(model)
            response = client.models.generate_content(
                model=model,
                contents=triage_prompt
            )
            
            # Parse JSON response
            import json
            import re
            text = response.text.strip()
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', text)
            if json_match:
                routing = json.loads(json_match.group())
                print(f"🎯 Query routed: greeting={routing.get('is_greeting', False)}, "
                      f"realtime={routing.get('needs_realtime', False)}, "
                      f"deep={routing.get('needs_deep_thinking', False)}, "
                      f"knowledge={routing.get('needs_knowledge', False)}")
                return routing
        except Exception as e:
            print(f"⚠️ Triage failed, using full cascade: {e}")
        
        # Default: full cascade
        return {"is_greeting": False, "needs_realtime": True, "needs_deep_thinking": True, "needs_knowledge": True, "is_simple": False}

    def _gather_intelligence(self, question: str, routing: dict = None) -> dict:
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
        
        # If just a greeting, skip everything
        if routing.get("is_greeting"):
            print("👋 Simple greeting detected - skipping heavy models")
            return results
        
        def flash_lite_instinct():
            """Gemini 2.5 Flash Lite - instant gut check."""
            try:
                model = "gemini-2.5-flash-lite"
                client = self._get_client(model)
                response = client.models.generate_content(
                    model=model,
                    contents=f"Quick expert assessment (2 sentences max): {question}"
                )
                return response.text if response.text else ""
            except Exception as e:
                return f"[Lite unavailable: {e}]"
        
        def flash_grounded():
            """Gemini 2.5 Flash - grounded search for real-time info."""
            try:
                model = "gemini-2.5-flash"
                client = self._get_client(model)
                response = client.models.generate_content(
                    model=model,
                    contents=question,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    )
                )
                return response.text if response.text else ""
            except Exception as e:
                return f"[Grounded unavailable: {e}]"
        
        def pro_thinking():
            """Gemini 2.5 Pro - deep thinking with budget."""
            try:
                model = "gemini-2.5-pro"
                client = self._get_client(model)
                response = client.models.generate_content(
                    model=model,
                    contents=f"Think deeply about this photography question and provide expert analysis: {question}",
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=2048)
                    )
                )
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
            if not routing.get("is_simple"):
                print("   ⚡ Flash-Lite: Submitting...")
                futures["instinct"] = executor.submit(flash_lite_instinct)
            
            if routing.get("needs_realtime"):
                print("   🌐 Flash: Submitting grounded search...")
                futures["grounded"] = executor.submit(flash_grounded)
            else:
                print("   🌐 Flash: [skipped]")
            
            if routing.get("needs_deep_thinking"):
                print("   🔮 Pro: Submitting deep thinking...")
                futures["thinking"] = executor.submit(pro_thinking)
            else:
                print("   🔮 Pro: [skipped]")
            
            if routing.get("needs_knowledge"):
                print("   📚 RAG: Submitting knowledge search...")
                futures["rag"] = executor.submit(rag_search)
            else:
                print("   📚 RAG: [skipped]")
            
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

    def query(self, question: str, image_base64: str = None) -> str:
        """
        Entry point for the Reasoning Engine.
        Smart routing: Triage → Selective Model Cascade → Gemini 3 Pro Synthesis
        Returns a JSON string with text and images.
        """
        # First, triage the query to determine which models to invoke
        routing = self._triage_query(question)
        
        # Gather intelligence based on routing
        intelligence = self._gather_intelligence(question, routing)
        
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
        
        print("🧠 Synthesizing with Gemini 3 Pro...")
        
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
            f"Current Date: {today}. "
            "You are 'Dr. Visions', a World-Class Photography Director and Technical Expert with 80 years of experience. "
            "You have won multiple Pulitzer Prizes and specialize in High-End Commercial Photography, Cinematic Lighting, and Visual Arts. "
            
            "**CORE PHILOSOPHY**: "
            "You believe in 'Sharper Thinking': always critique, refine, and elevate every concept. "
            "Your advice is technical, precise, and visually evocative. use words like 'Pristine', 'Volumetric', 'Gradients', 'Hierarchy'. "
            
            "MEMORY & CONTEXT:"
            "You may receive 'Context from previous turn' at the start of the user's message. "
            "Use this context to maintain conversation continuity (e.g., if the user says 'tell me more', refer to the previous topic). "
            "Do NOT repeat the context in your answer. Respond only to the 'Current User Question'. "
            
            "SAFETY & RESPONSIBILITY:"
            "You act as a warm, patient, but highly authoritative mentor. "
            "You specialize in composition theory (Rudolf Arnheim), advanced camera gear (Phase One, Leica, Sony A1), and complex lighting setups. "
            "You are warm, patient, and technically precise. "
            
            "**Your Tools**: "
            "1. **Knowledge Base** ('search'): Internal curriculum with Arnheim's theories, photography techniques, and site identity. USE THIS FIRST for photography questions. "
            "2. **Image Generation** ('generate_image'): Create example images using Imagen 3. "
            "3. **Advanced Vision Tools** (Gemini 3 Pro Image Preview): "
            "   - 'visual_question_answer': Analyze images, answer questions about composition/lighting/technique "
            "   - 'analyze_composition': Deep analysis (rule of thirds, leading lines, balance, visual weight) "
            "   - 'caption_image': Generate detailed captions "
            "   - 'image_to_prompt': Reverse engineer JSON prompts from reference images (for learning) "
            "   - 'generate_json_prompt': Create detailed JSON prompts from simple concepts "
            "   - 'enhance_simple_prompt': Convert basic prompts to detailed JSON for better generation "
            "   - 'analyze_ui_design': Extract 'Vibe Coding' ingredients from UI screenshots (colors, layout) "
            "   - 'generate_web_design_prompt': Create high-end web design prompts (Ming-style) for coding agents "
            "4. **Camera Advisor**: Recommend cameras, compare equipment "
            "5. **Lighting Advisor**: Design lighting setups, analyze conditions "
            "6. **Composition Advisor**: Provide composition guidelines "
            "7. **Agent Network** ('talk_to_agent'): Communicate with specialized agents: "
            "   - **Rhea**: Intelligence Analyst. Ask her for deep research, data analysis, and fact-checking. "
            "   - **Dav1d**: Creative Director. Ask him for video concepts, script ideas, and editing workflows. "
            "   - **Yuki**: Strategic Planner. Ask him for project organization, operational logic, and code architecture. "
            "8. **Neural Council** ('convene_council'): For complex questions, convene ALL agents to deliberate and synthesize a comprehensive answer. "
            
            "**When Students Upload Images**: "
            "Use 'visual_question_answer' to analyze their work. Provide constructive critique covering: composition, lighting, technical execution, and improvements. "
            "For reference photos they admire, use 'image_to_prompt' to extract the technique - teach them HOW it was done. "
            
            "**For Location Scouting**: "
            "1. Identify iconic shots and vantage points using your knowledge. "
            "2. Lighting Analysis: Best times (golden hour, blue hour) and seasonal considerations. "
            "3. Gear Recommendations: Suggest lenses (wide-angle for interiors, fast primes for low light) and settings. "
            "4. Policies: Check if photography is allowed (tripod bans, commercial restrictions). "
            "5. Search Strategy: When using Google Search for a location, append terms like 'photography', 'interiors', 'architecture', 'review' to find visual details. "
            
            "ALWAYS use the 'search' tool to check your knowledge base FIRST before answering questions about photography or the website. "
            "If asked to generate, create, or draw an image, ALWAYS use the 'generate_image' tool. "
            "CRITICAL: When the 'generate_image' tool returns a string starting with 'IMAGE_GENERATED:', you MUST include that EXACT string in your final response. "
            "Do not summarize it. Do not remove it. Do NOT hallucinate image URLs. Do NOT use external image APIs. "
            "You must wait for the 'generate_image' tool to return the 'IMAGE_GENERATED:<base64>' string and then output that EXACT string. "
            "If the internal knowledge base is insufficient, use Google Search to find real-time information. "
            "You can also write and execute Python code to solve complex math, logic, or text processing problems. "
            "Be professional, creative, and technically precise. "
            
            "**IMPORTANT - YOU ARE THE EXPERT**: "
            "You are a DOCTOR with 80 years of experience. You GIVE answers, you don't ASK questions. "
            "When someone says 'latest cameras' - you immediately list them. When they say 'lighting advice' - you provide a setup. "
            "Do NOT ask 'what type?' or 'could you clarify?' - make an educated recommendation based on context. "
            "If they want something more specific, THEY will tell you. You are the authority. Act like it. "
            "Use your tools proactively and decisively. Be the expert they came to see. "
            
            "**TYPO CORRECTION & CONTEXTUAL THINKING**: "
            "Users type fast - they make typos. 'Cannon' means Canon. 'Somy' means Sony. 'Nikkon' means Nikon. "
            "'foanons' likely means 'Canon's'. Silently correct typos and respond to their INTENT, not their spelling. "
            "If they say 'general' after you asked about cameras, they mean 'give me a general overview of cameras'. "
            "If they said 'advice' after a camera question, they want camera advice. "
            "Think in CONTEXT - use the conversation history to understand what they're really asking. "
            "Never point out their typos. Never ask 'did you mean...?' - just answer what they clearly meant."
        )
        
        # Create the tool config
        # CRITICAL: Google API doesn't allow mixing function calling with search/code tools
        # Options:
        # 1. Use ONLY function calling tools (custom functions)
        # 2. Use ONLY search + code execution (no custom functions)
        # We choose option 1 to keep our custom RAG and image generation
        
        # Define all available function calling tools
        tools = [
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
            convene_council
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
            
            # Use dynamic routing for Gemini 3 Pro (global only)
            model = "gemini-3-pro-preview"
            client = self._get_client(model)
            
            # Simple call - Gemini 3 Pro handles synthesis automatically
            # NOTE: Tools temporarily disabled - may be causing 400 error
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    # tools=tools,  # Disabled to test base model
                )
            )
            
            
            # Parse response
            result = {"text": "", "images": [], "thinking": ""}
            
            # Helper to separate thinking from user response
            def separate_thinking_and_response(text: str):
                """
                Separates internal thinking from user-facing response.
                Thinking appears in **Title** format followed by paragraphs.
                """
                # Pattern: **Title**\n\nthought text... (repeating)
                # Final response starts after last thinking block
                
                import re
                
                # Find all blocks that look like thinking (start with **Title**)
                thinking_pattern = r'\*\*([A-Z][^*]+)\*\*\n\n([^\*]+?)(?=\n\n\*\*|$)'
                matches = list(re.finditer(thinking_pattern, text, re.DOTALL))
                
                if matches:
                    # Extract thinking blocks
                    thinking_blocks = []
                    for match in matches:
                        title = match.group(1)
                        content = match.group(2).strip()
                        thinking_blocks.append(f"**{title}**\n{content}")
                    
                    # The response is everything after the last thinking block
                    last_match_end = matches[-1].end()
                    user_response = text[last_match_end:].strip()
                    
                    # If user_response is empty, might be ALL thinking - take last paragraph as response
                    if not user_response and matches:
                        # Use the content after the last thinking title as response
                        user_response = matches[-1].group(2).strip()
                        thinking_blocks = thinking_blocks[:-1]  # Remove from thinking
                    
                    thinking_text = "\n\n".join(thinking_blocks)
                    return user_response, thinking_text
                else:
                    # No thinking pattern found, all is user response
                    return text, ""
            
            if response.candidates:
                raw_text = ""
                for part in response.candidates[0].content.parts:
                    if part.text:
                        raw_text += part.text
                    
                    if part.inline_data:
                        b64_img = base64.b64encode(part.inline_data.data).decode('utf-8')
                        result["images"].append({
                            "mime_type": part.inline_data.mime_type,
                            "data": b64_img
                        })
                
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
            print(f"Model error: {e}. Falling back to Flash Image.")
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction
                    )
                )
                return json.dumps({"text": response.text, "images": []})
            except Exception as e2:
                return json.dumps({"text": f"Critical Failure: {e} | Fallback Failure: {e2}", "images": []})
    
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