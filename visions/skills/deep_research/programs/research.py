import argparse
import time
import sys
from google import genai
from visions.core.config import Config

def run_deep_research(prompt: str):
    """
    Executes a Deep Research task using the Gemini Deep Research Agent.
    """
    print(f"🔬 Starting Deep Research on: '{prompt}'")
    
    # Initialize Client (Vertex AI preferred, or AI Studio)
    # Config.validate() should have been called by the main agent, but we'll check API key availability
    if Config.GOOGLE_AI_STUDIO_API_KEY:
        client = genai.Client(api_key=Config.GOOGLE_AI_STUDIO_API_KEY)
        print("Using AI Studio Client")
    else:
        # Vertex AI fallback
        import vertexai
        vertexai.init(project=Config.VERTEX_PROJECT_ID, location=Config.VERTEX_LOCATION)
        client = genai.Client(vertexai=True, project=Config.VERTEX_PROJECT_ID, location=Config.VERTEX_LOCATION)
        print(f"Using Vertex AI Client ({Config.VERTEX_PROJECT_ID})")

    try:
        # Create Interaction
        # Note: 'agent' param used instead of 'model' for interactions
        interaction = client.interactions.create(
            input=prompt,
            agent=Config.MODEL_DEEP_RESEARCH,
            background=True
        )
        
        print(f"✅ Interaction started. ID: {interaction.name}")
        
        # Poll for completion
        start_time = time.time()
        while True:
            status = client.interactions.get(name=interaction.name)
            
            elapsed = int(time.time() - start_time)
            sys.stdout.write(f"\r⏳ Status: {status.state} ({elapsed}s)")
            sys.stdout.flush()
            
            if status.state == "SUCCEEDED": # API might return 'SUCCEEDED' or 'completed', checking standard vertex states
                print("\n✅ Research Completed!")
                # Get the final answer
                # Interactions output structure verification
                if hasattr(status, 'outputs'):
                     for output in status.outputs:
                        if hasattr(output, 'text'):
                             print("\n" + "="*80)
                             print("RESEARCH REPORT")
                             print("="*80)
                             print(output.text)
                break
            elif status.state == "FAILED":
                print(f"\n❌ Research Failed: {status.error}")
                break
            elif status.state == "CANCELLED":
                 print("\n🚫 Research Cancelled.")
                 break
            
            time.sleep(10)
            
    except Exception as e:
        print(f"\n❌ Error executing Deep Research: {str(e)}")
        # Fallback guidance
        print("Tip: Ensure the Deep Research API is enabled and your account has access to the preview.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gemini Deep Research Agent")
    parser.add_argument("prompt", help="Research topic or question")
    args = parser.parse_args()
    
    run_deep_research(args.prompt)
