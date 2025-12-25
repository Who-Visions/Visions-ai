from visions_director_engine import DirectorEngine

# Mock generation function for testing
def mock_generate(prompt, config):
    print(f"[MOCK AI] Generating for: {prompt[:50]}...")
    # Return a dummy response that satisfies the constraints for testing
    return "Analysis: All constraints met. Score: 10/10.\n1. Protagonist encounters their own hologram (Hook): FOUND\n2. Visual Motif: Reality Bleed - Memories projected on physical set: FOUND\n..."

if __name__ == "__main__":
    print("🧪 TEST: Verifying Cycle 007 Constraints...")
    engine = DirectorEngine(mock_generate)
    
    # Test text containing required elements
    test_story = """
    The detective stared at the hologram of his own face. It was bleeding memories onto the wet pavement (Reality Bleed).
    "You have 2 hours before the memory wipe," the hologram said.
    The camera pulled back, the world warping around him (Dolly Zoom).
    He knew he had to delete himself to kill the virus.
    "I am the leak," he whispered.
    A high-pitch whine filled his ears.
    """
    
    # Run check
    print("\n[Audit Result]")
    # We are testing if the engine *has* the new constraints loaded
    from visions_director_engine import MANDATORY_ELEMENTS
    required = [
        "Reality Bleed", "Dolly Zoom", "Self-deletion", "I am the leak"
    ]
    
    missing = []
    print("Checking internal configuration:")
    for req in required:
        found = False
        for element in MANDATORY_ELEMENTS:
            if req in element or req.lower() in element.lower():
                print(f"  ✅ Constraint Loaded: {element}")
                found = True
                break
        if not found:
            print(f"  ❌ MISSING: {req}")
            missing.append(req)
            
    if not missing:
        print("\n✅ All Cycle 007 Constraints Verified in Codebase.")
    else:
        print("\n❌ Verification Failed.")
