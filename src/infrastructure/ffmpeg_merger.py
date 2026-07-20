import subprocess
import os
from domain.exceptions import RemuxingException

class FFmpegMerger:
    """Tier 4: Lossless video/audio stream remuxer."""
    
    @staticmethod
    def merge(video_path: str, audio_path: str, output_path: str) -> str:
        """
        Merges video and audio streams using FFmpeg without re-encoding.
        """
        if not os.path.exists(video_path) or not os.path.exists(audio_path):
            raise RemuxingException("Video or audio file not found for merging")
            
        command = [
            'ffmpeg',
            '-y', # Overwrite output
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'copy',
            output_path
        ]
        
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            os.remove(video_path)
            os.remove(audio_path)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RemuxingException(f"FFmpeg remuxing failed: {e.stderr}")
        except FileNotFoundError:
             raise RemuxingException("FFmpeg not found in system PATH. Please install FFmpeg.")
