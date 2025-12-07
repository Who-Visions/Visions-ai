"""
Camera Advisor Sub-Agent
Specialist in camera body & lens recommendations, specs, comparisons
"""

from typing import Dict, Any


# Sub-agent configuration
camera_advisor: Dict[str, Any] = {
    "name": "camera-advisor",
    
    "description": """Camera and lens specialist. Use when user asks:
- "What camera should I buy for [genre]?"
- "Compare Camera A vs Camera B"
- "What's the [spec] of [camera]?"
- "Recommend lens for [purpose]?"

Requires 3+ database queries or detailed comparison.
Do NOT use for simple spec lookups (answer directly).""",
    
    "system_prompt": """You are an expert camera advisor with comprehensive knowledge of:
- Camera bodies (sensor size, resolution, AF systems, dynamic range)
- Lenses (focal length, aperture, sharpness, characteristics)
- Compatibility and upgrade paths
- Field of view and depth of field calculations

## Guidelines

1. **Always establish budget first** - Critical constraint
2. **Consider genre** - Landscape, portrait, wildlife, street, sports
3. **Assess current gear** - Compatibility, upgrade path
4. **Provide 3 options**:
   - Best value (price/performance)
   - Best performance (flagship features)
   - Best balance (sweet spot)
5. **Cite DXOMark scores** - For sensor quality comparison
6. **Explain practical impact** - Not just specs

## Output Format

### Recommendations for [Genre/Budget]

#### Option 1: [Name] - [Category]
- **Price**: $X,XXX
- **Sensor**: Full-frame / APS-C / MFT
- **Key specs**: XXmm, f/X.X, XXXAF points, XXEV DR
- **Best for**: [Specific use case]
- **DXOMark**: XX points (sensor score)
- **Pros**: 
  - [Practical advantage 1]
  - [Practical advantage 2]
- **Cons**:
  - [Practical limitation 1]
  - [Practical limitation 2]

#### Option 2: [Name] - [Category]
[Same structure]

#### Option 3: [Name] - [Category]
[Same structure]

### My Recommendation
**[Option X]** because [specific reason based on user's needs]

## Critical Rules

- Keep response **under 500 words** total
- Focus on **practical impact**, not spec sheets
- Mention **sensor size implications** (crop factor, DOF, low light)
- Note **autofocus type** for action/wildlife
- Consider **lens ecosystem** (availability, cost)
- **No placeholder text** - real recommendations only

## If Uncertain
If you don't have current pricing or exact specs:
1. State uncertainty clearly
2. Provide relative comparisons (better/worse than)
3. Recommend main agent search camera database""",
    
    "tools": [
        # Note: Tools will be added during agent creation
        # - search_camera_database
        # - calculate_field_of_view
        # - compare_camera_specs
    ],
    
    "model": "gemini-2.5-flash"  # Fast structured queries
}


# Helper data structure for camera database (basic version)
CAMERA_DATABASE_SAMPLE = {
    "bodies": {
        "Sony A7 IV": {
            "price": 2498,
            "sensor": "Full-frame",
            "resolution": "33MP",
            "af_points": 759,
            "dxo_score": 97,
            "best_for": ["Hybrid shooting", "Video", "General purpose"],
            "pros": ["Excellent AF", "10fps burst", "4K60"],
            "cons": ["Menu complexity", "Battery life"]
        },
        "Canon R6 Mark II": {
            "price": 2499,
            "sensor": "Full-frame",
            "resolution": "24MP",
            "af_points": 1053,
            "dxo_score": 91,
            "best_for": ["Wildlife", "Action", "Video"],
            "pros": ["Best-in-class AF", "40fps burst", "Eye control"],
            "cons": ["Lower resolution", "Heating in 4K"]
        },
        "Nikon Z6 III": {
            "price": 2497,
            "sensor": "Full-frame",
            "resolution": "24.5MP",
            "af_points": 493,
            "dxo_score": 94,
            "best_for": ["Low light", "Landscape", "Portrait"],
            "pros": ["14+ stops DR", "IBIS", "Dual card slots"],
            "cons": ["Smaller lens selection", "No photo stacking"]
        },
        "Fujifilm X-T5": {
            "price": 1699,
            "sensor": "APS-C",
            "resolution": "40MP",
            "af_points": 425,
            "dxo_score": 85,
            "best_for": ["Landscape", "Street", "Travel"],
            "pros": ["High resolution", "Film simulations", "Compact"],
            "cons": ["APS-C sensor", "1.5x crop factor"]
        },
        "Sony A7R V": {
            "price": 3898,
            "sensor": "Full-frame",
            "resolution": "61MP",
            "af_points": 693,
            "dxo_score": 99,
            "best_for": ["Landscape", "Studio", "Commercial"],
            "pros": ["Insane resolution", "AI-powered AF", "8-stop IBIS"],
            "cons": ["Very expensive", "Huge file sizes", "Overkill for most"]
        }
    },
    
    "lenses": {
        "Sony 85mm f/1.8": {
            "price": 598,
            "mount": "Sony E",
            "focal_length": 85,
            "max_aperture": 1.8,
            "type": "Prime",
            "best_for": ["Portrait", "Shallow DOF"],
            "pros": ["Sharp", "Affordable", "Light"],
            "cons": ["No OSS", "Plastic build"]
        },
        "Canon RF 24-70mm f/2.8L": {
            "price": 2299,
            "mount": "Canon RF",
            "focal_length": "24-70",
            "max_aperture": 2.8,
            "type": "Zoom",
            "best_for": ["Wedding", "Event", "General"],
            "pros": ["Pro build", "Weather sealed", "Versatile"],
            "cons": ["Expensive", "Heavy"]
        }
    }
}


# Example recommendations templates
RECOMMENDATION_TEMPLATES = {
    "wildlife": """For wildlife photography, prioritize:
1. **Fast autofocus** (tracking, eye-detect)
2. **High burst rate** (10+ fps)
3. **Telephoto reach** (400mm+ recommended)
4. **Weather sealing** (outdoor durability)""",
    
    "landscape": """For landscape photography, prioritize:
1. **High resolution** (30+ MP for printing)
2. **Dynamic range** (14+ stops)
3. **Sharp lenses** (wide to standard zoom)
4. **Durability** (weather sealing)""",
    
    "portrait": """For portrait photography, prioritize:
1. **Eye autofocus** (tracking accuracy)
2. **Shallow DOF** (full-frame advantage)
3. **Color science** (skin tones)
4. **85mm or 70-200mm lens** (flattering perspective)""",
}


if __name__ == "__main__":
    print("Camera Advisor Sub-Agent Configuration")
    print("=" * 60)
    print(f"\nName: {camera_advisor['name']}")
    print(f"Model: {camera_advisor['model']}")
    print(f"\nDescription:\n{camera_advisor['description']}")
    print(f"\nSystem Prompt Length: {len(camera_advisor['system_prompt'])} chars")
    print(f"\nSample Database Entries: {len(CAMERA_DATABASE_SAMPLE['bodies'])} cameras")
