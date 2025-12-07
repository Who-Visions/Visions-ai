"""
Integration tests for Visions AI Agent Harness
Tests backend configuration, sub-agent delegation, and workflows
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from visions_backend import create_visions_backend, VISIONS_PATHS, GuardedBackend
from subagents.camera_advisor import camera_advisor, CAMERA_DATABASE_SAMPLE
from tools import search_camera_database, calculate_field_of_view, compare_camera_specs


class TestBackendConfiguration:
    """Test 4-zone storage configuration."""
    
    def test_storage_zones_defined(self):
        """All 4 storage zones should be defined."""
        # Check that paths are defined (keys have no slashes)
        paths_str = str(VISIONS_PATHS.values())
        assert "/workspace/" in paths_str
        assert "/knowledge/" in paths_str
        assert "/memories/" in paths_str
        assert "/generated/" in paths_str
    
    def test_guarded_backend_blocks_writes(self):
        """GuardedBackend should block writes to denied prefixes."""
        backend = GuardedBackend(
            deny_prefixes=["/knowledge/"],
            root_dir=str(Path(__file__).parent),
            virtual_mode=True
        )
        
        # Knowledge path should be blocked
        assert not backend._is_write_allowed("/knowledge/test.md")
        
        # Other paths should be allowed
        assert backend._is_write_allowed("/workspace/test.md")
        assert backend._is_write_allowed("/memories/prefs.json")


class TestCameraAdvisor:
    """Test Camera Advisor sub-agent configuration."""
    
    def test_advisor_properly_configured(self):
        """Camera advisor should have required fields."""
        assert "name" in camera_advisor
        assert "description" in camera_advisor
        assert "system_prompt" in camera_advisor
        assert "model" in camera_advisor
        
        assert camera_advisor["name"] == "camera-advisor"
        assert camera_advisor["model"] == "gemini-2.5-flash"
    
    def test_description_includes_use_cases(self):
        """Description should include when to use."""
        desc = camera_advisor["description"]
        assert "camera should I buy" in desc
        assert "Compare" in desc
        assert "Recommend" in desc
    
    def test_system_prompt_comprehensive(self):
        """System prompt should be detailed but concise."""
        prompt = camera_advisor["system_prompt"]
        
        # Should mention key concepts
        assert "budget" in prompt.lower()
        assert "genre" in prompt.lower()
        assert "dxomark" in prompt.lower()
        assert "option" in prompt.lower()
        
        # Should be reasonably sized (not too long)
        assert len(prompt) < 5000, "System prompt too long"
        assert len(prompt) > 500, "System prompt too short"
    
    def test_sample_database_has_cameras(self):
        """Sample database should have multiple cameras."""
        assert len(CAMERA_DATABASE_SAMPLE["bodies"]) >= 3
        assert "Sony A7 IV" in CAMERA_DATABASE_SAMPLE["bodies"]
        assert "Canon R6 Mark II" in CAMERA_DATABASE_SAMPLE["bodies"]


class TestCameraTools:
    """Test camera-related tools."""
    
    def test_search_camera_database(self):
        """Database search should return formatted results."""
        result = search_camera_database(
            query="Sony",
            category="bodies",
            budget_max=3000
        )
        
        assert "Sony" in result
        assert "Price:" in result
        assert "Sensor:" in result
        assert isinstance(result, str)
    
    def test_search_with_filters(self):
        """Filters should narrow results."""
        # Search without filter
        result_all = search_camera_database("", category="bodies")
        
        # Search with budget filter
        result_budget = search_camera_database(
            "",
            category="bodies",
            budget_max=2000
        )
        
        # Budget filter should reduce results
        assert len(result_budget) <= len(result_all)
    
    def test_calculate_fov(self):
        """FOV calculation should return correct format."""
        result = calculate_field_of_view(
            focal_length=85,
            sensor_size="full-frame",
            subject_distance=3.0
        )
        
        assert "Horizontal FOV" in result
        assert "Vertical FOV" in result
        assert "Diagonal FOV" in result
        assert "Crop Factor" in result
        assert isinstance(result, str)
    
    def test_fov_crop_factor(self):
        """Different sensors should have different crop factors."""
        ff_result = calculate_field_of_view(50, "full-frame")
        apsc_result = calculate_field_of_view(50, "aps-c")
        
        # APS-C should mention higher crop factor
        assert "1.00x" in ff_result  # Full-frame = 1.0x
        assert ("1.5" in apsc_result or "1.6" in apsc_result)  # APS-C ≈ 1.5x
    
    def test_compare_cameras(self):
        """Camera comparison should create table."""
        result = compare_camera_specs(
            "Sony A7 IV",
            "Canon R6 Mark II"
        )
        
        assert "Camera Comparison" in result
        assert "Sony" in result
        assert "Canon" in result
        assert "|" in result  # Markdown table
        assert "Price" in result
        assert "Sensor" in result


class TestAgentWorkflows:
    """Test complete workflows (when agent is ready)."""
    
    @pytest.mark.skip(reason="Requires deepagents installation")
    def test_camera_recommendation_workflow(self):
        """End-to-end camera recommendation."""
        # This will be implemented once create_deep_agent() is integrated
        pass
    
    @pytest.mark.skip(reason="Requires deepagents installation")
    def test_memory_persistence(self):
        """User preferences should persist across sessions."""
        # This will test /memories/ storage
        pass
    
    @pytest.mark.skip(reason="Requires deepagents installation")
    def test_subagent_delegation(self):
        """Camera advisor should be called for recommendations."""
        # This will check delegation logic
        pass


class TestSystemPromptQuality:
    """Test system prompt best practices."""
    
    def test_advisor_output_length_constraint(self):
        """System prompt should specify output length limit."""
        prompt = camera_advisor["system_prompt"]
        assert "500 words" in prompt or "word" in prompt.lower()
    
    def test_advisor_instructs_structure(self):
        """System prompt should specify output structure."""
        prompt = camera_advisor["system_prompt"]
        assert "Option" in prompt
        assert "Recommendation" in prompt
        assert "format" in prompt.lower() or "Format" in prompt
    
    def test_no_placeholders_instruction(self):
        """Should explicitly ban placeholder text."""
        prompt = camera_advisor["system_prompt"]
        assert "placeholder" in prompt.lower() or "real" in prompt.lower()


if __name__ == "__main__":
    print("Running Visions AI Agent Harness Tests")
    print("=" * 60)
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
