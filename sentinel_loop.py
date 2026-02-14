
import time
import logging
import random
import sys
from datetime import datetime
from visions.modules.mem_store.memory_cloud import CloudMemoryManager
from visions.core.config import Config
from google import genai
from google.genai import types

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SENTINEL] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("docs/logs/sentinel.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Sentinel")

class VisionsSentinel:
    """
    Eternal Watchdog for Visions AI.
    Loops 24/7 to verify:
    1. Cloud Connectivity (GCS/BQ)
    2. Model Availability (Gemini 3)
    3. Memory System Integrity
    """
    def __init__(self):
        self.project_id = Config.VERTEX_PROJECT_ID
        self.location = Config.VERTEX_GLOBAL_LOCATION
        self.memory = CloudMemoryManager(project_id=self.project_id)
        self.client = None
        self.check_interval = 300 # 5 minutes

    def _get_client(self):
        if not self.client:
             self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)
        return self.client

    def pulse_check(self):
        """Performs a single health check cycle."""
        logger.info("💓 Pulse Check Initiated...")
        
        # 1. Memory Write Test (Heartbeat)
        try:
            hb_id = f"heartbeat_{int(time.time())}"
            self.memory.save_interaction(
                user_id="sentinel_system", 
                prompt="STATUS_CHECK", 
                response="OPERATIONAL"
            )
            logger.info("   ✅ Memory Systems (SQL/GCS/BQ/MD) - WRITABLE")
        except Exception as e:
            logger.error(f"   ❌ Memory Write Failed: {e}")

        # 2. Model Latency Test (Gemini 3 Flash)
        try:
            start = time.time()
            client = self._get_client()
            
            # Simple "ping" query
            response = client.models.generate_content(
                model=Config.MODEL_FLASH,
                contents="ping",
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low")
                )
            )
            latency = time.time() - start
            logger.info(f"   ✅ Gemini 3 Flash Response: {latency:.2f}s")
            
        except Exception as e:
            logger.error(f"   ❌ Model Inference Failed: {e}")

    def run_eternally(self):
        logger.info("🚀 Visions Sentinel Started. Monitoring 24/7.")
        while True:
            try:
                self.pulse_check()
                
                # Sleep with visual countdown (for local dev fun) or silent wait
                next_check = datetime.now().timestamp() + self.check_interval
                logger.info(f"💤 Sleeping until {datetime.fromtimestamp(next_check).strftime('%H:%M:%S')}...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Sentinel Stopped by User.")
                break
            except Exception as e:
                logger.critical(f"🔥 CRITICAL LOOP FAILURE: {e}")
                time.sleep(60) # Backoff before retry

if __name__ == "__main__":
    sentinel = VisionsSentinel()
    sentinel.run_eternally()
