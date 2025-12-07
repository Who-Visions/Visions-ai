import time
import random
import concurrent.futures
from visions_assistant.agent import get_chat_response

# Ground Truth Data
EXPECTED_ANSWERS = {
    "Owner": ["Dave Meralus", "Meralus"],
    "Filing Date": ["September 2, 2020", "Sep 02 2020", "2020-09-02"],
    "Headquarters": ["Brooklyn", "1245 Ocean Ave"],
    "CEO Collection Price": ["$1,000", "1000"],
    "Mission": ["illuminate", "elevate", "visual storytelling"]
}

QUESTIONS = [
    ("Who is the Registered Agent for WHO VISIONS LLC?", "Owner"),
    ("When was Who Visions LLC filed?", "Filing Date"),
    ("Where is the company located?", "Headquarters"),
    ("How much is the Headshots CEO Collection?", "CEO Collection Price"),
    ("What is the mission of WhoVisions?", "Mission"),
    ("Who runs the company?", "Owner"), # Variation
    ("What is the address of the business?", "Headquarters"), # Variation
    ("Tell me the price for the most expensive headshot package.", "CEO Collection Price"), # Variation
    ("Is the company based in New York?", "Headquarters"), # Implicit
    ("What is the filing date?", "Filing Date")
]

def run_test(i):
    question, key = random.choice(QUESTIONS)
    print(f"🚀 [Test {i}] Asking: {question}")
    
    start_time = time.time()
    try:
        response = get_chat_response(question)
        duration = time.time() - start_time
        
        # Validation
        passed = False
        expected = EXPECTED_ANSWERS[key]
        for exp in expected:
            if exp.lower() in response.lower():
                passed = True
                break
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} [Test {i}] ({duration:.2f}s)\n   Response: {response[:100]}...")
        return passed, duration, response
    except Exception as e:
        print(f"🔥 [Test {i}] CRASH: {e}")
        return False, 0, str(e)

def main():
    print("⚔️ Starting Stress Test Harness (100 Iterations)...")
    print("Target: Vertex AI Reasoning Engine (RAG Enabled)")
    
    total_tests = 100
    failures = 0
    total_time = 0
    
    # Serial Execution (to respect quotas initially, can switch to parallel)
    results = []
    for i in range(1, total_tests + 1):
        passed, duration, resp = run_test(i)
        total_time += duration
        if not passed:
            failures += 1
        
        # Rate limit slightly to avoid immediate 429 if quota is low
        time.sleep(0.5) 

    print("\n" + "="*40)
    print(f"🏁 STRESS TEST COMPLETE")
    print(f"Total Tests: {total_tests}")
    print(f"Failures: {failures}")
    print(f"Success Rate: {((total_tests-failures)/total_tests)*100}%")
    print(f"Avg Latency: {total_time/total_tests:.2f}s")
    print("="*40)

if __name__ == "__main__":
    main()
