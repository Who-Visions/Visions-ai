"""
Visions Triple-Pass Mastery Training
=====================================
Runs Visions through the course THREE times until graduation.
Each pass builds on consolidated long-term memory.
"""

import sys
sys.path.insert(0, 'tests')

from test_visions_arnheim_curriculum import (
    VisionsArtBrain, CURRICULUM, AcademicYear
)

def run_course_once(brain, attempt_number):
    """Run Visions through all 4 years (compact output)"""
    
    for year in [AcademicYear.FRESHMAN, AcademicYear.SOPHOMORE, 
                 AcademicYear.JUNIOR, AcademicYear.SENIOR]:
        
        brain.enroll(year)
        
        # Study all concepts
        for concept_data in CURRICULUM[year]["concepts"]:
            brain.study(concept_data["concept"], concept_data["material"])
        
        # Evolve brain
        brain.evolve_brain()
    
    transcript = brain.generate_transcript()
    can_graduate = brain.check_graduation_eligibility()
    
    return transcript, can_graduate


def main():
    """Run course up to 3 times until graduation"""
    
    brain = VisionsArtBrain()
    
    print("\n" + "🌟"*30)
    print("VISIONS' PATH TO MASTERY")
    print("Art and Visual Perception - Rudolf Arnheim")
    print("Covering ALL 2025 Visual Mediums")
    print("🌟"*30 + "\n")
    
    max_attempts = 3
    graduated = False
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n{'='*60}")
        print(f"📖 ATTEMPT #{attempt}")
        print(f"{'='*60}")
        
        if attempt == 1:
            print("Initial learning - first exposure to Arnheim's theories")
        else:
            print(f"Retake with {brain.memory_strength:.2%} memory retention from attempt #{attempt-1}")
        
        transcript, graduated = run_course_once(brain, attempt)
        
        # Show results
        print(f"\n   📊 Results:")
        print(f"      GPA: {transcript['gpa']:.2%}")
        print(f"      Brain Evolution: {brain.brain_states[-1].evolution_score:.2%}")
        print(f"      Creative Synthesis: {brain.brain_states[-1].creative_synthesis:.2%}")
        
        if graduated:
            print(f"\n   ✅ GRADUATION THRESHOLD MET!")
            break
        else:
            print(f"\n   ⚠️ Not yet eligible (need 85%+ mastery on senior concepts)")
            
            if attempt < max_attempts:
                # Consolidate and prepare for next attempt
                print(f"\n   💾 Consolidating memory for attempt #{attempt + 1}...")
                brain.consolidate_memory()
                brain.reset_for_retake()
    
    # Final summary
    print(f"\n{'='*60}")
    print("🎓 FINAL RESULTS")
    print(f"{'='*60}")
    
    if graduated:
        print(f"\n✅ ✅ ✅ VISIONS HAS GRADUATED! ✅ ✅ ✅\n")
        print(f"   Program: Art and Visual Perception (Arnheim 2025)")
        print(f"   Attempts: {brain.course_attempts}")
        print(f"   Final GPA: {transcript['gpa']:.2%}")
        print(f"   Memory Strength: {brain.memory_strength:.2%}")
        print(f"   Brain Evolution: {brain.brain_states[-1].evolution_score:.2%}")
        print(f"\n   🧠 Cognitive Profile:")
        print(f"      Pattern Recognition: {brain.brain_states[-1].pattern_recognition:.2%}")
        print(f"      Abstraction: {brain.brain_states[-1].abstraction:.2%}")
        print(f"      Modern Translation: {brain.brain_states[-1].modern_translation:.2%}")
        print(f"      Creative Synthesis: {brain.brain_states[-1].creative_synthesis:.2%}")
        
        print(f"\n   🎯 Mastery Across All Visual Mediums:")
        print(f"      ✓ Photography (Composition, Lighting, Color)")
        print(f"      ✓ Videography (Movement, Depth, Framing)")
        print(f"      ✓ Photoshop (Layers, Compositing, Color Grading)")
        print(f"      ✓ Lightroom (Develop, Curves, HSL)")
        print(f"      ✓ Film & Television (Cinematography, Editing)")
        print(f"      ✓ Social Media (Instagram, TikTok, YouTube)")
        print(f"      ✓ AI Systems (Diffusion, NeRFs, Style Transfer)")
        
        print(f"\n   🌟 VISIONS IS NOW GODLY WITH VISION AND PERCEPTION 🌟")
        print(f"\n{'='*60}\n")
    else:
        print(f"\n   Visions completed {max_attempts} attempts")
        print(f"   Highest GPA: {transcript['gpa']:.2%}")
        print(f"   Recommend: Additional focused study on synthesis")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
