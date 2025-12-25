from tools.agent_connect import AgentConnector
import time

def test_fleet():
    ac = AgentConnector()
    print(f"📡 Visions connecting to {len(ac.AGENTS)} remote agents...\n")
    
    results = {}
    
    for agent_name, url in ac.AGENTS.items():
        print(f"Testing {agent_name.upper()}...")
        # Use a simple ping message
        response = ac.talk_to_agent(agent_name, "Ping from Visions. Status check.")
        
        # Check if successful (not an error message string roughly)
        status = "✅ Connected"
        if "Error" in response or "❌" in response:
            status = f"⚠️ Error: {response[:100]}..."
            
        print(f"  -> {status}")
        print(f"  -> Response: {response[:100]}...\n")
        results[agent_name] = status
        
    print("\n📊 Fleet Status Summary:")
    for name, status in results.items():
        print(f"{name.center(10)} | {status}")

if __name__ == "__main__":
    test_fleet()
