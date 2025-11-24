"""
Configuration management for the Meeting Summarizer application.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # General Settings
    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    APP_ENV = os.getenv("APP_ENV", "development")
    
    # Directories
    RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "recordings")
    DB_PATH = os.getenv("DB_PATH", "meetings.db")
    
    # Recording Settings
    AUTO_DETECTION = os.getenv("AUTO_DETECTION", "false").lower() == "true"
    VAD_THRESHOLD = float(os.getenv("VAD_THRESHOLD", "0.03"))
    SILENCE_DURATION = int(os.getenv("SILENCE_DURATION", "10"))
    MIN_RECORDING_DURATION = int(os.getenv("MIN_RECORDING_DURATION", "3"))
    
    # LLM Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "600"))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
    LLM_RETRY_DELAY = int(os.getenv("LLM_RETRY_DELAY", "2"))
    
    # File Upload Settings
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", ".wav,.m4a,.mp3,.flac,.ogg").split(",")
    
    # CORS Settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    if APP_ENV == "development":
        CORS_ORIGINS = ["*"]  # Allow all in development
    
    # Pagination
    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY not set. LLM features will not work.")
        
        # Create directories if they don't exist
        os.makedirs(cls.RECORDINGS_DIR, exist_ok=True)
        
        return True


# Validate configuration on import
Config.validate()
