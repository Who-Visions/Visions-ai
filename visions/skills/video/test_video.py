import unittest
from unittest.mock import MagicMock, patch
from visions.skills.video.service import VideoService

class TestVideoService(unittest.TestCase):
    def setUp(self):
        with patch('visions.skills.video.service.genai') as mock_genai:
            self.service = VideoService(api_key="test_key")
            self.mock_client = self.service.client

    def test_generate_video_polling(self):
        # Mock operation
        mock_op = MagicMock()
        mock_op.done = False
        
        # Mock client operations
        self.mock_client.models.generate_videos.return_value = mock_op
        
        # Define side effects for polling: first call not done, second call done
        done_op = MagicMock()
        done_op.done = True
        done_op.response.generated_videos = [MagicMock(video=MagicMock(save=MagicMock()))]
        
        self.mock_client.operations.get.side_effect = [done_op]

        # Mock time.sleep to avoid waiting
        with patch('time.sleep'):
            result = self.service.generate_video("A cat jumping", output_path="test.mp4")
            
            self.assertEqual(result, "test.mp4")
            self.mock_client.files.download.assert_called()

    def test_generate_video_failure(self):
        self.mock_client.models.generate_videos.side_effect = Exception("API Error")
        result = self.service.generate_video("A cat", output_path="fail.mp4")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
