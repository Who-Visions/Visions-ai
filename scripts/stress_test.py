"""
Visions AI Stress Test
======================
Tests rate limiting, adaptive thinking, and fallback mechanisms.
"""

import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from visions.core.agent import VisionsAgent
import json

# Test queries of varying complexity
SIMPLE_QUERIES = [
    "what is aperture",
    "best camera under $500",
    "what is ISO",
    "recommend a lens",
    "photography basics",
]

COMPLEX_QUERIES = [
    "analyze the composition of a portrait with leading lines and rule of thirds",
    "compare Sony A1 II vs Canon R1 for professional wildlife photography",
    "plan a multi-step lighting setup for dramatic fashion photography",
    "critique and improve architectural photography workflow",
    "advanced technical strategy for low-light concert photography",
]

MIXED_QUERIES = SIMPLE_QUERIES + COMPLEX_QUERIES

def run_stress_test(queries, test_name="Stress Test", delay_override=None):
    """
    Run stress test with given queries.
    
    Args:
        queries: List of query strings
        test_name: Name of the test
        delay_override: If set, override agent's rate limit for testing
    """
    print(f"\n{'='*80}")
    print(f"🔥 {test_name.upper()}")
    print(f"{'='*80}\n")
    
    agent = VisionsAgent()
    
    # Override rate limit if specified (for testing)
    if delay_override is not None:
        agent._rate_limit_seconds = delay_override
        print(f"⚠️  Rate limit overridden to {delay_override}s for testing\n")
    
    results = {
        "test_name": test_name,
        "total_queries": len(queries),
        "successful": 0,
        "failed": 0,
        "fallback_used": 0,
        "deep_think_used": 0,
        "fast_think_used": 0,
        "errors": [],
        "timings": []
    }
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Query: {query[:60]}...")
        start_time = time.time()
        
        try:
            response_json = agent.query(query)
            response = json.loads(response_json)
            elapsed = time.time() - start_time
            
            results["timings"].append(elapsed)
            results["successful"] += 1
            
            # Check for fallback indicators
            if "Flash" in response.get("text", ""):
                results["fallback_used"] += 1
                print("⚠️  Flash fallback detected")
            
            print(f"✅ Success ({elapsed:.1f}s)")
            print(f"   Response preview: {response['text'][:100]}...")
            
        except Exception as e:
            elapsed = time.time() - start_time
            results["failed"] += 1
            results["errors"].append({
                "query": query,
                "error": str(e),
                "time": elapsed
            })
            print(f"❌ Failed ({elapsed:.1f}s): {str(e)[:100]}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 {test_name.upper()} RESULTS")
    print(f"{'='*80}")
    print(f"Total Queries:     {results['total_queries']}")
    print(f"✅ Successful:     {results['successful']}")
    print(f"❌ Failed:         {results['failed']}")
    print(f"⚠️  Fallback Used:  {results['fallback_used']}")
    
    if results["timings"]:
        avg_time = sum(results["timings"]) / len(results["timings"])
        min_time = min(results["timings"])
        max_time = max(results["timings"])
        print(f"\n⏱️  Timing Stats:")
        print(f"   Average: {avg_time:.1f}s")
        print(f"   Min:     {min_time:.1f}s")
        print(f"   Max:     {max_time:.1f}s")
    
    if results["errors"]:
        print(f"\n❌ Error Details:")
        for err in results["errors"][:5]:  # Show first 5 errors
            print(f"   - {err['error'][:80]}")
    
    print(f"{'='*80}\n")
    return results


def rapid_fire_test():
    """Test rate limiting by sending queries rapidly."""
    print("\n🚀 RAPID FIRE TEST - Testing 45-second rate limit")
    print("   This will attempt to send queries faster than allowed...\n")
    
    agent = VisionsAgent()
    rapid_queries = SIMPLE_QUERIES[:3]
    
    for i, query in enumerate(rapid_queries, 1):
        print(f"[{i}] Firing: {query}")
        start = time.time()
        try:
            agent.query(query)
            elapsed = time.time() - start
            print(f"    ✅ Completed in {elapsed:.1f}s")
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:80]}")
        print()


def quota_exhaustion_test():
    """Attempt to exhaust quota with many requests."""
    print("\n💥 QUOTA EXHAUSTION TEST - Sending requests until 429 error")
    print("   This will keep sending until quota limits are hit...\n")
    
    agent = VisionsAgent()
    count = 0
    max_attempts = 10
    
    while count < max_attempts:
        count += 1
        print(f"[{count}] Sending query...")
        
        try:
            agent.query(SIMPLE_QUERIES[count % len(SIMPLE_QUERIES)])
            print(f"    ✅ Success")
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"    🎯 QUOTA LIMIT REACHED at request #{count}")
                print(f"    Error: {error_str[:100]}")
                break
            else:
                print(f"    ❌ Other error: {error_str[:80]}")


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║                  🔥 VISIONS AI STRESS TEST 🔥                      ║
    ║                                                                    ║
    ║  This will push the system to its limits to test:                 ║
    ║  • Rate limiting (45-second delays)                                ║
    ║  • Adaptive thinking (LOW vs HIGH)                                 ║
    ║  • Flash fallback mechanism                                        ║
    ║  • Quota exhaustion handling                                       ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    input("⚠️  Press ENTER to start stress testing... (This will use API quota)")
    
    # Test 1: Simple queries only
    run_stress_test(SIMPLE_QUERIES, "Fast Think Test (Simple Queries)")
    
    # Test 2: Complex queries only
    run_stress_test(COMPLEX_QUERIES, "Deep Think Test (Complex Queries)")
    
    # Test 3: Mixed queries
    run_stress_test(MIXED_QUERIES[:5], "Mixed Query Test")
    
    # Test 4: Rapid fire (test rate limiting)
    rapid_fire_test()
    
    # Test 5: Quota exhaustion
    quota_exhaustion_test()
    
    print("\n✅ Stress testing complete!")
    print("📋 Check results above for any failures or issues.\n")
