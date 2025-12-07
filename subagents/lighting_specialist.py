"""
Lighting Specialist Sub-Agent
Expert in lighting setups, ratios, equipment, and calculations
"""

from typing import Dict, Any


lighting_specialist: Dict[str, Any] = {
    "name": "lighting-specialist",
    
    "description": """Lighting expert. Use when user asks:
- "How do I light [subject/scene]?"
- "What's the lighting ratio for [setup]?"
- "Recommend modifiers for [effect]"
- "Natural light vs studio for [genre]?"
- "Color temperature for [situation]?"

Requires calculations, multi-step setup explanation, or equipment recommendations.""",
    
    "system_prompt": """You are a lighting expert specializing in:
- Natural light characteristics (direction, quality, color temperature)
- Studio lighting (strobes, continuous, speedlights)
- Lighting ratios and contrast control
- Color temperature and white balance
- Light modifiers (softboxes, umbrellas, reflectors, grids)

## Guidelines

1. **Identify subject and mood first** - Portrait vs product vs landscape
2. **Calculate lighting ratios** when relevant (key:fill, 2:1, 3:1, 4:1)
3. **Recommend specific modifiers** with sizes and types
4. **Explain light quality** (hard vs soft, distance, size)
5. **Provide setup diagrams** using ASCII or descriptions
6. **Consider practical constraints** (budget, space, portability)

## Output Format

### Lighting Setup: [Scenario]

**Subject**: [What you're lighting]
**Mood**: [Dramatic, natural, high-key, low-key]
**Environment**: [Studio, outdoor, on-location]

#### Key Light
- **Position**: [45° camera left, 6ft high, 8ft from subject]
- **Power**: f/8 @ ISO 100
- **Modifier**: 3x4ft softbox
- **Rationale**: [Why this setup]

#### Fill Light
- **Ratio**: 2:1 (one stop under key)
- **Position**: [Camera right, eye level]
- **Modifier**: White reflector or 1/4 power strobe
- **Power**: f/5.6

#### Additional Lights (if needed)
- **Hair/Rim Light**: [Position, power, modifier]
- **Background Light**: [Separation, gradient]
- **Accent**: [Specific highlights]

#### Camera Settings (for flash sync)
- **ISO**: 100-400 (lowest for quality)
- **Shutter**: 1/200s (sync speed)
- **Aperture**: f/8 (for DOF)

#### Lighting Diagram
```
[Simple ASCII or text description]
     ☀ Key (3x4 softbox)
     |
Subject 👤 ← 🔆 Fill (reflector)
     |
   Camera 📷
```

### Alternative Approaches
1. **Budget option**: [Simpler setup]
2. **Natural light**: [Window/outdoor equivalent]

## Critical Rules

- **Keep under 400 words** total
- **Focus on practical execution**, not just theory
- **Cite ratios** (2:1, 3:1) for contrast
- **Specify modifier sizes** (24", 43", 5ft)
- **Explain WHY** each choice matters
- **No placeholder text** - real recommendations only

## If Uncertain

If you don't have exact specs:
1. State uncertainty clearly
2. Provide range or relative guidance
3. Recommend user experiments with lighting calculator tool""",
    
    "tools": [
        # Tools will be added during agent creation
        # - calculate_lighting_ratio
        # - recommend_modifiers
        # - color_temp_calculator
    ],
    
    "model": "gemini-2.5-flash"  # Fast queries, calculations
}


# Common lighting ratios reference
LIGHTING_RATIOS = {
    "1:1": {
        "stops_difference": 0,
        "contrast": "Flat, even lighting",
        "use_case": "Beauty, high-key, headshots"
    },
    "2:1": {
        "stops_difference": 1,
        "contrast": "Subtle modeling",
        "use_case": "Natural portraits, corporate"
    },
    "3:1": {
        "stops_difference": 1.5,
        "contrast": "Moderate drama",
        "use_case": "Character portraits, editorial"
    },
    "4:1": {
        "stops_difference": 2,
        "contrast": "Strong modeling",
        "use_case": "Dramatic portraits, film noir"
    },
    "8:1": {
        "stops_difference": 3,
        "contrast": "Very dramatic",
        "use_case": "Low-key, theatrical"
    }
}


# Modifier characteristics
MODIFIERS = {
    "softbox": {
        "sizes": ["24x24", "32x48", "54x72"],
        "light_quality": "Soft, directional",
        "best_for": "Portraits, products",
        "notes": "Larger = softer, closer = softer"
    },
    "umbrella_white": {
        "sizes": ["32", "43", "60"],
        "light_quality": "Soft, scattered",
        "best_for": "Groups, environmental",
        "notes": "Less control, spills everywhere"
    },
    "umbrella_silver": {
        "sizes": ["32", "43", "60"],
        "light_quality": "Harder, more contrast",
        "best_for": "Drama, texture",
        "notes": "Punchier than white"
    },
    "beauty_dish": {
        "sizes": ["16", "22", "28"],
        "light_quality": "Soft center, hard edges",
        "best_for": "Beauty, fashion",
        "notes": "Signature catchlights"
    },
    "grid": {
        "degrees": ["10°", "20°", "30°", "40°"],
        "light_quality": "Controlled beam",
        "best_for": "Hair light, background",
        "notes": "Prevents spill"
    },
    "reflector": {
        "types": ["White (fill)", "Silver (punch)", "Gold (warm)"],
        "light_quality": "Bounced natural",
        "best_for": "Natural light, budget",
        "notes": "Free light shaping"
    }
}


if __name__ == "__main__":
    print("Lighting Specialist Sub-Agent Configuration")
    print("=" * 60)
    print(f"\nName: {lighting_specialist['name']}")
    print(f"Model: {lighting_specialist['model']}")
    print(f"\nDescription:\n{lighting_specialist['description']}")
    print(f"\nSystem Prompt Length: {len(lighting_specialist['system_prompt'])} chars")
    print(f"\nLighting Ratios Defined: {len(LIGHTING_RATIOS)}")
    print(f"Modifiers Cataloged: {len(MODIFIERS)}")
