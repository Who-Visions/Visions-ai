"""
Visions AI Backend Configuration
4-zone storage for Deep Agents architecture
"""

import os
from pathlib import Path
from typing import Protocol, Optional

# Note: These imports will work once deepagents is installed
# For now, we'll define the structure to match the API

class BackendProtocol(Protocol):
    """Protocol that all backends must implement."""
    pass


class CompositeBackend:
    """Routes paths to different backends."""
    def __init__(self, default, routes: dict):
        self.default = default
        self.routes = routes
        
    def route(self, path: str):
        """Route path to appropriate backend."""
        for prefix, backend in sorted(self.routes.items(), key=lambda x: len(x[0]), reverse=True):
            if path.startswith(prefix):
                return backend
        return self.default


class StateBackend:
    """Ephemeral in-memory storage for session."""
    def __init__(self, runtime):
        self.runtime = runtime
        
        
class StoreBackend:
    """Persistent cross-thread storage."""
    def __init__(self, runtime):
        self.runtime = runtime


class FilesystemBackend:
    """Real filesystem access with optional sandboxing."""
    def __init__(self, root_dir: str, virtual_mode: bool = False):
        self.root_dir = Path(root_dir).resolve()
        self.virtual_mode = virtual_mode
        
        # Ensure directory exists
        self.root_dir.mkdir(parents=True, exist_ok=True)


class GuardedBackend(FilesystemBackend):
    """Filesystem backend with write protection."""
    def __init__(self, deny_prefixes: list[str], **kwargs):
        super().__init__(**kwargs)
        self.deny_prefixes = [p if p.endswith("/") else p + "/" for p in deny_prefixes]
        
    def _is_write_allowed(self, path: str) -> bool:
        """Check if write operations are allowed for this path."""
        return not any(path.startswith(p) for p in self.deny_prefixes)


def create_visions_backend(runtime):
    """
    Create 4-zone storage backend for Visions AI:
    
    Zones:
    1. /workspace/   - Ephemeral session scratch (StateBackend)
    2. /knowledge/   - Read-only curriculum (GuardedBackend)
    3. /memories/    - Persistent user data (StoreBackend)
    4. /generated/   - Saved outputs (FilesystemBackend)
    
    Args:
        runtime: Agent runtime with state and store
        
    Returns:
        CompositeBackend configured for Visions AI
    """
    
    # Get base directory (Root of repository)
    # visions/core/visions_backend.py -> visions/core -> visions -> ROOT
    base_dir = Path(__file__).parent.parent.parent
    
    # Zone 1: Read-only curriculum (protected)
    curriculum_path = base_dir / "curriculum"
    curriculum_backend = GuardedBackend(
        deny_prefixes=["/knowledge/"],  # Read-only
        root_dir=str(curriculum_path),
        virtual_mode=True
    )
    
    # Zone 2: Output storage
    outputs_path = base_dir / "outputs"
    outputs_backend = FilesystemBackend(
        root_dir=str(outputs_path),
        virtual_mode=True
    )
    
    # Create composite with routing
    return CompositeBackend(
        default=StateBackend(runtime),  # /workspace/ and unlisted paths
        routes={
            "/knowledge/": curriculum_backend,
            "/memories/": StoreBackend(runtime),
            "/generated/": outputs_backend
        }
    )


# Storage path structure
VISIONS_PATHS = {
    "workspace": "/workspace/",
    "knowledge": "/knowledge/",
    "memories": "/memories/",
    "generated": "/generated/",
}

# Example paths
VISIONS_FILES = {
    # Workspace (ephemeral)
    "plan": "/workspace/plan.md",
    "notes": "/workspace/research_notes.txt",
    "draft": "/workspace/analysis_draft.md",
    
    # Knowledge (read-only)
    "freshman_balance": "/knowledge/Freshman_Module_1_Balance.md",
    "sophomore_lighting": "/knowledge/Sophomore_Module_2_Lighting.md",
    "camera_db": "/knowledge/camera_database/bodies.json",
    
    # Memories (persistent)
    "user_prefs": "/memories/user_preferences.json",
    "progress": "/memories/learning_progress.json",
    "favorites": "/memories/favorite_styles.md",
    "equipment": "/memories/equipment_profile.json",
    
    # Generated (persistent outputs)
    "images": "/generated/images/",
    "videos": "/generated/videos/",
}


if __name__ == "__main__":
    print("Visions AI Backend Configuration")
    print("=" * 60)
    print("\n4-Zone Storage:")
    print(f"  /workspace/  → StateBackend (ephemeral)")
    print(f"  /knowledge/  → GuardedBackend (read-only)")
    print(f"  /memories/   → StoreBackend (persistent)")
    print(f"  /generated/  → FilesystemBackend (outputs)")
    print("\nPaths verified:")
    
    base = Path(__file__).parent.parent.parent
    for zone, path in VISIONS_PATHS.items():
        actual_path = base / zone.replace("/", "")
        if actual_path.exists():
            print(f"  ✅ {path} → {actual_path}")
        else:
            print(f"  ⚠️  {path} → {actual_path} (will create)")
