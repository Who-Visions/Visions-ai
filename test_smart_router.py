
import unittest
from unittest.mock import MagicMock, patch
import json
from visions.core.agent import VisionsAgent, Config

class TestSmartRouter(unittest.TestCase):
    def setUp(self):
        # Mock GCP init to avoid real creds during unit test
        with patch('visions.core.agent.vertexai.init'), \
             patch('visions.core.agent.genai.Client'), \
             patch('visions.core.agent.CloudMemoryManager'):
            self.agent = VisionsAgent(project="test-project", location="global")
            
    def test_routing_tiers(self):
        """Verify 6-Level Reasoning Heuristic Ladder"""
        print("\n🧪 Testing Smart Router Tiers...")
        
        test_cases = [
            # (Complexity, HighRisk, Expected Tier Name)
            (1, False, "Tier 1: Flash / Minimal"),
            (1, True,  "Tier 6: Pro / High"), # Risk Override
            (3, False, "Tier 2: Flash / Low"),
            (5, False, "Tier 3: Flash / Medium"),
            (6, False, "Tier 4: Flash / High"),
            (7, False, "Tier 5: Pro / Low"),
            (9, False, "Tier 6: Pro / High"),
            (10, False, "Tier 6: Pro / High"),
        ]

        for complexity, high_risk, expected_tier in test_cases:
            # Mock the _triage_query response
            self.agent._triage_query = MagicMock(return_value={
                "complexity": complexity,
                "is_high_risk": high_risk,
                "needs_search": False
            })

            # Mock generation to avoid API call
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Mock Response"
            mock_client.models.generate_content.return_value = mock_response
            self.agent._get_client = MagicMock(return_value=mock_client)
            
            # We need to spy on the logging or internal state. 
            # Since I modified the code to log "➡️ Routing Decision: {tier}", 
            # we can verify logic by inspecting the args passed to _get_client 
            # and the ThinkingConfig.
            
            self.agent.query("test query")
            
            # Verify Model Selection
            model_called = self.agent._get_client.call_args[0][0]
            
            # Verify Thinking Level
            # access the call arguments to generate_content
            config_arg = mock_client.models.generate_content.call_args[1]['config']
            thinking_level = config_arg.thinking_config.thinking_level
            
            # Determine Expected Model/Thinking from Tier Name
            if "Pro" in expected_tier:
                expected_model = Config.MODEL_PRO
            else:
                expected_model = Config.MODEL_FLASH
                
            if "High" in expected_tier:
                expected_think = Config.THINKING_LEVEL_HIGH
            elif "Medium" in expected_tier:
                expected_think = Config.THINKING_LEVEL_MEDIUM
            elif "Low" in expected_tier:
                expected_think = Config.THINKING_LEVEL_LOW
            elif "Minimal" in expected_tier:
                expected_think = Config.THINKING_LEVEL_MINIMAL
                
            print(f"   👉 Case [C:{complexity}, Risk:{high_risk}] -> Got: {model_called} / {thinking_level}")
            
            self.assertEqual(model_called, expected_model, f"Model mismatch for {expected_tier}")
            self.assertEqual(thinking_level, expected_think, f"Thinking level mismatch for {expected_tier}")

        print("✅ All Routing Tiers Verified Successfully.")

if __name__ == '__main__':
    unittest.main()
