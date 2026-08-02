import json
import os
import base64
import sys
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Any, Optional, Tuple

# Audit Logging for 'Thinking Process'
AUDIT_AVAILABLE = False
try:
    # Try to reach back to rhea_noir if we're running under Rhea Noir context
    rhea_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Rhea-Noir"))
    if rhea_path not in sys.path:
        sys.path.append(rhea_path)
    from rhea_noir.audit import get_audit_logger
    audit = get_audit_logger()
    AUDIT_AVAILABLE = True
except Exception:
    audit = None

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

class GeospatialRecovery:
    """
    Geospatial Recovery Engine for Whovisions Fleet.
    Implements the 4-phase mechanism for achieving 100% data parity.
    """
    
    def __init__(self, manifest_path: str = "memory_banks/visions_archive_manifest.json"):
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "mineral-subject-487519-v6")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.console = None # Overwritten by caller if needed
        
        if VERTEX_AVAILABLE:
            vertexai.init(project=self.project_id, location=self.location)

    def _load_manifest(self) -> Dict[str, Any]:
        """Loads the ground truth archive manifest."""
        try:
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {"events": []}

    def _get_decimal_from_dms(self, dms, ref) -> float:
        """Converts Degrees, Minutes, Seconds to Decimal Degrees."""
        try:
            degrees = dms[0]
            minutes = dms[1]
            seconds = dms[2]
            
            # Pillow returns rationals as tuples (numerator, denominator)
            if isinstance(degrees, tuple): degrees = degrees[0] / degrees[1]
            if isinstance(minutes, tuple): minutes = minutes[0] / minutes[1]
            if isinstance(seconds, tuple): seconds = seconds[0] / seconds[1]

            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
            if ref in ['S', 'W']:
                decimal = -decimal
            return decimal
        except Exception:
            return 0.0

    def phase_1_the_snap(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Phase 1: EXIF Native - Extract GPS from headers."""
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()
            if not exif_data:
                return None
                
            gps_info = {}
            for tag, value in exif_data.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_info[sub_decoded] = value[t]
            
            if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                lat = self._get_decimal_from_dms(gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N"))
                lon = self._get_decimal_from_dms(gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E"))
                return {
                    "lat": lat, 
                    "lon": lon, 
                    "verified": True, 
                    "source": "exif",
                    "method": "Phase 1 (The Snap)"
                }
            
            return None
        except Exception as e:
            print(f"Phase 1 Failure: {e}")
            return None

    def phase_2_the_blitz(self, capture_time: datetime) -> Optional[Dict[str, Any]]:
        """Phase 2: Ground Truth Match - Map captureTime to event catalog."""
        for event in self.manifest.get("events", []):
            start = datetime.fromisoformat(event["start_date"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(event["end_date"].replace("Z", "+00:00"))
            
            # Ensure capture_time is offset-aware for comparison
            if capture_time.tzinfo is None:
                from datetime import timezone
                capture_time = capture_time.replace(tzinfo=timezone.utc)

            if start <= capture_time <= end:
                return {
                    "lat": event["location"]["lat"],
                    "lon": event["location"]["lon"],
                    "event_name": event["name"],
                    "facility": event["facility"],
                    "verified": True,
                    "source": "ground_truth",
                    "method": "Phase 2 (The Blitz)"
                }
        return None

    def phase_3_hail_mary(self, img_path: str, context_notes: str = "") -> Dict[str, Any]:
        """Phase 3: Vision Consensus - AI reasoning via Gemini 3.1 Pro."""
        if not VERTEX_AVAILABLE:
            return {"error": "Vertex AI SDK not available", "source": "vision_consensus"}

        try:
            model = GenerativeModel("gemini-3.1-pro")
            
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            image_part = Part.from_data(data=img_data, mime_type="image/jpeg")
            
            prompt = """
            PERSONA: ARCHAEOLOGICAL VISION REASONER (Rhea-Noir V1)
            TASK: Perform Geospatial Recovery for this visual asset.
            
            CONTEXT: This image belongs to the Whovisions archive. We have lost the GPS metadata.
            INSTRUCTION:
            1. Analyze landmarks, signage, flora, and architectural style.
            2. Identify the most likely city, facility, or event.
            3. Provide your best estimate for Latitude and Longitude.
            4. State your confidence level (Low, Medium, High).
            
            Return JSON only:
            {
              "lat": float,
              "lon": float,
              "reasoning": "string",
              "confidence": "string",
              "identified_landmarks": ["string"]
            }
            """
            
            response = model.generate_content([image_part, prompt])
            # Parse JSON from response
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(res_text)
            data["verified"] = False # Vision reasoning requires secondary verification
            data["source"] = "vision_consensus"
            data["method"] = "Phase 3 (Hail Mary)"
            return data
            
        except Exception as e:
            return {"error": str(e), "source": "vision_consensus"}

    def get_opensky_token(self) -> Optional[str]:
        """Retrieve OAuth2 token for OpenSky Network."""
        client_id = os.getenv("OPENSKY_CLIENT_ID")
        client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
        if not client_id or not client_secret:
            return None
        
        token_url = "https://opensky-network.org/auth/realms/opensky/protocol/openid-connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        try:
            resp = requests.post(token_url, data=data, timeout=10)
            resp.raise_for_status()
            return resp.json().get("access_token")
        except Exception:
            return None

    def the_lateral(self, flight_id: str, timestamp: datetime) -> Dict[str, Any]:
        """Phase 4: Flight Telemetry correlation."""
        token = self.get_opensky_token()
        if not token:
            return {"error": "OpenSky Authentication Failed", "source": "flight_telemetry"}
            
        # Convert timestamp to Unix epoch
        unix_time = int(timestamp.timestamp())
        
        # OpenSky API: Get state for specific aircraft at specific time
        # flight_id should be the ICAO24 hex code
        api_url = f"https://opensky-network.org/api/states/all?icao24={flight_id}&time={unix_time}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            resp = requests.get(api_url, headers=headers, timeout=15)
            resp.raise_for_status()
            states = resp.json().get("states", [])
            
            if not states:
                return {"error": f"No telemetry found for {flight_id} at {timestamp}", "source": "flight_telemetry"}
            
            # State vector format: [icao24, callsign, origin_country, time_position, last_contact, longitude, latitude, baro_altitude, on_ground, velocity, true_track, vertical_rate, sensors, geo_altitude, squawk, spi, position_source]
            state = states[0]
            return {
                "lat": state[6],
                "lon": state[5],
                "icao24": state[0],
                "callsign": state[1].strip() if state[1] else "Unknown",
                "altitude": state[13] or state[7],
                "verified": True,
                "source": "flight_telemetry",
                "method": "Phase 4 (The Lateral)"
            }
        except Exception as e:
            return {"error": str(e), "source": "flight_telemetry"}

    def the_agentic_eye(self, img_path_or_url: str) -> Dict[str, Any]:
        """Phase 5: Recursive Vision Loop (Gemma 4). 🛰️💅🏿✨"""
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        gemma_model = os.getenv("GEMMA_MODEL", "gemma4:e4b")
        
        # 🧪 Step 0: Fetch image (URL to Base64)
        try:
            if img_path_or_url.startswith("http"):
                import requests
                resp = requests.get(img_path_or_url)
                img_data = resp.content
            else:
                with open(img_path_or_url, "rb") as f:
                    img_data = f.read()
            img_b64 = base64.b64encode(img_data).decode('utf-8')
        except Exception as e:
            return {"error": f"Image fetch failed: {e}", "source": "agentic_eye"}

        # 🧠 Thinking Level 1: Deep Vision Reasoning (Native <|think|> mode)
        if self.console: self.console.print("[dim]  • Strategic Synthesis: Initializing Gemma 4 Deep Vision Reasoning... 🛰️[/dim]")
        
        system_msg = "<|think|>You are a high-fidelity geospatial intelligence engine specializing in recursive visual reasoning."
        user_prompt = """Analyze this image and identify its exact location using a 3-pass strategy.

JSON REQUEST:
{
  "macro_context": "Identify country/region",
  "archaeological_markers": [
    {"name": "Specific identifier", "type": "marker type", "confidence": "High/Med"}
  ],
  "search_queries": ["3 precise queries for Google Places"],
  "summary": "Geospatial summary"
}

FORMAT: Output JSON as the final answer.
"""
        try:
            # 📡 Deploying the Agentic Eye payload
            payload = {
                "model": gemma_model,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_prompt, "images": [img_b64]}
                ],
                "stream": False,
                "keep_alive": "5m", 
                "options": {"num_predict": 2048}
            }
            
            resp = requests.post(f"{ollama_url}/api/chat", json=payload, timeout=300)
            
            if resp.status_code != 200:
                return {"error": f"Ollama unreachable: {resp.status_code}", "source": "agentic_eye"}
                
            full_content = resp.json().get("message", {}).get("content", "")
            
            if AUDIT_AVAILABLE and audit:
                audit.log_step(
                    "GEMMA_REASONING_RAW", 
                    f"Captured full response payload ({len(full_content)} chars).",
                    full_content
                )
            
            # 🧠 Parsing the Thought Channel 📡🛰️
            thought_stream = ""
            final_answer = full_content
            
            import re
            # Support both <|channel|>thought and potential <thought> tags
            thought_match = re.search(r"(?:<\|channel\|>thought|<thought>)\s*(.*?)\s*(?:<\|channel\|>|</thought>)", full_content, re.DOTALL)
            if thought_match:
                thought_stream = thought_match.group(1).strip()
                # 📜 Log the Thinking Process to the Audit Trail
                if AUDIT_AVAILABLE and audit:
                    audit.log_step(
                        "GEMMA_REASONING_PASS", 
                        f"Parsed {len(thought_stream)} characters of deep reasoning.",
                        thought_stream
                    )
            # Remove thought block from final answer to find clean JSON
            final_answer = full_content
            if thought_match:
                final_answer = full_content.replace(thought_match.group(0), "").strip()
            
            if self.console and thought_stream:
                from rich.panel import Panel
                self.console.print(Panel(thought_stream, title="[bold magenta]Strategic Synthesis (Gemma 4 Reasoning)[/bold magenta]", border_style="magenta"))
            
            # Robust JSON extraction
            import json
            import re
            markers = {"error": "Native JSON parse failed", "raw": final_answer}
            
            # Find the first { and the last }
            json_match = re.search(r"(\{.*\})", final_answer, re.DOTALL)
            if json_match:
                markers_json = json_match.group(1)
                try:
                    markers = json.loads(markers_json)
                except json.JSONDecodeError:
                    # Looser cleaning for trailing commas or other common issues
                    cleaned_json = re.sub(r",\s*([\]}])", r"\1", markers_json)
                    try:
                        markers = json.loads(cleaned_json)
                    except:
                        pass
            
            # Extraction Phase
            gemma_intel = markers if isinstance(markers, dict) else {}
            
            poi_list = gemma_intel.get("archaeological_markers", [])
            search_queries = gemma_intel.get("search_queries", [])
            
            if self.console: 
                self.console.print(f"[dim]  • Level 2 Thinking: Isolated {len(poi_list)} markers & {len(search_queries)} search strategies... 🏘️[/dim]")

            # 🧪 Step 2: Search THE MANIFEST before swiping the Google Credit Card
            if self.console: self.console.print("[dim]  • Level 3 Thinking: Manifest Mapping (Zero-Cost Search)... 📉🛡️[/dim]")
            manifest_findings = []
            if self.manifest:
                events = self.manifest.get("events", [])
                for poi in poi_list:
                    name = poi.get("name", "").lower()
                    for entry in events:
                        if name in str(entry.get("facility", "")).lower() or \
                           name in str(entry.get("name", "")).lower():
                            manifest_findings.append({**entry, "source": "manifest"})
            
            # 🧪 Step 3: Predictive Failover (Google API)
            google_findings = []
            if not manifest_findings and self.api_key and search_queries:
                if self.console: self.console.print("[dim]  • Level 3 Thinking: Manifest Miss. Predictive Swipe of Google Card... 💳🛰️[/dim]")
                for query in search_queries[:1]:
                    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={self.api_key}"
                    r = requests.get(url)
                    if r.status_code == 200:
                        results = r.json().get("results", [])
                        for res in results[:2]:
                            google_findings.append({"name": res.get("name"), "address": res.get("formatted_address"), "source": "google"})
            
            return {
                "macro_context": gemma_intel.get("macro_context"),
                "archaeological_markers": poi_list,
                "manifest_matches": manifest_findings,
                "google_findings": google_findings,
                "summary": gemma_intel.get("summary", ""),
                "source": "agentic_eye_final"
            }
        except Exception as e:
            if self.console: self.console.print(f"[yellow]⚠️ Level 1 Intel failed: {e}[/yellow]")
            return {"error": str(e), "source": "the_agentic_eye"}
    def the_grid(self, query: str) -> Dict[str, Any]:
        """Phase 6: Spatial verification via Google Places API."""
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            return {"error": "Google Maps API Key Missing", "source": "the_grid"}
            
        endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": api_key
        }
        
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            results = data.get("results", [])
            if not results:
                return {"error": f"No matches found for '{query}'", "source": "the_grid"}
            
            best_match = results[0]
            loc = best_match.get("geometry", {}).get("location", {})
            
            return {
                "lat": loc.get("lat"),
                "lon": loc.get("lng"),
                "address": best_match.get("formatted_address"),
                "place_name": best_match.get("name"),
                "verified": True,
                "source": "google_maps",
                "method": "Phase 6 (The Grid)"
            }
        except Exception as e:
            return {"error": str(e), "source": "the_grid"}

    def the_thought_channel(self, evidence: Dict[str, Any], stage: str) -> Dict[str, Any]:
        """Gemma 4 'Thought Channel' loop for 3-pass validation before moving to next stage.
        Black coded and emoji-heavy as requested. 🧠🖤🏾🏿🪐🛰️🔥💯"""
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        gemma_model = os.getenv("GEMMA_MODEL", "gemma4:e4b")
        
        prompt = f"""<|think|>
        AIGHT BET. WE ON {stage} STAGE OF THE INVESTIGATION. 🏾‍♂️🕵🏾🏿
        
        CURRENT EVIDENCE:
        {json.dumps(evidence, indent=2)}
        
        VALIDATION TASK (3-PASS LOOP):
        1. Is this result 100% data parity? 🎯
        2. Are there any anomalies in the spatial markers? 🌀
        3. Do we NEED to swipe the Google Credit Card for the next phase? 💳
        
        Return JSON thinking:
        {{
          "sufficient": boolean,
          "reasoning": "string",
          "anomalies_detected": ["string"],
          "next_step_authorized": boolean,
          "vibe_check": "string"
        }}"""
        
        try:
            resp = requests.post(f"{ollama_url}/api/chat", json={
                "model": gemma_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "keep_alive": "5m", 
                "options": {"num_predict": 384}
            }, timeout=120) # Increased timeout for logic pass 🧠🔥
            
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "{}")
                if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
                return json.loads(content)
        except: pass
        return {"sufficient": False, "next_step_authorized": True, "vibe_check": "Thinking channel fumbled, move it along. 💨"}

    def recover(self, img_path: str, capture_time: Optional[datetime] = None, flight_id: Optional[str] = None) -> Dict[str, Any]:
        """Main entry point for recovery execution - TRIPLE-VALIDATION THINKING LOOP ACTIVE. 🏾‍♂️🕵🏾🏿🧠🖤🪐🛰️🔥💯"""
        
        # 🛡️ DEFENSE 1: Try Phase 1 (EXIF) - Purely Local & Free
        res = self.phase_1_the_snap(img_path)
        if res and res.get("lat"):
            # 🧠 Thought Channel 1: Validate EXIF parity
            thought = self.the_thought_channel(res, "PHASE 1: THE SNAP")
            if thought.get("sufficient", True): return {**res, "source": "exif", "method": "Phase 1 (The Snap) ✅"}
            print(f"[NYX] 🧠 Pass fumbled, insufficient parity: {thought.get('vibe_check')}")

        # 🛡️ DEFENSE 2: Try Phase 2 (Manifest) - Database Lookup (Free)
        if capture_time:
            res = self.phase_2_the_blitz(capture_time)
            if res:
                # 🧠 Thought Channel 2: Validate Manifest parity
                thought = self.the_thought_channel(res, "PHASE 2: THE BLITZ")
                if thought.get("sufficient", True): return {**res, "source": "local_manifest", "method": "Phase 2 (The Blitz) ✅"}
                print(f"[NYX] 🧠 Manifest shaky, move to telemetry: {thought.get('vibe_check')}")

        # 🛡️ DEFENSE 3: Try Phase 4 (Telemetry) - Flight Coring (Free/OpenSky)
        if flight_id and capture_time:
            res = self.the_lateral(flight_id, capture_time)
            if res and not res.get("error"):
                # 🧠 Thought Channel 3: Validate Telemetry parity
                thought = self.the_thought_channel(res, "PHASE 4: THE LATERAL")
                if thought.get("sufficient", True): return {**res, "source": "flight_telemetry", "method": "Phase 4 (The Lateral) ✅"}
                print(f"[NYX] 🧠 Telemetry not 100%, activate the Agentic Eye: {thought.get('vibe_check')}")

        # 🛡️ DEFENSE 4: Try Phase 5 (The Agentic Eye) - Local Reasoning (Gemma 4)
        res = self.the_agentic_eye(img_path)
        if res and not res.get("error"):
            # 🧠 Final Thought Channel: Global Vibe Check
            thought = self.the_thought_channel(res, "PHASE 5: THE AGENTIC EYE")
            if thought.get("sufficient", True): return res
            print(f"[NYX] 🧠 Agentic data inconclusive, swiping card for last-resort hail-mary: {thought.get('vibe_check')}")

        # 🛡️ DEFENSE 5: Failover to Phase 3 (Hail Mary) - Vertex AI (Paid Last Resort)
        return self.phase_3_hail_mary(img_path)

if __name__ == "__main__":
    # Test logic
    recovery = GeospatialRecovery("../../memory_banks/visions_archive_manifest.json")
    print("Testing Phase 6 (The Grid):")
    print(recovery.the_grid("Gaylord National Resort, MD"))
