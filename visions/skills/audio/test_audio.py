import unittest
from unittest.mock import MagicMock, patch
from visions.skills.audio.service import AudioService

class TestAudioService(unittest.TestCase):
    def setUp(self):
        # Mock genai to prevent actual API calls during testing
        with patch('visions.skills.audio.service.genai') as mock_genai:
            self.service = AudioService(api_key="test_key")
            self.mock_client = self.service.client

    def test_generate_speech_success(self):
        # Mock response
        mock_response = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data.data = b"fake_audio_data"
        mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
        self.mock_client.models.generate_content.return_value = mock_response

        # Mock wave file writing
        with patch('wave.open') as mock_wave:
            result = self.service.generate_speech("Hello world", output_path="test.wav")
            
            self.assertEqual(result, "test.wav")
            mock_wave.assert_called_once()

    def test_generate_speech_failure(self):
        # Mock exception
        self.mock_client.models.generate_content.side_effect = Exception("API Error")
        
        result = self.service.generate_speech("Hello world")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
