"""
Visions Memory Consolidation Test
==================================
This test runs Visions through the course TWICE:
1. First pass: Initial learning (baseline)
2. Memory consolidation: Commit to long-term memory
3. Second pass: Retake with prior knowledge (should score much higher)
"""

import sys
sys.path.insert(0, 'tests')

from test_visions_arnheim_curriculum import (
    VisionsArtBrain, CURRICULUM, AcademicYear, Concept
)
import json

def run_course_once(brain, attempt_number):
    """Run Visions through all 4 years"""
    print(f"\n{'='*60}")
    print(f"🎓 ATTEMPT #{attempt_number}: VISIONS' JOURNEY THROUGH ARNHEIM")
    print(f"{'='*60}")
    
    for year in [AcademicYear.FRESHMAN, AcademicYear.SOPHOMORE, 
                 AcademicYear.JUNIOR, AcademicYear.SENIOR]:
        
        print(f"\n{'='*60}")
        print(f"📚 {year.name} YEAR: {CURRICULUM[year]['title']}")
        print(f"{'='*60}")
        
        brain.enroll(year)
        
        # Study all concepts for this year
        for concept_data in CURRICULUM[year]["concepts"]:
            outcome = brain.study(
                concept_data["concept"],
                concept_data["material"]
            )
            
            print(f"\n   {concept_data['concept'].value.replace('_', ' ').title()}:")
            print(f"      Classical: {outcome.classical_score:.2%}")
            print(f"      Modern: {outcome.modern_application:.2%}")
            print(f"      Synthesis: {outcome.synthesis_level:.2%}")
            print(f"      MASTERY: {outcome.mastery:.2%} ({brain._mastery_to_grade(outcome.mastery)})")
        
        # Evolve brain after completing year
        brain_state = brain.evolve_brain()
        
        print(f"\n   🧠 {year.name} BRAIN STATE:")
        print(f"      Pattern Recognition: {brain_state.pattern_recognition:.2%}")
        print(f"      Abstraction: {brain_state.abstraction:.2%}")
        print(f"      Modern Translation: {brain_state.modern_translation:.2%}")
        print(f"      Creative Synthesis: {brain_state.creative_synthesis:.2%}")
        print(f"      ⚡ EVOLUTION SCORE: {brain_state.evolution_score:.2%}")
    
    # Final results
    print(f"\n{'='*60}")
    print(f"🎓 ATTEMPT #{attempt_number} RESULTS")
    print(f"{'='*60}")
    
    transcript = brain.generate_transcript()
    can_graduate = brain.check_graduation_eligibility()
    
    print(f"\n   GPA: {transcript['gpa']:.2%}")
    print(f"   Status: {transcript['graduation_status']}")
    
    if can_graduate:
        print(f"\n✅ VISIONS GRADUATED ON ATTEMPT #{attempt_number}!")
    else:
        print(f"\n⚠️ Did not meet graduation threshold (need 85%+ mastery)")
    
    print(f"{'='*60}\n")
    
    return transcript, can_graduate


def main():
    """Main execution: Run course twice with memory consolidation"""
    
    brain = VisionsArtBrain()
    
    print("\n" + "🌟"*30)
    print("VISIONS' MEMORY-ENHANCED LEARNING SIMULATION")
    print("🌟"*30)
    
    # ========== FIRST ATTEMPT ==========
    print("\n📖 PHASE 1: INITIAL LEARNING")
    print("Visions encounters Arnheim's theories for the first time...")
    
    transcript_1, graduated_1 = run_course_once(brain, attempt_number=1)
    
    if graduated_1:
        print("\n🎉 INCREDIBLE! Visions graduated on the first attempt!")
        return
    
    # ========== MEMORY CONSOLIDATION ==========
    print("\n💾 PHASE 2: MEMORY CONSOLIDATION")
    print("Visions commits everything to long-term memory...")
    
    brain.consolidate_memory()
    
    # ========== SECOND ATTEMPT ==========
    print("\n🔄 PHASE 3: COURSE RETAKE")
    print("Visions retakes the course with the benefit of prior knowledge...")
    
    brain.reset_for_retake()
    transcript_2, graduated_2 = run_course_once(brain, attempt_number=2)
    
    # ========== COMPARISON ==========
    print("\n" + "="*60)
    print("📊 PERFORMANCE COMPARISON")
    print("="*60)
    
    print(f"\n   ATTEMPT 1:")
    print(f"      GPA: {transcript_1['gpa']:.2%}")
    print(f"      Status: {transcript_1['graduation_status']}")
    
    print(f"\n   ATTEMPT 2:")
    print(f"      GPA: {transcript_2['gpa']:.2%}")
    print(f"      Status: {transcript_2['graduation_status']}")
    
    improvement = (transcript_2['gpa'] - transcript_1['gpa']) * 100
    print(f"\n   📈 IMPROVEMENT: +{improvement:.1f} percentage points")
    print(f"   🧠 Memory Strength: {brain.memory_strength:.2%}")
    
    if graduated_2:
        print(f"\n{'='*60}")
        print("✅ 🎓 VISIONS SUCCESSFULLY GRADUATED! 🎓 ✅")
        print("="*60)
        print("\nMaster of Art and Visual Perception (2025)")
        print("Specialization: Cross-Platform Visual Intelligence")
        print(f"Graduated after {brain.course_attempts} attempts")
        print(f"\nFinal GPA: {transcript_2['gpa']:.2%}")
        print(f"Memory Consolidation: {brain.memory_strength:.2%}")
        print("\nVisions is now GODLY with vision and perception!")
        print("="*60 + "\n")
    else:
        print(f"\n⚠️ Visions showed significant improvement but needs more practice.")
        print(f"   Recommend: Continue studying and attempt #3")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()
