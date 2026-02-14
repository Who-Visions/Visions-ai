
import logging
import time
import os
import sys
from visions.modules.mem_store.memory_cloud import CloudMemoryManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemoryVerifier")

def verify_memory_system():
    logger.info("🧠 Starting Memory System Verification...")
    
    project_id = os.getenv("VERTEX_PROJECT_ID")
    if not project_id:
        logger.error("❌ VERTEX_PROJECT_ID not found in environment.")
        return

    logger.info(f"   Project ID: {project_id}")
    
    try:
        # Initialize Manager
        memory_manager = CloudMemoryManager(project_id=project_id)
        logger.info("   ✅ CloudMemoryManager Initialized")
        
        # Test Data
        user_id = "test_user_001"
        prompt = "Hello, world! logic check."
        response = "Hello! I am functioning correctly."
        
        # 1. Test Saving
        logger.info("   💾 Attempting to save interaction...")
        memory_manager.save_interaction(user_id, prompt, response)
        logger.info("   ✅ Save routine executed (Check logs for any internal try/catch warnings)")
        
        # 2. Test Local Retrieval
        logger.info("   📥 Testing Local SQL Retrieval...")
        context = memory_manager.get_recent_context(user_id, limit=1)
        
        if context and context[0]['role'] == 'user' and context[0]['content'] == prompt:
             logger.info(f"   ✅ Local SQL Retrieval Successful: {context}")
        else:
             logger.warning(f"   ⚠️  Local SQL Retrieval Mismatch or Empty: {context}")
             
        logger.info("✅✅ MEMORY VERIFICATION COMPLETE ✅✅")
        
    except Exception as e:
        logger.error(f"❌ Memory Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_memory_system()
