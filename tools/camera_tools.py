"""
Camera-related tools for Visions AI
Database search, spec comparison, FOV calculation
"""

import json
from typing import Optional, Dict, List
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def search_camera_database(
    query: str,
    category: str = "bodies",
    budget_max: Optional[int] = None,
    sensor_size: Optional[str] = None
) -> str:
    """
    Search camera/lens database.
    
    Args:
        query: Search term (camera name, brand, feature)
        category: "bodies" or "lenses"
        budget_max: Maximum price filter
        sensor_size: "full-frame", "aps-c", "mft"
    
    Returns:
        Formatted search results with key specs
    """
    # Load database
    db_path = Path(__file__).parent.parent / "knowledge" / "camera_database" / f"{category}.json"
    
    if not db_path.exists():
        # Use sample data from camera_advisor
        try:
            from subagents.camera_advisor import CAMERA_DATABASE_SAMPLE
            database = CAMERA_DATABASE_SAMPLE.get(category, {})
        except ImportError:
            # Fallback to hardcoded sample
            database = _get_sample_database(category)
    else:
        with open(db_path) as f:
            database = json.load(f)

    
    # Filter results
    results = []
    query_lower = query.lower()
    
    for name, specs in database.items():
        # Match query
        if query_lower not in name.lower():
            continue
            
        # Apply filters
        if budget_max and specs.get("price", 0) >budget_max:
            continue
            
        if sensor_size and specs.get("sensor", "").lower() != sensor_size.lower():
            continue
            
        results.append((name, specs))
    
    # Format output
    if not results:
        return f"No {category} found matching '{query}' with given filters."
    
    output = [f"Found {len(results)} matching {category}:\n"]
    
    for i, (name, specs) in enumerate(results[:5], 1):  # Limit to top 5
        if category == "bodies":
            output.append(f"{i}. **{name}**")
            output.append(f"   - Price: ${specs.get('price', 'N/A'):,}")
            output.append(f"   - Sensor: {specs.get('sensor', 'N/A')}, {specs.get('resolution', 'N/A')}")
            output.append(f"   - AF: {specs.get('af_points', 'N/A')} points")
            output.append(f"   - DXOMark: {specs.get('dxo_score', 'N/A')} points")
            output.append(f"   - Best for: {', '.join(specs.get('best_for', []))}")
        else:  # lenses
            output.append(f"{i}. **{name}**")
            output.append(f"   - Price: ${specs.get('price', 'N/A'):,}")
            output.append(f"   - Mount: {specs.get('mount', 'N/A')}")
            output.append(f"   - Focal: {specs.get('focal_length', 'N/A')}mm, f/{specs.get('max_aperture', 'N/A')}")
            output.append(f"   - Type: {specs.get('type', 'N/A')}")
        output.append("")
    
    return "\n".join(output)


def calculate_field_of_view(
    focal_length: int,
    sensor_size: str = "full-frame",
    subject_distance: float = 10.0
) -> str:
    """
    Calculate field of view for lens/sensor combination.
    
    Args:
        focal_length: Lens focal length in mm
        sensor_size: "full-frame", "aps-c", "mft"
        subject_distance: Distance to subject in meters
    
    Returns:
        FOV dimensions and equivalent focal length info
    """
    # Sensor dimensions (mm)
    sensors = {
        "full-frame": (36, 24),
        "aps-c": (23.6, 15.6),  # Canon
        "aps-c-sony": (23.5, 15.6),
        "mft": (17.3, 13.0)
    }
    
    if sensor_size not in sensors:
        return f"Unknown sensor size: {sensor_size}"
    
    sensor_width, sensor_height = sensors[sensor_size]
    
    # Calculate crop factor
    ff_diagonal = (36**2 + 24**2) ** 0.5
    sensor_diagonal = (sensor_width**2 + sensor_height**2) ** 0.5
    crop_factor = ff_diagonal / sensor_diagonal
    
    # Calculate FOV
    fov_h = 2 * subject_distance * (sensor_width / 2) / focal_length
    fov_v = 2 * subject_distance * (sensor_height / 2) / focal_length
    
    # Diagonal FOV angle
    import math
    fov_angle = 2 * math.atan(sensor_diagonal / (2 * focal_length)) * (180 / math.pi)
    
    # Equivalent focal length on full-frame
    equivalent_ff = focal_length * crop_factor
    
    output = [
        f"**Field of View Calculation**",
        f"",
        f"Lens: {focal_length}mm",
        f"Sensor: {sensor_size.title()}",
        f"Distance: {subject_distance}m",
        f"",
        f"**Results:**",
        f"- Horizontal FOV: {fov_h:.2f} meters",
        f"- Vertical FOV: {fov_v:.2f} meters",
        f"- Diagonal FOV: {fov_angle:.1f}°",
        f"- Crop Factor: {crop_factor:.2f}x",
        f"- Full-frame Equivalent: {equivalent_ff:.0f}mm",
        f"",
        f"**Practical Context:**"
    ]
    
    # Add practical context
    if equivalent_ff < 24:
        output.append("- Ultra-wide angle (architectural, landscapes)")
    elif equivalent_ff < 35:
        output.append("- Wide angle (environmental portraits, street)")
    elif equivalent_ff < 70:
        output.append("- Standard (natural perspective, general use)")
    elif equivalent_ff < 135:
        output.append("- Portrait (flattering compression, headshots)")
    else:
        output.append("- Telephoto (compression, isolation, wildlife)")
    
    return "\n".join(output)


def _get_sample_database(category):
    """Fallback sample database if imports fail."""
    if category == "bodies":
        return {
            "Sony A7 IV": {
                "price": 2498,
                "sensor": "Full-frame",
                "resolution": "33MP",
                "af_points": 759,
                "dxo_score": 97,
                "best_for": ["Hybrid", "Video"],
                "pros": ["Excellent AF", "10fps"],
                "cons": ["Menu complexity"]
            },
            "Canon R6 Mark II": {
                "price": 2499,
                "sensor": "Full-frame",
                "resolution": "24MP",
                "af_points": 1053,
                "dxo_score": 91,
                "best_for": ["Wildlife", "Action"],
                "pros": ["Best AF", "40fps"],
                "cons": ["Lower resolution"]
            }
        }
    return {}


def compare_camera_specs(
    camera1: str,
    camera2: str,
    camera3: Optional[str] = None
) -> str:
    """
    Side-by-side comparison of camera specs.
    
    Args:
        camera1: First camera name
        camera2: Second camera name
        camera3: Optional third camera
    
    Returns:
        Formatted comparison table
    """
    try:
        from subagents.camera_advisor import CAMERA_DATABASE_SAMPLE
        database = CAMERA_DATABASE_SAMPLE["bodies"]
    except ImportError:
        database = _get_sample_database("bodies")
    
    cameras = [c for c in [camera1, camera2, camera3] if c]
    
    # Find cameras
    specs_list = []
    for name in cameras:
        found = None
        for db_name, specs in database.items():
            if name.lower() in db_name.lower():
                found = (db_name, specs)
                break
        if found:
            specs_list.append(found)
        else:
            return f"Camera not found: {name}"
    
    if not specs_list:
        return "No cameras found for comparison."
    
    # Format comparison
    output = ["**Camera Comparison**\n"]
    
    # Header
    names = [name for name, _ in specs_list]
    output.append(f"| Spec | {' | '.join(names)} |")
    output.append(f"|------|{'----|' * len(names)}")
    
    # Rows
    specs_to_compare = [
        ("Price", "price", lambda x: f"${x:,}"),
        ("Sensor", "sensor", str),
        ("Resolution", "resolution", str),
        ("AF Points", "af_points", str),
        ("DXOMark", "dxo_score", lambda x: f"{x} pts"),
    ]
    
    for label, key, formatter in specs_to_compare:
        values = [formatter(specs.get(key, "N/A")) for _, specs in specs_list]
        output.append(f"| **{label}** | {' | '.join(values)} |")
    
    output.append("")
    output.append("**Best For:**")
    for name, specs in specs_list:
        best_for = ", ".join(specs.get("best_for", []))
        output.append(f"- {name}: {best_for}")
    
    return "\n".join(output)


# Tool definitions for LangChain integration
if __name__ == "__main__":
    print("Camera Tools Demo")
    print("=" * 60)
    
    print("\n1. Search for wildlife cameras under $3000:")
    print(search_camera_database(
        query="",
        category="bodies",
        budget_max=3000
    ))
    
    print("\n2. Calculate FOV for 85mm on full-frame:")
    print(calculate_field_of_view(85, "full-frame", 3.0))
    
    print("\n3. Compare Sony A7 IV vs Canon R6:")
    print(compare_camera_specs("Sony A7 IV", "Canon R6"))
