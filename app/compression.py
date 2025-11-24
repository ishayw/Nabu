"""
Audio compression utilities for the Meeting Summarizer application.
Handles conversion of audio files to more efficient formats to save disk space.
"""

import os
from pydub import AudioSegment
from app.logger import get_logger
from app.settings import get_settings_manager

logger = get_logger(__name__)


def compress_audio_file(input_path: str, output_path: str = None, format: str = "mp3", bitrate: str = "128k") -> str:
    """
    Compress an audio file to a more efficient format.
    
    Args:
        input_path: Path to the input audio file
        output_path: Optional output path. If not provided, replaces input file
        format: Output format (default: mp3)
        bitrate: Output bitrate (default: 128k)
    
    Returns:
        Path to the compressed file
    """
    try:
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return input_path
        
        # Load audio file
        logger.info(f"Compressing {input_path}...")
        audio = AudioSegment.from_file(input_path)
        
        # Set output path
        if output_path is None:
            base, _ = os.path.splitext(input_path)
            output_path = f"{base}.{format}"
        
        # Export compressed version
        audio.export(
            output_path,
            format=format,
            bitrate=bitrate,
            parameters=["-q:a", "2"]  # Quality setting for MP3
        )
        
        # Get file sizes for logging
        original_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        reduction = ((original_size - compressed_size) / original_size) * 100
        
        logger.info(f"Compressed: {original_size:.2f}MB → {compressed_size:.2f}MB ({reduction:.1f}% reduction)")
        
        # Delete original if different path
        if output_path != input_path and os.path.exists(output_path):
            os.remove(input_path)
            logger.info(f"Deleted original file: {input_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Audio compression failed: {e}")
        return input_path  # Return original path if compression fails


def should_compress() -> bool:
    """Check if audio compression is enabled in settings."""
    try:
        settings_manager = get_settings_manager()
        compress_setting = settings_manager.get("compress_recordings")
        return compress_setting == "true"
    except:
        return True  # Default to true if settings not available
