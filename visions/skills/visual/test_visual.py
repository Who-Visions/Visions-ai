import unittest
from unittest.mock import MagicMock, patch
from visions.skills.visual.service import VisionService, MODEL_NANO_BANANA_FAST, MODEL_VEO

class TestVisionService(unittest.TestCase):
    def setUp(self):
        with patch('visions.skills.visual.service.genai') as mock_genai:
            self.service = VisionService(project_id="test_project")
            self.mock_client = self.service.client

    def test_generate_image_fast(self):
        # Mock response setup
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data.data = b"fake_image_bytes"
        mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
        self.mock_client.models.generate_content.return_value = mock_response

        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            result = self.service.generate_image("A cat", mode="fast", output_path="cat.png")
            
            # Verify correct model called
            self.mock_client.models.generate_content.assert_called()
            args, kwargs = self.mock_client.models.generate_content.call_args
            self.assertEqual(kwargs['model'], MODEL_NANO_BANANA_FAST)
            
            self.assertEqual(result, "cat.png")

    def test_generate_video_polling(self):
        # Mock operation
        mock_operation = MagicMock()
        mock_operation.done = False # Start not done
        self.mock_client.models.generate_videos.return_value = mock_operation
        
        # Mock polling update
        mock_finished_op = MagicMock()
        mock_finished_op.done = True
        mock_finished_op.response.generated_videos = [MagicMock(video=MagicMock(video_bytes=b"video_data"))]
        
        # Setup polling client return (first call gets unfinished op (logic inside poll loop handles this by calling .get), 
        # actually my mock logic needs to handle the loop inside _poll_operation)
        self.mock_client.operations.get.return_value = mock_finished_op

        # Patch time.sleep to avoid waiting
        with patch('time.sleep', return_value=None):
            with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
                result = self.service.generate_video("A lion running")
                
                # Check model
                args, kwargs = self.mock_client.models.generate_videos.call_args
                self.assertEqual(kwargs['model'], MODEL_VEO)
                
                self.assertIn("veo_gen", result)

    def test_visual_question_answer_success(self):
        mock_response = MagicMock()
        mock_response.text = "This is a cat."
        self.mock_client.models.generate_content.return_value = mock_response

        with patch('builtins.open', unittest.mock.mock_open(read_data=b"image_data")):
            result = self.service.visual_question_answer("fake.jpg", "What is this?")
            self.assertEqual(result, "This is a cat.")

if __name__ == '__main__':
    unittest.main()
