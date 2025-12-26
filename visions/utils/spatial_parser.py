import json
import re
from typing import List, Dict, Union, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class BoundingBox2D:
    label: str
    ymin: int
    xmin: int
    ymax: int
    xmax: int
    confidence: Optional[float] = None

    def to_absolute(self, width: int, height: int) -> Dict[str, Any]:
        """Converts normalized (0-1000) coordinates to absolute pixel values."""
        return {
            "label": self.label,
            "x": int((self.xmin / 1000.0) * width),
            "y": int((self.ymin / 1000.0) * height),
            "width": int(((self.xmax - self.xmin) / 1000.0) * width),
            "height": int(((self.ymax - self.ymin) / 1000.0) * height)
        }

@dataclass
class BoundingBox3D:
    label: str
    center_x: float
    center_y: float
    center_z: float
    size_x: float
    size_y: float
    size_z: float
    roll: float
    pitch: float
    yaw: float

def parse_code_fencing(text: str) -> str:
    """Removes markdown code fencing from JSON strings."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def parse_2d_boxes(text: str) -> List[BoundingBox2D]:
    """
    Parses Geminis standard 2D bounding box JSON output.
    Expected format: [{"box_2d": [ymin, xmin, ymax, xmax], "label": "str"}]
    """
    clean_json = parse_code_fencing(text)
    try:
        data = json.loads(clean_json)
        boxes = []
        for item in data:
            if "box_2d" in item:
                # Gemini returns [ymin, xmin, ymax, xmax]
                box = item["box_2d"]
                if len(box) == 4:
                    boxes.append(BoundingBox2D(
                        label=item.get("label", "detected_object"),
                        ymin=box[0],
                        xmin=box[1],
                        ymax=box[2],
                        xmax=box[3]
                    ))
        return boxes
    except json.JSONDecodeError:
        print(f"Failed to parse 2D spatial JSON: {text[:100]}...")
        return []

def parse_3d_boxes(text: str) -> List[BoundingBox3D]:
    """
    Parses Gemini's 3D bounding box JSON output.
    Expected format: [{"box_3d": [cx, cy, cz, sx, sy, sz, r, p, y], "label": "str"}]
    """
    clean_json = parse_code_fencing(text)
    try:
        data = json.loads(clean_json)
        boxes = []
        for item in data:
            if "box_3d" in item:
                b = item["box_3d"]
                if len(b) == 9:
                    boxes.append(BoundingBox3D(
                        label=item.get("label", "3d_object"),
                        center_x=b[0], center_y=b[1], center_z=b[2],
                        size_x=b[3], size_y=b[4], size_z=b[5],
                        roll=b[6], pitch=b[7], yaw=b[8]
                    ))
        return boxes
    except json.JSONDecodeError:
         print(f"Failed to parse 3D spatial JSON: {text[:100]}...")
         return []
