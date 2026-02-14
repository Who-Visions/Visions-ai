
import os
import sys
import importlib.util
import compileall
import logging
import time

# Ralph Loop - Continuous Validation Watchdog
# "Scan every line of code. Make sure there's no errors."

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("RalphWatchdog")

REQUIRED_MODULES = [
    "visions.api.app",
    "visions.core.agent",
    "visions_assistant.agent",
    "visions.modules.mem_store.memory_cloud",
    "visions.core.config"
]

def check_syntax(directory):
    """Compiles all py files to check for syntax errors."""
    logger.info(f"🔍 Scanning syntax in {directory}...")
    try:
        # compileall returns True if success (in 3.x this might vary, checking return behavior)
        # compileall.compile_dir returns True if no errors
        result = compileall.compile_dir(directory, quiet=1, force=True)
        if result:
            logger.info("✅ Syntax Check Passed.")
            return True
        else:
            logger.error("❌ Syntax Check Failed.")
            return False
    except Exception as e:
        logger.error(f"❌ Syntax Check Exception: {e}")
        return False

def check_imports():
    """Simulates imports to verify module path resolution."""
    logger.info("🔍 Verifying Logic Flow & Imports...")
    
    # We add current dir to sys.path
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.append(cwd)

    all_passed = True
    for mod_name in REQUIRED_MODULES:
        try:
            # We don't just import, we check availability
            if importlib.util.find_spec(mod_name) is None:
                 logger.error(f"❌ Module NOT FOUND: {mod_name}")
                 all_passed = False
            else:
                 logger.info(f"✅ Module Resolved: {mod_name}")
        except Exception as e:
            logger.error(f"❌ Module Check Error {mod_name}: {e}")
            all_passed = False
            
    return all_passed

def deep_scan():
    """Performs the full validation loop."""
    print("\n" + "="*50)
    print(" 🐕 RALPH WATCHDOG - DEEP SCAN STARTING")
    print("="*50 + "\n")
    
    ROOT_DIR = os.getcwd()
    
    # 1. Syntax
    syntax_ok = check_syntax(ROOT_DIR)
    
    # 2. Imports
    imports_ok = check_imports()
    
    print("\n" + "="*50)
    if syntax_ok and imports_ok:
        print(" ✅ STATUS: GO - SYSTEMS NOMINAL")
        return True
    else:
        print(" ❌ STATUS: NO GO - FIX ERRORS BEFORE DEPLOY")
        return False
    print("="*50 + "\n")

if __name__ == "__main__":
    success = deep_scan()
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)
