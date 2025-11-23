import os
import subprocess
import json


def get_audio_duration(filepath: str) -> float:
    """
    Get the duration of an audio file in seconds.
    Supports M4A, WAV, MP3, and other formats.
    
    Uses multiple fallback methods:
    1. ffprobe (most reliable, supports all formats)
    2. pydub (if available)
    3. soundfile (for WAV files only)
    
    Args:
        filepath: Path to the audio file
        
    Returns:
        Duration in seconds, or 0.0 if unable to determine
    """
    if not os.path.exists(filepath):
        print(f"Audio file not found: {filepath}")
        return 0.0
    
    # Method 1: Try ffprobe (most reliable)
    duration = _get_duration_ffprobe(filepath)
    if duration > 0:
        return duration
    
    # Method 2: Try pydub
    duration = _get_duration_pydub(filepath)
    if duration > 0:
        return duration
    
    # Method 3: Try soundfile (WAV only)
    duration = _get_duration_soundfile(filepath)
    if duration > 0:
        return duration
    
    print(f"Warning: Could not determine duration for {filepath}")
    return 0.0


def _get_duration_ffprobe(filepath: str) -> float:
    """Get duration using ffprobe (from ffmpeg)."""
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                filepath
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            if duration > 0:
                print(f"Duration detected (ffprobe): {duration:.2f}s")
                return duration
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError) as e:
        # ffprobe not available or failed
        pass
    except Exception as e:
        print(f"ffprobe error: {e}")
    
    return 0.0


def _get_duration_pydub(filepath: str) -> float:
    """Get duration using pydub library."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(filepath)
        duration = len(audio) / 1000.0  # Convert milliseconds to seconds
        if duration > 0:
            print(f"Duration detected (pydub): {duration:.2f}s")
            return duration
    except ImportError:
        # pydub not installed
        pass
    except Exception as e:
        print(f"pydub error: {e}")
    
    return 0.0


def _get_duration_soundfile(filepath: str) -> float:
    """Get duration using soundfile library (WAV files only)."""
    try:
        import soundfile as sf
        with sf.SoundFile(filepath) as f:
            duration = len(f) / f.samplerate
            if duration > 0:
                print(f"Duration detected (soundfile): {duration:.2f}s")
                return duration
    except ImportError:
        # soundfile not installed
        pass
    except Exception as e:
        # Not a WAV file or other error
        pass
    
    return 0.0
