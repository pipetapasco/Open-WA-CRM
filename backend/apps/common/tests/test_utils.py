
from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from apps.common.utils import convert_media_for_whatsapp, get_media_duration
import os

class MediaConversionTests(TestCase):
    @override_settings(MEDIA_ROOT='/app/media', MEDIA_URL='/media/')
    @patch('apps.common.utils.os.path.exists')
    @patch('apps.common.utils.subprocess.run')
    def test_convert_media_url_path(self, mock_run, mock_exists):
        """
        Test that a path starting with MEDIA_URL is correctly resolved and returned as URL.
        """
        # Setup
        input_url = '/media/whatsapp/uploads/test.webm'
        expected_file_path = '/app/media/whatsapp/uploads/test.webm'
        output_file_path = '/app/media/whatsapp/uploads/test.ogg'
        expected_output_url = '/media/whatsapp/uploads/test.ogg'
        
        # Mock existence
        def exists_side_effect(path):
            if path == expected_file_path:
                return True
            if path == output_file_path:
                return True # Simulate output created
            return False
            
        mock_exists.side_effect = exists_side_effect
        
        # Run
        result = convert_media_for_whatsapp(input_url)
        
        # Verify
        self.assertEqual(result, expected_output_url)
        
        # Verify ffmpeg called with correct path
        args, _ = mock_run.call_args
        command = args[0]
        self.assertIn(expected_file_path, command)
        self.assertIn(output_file_path, command)

    @override_settings(MEDIA_ROOT='/app/media', MEDIA_URL='/media/')
    @patch('apps.common.utils.os.path.exists')
    @patch('apps.common.utils.subprocess.run')
    def test_convert_relative_path(self, mock_run, mock_exists):
        """
        Test that a relative path is correctly resolved and returned as relative.
        """
        # Setup
        input_path = 'whatsapp/uploads/test.webm'
        expected_file_path = '/app/media/whatsapp/uploads/test.webm'
        output_file_path = '/app/media/whatsapp/uploads/test.ogg'
        expected_output_path = 'whatsapp/uploads/test.ogg'
        
        # Mock existence
        def exists_side_effect(path):
            if path == expected_file_path:
                return True
            if path == output_file_path:
                return True
            return False
            
        mock_exists.side_effect = exists_side_effect
        
        # Run
        result = convert_media_for_whatsapp(input_path)
        
        # Verify
        self.assertEqual(result, expected_output_path)

    @override_settings(MEDIA_ROOT='/app/media', MEDIA_URL='/media/')
    @patch('apps.common.utils.os.path.exists')
    @patch('apps.common.utils.subprocess.run')
    def test_get_media_duration(self, mock_run, mock_exists):
        """
        Test that get_media_duration returns the correct duration from ffprobe output.
        """
        # Setup
        input_file = '/app/media/whatsapp/voice.ogg'
        mock_exists.return_value = True
        
        # Mock subprocess output
        mock_result = MagicMock()
        mock_result.stdout = "15.5\n"
        mock_run.return_value = mock_result
        
        # Run
        duration = get_media_duration(input_file)
        
        # Verify
        self.assertEqual(duration, 15.5)
        
        # Verify command
        args, _ = mock_run.call_args
        command = args[0]
        self.assertEqual(command[0], 'ffprobe')
        self.assertIn(input_file, command)
