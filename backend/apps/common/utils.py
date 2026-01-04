import mimetypes
import os
import subprocess

from django.conf import settings


def convert_media_for_whatsapp(media_path: str) -> str:
    full_path = media_path

    if media_path.startswith(settings.MEDIA_URL):
        relative_path = media_path[len(settings.MEDIA_URL) :]
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    elif not os.path.isabs(media_path):
        full_path = os.path.join(settings.MEDIA_ROOT, media_path)

    if not os.path.exists(full_path):
        return media_path

    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type and full_path.endswith('.webm'):
        mime_type = 'video/webm'

    if mime_type in ['video/webm', 'audio/webm']:
        directory = os.path.dirname(full_path)
        filename = os.path.splitext(os.path.basename(full_path))[0]
        output_filename = f'{filename}.ogg'
        output_path = os.path.join(directory, output_filename)

        try:
            command = ['ffmpeg', '-i', full_path, '-c:a', 'libopus', '-b:a', '32k', '-vn', '-y', output_path]

            subprocess.run(command, check=True, capture_output=True)

            if os.path.exists(output_path):
                if media_path.startswith(settings.MEDIA_URL):
                    rel_dir = os.path.dirname(relative_path)
                    new_rel_path = os.path.join(rel_dir, output_filename)
                    return os.path.join(settings.MEDIA_URL, new_rel_path)
                elif not os.path.isabs(media_path):
                    rel_dir = os.path.dirname(media_path)
                    return os.path.join(rel_dir, output_filename)
                else:
                    return output_path

        except subprocess.CalledProcessError:
            pass
        except Exception:
            pass

    return media_path


def get_media_duration(media_path: str) -> float:
    try:
        full_path = media_path

        if media_path.startswith(settings.MEDIA_URL):
            relative_path = media_path[len(settings.MEDIA_URL) :]
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        elif not os.path.isabs(media_path):
            full_path = os.path.join(settings.MEDIA_ROOT, media_path)

        if not os.path.exists(full_path):
            return 0.0

        command = [
            'ffprobe',
            '-v',
            'error',
            '-show_entries',
            'format=duration',
            '-of',
            'default=noprint_wrappers=1:nokey=1',
            full_path,
        ]

        result = subprocess.run(command, check=True, capture_output=True, text=True)

        duration = float(result.stdout.strip())
        return duration

    except Exception:
        return 0.0
