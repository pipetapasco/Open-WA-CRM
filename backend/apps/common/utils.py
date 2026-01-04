
import os
import subprocess
import logging
import mimetypes
from django.conf import settings

logger = logging.getLogger(__name__)

def convert_media_for_whatsapp(media_path: str) -> str:
    """
    Checks if the media file needs conversion for WhatsApp compatibility.
    Specifically converts video/webm (often created by browser audio recorders) 
    to audio/ogg (Opus), which is widely supported by WhatsApp for voice notes.
    
    Args:
        media_path: Relative path (from MEDIA_ROOT) or absolute path to the file.
        
    Returns:
        str: Path to the converted file (relative if input was relative) or original path if no conversion needed.
    """
    full_path = media_path
    
    # Check if it starts with MEDIA_URL (e.g. /media/whatsapp/...)
    if media_path.startswith(settings.MEDIA_URL):
        # Strip MEDIA_URL to get relative path
        relative_path = media_path[len(settings.MEDIA_URL):]
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    # Resolve absolute path if it is relative
    elif not os.path.isabs(media_path):
        full_path = os.path.join(settings.MEDIA_ROOT, media_path)
        
    if not os.path.exists(full_path):
        logger.warning(f"Media file not found for conversion: {full_path} (Original: {media_path}, Root: {settings.MEDIA_ROOT})")
        return media_path
        
    # Check mime type
    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type:
        # Fallback detection using file extension if mimetypes fails
        if full_path.endswith('.webm'):
            mime_type = 'video/webm'
    
    # Meta WhatsApp API often rejects video/webm for audio messages.
    # Browser MediaRecorder produces 'video/webm' (or audio/webm) for audio recording.
    # blocked_types = ['video/webm', 'audio/webm']
    
    # We simply check if it is webm.
    if mime_type in ['video/webm', 'audio/webm']:
        logger.info(f"Converting WebM media to OGG for WhatsApp: {full_path}")
        
        # Prepare output filename
        # Replace extension with .ogg
        directory = os.path.dirname(full_path)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        output_filename = f"{filename}.ogg"
        output_path = os.path.join(directory, output_filename)
        
        try:
            # Run ffmpeg conversion
            # -i input
            # -c:a libopus (Opus codec is standard for WhatsApp OGG audio)
            # -b:a 16k to 64k (WhatsApp voice notes usually low bitrate, 32k is good)
            # -vn (No video)
            # -y (Overwrite output)
            
            command = [
                'ffmpeg',
                '-i', full_path,
                '-c:a', 'libopus', 
                '-b:a', '32k',
                '-vn',
                '-y',
                output_path
            ]
            
            subprocess.run(
                command, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Check if output exists
            if os.path.exists(output_path):
                logger.info(f"Conversion successful: {output_path}")
                
                # Return path in same format as input
                if media_path.startswith(settings.MEDIA_URL):
                    # Reconstruct URL: /media/ + whatsapp/uploads/file.ogg
                    # relative_path was defined earlier as media_path without MEDIA_URL prefix
                    # We need to compute the new relative path
                    rel_dir = os.path.dirname(relative_path)
                    new_rel_path = os.path.join(rel_dir, output_filename)
                    return os.path.join(settings.MEDIA_URL, new_rel_path)
                elif not os.path.isabs(media_path):
                    # Reconstruct relative path
                    rel_dir = os.path.dirname(media_path)
                    return os.path.join(rel_dir, output_filename)
                else:
                    return output_path
            else:
                logger.error("ffmpeg finished but output file missing.")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during media conversion: {e}")
            
    return media_path


def get_media_duration(media_path: str) -> float:
    """
    Get the duration of a media file in seconds using ffprobe.
    
    Args:
        media_path: Relative path (from MEDIA_ROOT) or absolute path to the file.
        
    Returns:
        float: Duration in seconds, or 0.0 if extraction fails.
    """
    try:
        full_path = media_path
        
        # Check if it starts with MEDIA_URL
        if media_path.startswith(settings.MEDIA_URL):
            relative_path = media_path[len(settings.MEDIA_URL):]
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        elif not os.path.isabs(media_path):
            full_path = os.path.join(settings.MEDIA_ROOT, media_path)
            
        if not os.path.exists(full_path):
            logger.warning(f"Media file not found for duration extraction: {full_path}")
            return 0.0
            
        # Command to get duration in seconds
        # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.file
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            full_path
        ]
        
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        duration = float(result.stdout.strip())
        return duration
        
    except Exception as e:
        logger.error(f"Error extracting duration for {media_path}: {e}")
        return 0.0
