
import logging
import sys
import time
import unittest
import importlib.util
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from datetime import datetime

# Import Validation Logic
import verify_imports
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
logger = logging.getLogger("Sentinel-DeepScour")

class DeepScourSentinel:
    """
    🛡️ VISIONS AI - DEEP SCOUR SENTINEL
    Autonomous fail-safe validation loop.
    
    Checks:
    1. Import Integrity (Environment Check)
    2. Unit Test Suite (Logic Check)
    3. Gemini 3 Connectivity (Model Check)
    4. Memory Matrix Persistence (Data Check)
    """
    def __init__(self):
        self.interval = 300 # 5 minutes
        self.project_id = Config.VERTEX_PROJECT_ID
        self.memory = CloudMemoryManager(project_id=self.project_id)
    
    def check_imports(self):
        logger.info("📦 [CHECK 1/4] Validation Imports...")
        required = ["google.genai", "google.cloud.storage", "vertexai", "visions.core.agent"]
        missing = []
        for mod in required:
            if importlib.util.find_spec(mod) is None:
                missing.append(mod)
        if missing:
            logger.critical(f"❌ CRITICAL: Missing modules: {missing}")
            return False
        logger.info("   ✅ Environment Integrity Confirmed.")
        return True

    def check_unit_tests(self):
        logger.info("🧪 [CHECK 2/4] Running Smart Router Logic Tests...")
        # Run test_smart_router.py suite programmatically
        try:
            loader = unittest.TestLoader()
            suite = loader.discover('.', pattern='test_smart_router.py')
            runner = unittest.TextTestRunner(stream=open('os.devnull', 'w'), verbosity=0)
            result = runner.run(suite)
            if result.wasSuccessful():
                logger.info("   ✅ Smart Router Logic Verified (All Tiers Pass).")
                return True
            else:
                logger.error(f"❌ Smart Router Tests Failed! Failures: {len(result.failures)}")
                return False
        except Exception as e:
            logger.error(f"❌ Test Suite Execution Error: {e}")
            return False

    def check_gemini_3(self):
        logger.info("🧠 [CHECK 3/4] Pinging Gemini 3 Flash (Global)...")
        try:
            client = genai.Client(vertexai=True, project=self.project_id, location="global")
            start = time.time()
            response = client.models.generate_content(
                model=Config.MODEL_FLASH,
                contents="ping",
                config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_level="low"))
            )
            latency = time.time() - start
            logger.info(f"   ✅ Gemini 3 Alive. Latency: {latency:.2f}s")
            return True
        except Exception as e:
            logger.error(f"❌ Gemini 3 Unreachable: {e}")
            return False

    def check_memory(self):
        logger.info("💾 [CHECK 4/4] Writing Heartbeat to Memory Matrix...")
        try:
            self.memory.save_interaction("sentinel", "HEARTBEAT_DEEP_SCOUR", "OK")
            # Verify read
            recent = self.memory.get_recent_context("sentinel", 1)
            if recent and recent[0]['content'] == "HEARTBEAT_DEEP_SCOUR":
                logger.info("   ✅ Memory Read/Write Confirmed.")
                return True
            else:
                logger.warning("   ⚠️  Memory Write succeeded but Read verification failed.")
                return False
        except Exception as e:
             logger.error(f"❌ Memory Matrix Failure: {e}")
             return False

    def run_scour(self):
        logger.info("🚀 Initiating Deep Scour Sequence...")
        results = [
            self.check_imports(),
            self.check_unit_tests(),
            self.check_gemini_3(),
            self.check_memory()
        ]
        
        if all(results):
            logger.info(f"🟢 SYSTEM HEALTH: EXCELLENT. NEXT SCAN IN {self.interval}s.")
        else:
            logger.warning("🟠 SYSTEM HEALTH: DEGRADED. CHECK LOGS.")
            
    def run_eternally(self):
        logger.info("♾️  Sentinel Loop Started.")
        while True:
            try:
                self.run_scour()
                time.sleep(self.interval)
            except KeyboardInterrupt:
                logger.info("🛑 Sentinel Stopped.")
                break
            except Exception as e:
                logger.critical(f"🔥 Sentinel Crash: {e}")
                time.sleep(60)

if __name__ == "__main__":
    sentinel = DeepScourSentinel()
    sentinel.run_eternally()
